#!/usr/bin/env python3
"""Simple threaded HTTP server for serving the topology app."""
import http.server
import socketserver
import os
import io
import gzip
import json
import glob
import re
import subprocess
import queue
import threading
import uuid
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List, Optional

PORT = int(os.environ.get('TOPOLOGY_PORT', 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BUG_EVIDENCE_DIR = os.path.expanduser("~/SCALER/FLOWSPEC_VPN/bug_evidence")
DISCOVERY_API = "http://localhost:8765"
SCALER_BRIDGE_API = "http://localhost:8766"
XRAY_SCALER_DEVICES_FILE = os.environ.get(
    "XRAY_SCALER_DEVICES_FILE", "/home/dn/SCALER/db/devices.json"
)

# External health-monitor state directory (written by topology/health_monitor.py
# under a systemd --user timer). serve.py only reads from it to expose the
# latest probe summary at GET /api/monitor/health for the admin/debug UI.
HEALTH_MONITOR_DIR = os.environ.get(
    "TOPOLOGY_HEALTH_DIR", "/home/dn/.topology_health"
)

# XRAY config layout:
#   Global / legacy single-user:    ~/.xray_config.json
#   Per-user (multiuser enabled):   ~/.topology_users/<user>/xray.json
#   Per-user capture pcaps:         ~/.topology_users/<user>/captures/
#
# Each XRAY_CAPTURES entry stores _owner = username so non-admin users can
# only see / stop / download captures they themselves started.
XRAY_CONFIG_PATH = os.environ.get(
    "XRAY_GLOBAL_CONFIG", os.path.expanduser("~/.xray_config.json")
)
TOPOLOGY_USERS_BASE = os.environ.get(
    "TOPOLOGY_USERS_BASE", os.path.expanduser("~/.topology_users")
)
XRAY_GLOBAL_CAPTURES_DIR = os.environ.get(
    "XRAY_GLOBAL_CAPTURES_DIR", os.path.expanduser("~/.xray_captures/global")
)
XRAY_CAPTURES = {}  # capture_id -> { process, status, output_lines, pcap_path, error, _owner }
_YAREL_PCAP_RETAIN_USERS = {"yarel", "yor", "yarel-or", "yarelor"}
_XRAY_EPHEMERAL_CLEANUP_SECONDS = 10 * 60

# Mac-delivery sub-step order. Later indices win, so a stale "mac_verified"
# never overwrites a fresher "opening_wireshark" if log lines arrive
# out-of-order (which can happen because we read one stdout line at a time
# but the helper writes through three SSH/SFTP channels in parallel).
_XRAY_DELIVERY_STEP_ORDER = (
    "queued",
    "sftp_connecting",
    "mac_verified",
    "sftp_done",
    "opening_wireshark",
    "opened",
    "failed",
)


def _xray_promote_step(entry, new_step):
    """Advance entry['mac_delivery_step'] to new_step iff it strictly progresses.

    `failed` always wins so a late SFTP-failed marker still overrides an
    in-flight 'opening_wireshark' step on the way down.
    """
    cur = entry.get("mac_delivery_step") or "queued"
    if new_step == "failed":
        entry["mac_delivery_step"] = "failed"
        return
    try:
        cur_idx = _XRAY_DELIVERY_STEP_ORDER.index(cur)
    except ValueError:
        cur_idx = 0
    try:
        new_idx = _XRAY_DELIVERY_STEP_ORDER.index(new_step)
    except ValueError:
        return
    if new_idx > cur_idx:
        entry["mac_delivery_step"] = new_step


def should_retain_pcap(username):
    """Only Yarel's account may keep server-side XRAY pcaps after delivery."""
    normalized = (username or "").strip().lower().replace("_", "-")
    return normalized in _YAREL_PCAP_RETAIN_USERS

# -------------------------------------------------------------------------
# AI assistant module (soft import).
#
# The ai/ module implements the LLM client, knowledge digest loader and
# live per-user context builder. It is only used by the three AI routes
# registered below -- if the module is missing or fails to import, the
# rest of serve.py still starts and those three routes return a clean
# 503 "AI assistant not available" response.
# -------------------------------------------------------------------------
try:
    import ai as _ai_module
    _ai_available = True
    _ai_import_error = None
except Exception as _e:  # pragma: no cover -- diagnostic only
    _ai_module = None
    _ai_available = False
    _ai_import_error = str(_e)
    print(f"[STARTUP] AI assistant module not available: {_e}")


def _ensure_ai_module():
    """Self-healing wrapper around the ``ai`` module import.

    The ``_ai_available`` flag is set once at serve.py import time. If
    the import failed then -- maybe because a file in ``ai/`` was mid-
    rewrite, a venv dependency wasn't ready yet, or any other transient
    startup glitch -- the flag stays ``False`` for the entire lifetime
    of the process, and every ``/api/ai/chat`` call returns a stale 503
    even after the filesystem is repaired. Reported 2026-04-24h: a
    34-hour-old serve.py process kept returning 503 "AI assistant
    module unavailable" despite a one-line ``python3 -c 'import ai'``
    succeeding cleanly in a fresh process.

    Rather than requiring a manual server restart every time this
    happens, AI route handlers now call this helper before the
    availability check. If the flag is already True we short-circuit
    (no per-request import cost). If it's False we try to re-import;
    a success flips the module-level flag and the route proceeds as if
    nothing went wrong. A fresh failure refreshes
    ``_ai_import_error`` so the 503 body names today's cause, not a
    stale one.
    """
    global _ai_module, _ai_available, _ai_import_error
    if _ai_available and _ai_module is not None:
        return True
    try:
        import importlib
        if _ai_module is not None:
            # Reload in case the first import half-succeeded (module
            # object exists but some submodule failed). Fresh reload
            # is idempotent on healthy modules.
            _ai_module = importlib.reload(_ai_module)
        else:
            _ai_module = importlib.import_module("ai")
        _ai_available = True
        _ai_import_error = None
        try:
            print("[RUNTIME] AI assistant module re-import succeeded; "
                  "recovering from stale _ai_available=False state")
        except Exception:
            pass
        return True
    except Exception as exc:
        _ai_available = False
        _ai_import_error = str(exc)
        return False

# Custom sections (legacy DNAAS save target).
#
# Layout:
#   Legacy global (pre-multiuser):       ~/.topology_sections/
#                                            _sections.json
#                                            <section_id>/<topo>.json
#   Per-user (multiuser, current):       ~/.topology_users/<user>/sections/
#                                            _sections.json
#                                            <section_id>/<topo>.json
#
# All `/api/sections/*` endpoints already require auth (`_require_auth`),
# so we always have a username to scope by. The legacy global directory is
# auto-migrated into the founder's per-user dir on first read so the
# original user does not lose their existing DNAAS topologies, and every
# other user starts with their own empty workspace (no cross-user leakage).
CUSTOM_SECTIONS_LEGACY_DIR = os.path.expanduser("~/.topology_sections")
CUSTOM_SECTIONS_LEGACY_CONFIG = os.path.join(CUSTOM_SECTIONS_LEGACY_DIR, "_sections.json")
# Inheritor for the historical global ~/.topology_sections directory.
# Pre-username-migration this was "yarel"; post-migration the same human
# logs in as "yor" (their @drivenets.com email local part). We accept
# *both* by default so the legacy section migration still fires
# regardless of which DB row first reaches this code path. Operators can
# pin it to a single username via the LEGACY_SECTIONS_OWNER env var.
_LEGACY_SECTIONS_OWNERS_DEFAULT = ("yor", "yarel")
_legacy_owners_env = (os.environ.get("LEGACY_SECTIONS_OWNER") or "").strip()
LEGACY_SECTIONS_OWNERS = (
    tuple(u.strip() for u in _legacy_owners_env.split(",") if u.strip())
    if _legacy_owners_env
    else _LEGACY_SECTIONS_OWNERS_DEFAULT
)
LEGACY_SECTIONS_OWNER = LEGACY_SECTIONS_OWNERS[0]  # back-compat alias for old refs
_legacy_sections_migrated = False  # process-wide one-shot guard

# Built-in (undeletable) sections injected for every user.
#
# These appear in every user's "Topology Domains" list. They cannot be
# deleted or renamed (only icon/color tweaks survive an update call).
# `__bugs` is the home for bug-replica topologies created by the
# "Create Bug Topology" feature; one per Jira SW-XXXXX ticket.
# `__ai` was historically the home for topologies generated by the in-
# app AI assistant. The assistant no longer auto-saves there -- new
# generations prompt the user to pick (or create) a destination domain
# via the placement card in topology-ai.js. We keep the `__ai` builtin
# injected so users who ALREADY have topologies under it keep seeing
# them in their dropdown; a future migration could move them out and
# retire the builtin entirely.
BUILTIN_SECTIONS = [
    {
        "id": "__bugs",
        "name": "Bugs",
        "icon": "bug",
        "color": "#e74c3c",
        "builtin": True,
        "description": "Bug-replica topologies (one per Jira SW-XXXXX). Built-in, cannot be deleted.",
    },
    {
        "id": "__ai",
        "name": "AI",
        "icon": "sparkles",
        "color": "#8e5cff",
        "builtin": True,
        "description": (
            "Legacy home for AI-generated topologies. New generations are placed "
            "by the user into a chosen domain instead. Built-in, cannot be deleted."
        ),
    },
    {
        "id": "__dnaas",
        "name": "DNAAS",
        "icon": "network",
        "color": "#FF5E1F",
        "builtin": True,
        "description": (
            "DNAAS discovery/import topologies. Built-in domain; topologies "
            "inside it can still be deleted normally."
        ),
    },
]
BUILTIN_SECTION_IDS = {s["id"] for s in BUILTIN_SECTIONS}
DOMAIN_TOPOLOGY_LIMIT = 15

# Issue types we consider "bug-like" for the Create Bug Topology flow.
# Anything else (Story, Epic, Task, Sub-task, Improvement, ...) is rejected
# unless the user explicitly forces a placeholder via force_placeholder=true.
# Match is case-insensitive on the issuetype.name field. We also accept any
# name containing the substring "bug" or "defect" to handle custom workflows
# (e.g. "Production Bug", "Sub-Bug", "Customer Defect").
BUG_LIKE_ISSUE_TYPES = {
    "bug",
    "defect",
    "sub-bug",
    "production bug",
    "customer issue",
    "incident",
}


def _user_xray_dir(username):
    """~/.topology_users/<username>/ if username is set and not the default sentinel."""
    if not username or username in ("default", "unknown"):
        return None
    try:
        store = _mirror_user_store()
        if store:
            return str(store.ensure_user_workspace(username))
    except Exception:
        pass
    return os.path.join(TOPOLOGY_USERS_BASE, username)


def _ensure_user_workspace(username):
    """Create ~/.topology_users/<username>/captures/ on first use. Returns the user dir."""
    user_dir = _user_xray_dir(username)
    if not user_dir:
        return None
    try:
        os.makedirs(os.path.join(user_dir, "captures"), exist_ok=True)
    except OSError:
        pass
    return user_dir


def _user_xray_config_path(username):
    """Per-user XRAY config path, or global path when no user is logged in."""
    if username and username not in ("default", "unknown"):
        try:
            store = _mirror_user_store()
            if store:
                store.ensure_user_workspace(username)
                return str(store.user_xray_config_path(username))
        except Exception:
            pass
    user_dir = _user_xray_dir(username)
    if user_dir:
        _ensure_user_workspace(username)
        return os.path.join(user_dir, "xray.json")
    return XRAY_CONFIG_PATH


def _user_captures_dir(username):
    """Per-user captures directory, falling back to a shared global dir."""
    if username and username not in ("default", "unknown"):
        try:
            store = _mirror_user_store()
            if store:
                return str(store.user_captures_dir(username))
        except Exception:
            pass
    user_dir = _user_xray_dir(username)
    if user_dir:
        path = os.path.join(_ensure_user_workspace(username), "captures")
    else:
        path = XRAY_GLOBAL_CAPTURES_DIR
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    return path


def _xray_entry_pcap_paths(entry):
    """Return server-side pcap files owned by one XRAY capture entry only."""
    if not isinstance(entry, dict):
        return []
    owner = entry.get("_owner") or ""
    allowed_dirs = []
    try:
        allowed_dirs.append(os.path.realpath(_user_captures_dir(owner)))
    except Exception:
        pass
    try:
        allowed_dirs.append(os.path.realpath(XRAY_GLOBAL_CAPTURES_DIR))
    except Exception:
        pass
    target = entry.get("_target_pcap") or ""
    target_real = os.path.realpath(target) if target else ""
    out = []
    for raw in (entry.get("pcap_path"), entry.get("local_pcap_path"), target):
        if not raw:
            continue
        real = os.path.realpath(str(raw))
        if not os.path.isfile(real):
            continue
        if not any(real.startswith(d + os.sep) for d in allowed_dirs if d):
            continue
        if real not in out:
            out.append(real)
    return out


def _xray_cleanup_capture_pcaps(entry, reason):
    """Best-effort cleanup for ephemeral non-Yarel capture files."""
    removed = []
    for pcap_path in _xray_entry_pcap_paths(entry):
        try:
            os.remove(pcap_path)
            removed.append(pcap_path)
        except FileNotFoundError:
            removed.append(pcap_path)
        except OSError:
            continue
    if removed:
        removed_set = {os.path.realpath(p) for p in removed}
        for key in ("pcap_path", "local_pcap_path"):
            value = entry.get(key)
            if value and os.path.realpath(str(value)) in removed_set:
                entry[key] = None
        entry["server_pcap_cleaned"] = True
        entry["pcap_cleanup_reason"] = reason
    return removed


def _xray_schedule_ephemeral_cleanup(entry, reason, delay=_XRAY_EPHEMERAL_CLEANUP_SECONDS):
    """Schedule bounded retention for non-Yarel pcaps awaiting user download."""
    if not isinstance(entry, dict) or should_retain_pcap(entry.get("_owner")):
        return
    entry["_pcap_ephemeral"] = True
    entry["_pcap_cleanup_reason"] = reason
    entry["_pcap_cleanup_deadline"] = time.time() + max(1, int(delay))
    timer = entry.get("_pcap_cleanup_timer")
    try:
        if timer:
            timer.cancel()
    except Exception:
        pass

    def _cleanup():
        _xray_cleanup_capture_pcaps(entry, reason)

    timer = threading.Timer(max(1, int(delay)), _cleanup)
    timer.daemon = True
    entry["_pcap_cleanup_timer"] = timer
    timer.start()


def _jwt_payload(auth_header):
    """Decode JWT payload (sub, role) without verification. Auth-bearing routes
    in scaler_bridge already verify the signature; this helper is only used
    here to scope per-user state."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    import base64
    try:
        parts = auth_header[7:].split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None

_GZIP_TYPES = {
    'text/html', 'text/css', 'text/javascript', 'application/javascript',
    'application/json', 'text/plain', 'image/svg+xml', 'application/xml',
}
_GZIP_MIN_SIZE = 256
_STATIC_CACHE_SECS = 86400 * 7  # 7 days for versioned assets
_BACKUP_PREFIXES = ('topology_WORKING_BACKUP_', 'bundle.js')

# In-memory cache for gzipped static files:
# {filepath: (mtime_ns, file_size, raw_bytes, gzipped_bytes)}
_gz_cache = {}
_gz_cache_lock = threading.Lock()

# Shared state for service monitor (updated by monitor thread, read by Handler and __main__)
_child_procs = {"discovery": None, "bridge": None}
_child_start_times = {"discovery": 0.0, "bridge": 0.0}
_discovery_file_mtime = 0.0
_health_fail_count = {"discovery": 0, "bridge": 0}
_restart_timestamps = []  # (timestamp, service_name) for crash-loop detection
_monitor_lock = threading.Lock()

def _extract_jwt_username(auth_header):
    """Extract username from JWT payload (for proxy tagging / scope keys)."""
    payload = _jwt_payload(auth_header)
    return payload.get("sub") if payload else None


def _extract_jwt_role(auth_header):
    """Extract role claim from JWT payload (for admin gates on /api/xray/*)."""
    payload = _jwt_payload(auth_header)
    return payload.get("role") if payload else None


# ---------------------------------------------------------------------------
# Deployment owner / admin / announcement infrastructure (2026-04-22)
# ---------------------------------------------------------------------------
# The user dropdown now exposes admin-tier and owner-tier menu items that
# hit the endpoints defined later in this file. To keep the dependency
# footprint small (this module uses the stdlib `BaseHTTPRequestHandler`,
# not FastAPI), we redo the minimal role gating inline: JWT payload is
# already decoded per-request, so we just need to know (a) whether the
# caller is an admin, and (b) whether the caller is the deployment
# owner. Owner detection mirrors `api/auth/service.py::is_owner_user`.
#
# Three in-memory stores live here:
#   _ADMIN_AUDIT_RING   -- last 200 events (login / ai-config change / etc.)
#   _ANNOUNCEMENTS      -- last 10 broadcast toasts (polled by every client)
#   _FEATURE_FLAGS_PATH -- disk-backed feature-flag JSON
_OWNER_CANONICAL_USERNAMES = {"yor", "yarel", "yarel-or", "yarelor"}
_OWNER_DISPLAY_NAME = "yarel or"

_ADMIN_AUDIT_RING = []
_ADMIN_AUDIT_LOCK = threading.Lock()
_ADMIN_AUDIT_MAX = 200

_ANNOUNCEMENTS = []
_ANNOUNCEMENTS_LOCK = threading.Lock()
_ANNOUNCEMENTS_MAX = 10

_FEATURE_FLAGS_PATH = os.environ.get(
    "FEATURE_FLAGS_PATH",
    os.path.expanduser("~/.topology_feature_flags.json"),
)
_FEATURE_FLAGS_LOCK = threading.Lock()
_FEATURE_FLAGS_DEFAULTS = {
    # UI feature toggles. Safe defaults (off for experiments).
    "ai_generate_showcase": True,   # flashy AI topology reveal animation
    "link_overlap_rims":    True,   # dark rim on overlapping same-color links
    "keyboard_nav_menu":    True,   # Arrow key navigation in user dropdown
    "cloud_avatar_sparkle": False,  # sparkle ring on header avatar (opt-in)
    "experimental_dnaas":   False,  # DNAAS wizards behind a flag
}


def _is_owner_user(username, display_name=""):
    """Lightweight mirror of api/auth/service.is_owner_user, for the HTTP
    handler (serve.py) which doesn't depend on FastAPI.

    Falls back to (username == 'default') when the request carries no JWT,
    since single-user mode treats the default user as the operator.
    """
    u = (username or "").strip().lower()
    d = (display_name or "").strip().lower()
    env_owner = (os.environ.get("OWNER_USERNAME") or "").strip().lower()
    if u == "default":
        return True
    if env_owner and u == env_owner:
        return True
    if u in _OWNER_CANONICAL_USERNAMES:
        return True
    if d == _OWNER_DISPLAY_NAME:
        return True
    return False


def _record_audit(event, username=None, detail=None):
    """Append an event to the admin audit ring buffer.

    event  -- short verb, e.g. "login", "ai_config_saved", "broadcast_sent"
    detail -- free-form dict with per-event context

    Silently no-ops on any failure so audit recording never blocks a request.
    """
    try:
        entry = {
            "ts": time.time(),
            "event": str(event)[:64],
            "username": (username or "unknown")[:64],
            "detail": detail if isinstance(detail, dict) else ({"note": str(detail)[:200]} if detail else {}),
        }
        with _ADMIN_AUDIT_LOCK:
            _ADMIN_AUDIT_RING.append(entry)
            # Cap the ring so long-running processes don't leak memory.
            if len(_ADMIN_AUDIT_RING) > _ADMIN_AUDIT_MAX:
                del _ADMIN_AUDIT_RING[: len(_ADMIN_AUDIT_RING) - _ADMIN_AUDIT_MAX]
    except Exception:
        pass


def _load_feature_flags():
    """Return feature-flags dict merged with defaults. Disk-backed."""
    flags = dict(_FEATURE_FLAGS_DEFAULTS)
    try:
        with _FEATURE_FLAGS_LOCK:
            if os.path.exists(_FEATURE_FLAGS_PATH):
                with open(_FEATURE_FLAGS_PATH, "r", encoding="utf-8") as f:
                    on_disk = json.load(f) or {}
                if isinstance(on_disk, dict):
                    flags.update({k: bool(v) for k, v in on_disk.items() if k in _FEATURE_FLAGS_DEFAULTS or isinstance(v, bool)})
    except Exception:
        pass
    return flags


def _save_feature_flags(flags):
    """Persist feature-flags dict. Returns True on success."""
    if not isinstance(flags, dict):
        return False
    try:
        with _FEATURE_FLAGS_LOCK:
            with open(_FEATURE_FLAGS_PATH, "w", encoding="utf-8") as f:
                json.dump(flags, f, indent=2, sort_keys=True)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Legacy <-> multi-user mirror helpers
# ---------------------------------------------------------------------------
# When a user shares a topology that lived only in the legacy /api/sections
# tree, the frontend migration helper (topology-file-ops.js
# _ensureLegacyTopologyMigrated) POSTs a mapping to
# /api/sections/<sid>/_mirror-register so subsequent owner saves / renames /
# deletes can be mirrored into the multi-user DB and shared recipients see
# every change without a second round-trip.
#
# Mapping layout, per user, per section:
#   ~/.topology_users/<user>/sections/_multiuser_mirror__<sid>.json
#   {
#     "<filename.json>": { "domain_id": "<uuid>", "topology_id": "<uuid>" },
#     ...
#   }
#
# The file is best-effort: a missing / corrupt mapping silently falls back to
# "legacy-only" behaviour (no mirror), which preserves the original UX for
# files that were never shared.
def _mirror_map_path(username, section_id):
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(section_id))
    return os.path.join(
        TOPOLOGY_USERS_BASE, username, "sections",
        f"_multiuser_mirror__{safe}.json",
    )


def _mirror_read_all(username, section_id):
    p = _mirror_map_path(username, section_id)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _mirror_write_all(username, section_id, data):
    p = _mirror_map_path(username, section_id)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump(data or {}, f, indent=2)
    except Exception:
        pass


def _mirror_get(username, section_id, filename):
    return _mirror_read_all(username, section_id).get(filename)


def _mirror_set(username, section_id, filename, domain_id, topology_id):
    data = _mirror_read_all(username, section_id)
    data[filename] = {"domain_id": domain_id, "topology_id": topology_id}
    _mirror_write_all(username, section_id, data)


def _mirror_clear(username, section_id, filename):
    data = _mirror_read_all(username, section_id)
    if filename in data:
        data.pop(filename, None)
        _mirror_write_all(username, section_id, data)


def _mirror_clear_section(username, section_id):
    p = _mirror_map_path(username, section_id)
    try:
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass


def _mirror_user_store():
    """Lazy import so serve.py stays importable if the api package fails to
    load (e.g. during early bootstrap or in a reduced test environment).
    Returns None when the multi-user layer is unavailable."""
    try:
        from api.auth.user_store import user_store
        return user_store
    except Exception:
        try:
            from topology.api.auth.user_store import user_store  # type: ignore
            return user_store
        except Exception:
            return None


_STALE_SAVE_SKEW_SECONDS = 5


def _iso_from_epoch(ts):
    """UTC ISO timestamp for stale-save debug payloads."""
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return ""


def _epoch_from_iso(value):
    """Parse an ISO-8601 timestamp from user_store into epoch seconds."""
    if not value:
        return None
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc).timestamp() if dt.tzinfo is None else dt.timestamp()
    except Exception:
        return None


def _stale_save_conflict_payload(user, sid, filename, mapping, meta, disk_mtime, db_ts, reason):
    """Build the debug payload returned with legacy section-save 409s.

    Keep this free of absolute filesystem paths. Operators need timestamp
    math, share counts and last-writer identity; they do not need server path
    internals in a browser response.
    """
    share_info = {
        "topology_share_count": int((meta or {}).get("topology_share_count") or 0),
        "topology_write_share_count": int((meta or {}).get("topology_write_share_count") or 0),
        "domain_share_count": int((meta or {}).get("domain_share_count") or 0),
        "domain_write_share_count": int((meta or {}).get("domain_write_share_count") or 0),
        "share_recipient_count": int((meta or {}).get("share_recipient_count") or 0),
        "write_share_recipient_count": int((meta or {}).get("write_share_recipient_count") or 0),
    }
    last_writer = {
        "username": (meta or {}).get("last_actor") or "",
        "display_name": (meta or {}).get("last_actor_display_name") or (
            (meta or {}).get("last_actor") or ""
        ),
        "event_type": (meta or {}).get("last_event_type") or "",
        "event_summary": (meta or {}).get("last_event_summary") or "",
        "event_at": (meta or {}).get("last_event_at") or "",
    }
    return {
        "reason": reason,
        "section_id": sid,
        "filename": filename,
        "owner": user,
        "domain_id": (mapping or {}).get("domain_id"),
        "topology_id": (mapping or {}).get("topology_id"),
        "disk_mtime_epoch": float(disk_mtime) if disk_mtime is not None else None,
        "disk_mtime": _iso_from_epoch(disk_mtime) if disk_mtime is not None else "",
        "db_updated_at": (meta or {}).get("updated_at") or "",
        "db_updated_at_epoch": float(db_ts) if db_ts is not None else None,
        "delta_seconds": (
            round(float(db_ts) - float(disk_mtime), 3)
            if db_ts is not None and disk_mtime is not None else None
        ),
        "threshold_seconds": _STALE_SAVE_SKEW_SECONDS,
        "shares": share_info,
        "last_writer": last_writer,
    }


# Lazy-initialised ConversationStore singleton. We keep it module-level
# so every request reuses the same object (the store itself is stateless
# -- each call opens/closes its own sqlite3 connection -- so concurrent
# requests don't race). Initialisation is delayed until first use so a
# broken ai.conversation_store module doesn't prevent serve.py from
# booting (AI is optional; the rest of the app must still start).
_ai_conv_store = None
_ai_conv_store_lock = threading.Lock()


def _conversation_store():
    """Return the shared ConversationStore, or None on import error."""
    global _ai_conv_store
    if _ai_conv_store is not None:
        return _ai_conv_store
    with _ai_conv_store_lock:
        if _ai_conv_store is not None:
            return _ai_conv_store
        try:
            from ai.conversation_store import ConversationStore
            from api.config import settings
            _ai_conv_store = ConversationStore(settings.users_base_dir)
        except Exception as exc:
            try:
                print(f"[ai] conversation_store unavailable: {exc}")
            except Exception:
                pass
            _ai_conv_store = None
    return _ai_conv_store


# ---------------------------------------------------------------------------
# SSE (Server-Sent Events) pub-sub for live topology change notifications.
#
# When an owner's legacy save (/api/sections/<sid>/save) mirrors into the
# multi-user DB, we broadcast a `topology-updated` event to every recipient
# of that shared topology who currently has an EventSource connection open.
# Clients respond by re-fetching the domain list so the dropdown picks up
# the new content without a page reload.
#
# Keyed by `username`. A single user can have multiple queues (one per open
# browser tab). `queue.Queue.put_nowait` means if a client's queue is full
# (stuck tab?) we drop the event rather than block the publisher -- the
# client will self-heal on reconnect or the next save.
_sse_lock = threading.Lock()
_sse_subscribers = {}  # Dict[str, List[queue.Queue]]


def _sse_subscribe(username):
    q = queue.Queue(maxsize=64)
    with _sse_lock:
        _sse_subscribers.setdefault(username, []).append(q)
    return q


def _sse_unsubscribe(username, q):
    with _sse_lock:
        lst = _sse_subscribers.get(username, [])
        try:
            lst.remove(q)
        except ValueError:
            pass
        if not lst and username in _sse_subscribers:
            _sse_subscribers.pop(username, None)


def _sse_publish(usernames, event):
    """Fan-out `event` (dict) to every queue subscribed under any of
    `usernames`. Duplicates in the list are de-duped with a set()."""
    if not usernames:
        return
    with _sse_lock:
        for u in set(usernames):
            for q in list(_sse_subscribers.get(u, [])):
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass


def _sse_publish_all(event):
    """Fan-out `event` to every active SSE subscriber regardless of user.

    Used for service-wide signals like graceful-restart announcements
    where every open browser tab needs the heads-up. Same drop-on-full
    semantics as `_sse_publish`.
    """
    with _sse_lock:
        for queues in list(_sse_subscribers.values()):
            for q in list(queues):
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass


# Most-recent intentional restart announcement. Set by
# POST /api/monitor/announce-restart before the supervisor takes the
# process down so reconnecting clients can recognise that the dropped
# connection was expected (and skip the red "ConnectionRefused" cascade).
_RESTART_ANNOUNCE_LOCK = threading.Lock()
_RESTART_ANNOUNCE = {
    "announced_at": 0.0,    # epoch seconds
    "reason": None,
    "eta_seconds": 0,
    "source": None,
}


def _sse_publish_mirror_event(owner, mapping, kind, extra=None):
    """Send a `topology-updated` event to the owner + every recipient of
    the topology identified by `mapping`. Safe to call with a None mapping
    (no-op). Extra fields (e.g. {"new_name": "foo"}) are merged in."""
    if not mapping or not owner:
        return
    store = _mirror_user_store()
    targets = [owner]
    if store is not None:
        try:
            targets += store.list_topology_recipients(
                owner, mapping.get("domain_id"), mapping.get("topology_id"),
            )
        except Exception as exc:
            print(f"[sse] list_topology_recipients failed: {exc}")
    payload = {
        "kind": kind,
        "owner": owner,
        "domain_id": mapping.get("domain_id"),
        "topology_id": mapping.get("topology_id"),
        "at": time.time(),
    }
    if isinstance(extra, dict):
        payload.update(extra)
    _sse_publish(targets, payload)


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if not hasattr(self, '_cache_set'):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

    def _set_cache_headers(self, path_str):
        """Set smart cache headers: long cache for versioned static assets, no-cache for API."""
        if '?v=' in self.path or '?v=' in path_str:
            self.send_header('Cache-Control', 'public, max-age=60')
            self._cache_set = True
        elif path_str.endswith(('.js', '.css', '.woff2', '.woff', '.ttf')):
            self.send_header('Cache-Control', 'public, max-age=60')
            self._cache_set = True

    def _accepts_gzip(self):
        return 'gzip' in self.headers.get('Accept-Encoding', '')

    def _gzip_bytes(self, data):
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as gz:
            gz.write(data)
        return buf.getvalue()

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        if self._accepts_gzip() and len(body) >= _GZIP_MIN_SIZE:
            body = self._gzip_bytes(body)
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_mcp_oauth_metadata(self):
        """Return JSON for Cursor's OAuth discovery probe.

        The Topology MCP uses pre-issued per-user bearer tokens, not an OAuth
        flow. Some MCP clients still probe the well-known resource metadata URL
        before using configured headers; returning JSON here avoids falling back
        to SimpleHTTPRequestHandler's HTML 404, which those clients reject.
        """
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or f"127.0.0.1:{PORT}"
        scheme = self.headers.get("X-Forwarded-Proto") or "http"
        base = f"{scheme}://{host}".rstrip("/")
        return self._send_json({
            "resource": f"{base}/mcp",
            "resource_name": "DriveNets Topology MCP",
            "authorization_servers": [],
            "bearer_methods_supported": ["header"],
            "scopes_supported": [],
        })

    def do_GET(self):
        """Override to add gzip and smart caching for static file serving."""
        path = self.path.split("?")[0]

        # WebSocket upgrade passthrough for bridge-backed endpoints.
        # Must fire BEFORE the regular dispatch below -- a WS upgrade
        # is still a GET on the wire but we hijack the socket, so the
        # normal request/response flow never completes.
        #
        # The paths below are the WS surface exposed by scaler_bridge:
        #   /api/events/ws          device-event bus (routes/events.py)
        #   /api/terminal/ws        in-browser SSH/virsh console (routes/ssh.py)
        #   /ws/progress/<job_id>   push-progress stream (api/main.py)
        if self._is_websocket_upgrade() and (
            path == "/api/events/ws"
            or path == "/api/terminal/ws"
            or path.startswith("/ws/progress/")
        ):
            return self._proxy_websocket("127.0.0.1", 8766)

        # Block serving backup files
        basename = os.path.basename(path)
        if any(basename.startswith(p) for p in _BACKUP_PREFIXES):
            self._send_json({"detail": "Backup files are not served"}, 403)
            return

        if path.startswith("/.well-known/oauth-protected-resource") or path.startswith("/mcp/.well-known/oauth-protected-resource"):
            return self._handle_mcp_oauth_metadata()

        # Let API routes through (proxied responses handle their own encoding)
        if path.startswith("/api/") or path.startswith("/mcp/") or path.startswith("/debug-dnos-"):
            return self._do_GET_api_routes()

        # Static file serving with gzip
        return self._serve_static_gzipped()

    def do_HEAD(self):
        """HEAD returns same headers as GET but no body."""
        path = self.path.split("?")[0]
        basename = os.path.basename(path)
        if any(basename.startswith(p) for p in _BACKUP_PREFIXES):
            self.send_response(403)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if path.startswith("/api/") or path.startswith("/debug-dnos-"):
            return super().do_HEAD()
        fpath = self.translate_path(self.path)
        if os.path.isdir(fpath):
            for idx in ("index.html", "index.htm"):
                if os.path.exists(os.path.join(fpath, idx)):
                    fpath = os.path.join(fpath, idx)
                    break
        if not os.path.isfile(fpath):
            self.send_error(404, "File not found")
            return
        raw_size = os.path.getsize(fpath)
        ctype = self.guess_type(fpath)
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self._set_cache_headers(self.path)
        base_ctype = ctype.split(';')[0].strip()
        if self._accepts_gzip() and base_ctype in _GZIP_TYPES and raw_size >= _GZIP_MIN_SIZE:
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(raw_size))
        self.end_headers()

    def _serve_static_gzipped(self):
        """Serve static files with gzip compression and in-memory cache."""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            for index in ("index.html", "index.htm"):
                idx = os.path.join(path, index)
                if os.path.exists(idx):
                    path = idx
                    break

        if not os.path.isfile(path):
            self.send_error(404, "File not found")
            return

        ctype = self.guess_type(path)
        base_ctype = ctype.split(';')[0].strip()
        can_gzip = base_ctype in _GZIP_TYPES
        want_gzip = self._accepts_gzip() and can_gzip

        try:
            stat = os.stat(path)
            mtime_ns = getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000))
            file_size = stat.st_size
        except OSError:
            self.send_error(404, "File not found")
            return

        # Check in-memory cache. Use nanosecond mtime + size so rapid
        # agent edits cannot leave a same-second stale JS/CSS response in
        # memory while index.html points at a new cache-buster URL.
        cached = _gz_cache.get(path)
        if cached and cached[0] == mtime_ns and cached[1] == file_size:
            raw_bytes, gz_bytes = cached[2], cached[3]
        else:
            try:
                with open(path, 'rb') as f:
                    raw_bytes = f.read()
            except OSError:
                self.send_error(404, "File not found")
                return
            if can_gzip and len(raw_bytes) >= _GZIP_MIN_SIZE:
                gz_bytes = self._gzip_bytes(raw_bytes)
            else:
                gz_bytes = None
            with _gz_cache_lock:
                _gz_cache[path] = (mtime_ns, len(raw_bytes), raw_bytes, gz_bytes)

        body = gz_bytes if (want_gzip and gz_bytes) else raw_bytes

        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self._set_cache_headers(self.path)
        if want_gzip and gz_bytes:
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_monitor_health(self):
        """Return the latest snapshot written by topology/health_monitor.py.

        Read-only. The external monitor (run via systemd --user timer)
        owns ``$TOPOLOGY_HEALTH_DIR`` and writes ``status.json`` after
        every probe cycle. This endpoint returns 200 with the snapshot
        when fresh, 503 with a stub when no snapshot exists yet, and
        flags ``stale = True`` when the snapshot is older than a few
        timer intervals so the UI can warn that the monitor itself
        stopped running.
        """
        status_path = os.path.join(HEALTH_MONITOR_DIR, "status.json")
        failures_path = os.path.join(HEALTH_MONITOR_DIR, "failures.json")
        try:
            with open(status_path, "r", encoding="utf-8") as fh:
                snapshot = json.load(fh)
        except FileNotFoundError:
            return self._send_json({
                "status": "no_data",
                "monitor_dir": HEALTH_MONITOR_DIR,
                "detail": "no monitor snapshot yet -- timer may not be running",
                "expected_unit": "topology-health-monitor.timer",
            }, 503)
        except Exception as e:
            return self._send_json({
                "status": "error",
                "monitor_dir": HEALTH_MONITOR_DIR,
                "detail": f"failed to read snapshot: {e}",
            }, 500)
        try:
            mtime = os.path.getmtime(status_path)
        except Exception:
            mtime = 0.0
        age_s = max(0, int(time.time() - mtime)) if mtime else None
        # The default timer fires every 60s; treat anything older than
        # ~5 minutes as stale (monitor likely stopped).
        stale = (age_s is not None and age_s > 300)
        try:
            with open(failures_path, "r", encoding="utf-8") as fh:
                failures = json.load(fh)
        except Exception:
            failures = {}
        snapshot["snapshot_age_s"] = age_s
        snapshot["snapshot_path"] = status_path
        snapshot["stale"] = stale
        snapshot["restart_history"] = {
            "last_restart_at": failures.get("last_restart_at"),
            "recent_restarts": failures.get("recent_restarts", []),
        }
        with _RESTART_ANNOUNCE_LOCK:
            ann = dict(_RESTART_ANNOUNCE)
        ann_age = (time.time() - float(ann.get("announced_at") or 0.0)) if ann.get("announced_at") else None
        snapshot["restart_announce"] = {
            "announced_at": ann.get("announced_at") or None,
            "reason": ann.get("reason"),
            "eta_seconds": ann.get("eta_seconds") or 0,
            "source": ann.get("source"),
            "age_s": int(ann_age) if ann_age is not None else None,
            # `recent` is true for ~3 minutes after an announce so a
            # browser that reloaded mid-restart still sees we just came
            # back up and can skip the alarming reconnect noise.
            "recent": bool(ann_age is not None and ann_age < 180),
        }
        return self._send_json(snapshot)

    def _handle_announce_restart(self, raw_body=None):
        """Broadcast a graceful-restart heads-up to every live SSE client.

        Local-only (we check the peer is loopback) so any user on the
        host -- including the health monitor running under the same
        systemd user manager -- can call it without juggling JWTs, but
        no remote browser can spam announcements. The payload is
        opaque; the frontend's graceful-restart coordinator decides
        what to render.

        ``raw_body`` is forwarded from ``do_POST`` which already drained
        the request body. We MUST NOT read self.rfile again here -- a
        second read with no data left will block the worker.
        """
        peer = (self.client_address or ("",))[0]
        if peer not in ("127.0.0.1", "::1", "localhost"):
            return self._send_json({"detail": "loopback only"}, 403)
        try:
            if isinstance(raw_body, (bytes, bytearray)):
                body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            elif isinstance(raw_body, str):
                body = json.loads(raw_body) if raw_body else {}
            else:
                body = {}
            if not isinstance(body, dict):
                body = {}
        except Exception:
            body = {}
        reason = str(body.get("reason") or "manual restart")
        try:
            eta = int(body.get("eta_seconds") or 15)
        except Exception:
            eta = 15
        eta = max(2, min(120, eta))
        source = str(body.get("source") or "unknown")[:64]
        now = time.time()
        with _RESTART_ANNOUNCE_LOCK:
            _RESTART_ANNOUNCE.update({
                "announced_at": now,
                "reason": reason,
                "eta_seconds": eta,
                "source": source,
            })
        # Broadcast on the existing SSE channel under a distinct event
        # name so existing `topology-updated` listeners ignore it. The
        # frontend graceful-restart coordinator listens for
        # `service-restart` and pauses polls/reconnects for `eta`
        # seconds.
        event = {
            "_event_name": "service-restart",
            "kind": "imminent",
            "reason": reason,
            "eta_seconds": eta,
            "source": source,
            "at": now,
        }
        try:
            _sse_publish_all(event)
        except Exception as exc:
            print(f"[announce-restart] broadcast failed: {exc}")
        print(f"[announce-restart] reason={reason!r} eta={eta}s source={source!r}")
        return self._send_json({
            "ok": True,
            "broadcast_at": now,
            "reason": reason,
            "eta_seconds": eta,
            "source": source,
        })

    def _handle_health(self):
        """Return aggregated status of serve + discovery_api + scaler_bridge."""
        now = time.time()
        result = {
            "serve": {"status": "ok", "port": PORT},
            "discovery_api": {"status": "unknown", "port": 8765},
            "scaler_bridge": {"status": "unknown", "port": 8766},
        }
        proc = _child_procs.get("discovery")
        if proc is not None and proc.poll() is None:
            uptime = now - _child_start_times.get("discovery", now)
            result["discovery_api"] = {
                "status": "ok",
                "port": 8765,
                "pid": proc.pid,
                "uptime_s": int(uptime),
            }
        else:
            try:
                req = urllib.request.Request(DISCOVERY_API + "/api/health", method="GET")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if 200 <= resp.status < 400:
                        result["discovery_api"] = {"status": "ok", "port": 8765, "managed": proc is not None}
                    else:
                        result["discovery_api"] = {"status": "down", "port": 8765, "code": resp.status}
            except Exception:
                result["discovery_api"] = {"status": "down", "port": 8765}
        proc = _child_procs.get("bridge")
        if proc is not None and proc.poll() is None:
            uptime = now - _child_start_times.get("bridge", now)
            result["scaler_bridge"] = {
                "status": "ok",
                "port": 8766,
                "pid": proc.pid,
                "uptime_s": int(uptime),
            }
        else:
            try:
                req = urllib.request.Request(SCALER_BRIDGE_API + "/api/health", method="GET")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if 200 <= resp.status < 400:
                        result["scaler_bridge"] = {"status": "ok", "port": 8766, "managed": proc is not None}
                    else:
                        result["scaler_bridge"] = {"status": "down", "port": 8766, "code": resp.status}
            except Exception:
                result["scaler_bridge"] = {"status": "down", "port": 8766}
        return self._send_json(result)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def _proxy_to_discovery(self, method="GET", body=None):
        """Proxy /api/dnaas/* and /api/network-mapper/* to discovery_api on port 8765."""
        # /api/dnaas/discovery/list -> /api/discovery/list
        # /api/dnaas/multi-bd/start -> /api/multi-bd/start
        # /api/network-mapper/* -> /api/network-mapper/* (pass through as-is)
        if self.path.startswith("/api/network-mapper/"):
            upstream = self.path
        else:
            upstream = self.path.replace("/api/dnaas/", "/api/", 1)
        url = DISCOVERY_API + upstream
        if "device-gitcommit" in self.path:
            timeout = 12
        elif "enable-lldp" in self.path and method == "GET":
            timeout = 5
        elif method == "GET":
            timeout = 10
        elif "device-stack-live" in self.path:
            timeout = 20
        else:
            timeout = 60
        last_error = None
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=body, method=method)
                if body:
                    req.add_header('Content-Type', 'application/json')
                auth_header = self.headers.get("Authorization")
                if auth_header:
                    req.add_header("Authorization", auth_header)
                    username = _extract_jwt_username(auth_header)
                    if username:
                        req.add_header("X-User", username)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                return
            except urllib.error.HTTPError as e:
                # Relay the upstream status verbatim (404 stays 404, 400
                # stays 400, etc.). When the upstream body is missing we
                # synthesise a small JSON blob that still distinguishes
                # "device not reachable / unknown" (4xx) from "upstream
                # crashed" (5xx) so the frontend can render a useful
                # toast instead of a generic "Bad Gateway". Surface the
                # upstream path + the reason phrase for debuggability.
                try:
                    err_body = e.read() if e.fp else b""
                except Exception:
                    err_body = b""
                if not err_body:
                    fallback = {
                        "error": f"upstream {e.code} {e.reason or ''}".strip(),
                        "endpoint": upstream,
                        "detail": (
                            "Device unreachable or LLDP data not available"
                            if e.code in (400, 404, 409) and "lldp" in self.path
                            else f"upstream returned HTTP {e.code}"
                        ),
                    }
                    err_body = json.dumps(fallback).encode("utf-8")
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
                return
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                last_error = e
                if attempt == 0:
                    time.sleep(1)
        detail = "Check if discovery_api.py is running on port 8765"
        try:
            hurl = DISCOVERY_API + "/api/health"
            with urllib.request.urlopen(hurl, timeout=3) as hr:
                health = json.loads(hr.read())
                detail = (
                    f"discovery_api is running (uptime {health.get('uptime_s', '?')}s, "
                    f"MCP: {health.get('mcp_client', '?')}), but request to {upstream} "
                    f"failed"
                )
        except Exception:
            detail = "discovery_api.py is not responding on port 8765 -- may need restart"
        # Always include the last transport error so the UI (or the
        # admin reading devtools) has a concrete root cause instead of
        # a generic 502. `last_error_kind` is a stable tag the
        # frontend can branch on without string-matching.
        last_error_kind = "unreachable"
        last_error_msg = str(last_error) if last_error else ""
        if isinstance(last_error, TimeoutError):
            last_error_kind = "timeout"
        elif isinstance(last_error, urllib.error.URLError):
            reason = getattr(last_error, "reason", "") or ""
            if "timed out" in str(reason).lower():
                last_error_kind = "timeout"
            last_error_msg = str(reason) or last_error_msg
        self._send_json({
            "error": "Discovery API unavailable",
            "endpoint": upstream,
            "detail": f"{detail} (upstream: {upstream})",
            "last_error": last_error_msg,
            "last_error_kind": last_error_kind,
        }, 502)

    def _proxy_sse_stream(self):
        """Stream SSE from scaler_bridge to the client without buffering.
        Forward upstream HTTP status faithfully (401/403/404 etc.) so the EventSource
        on the frontend doesn't keep retrying a job the bridge has already cleaned up
        or rejected -- we used to mask everything as 502, which produced reconnect spam.

        EventSource can't attach custom headers, so SSE clients pass the JWT as a
        ``?token=`` query parameter. Promote that to ``Authorization: Bearer <jwt>``
        before proxying upstream so the bridge's auth middleware sees a uniform
        header surface regardless of whether the caller is fetch() or EventSource.
        The bridge middleware also accepts ``?token=`` directly as a belt-and-
        suspenders measure -- this promotion just keeps the upstream contract
        clean and means the token stops appearing in upstream access logs twice.
        """
        url = SCALER_BRIDGE_API + self.path
        try:
            req = urllib.request.Request(url, method="GET")
            auth_header = self.headers.get("Authorization")
            if not auth_header:
                try:
                    from urllib.parse import urlparse, parse_qs
                    q = parse_qs(urlparse(self.path).query)
                    tok = (q.get("token") or [""])[0]
                    if tok:
                        auth_header = "Bearer " + tok
                except Exception:
                    auth_header = None
            if auth_header:
                req.add_header("Authorization", auth_header)
                username = _extract_jwt_username(auth_header)
                if username:
                    req.add_header("X-User", username)
            try:
                resp = urllib.request.urlopen(req, timeout=600)
            except urllib.error.HTTPError as he:
                # Bridge returned a non-2xx response (e.g. 401 expired token, 403 not your
                # job, 404 unknown). Relay the same status; do NOT convert to 502.
                err_body = b""
                try:
                    err_body = he.read() or b""
                except Exception:
                    pass
                if not err_body:
                    err_body = json.dumps({"detail": f"upstream {he.code}"}).encode("utf-8")
                self.send_response(he.code)
                self.send_header("Content-Type", he.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                try:
                    self.wfile.write(err_body)
                except Exception:
                    pass
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            while True:
                line = resp.readline()
                if not line:
                    break
                self.wfile.write(line)
                self.wfile.flush()
        except Exception as e:
            # True transport failure (connection refused, broken pipe, etc.). 503 is more
            # accurate than 502: bridge process is unavailable, not returning a bad gateway
            # response. Frontend will still see a connection error and may reconnect, but
            # at least the proxy log records the real cause.
            try:
                self._send_json({"detail": f"SSE proxy error: {e}"}, 503)
            except Exception:
                pass

    # -------------------------------------------------------------
    # WebSocket proxy (2026-04-22) -- remote-access same-origin fix.
    #
    # Most of our real-time features (per-user device-event bus in
    # routes/events.py::/api/events/ws, in-browser terminal in
    # routes/ssh.py::/api/terminal/ws, and push-progress in
    # api/main.py::/ws/progress/<job_id>) live on scaler_bridge at
    # port 8766. In local dev the browser can hit 8766 directly, but
    # remote-access deployments (CGNAT 100.64/10) only expose serve.py
    # on 8080 -- per the "serve.py is the single entry point" rule in
    # .cursor/rules/remote-access-proxy.mdc. Hitting 8766 from outside
    # the lab just produces WebSocket close code 1006 and infinite
    # reconnect spam in devtools.
    #
    # This helper lets `ws://<serve>:8080/api/events/ws?...` tunnel to
    # the bridge, so the browser stays same-origin and the client code
    # never needs to know about port 8766.
    #
    # Each request runs in its own daemon thread (ThreadedHTTPServer),
    # so the long-lived select() loop here cannot block other clients.
    # -------------------------------------------------------------
    def _is_websocket_upgrade(self):
        """Return True iff the request headers describe a WS handshake.

        HTTP/1.1 defines the `Upgrade: websocket` + `Connection: Upgrade`
        pair; we match case-insensitively and accept `Connection` values
        that include other tokens (e.g. `keep-alive, Upgrade`)."""
        upg = (self.headers.get("Upgrade") or "").strip().lower()
        if upg != "websocket":
            return False
        conn_values = ",".join(self.headers.get_all("Connection") or [])
        tokens = [t.strip().lower() for t in conn_values.split(",") if t.strip()]
        return "upgrade" in tokens

    def _proxy_websocket(self, upstream_host, upstream_port):
        """Tunnel a WebSocket handshake + frames to an internal upstream.

        Steps:
          1. Open a fresh TCP socket to the upstream.
          2. Forward the HTTP/1.1 handshake verbatim, rewriting `Host`.
          3. Read the upstream response headers up to \\r\\n\\r\\n and
             send them back to the browser. At this point the WS is
             OPEN on both sides.
          4. Shuffle raw bytes in both directions with select() until
             either side closes (normal close, timeout, or TCP reset).

        We do NOT try to parse or rewrite WS frames -- uvicorn/FastAPI
        speak the standard protocol and the browser does too; serve.py
        just needs to get out of the way. Keeps auth query params
        (`?token=...`) intact because we forward the original path.
        """
        import socket
        import select

        raw_path = self.path  # keep query string + token intact
        request_line = f"GET {raw_path} HTTP/1.1\r\n"
        header_lines = []
        for name in self.headers:
            for val in self.headers.get_all(name):
                if name.lower() == "host":
                    continue
                header_lines.append(f"{name}: {val}")
        header_lines.append(f"Host: {upstream_host}:{upstream_port}")
        handshake = (
            request_line + "\r\n".join(header_lines) + "\r\n\r\n"
        ).encode("iso-8859-1", errors="replace")

        try:
            upstream = socket.create_connection(
                (upstream_host, upstream_port), timeout=10
            )
        except Exception as e:
            try:
                self.send_error(502, f"ws upstream unreachable: {e}")
            except Exception:
                pass
            return

        try:
            upstream.sendall(handshake)
        except Exception as e:
            upstream.close()
            try:
                self.send_error(502, f"ws handshake write failed: {e}")
            except Exception:
                pass
            return

        # Read upstream response headers until the empty line.
        upstream.settimeout(10)
        buf = b""
        max_header_bytes = 65536
        while b"\r\n\r\n" not in buf:
            try:
                chunk = upstream.recv(4096)
            except Exception as e:
                upstream.close()
                try:
                    self.send_error(502, f"ws handshake read failed: {e}")
                except Exception:
                    pass
                return
            if not chunk:
                upstream.close()
                try:
                    self.send_error(502, "ws upstream closed during handshake")
                except Exception:
                    pass
                return
            buf += chunk
            if len(buf) > max_header_bytes:
                upstream.close()
                try:
                    self.send_error(502, "ws handshake headers too large")
                except Exception:
                    pass
                return

        hdr_end = buf.index(b"\r\n\r\n") + 4
        header_bytes = buf[:hdr_end]
        leftover = buf[hdr_end:]

        # Relay upstream handshake response to the client verbatim.
        # If upstream rejected the upgrade (e.g. 401/403) the browser's
        # WebSocket will fire the appropriate close; we're a pipe.
        try:
            self.wfile.write(header_bytes)
            self.wfile.flush()
            if leftover:
                self.wfile.write(leftover)
                self.wfile.flush()
        except Exception:
            upstream.close()
            return

        client_sock = self.connection
        try:
            client_sock.settimeout(None)
            upstream.settimeout(None)
        except Exception:
            pass

        try:
            while True:
                try:
                    rlist, _, xlist = select.select(
                        [client_sock, upstream],
                        [],
                        [client_sock, upstream],
                        60,
                    )
                except Exception:
                    return
                if xlist:
                    return
                if not rlist:
                    # Idle timeout: WS has its own ping/pong; keep looping.
                    continue
                for s in rlist:
                    try:
                        data = s.recv(16384)
                    except Exception:
                        return
                    if not data:
                        return
                    target = upstream if s is client_sock else client_sock
                    try:
                        target.sendall(data)
                    except Exception:
                        return
        finally:
            try:
                upstream.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                upstream.close()
            except Exception:
                pass

    def _handle_sse_topology_events(self):
        """Long-lived event stream pushing `topology-updated` events to open
        client tabs. Recipients listen for save/rename/delete on topologies
        shared with them so their dropdown refreshes without F5.

        EventSource in the browser can't attach custom headers -- the only
        way to authenticate is a cookie (we don't use one) or a query-string
        token. We accept `?token=<jwt>` as an alternative to the Authorization
        header so the client can pass the same JWT it already owns.
        """
        try:
            username = self._require_auth_for_sse()
        except Exception:
            username = None
        if not username:
            self._send_json({"detail": "Authentication required for event stream"}, 401)
            return
        q = _sse_subscribe(username)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            # Initial comment so curl / browser can confirm the stream is up.
            try:
                self.wfile.write(b": connected\n\n")
                self.wfile.flush()
            except Exception:
                return
            # 15 s heartbeat interval. SSE comments (`:` prefix) are ignored by
            # browsers but keep proxies and the client from timing out.
            while True:
                try:
                    event = q.get(timeout=15)
                except queue.Empty:
                    try:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                    except Exception:
                        return
                    continue
                try:
                    # Allow publishers to override the SSE event name (the
                    # default `topology-updated` is what shared-topology
                    # mirror events use). The marker is popped from the
                    # payload so JSON consumers don't see it.
                    if isinstance(event, dict) and "_event_name" in event:
                        ev_payload = dict(event)
                        ev_name = str(ev_payload.pop("_event_name") or "topology-updated")
                    else:
                        ev_payload = event
                        ev_name = "topology-updated"
                    payload = json.dumps(ev_payload).encode("utf-8")
                    self.wfile.write(("event: " + ev_name + "\n").encode("utf-8"))
                    self.wfile.write(b"data: " + payload + b"\n\n")
                    self.wfile.flush()
                except Exception:
                    return
        finally:
            _sse_unsubscribe(username, q)

    def _require_auth_for_sse(self):
        """Like _require_auth but also accepts `?token=<jwt>` since
        EventSource cannot send custom headers. Returns username or None."""
        auth = self.headers.get("Authorization", "")
        username = _extract_jwt_username(auth) if auth else None
        if username:
            return username
        try:
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            tok = (q.get("token") or [""])[0]
            if tok:
                return _extract_jwt_username("Bearer " + tok)
        except Exception:
            pass
        return None

    def _proxy_to_scaler_bridge(self, method="GET", body=None):
        """Proxy /api/config/* and /api/devices/{id}/context to scaler_bridge on port 8766."""
        url = SCALER_BRIDGE_API + self.path
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=body, method=method)
                if body:
                    req.add_header("Content-Type", "application/json")
                auth_header = self.headers.get("Authorization")
                if auth_header:
                    req.add_header("Authorization", auth_header)
                with urllib.request.urlopen(req, timeout=self._scaler_bridge_timeout()) as resp:
                    data = resp.read()
                    self.send_response(resp.status)
                    self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            except urllib.error.HTTPError as e:
                err_body = e.read() if e.fp else b'{"detail":"upstream error"}'
                try:
                    json.loads(err_body)
                except (json.JSONDecodeError, ValueError):
                    msg = err_body.decode("utf-8", errors="replace")[:200]
                    err_body = json.dumps({"detail": msg}).encode("utf-8")
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
                return
            except Exception as e:
                if attempt == 0:
                    proc = _child_procs.get("bridge")
                    bridge_dead = proc is None or proc.poll() is not None
                    if bridge_dead:
                        print("[INFO] Bridge down on request, attempting on-demand start...")
                        new_proc = _start_scaler_bridge()
                        if new_proc:
                            with _monitor_lock:
                                _child_procs["bridge"] = new_proc
                                _child_start_times["bridge"] = time.time()
                            continue
                if self._try_topology_read_fallback(method):
                    return
                self._send_json({"detail": f"Scaler bridge unavailable: {e}"}, 503)
                return

    def _scaler_bridge_timeout(self):
        """Short timeout for UI topology reads; long timeout for operations.

        Domain/topology list calls are the browser's navigation substrate. If
        the bridge wedges, waiting 120 seconds makes the app look as if every
        topology disappeared. Keep read-only topology calls snappy and let the
        local fallback below serve from the per-user SQLite store.
        """
        if self.command == "GET" and (
            self.path == "/api/domains"
            or self.path.startswith("/api/domains/")
            or self.path.startswith("/api/auth/me")
        ):
            return 6
        return 120

    def _try_topology_read_fallback(self, method):
        """Serve critical topology reads locally when scaler_bridge is down.

        `serve.py` and `scaler_bridge.py` run from the same code tree and use
        the same per-user `user_store`. Falling back here keeps all users' domain
        and topology dropdowns visible during a bridge outage instead of
        replacing the UI with an empty/error state.
        """
        if method != "GET":
            return False
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if not (path == "/api/domains" or path.startswith("/api/domains/")):
            return False
        # Sharing observability endpoints are nice-to-have decoration; failing
        # them closed is better than pretending there are no shares.
        if path.startswith("/api/domains/share/"):
            return False
        user = self._require_auth()
        if not user:
            return True
        store = _mirror_user_store()
        if store is None:
            return False
        try:
            if path == "/api/domains":
                self._send_json(store.list_domains(user))
                return True
            parts = [urllib.parse.unquote(p) for p in path.split("/") if p]
            # /api/domains/{domain_id}/topologies
            if len(parts) == 4 and parts[:2] == ["api", "domains"] and parts[3] == "topologies":
                self._send_json(store.list_topologies(user, parts[2]))
                return True
            # /api/domains/{domain_id}/topologies/{topology_id}
            if len(parts) == 5 and parts[:2] == ["api", "domains"] and parts[3] == "topologies":
                topo = store.load_topology(user, parts[2], parts[4])
                if topo:
                    self._send_json(topo)
                else:
                    self._send_json({"detail": "Topology not found"}, 404)
                return True
        except Exception as exc:
            print(f"[topology-read-fallback] {path}: {exc}")
            return False
        return False

    def _serve_debug_dnos_list(self):
        """Serve list of .topology.json files from bug_evidence."""
        try:
            pattern = os.path.join(BUG_EVIDENCE_DIR, "*.topology.json")
            files = sorted(glob.glob(pattern))
            items = []
            for f in files:
                name = os.path.basename(f)
                display_name = name.replace(".topology.json", "")
                items.append({"name": display_name, "filename": name})
            self._send_json({"topologies": items})
        except Exception as e:
            self._send_json({"topologies": [], "error": str(e)}, 500)
    
    def _save_debug_dnos_file(self, body):
        """Save a topology as a .topology.json bug evidence file."""
        try:
            data = json.loads(body) if body else {}
            name = data.get("name", "").strip()
            topology = data.get("topology", {})
            if not name:
                return self._send_json({"error": "Name is required"}, 400)
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            filename = f"{safe_name}.topology.json"
            os.makedirs(BUG_EVIDENCE_DIR, exist_ok=True)
            path = os.path.join(BUG_EVIDENCE_DIR, filename)
            with open(path, "w") as f:
                json.dump(topology, f, indent=2)
            return self._send_json({"ok": True, "filename": filename, "path": path})
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)

    # --- Custom Topology Sections (LEGACY -- deprecated, use /api/domains) ---

    def _require_auth(self):
        """Validate JWT from Authorization header. Returns username or sends 401."""
        auth = self.headers.get("Authorization", "")
        username = _extract_jwt_username(auth) if auth else None
        if not username:
            self._send_json({"detail": "Authentication required (legacy sections deprecated -- use domain API)"}, 401)
            return None
        return username

    def _user_sections_dir(self, username):
        """Per-user sections root: ~/.topology_users/<user>/sections/.

        Always returns a usable path (creates the directory on demand).
        Falls back to the legacy global path only when no username is supplied --
        but every `/api/sections/*` route requires auth, so this fallback is only
        reachable from administrative tooling that runs in-process.
        """
        if not username:
            return CUSTOM_SECTIONS_LEGACY_DIR
        user_dir = _ensure_user_workspace(username) or _user_xray_dir(username)
        if not user_dir:
            return CUSTOM_SECTIONS_LEGACY_DIR
        sdir = os.path.join(user_dir, "sections")
        os.makedirs(sdir, exist_ok=True)
        return sdir

    def _user_sections_config(self, username):
        return os.path.join(self._user_sections_dir(username), "_sections.json")

    def _user_topology_order_config(self, username):
        return os.path.join(self._user_sections_dir(username), "_topology_order.json")

    def _topology_orders_read(self, username):
        cfg = self._user_topology_order_config(username)
        try:
            with open(cfg, "r") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _topology_orders_write(self, username, orders):
        cfg = self._user_topology_order_config(username)
        os.makedirs(os.path.dirname(cfg), exist_ok=True)
        with open(cfg, "w") as f:
            json.dump(orders or {}, f, indent=2)

    def _normalize_topology_order(self, order, existing_files):
        existing = [f for f in (existing_files or []) if str(f).endswith(".json")]
        existing_set = set(existing)
        clean = []
        seen = set()
        for raw in order or []:
            fname = str(raw or "").strip()
            if not fname:
                continue
            if not fname.lower().endswith(".json"):
                fname = fname + ".json"
            fname = os.path.basename(fname)
            if fname in existing_set and fname not in seen:
                clean.append(fname)
                seen.add(fname)
        clean.extend(f for f in existing if f not in seen)
        return clean

    def _topology_order_read(self, username, section_id, existing_files):
        orders = self._topology_orders_read(username)
        return self._normalize_topology_order(orders.get(section_id) or [], existing_files)

    def _topology_order_write(self, username, section_id, order, existing_files):
        orders = self._topology_orders_read(username)
        normalized = self._normalize_topology_order(order, existing_files)
        orders[section_id] = normalized
        self._topology_orders_write(username, orders)
        return normalized

    def _maybe_migrate_legacy_sections(self, username):
        """One-shot migration: copy the legacy global ~/.topology_sections/ tree
        into the founder's per-user sections dir on first read.

        Only a user listed in ``LEGACY_SECTIONS_OWNERS`` (default
        ``yor``, ``yarel``) inherits the legacy data. Every other user
        starts with an empty workspace. The two-name default exists so
        the inheritor is recognised both before and after the
        ``yarel -> yor`` username migration.
        """
        global _legacy_sections_migrated
        if _legacy_sections_migrated:
            return
        if username not in LEGACY_SECTIONS_OWNERS:
            return
        target_dir = self._user_sections_dir(username)
        target_cfg = self._user_sections_config(username)
        if os.path.exists(target_cfg):
            _legacy_sections_migrated = True
            return
        if not os.path.exists(CUSTOM_SECTIONS_LEGACY_CONFIG):
            _legacy_sections_migrated = True
            return
        try:
            import shutil
            for entry in os.listdir(CUSTOM_SECTIONS_LEGACY_DIR):
                src = os.path.join(CUSTOM_SECTIONS_LEGACY_DIR, entry)
                dst = os.path.join(target_dir, entry)
                if os.path.exists(dst):
                    continue
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            print(f"[serve.py] Migrated legacy ~/.topology_sections -> {target_dir}")
        except Exception as e:
            print(f"[serve.py] Legacy sections migration FAILED for {username}: {e}")
        finally:
            _legacy_sections_migrated = True

    def _sections_read(self, username):
        self._maybe_migrate_legacy_sections(username)
        cfg = self._user_sections_config(username)
        try:
            with open(cfg, "r") as f:
                sections = json.load(f)
        except Exception:
            sections = []
        sections = self._inject_builtin_sections(username, sections)
        return sections

    def _inject_builtin_sections(self, username, sections):
        """Ensure every user sees the built-in (undeletable) sections.

        - If a built-in is missing from disk, prepend a fresh copy.
        - If a built-in already exists on disk, refresh the immutable
          fields (name/builtin) but keep the user's icon/color tweaks.
        - If the user has an older user-created section with the same
          name as a built-in (e.g. "Bugs" from before this feature),
          migrate its files into the built-in's directory then drop
          the old section.
        """
        sections = list(sections or [])
        changed = False
        for built in BUILTIN_SECTIONS:
            built_id = built["id"]
            built_name_lc = (built["name"] or "").lower()
            existing = next((s for s in sections if s.get("id") == built_id), None)
            if existing:
                existing["name"] = built["name"]
                existing["builtin"] = True
                existing.setdefault("icon", built["icon"])
                existing.setdefault("color", built["color"])
                # One-time migration: the Bugs builtin originally seeded
                # with the "alert" icon and users had no UI to customize
                # it (Edit was blocked for builtins). Flip the stale
                # default to the new "bug" icon so existing accounts see
                # the upgrade without action. Users who later pick a
                # different icon via Edit stay on their choice because
                # this check only fires on the exact old default value.
                if built_id == "__bugs" and existing.get("icon") == "alert":
                    existing["icon"] = built["icon"]
                    changed = True
                continue
            legacy = next(
                (s for s in sections
                 if not s.get("builtin")
                 and (s.get("name") or "").lower() == built_name_lc),
                None,
            )
            if legacy:
                legacy_id = legacy.get("id")
                if legacy_id and legacy_id != built_id:
                    self._migrate_section_files(username, legacy_id, built_id)
                migrated = dict(legacy)
                migrated["id"] = built_id
                migrated["name"] = built["name"]
                migrated["icon"] = legacy.get("icon") or built["icon"]
                migrated["color"] = legacy.get("color") or built["color"]
                migrated["builtin"] = True
                sections = [migrated if s.get("id") == legacy_id else s for s in sections]
                changed = True
            else:
                sections.insert(0, dict(built))
                changed = True
        if changed:
            try:
                self._sections_write_raw(username, sections)
            except Exception as e:
                print(f"[serve.py] _inject_builtin_sections write failed for {username}: {e}")
        return sections

    def _migrate_section_files(self, username, src_id, dst_id):
        """Move every topology file from one section dir to another."""
        import shutil
        src = self._section_dir(username, src_id)
        dst = self._section_dir(username, dst_id)
        if not os.path.isdir(src):
            return
        os.makedirs(dst, exist_ok=True)
        try:
            for fname in os.listdir(src):
                if not fname.endswith(".json"):
                    continue
                src_path = os.path.join(src, fname)
                dst_path = os.path.join(dst, fname)
                if os.path.isfile(dst_path):
                    base, ext = os.path.splitext(fname)
                    dst_path = os.path.join(dst, f"{base}_migrated{ext}")
                shutil.move(src_path, dst_path)
            try:
                shutil.rmtree(src)
            except OSError:
                pass
            print(f"[serve.py] Migrated section files: {src_id} -> {dst_id} for {username}")
        except Exception as e:
            print(f"[serve.py] Section file migration failed ({src_id} -> {dst_id}): {e}")

    def _sections_write_raw(self, username, sections):
        cfg = self._user_sections_config(username)
        os.makedirs(os.path.dirname(cfg), exist_ok=True)
        with open(cfg, "w") as f:
            json.dump(sections, f, indent=2)

    def _sections_write(self, username, sections):
        self._sections_write_raw(username, sections)

    def _section_dir(self, username, section_id):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in section_id)
        return os.path.join(self._user_sections_dir(username), safe)

    def _section_topology_files(self, username, section_id):
        sdir = self._section_dir(username, section_id)
        files = []
        if os.path.isdir(sdir):
            files = [
                f for f in sorted(os.listdir(sdir))
                if f.endswith(".json") and not f.startswith("_")
            ]
        ordered = self._topology_order_read(username, section_id, files)
        out = []
        for f in ordered:
            fpath = os.path.join(sdir, f)
            if not os.path.isfile(fpath):
                continue
            out.append({
                "name": f.replace(".json", ""),
                "filename": f,
                "modified": os.path.getmtime(fpath),
            })
        return out

    def _section_limit_payload(self, username, section_id):
        topologies = self._section_topology_files(username, section_id)
        return {
            "error": (
                f"Domain already has {len(topologies)} topology file(s). "
                f"The limit is {DOMAIN_TOPOLOGY_LIMIT}. Delete one or more topologies before creating another."
            ),
            "code": "domain-topology-limit",
            "section_id": section_id,
            "domain_id": section_id,
            "limit": DOMAIN_TOPOLOGY_LIMIT,
            "topology_count": len(topologies),
            "topologies": topologies,
        }

    def _handle_sections_get(self, path):
        if path == "/api/sections":
            user = self._require_auth()
            if not user:
                return True
            self._send_json({"sections": self._sections_read(user)})
            return True
        if path.startswith("/api/sections/") and path.endswith("/topologies"):
            user = self._require_auth()
            if not user:
                return True
            sid = path.split("/")[3]
            topos = self._section_topology_files(user, sid)
            self._send_json({"topologies": topos})
            return True
        # ----------------------------------------------------------------
        # Mirror map lookup: lets the frontend translate a legacy
        # (section_id, filename) back to the multi-user (domain_id,
        # topology_id, updated_at) pair so it can register the file with
        # the live-sync / activity-log pipelines. Only files that have
        # already been shared (and therefore migrated into the user's
        # multi-user DB) appear in the mapping; legacy-only files return
        # {"mirrored": false} so the frontend can degrade gracefully.
        # ----------------------------------------------------------------
        if (path.startswith("/api/sections/")
                and "/_mirror-map" in path
                and not path.endswith("/_mirror-register")):
            user = self._require_auth()
            if not user:
                return True
            parts = path.split("/")
            sid = parts[3] if len(parts) > 3 else ""
            fname = parts[5] if len(parts) > 5 else ""
            if not sid:
                self._send_json({"error": "section id required"}, 400)
                return True
            mapping = _mirror_read_all(user, sid) or {}
            store = _mirror_user_store()
            if fname:
                if not fname.lower().endswith(".json"):
                    fname = fname + ".json"
                entry = mapping.get(fname)
                if not entry:
                    self._send_json({"mirrored": False})
                    return True
                out = {
                    "mirrored": True,
                    "filename": fname,
                    "domain_id": entry.get("domain_id"),
                    "topology_id": entry.get("topology_id"),
                    "updated_at": "",
                }
                if store is not None:
                    try:
                        meta = store.get_topology_meta(
                            user, entry["domain_id"], entry["topology_id"],
                        )
                        if meta and meta.get("updated_at"):
                            out["updated_at"] = meta["updated_at"]
                    except Exception:
                        pass
                self._send_json(out)
                return True
            enriched = {}
            for fn, ent in mapping.items():
                row = {
                    "domain_id": ent.get("domain_id"),
                    "topology_id": ent.get("topology_id"),
                    "updated_at": "",
                }
                if store is not None:
                    try:
                        meta = store.get_topology_meta(
                            user, ent["domain_id"], ent["topology_id"],
                        )
                        if meta and meta.get("updated_at"):
                            row["updated_at"] = meta["updated_at"]
                    except Exception:
                        pass
                enriched[fn] = row
            self._send_json({"mirrored": True, "entries": enriched})
            return True
        if "/topologies/" in path:
            user = self._require_auth()
            if not user:
                return True
            parts = path.split("/")
            sid, fname = parts[3], parts[5]
            fpath = os.path.join(self._section_dir(user, sid), fname)
            if not os.path.isfile(fpath):
                self._send_json({"error": "Not found"}, 404)
                return True
            with open(fpath, "r") as f:
                self._send_json(json.load(f))
            return True
        return None

    def _handle_sections_post(self, path, body):
        user = self._require_auth()
        if not user:
            return True
        data = json.loads(body) if body else {}
        if path == "/api/sections":
            sections = self._sections_read(user)
            new_sec = data
            new_name = (new_sec.get("name") or "").strip()
            if new_name.lower() == "dnaas":
                self._send_json({"error": "\"DNAAS\" is a reserved domain name"}, 400)
                return True
            if any(
                b["name"].lower() == new_name.lower()
                for b in BUILTIN_SECTIONS
            ):
                self._send_json(
                    {"error": f"\"{new_name}\" is a reserved built-in domain name"},
                    400,
                )
                return True
            new_sec.pop("builtin", None)
            if any((s.get("name") or "").lower() == new_name.lower() for s in sections):
                self._send_json({"error": f"Domain \"{new_name}\" already exists"}, 400)
                return True
            new_sec.setdefault("id", "sec_" + str(int(time.time())))
            sections.append(new_sec)
            self._sections_write(user, sections)
            self._send_json({"ok": True, "section": new_sec})
            return True
        if path == "/api/sections/reorder":
            self._sections_write(user, data.get("sections", []))
            self._send_json({"ok": True})
            return True
        if path.startswith("/api/sections/") and path.endswith("/topologies/reorder"):
            sid = path.split("/")[3]
            sdir = self._section_dir(user, sid)
            existing = []
            if os.path.isdir(sdir):
                existing = sorted(f for f in os.listdir(sdir) if f.endswith(".json"))
            order = data.get("order")
            if order is None:
                order = data.get("topologies", [])
            normalized = self._topology_order_write(user, sid, order, existing)
            self._send_json({"ok": True, "order": normalized})
            return True
        if path.startswith("/api/sections/") and path.endswith("/topologies/cleanup"):
            sid = path.split("/")[3]
            sdir = self._section_dir(user, sid)
            existing = self._section_topology_files(user, sid)
            existing_by_name = {t["filename"]: t for t in existing}
            delete_all = bool(data.get("delete_all"))
            requested = data.get("filenames") or data.get("topologies") or []
            normalized = []
            if delete_all:
                normalized = list(existing_by_name)
            else:
                for raw in requested:
                    fname = os.path.basename(str(raw or "").strip())
                    if not fname:
                        continue
                    if not fname.endswith(".json"):
                        fname += ".json"
                    if fname in existing_by_name and fname not in normalized:
                        normalized.append(fname)
            if not normalized:
                self._send_json({
                    "ok": False,
                    "error": "Select at least one topology to delete",
                    "code": "empty-cleanup-selection",
                    "section_id": sid,
                    "topologies": existing,
                }, 400)
                return True
            deleted = []
            store = _mirror_user_store()
            for fname in normalized:
                fpath = os.path.join(sdir, fname)
                if not os.path.isfile(fpath):
                    continue
                os.remove(fpath)
                deleted.append(existing_by_name.get(fname, {"filename": fname, "name": fname.replace(".json", "")}))
                mapping = _mirror_get(user, sid, fname)
                if mapping:
                    _sse_publish_mirror_event(
                        user, mapping, "delete",
                        {"filename": fname, "reason": "domain-cleanup"},
                    )
                    if store is not None:
                        try:
                            store.delete_topology(
                                user,
                                mapping["domain_id"],
                                mapping["topology_id"],
                            )
                        except Exception as exc:
                            print(
                                f"[mirror-cleanup-file] {sid}/{fname} "
                                f"({mapping}): {exc}"
                            )
                    _mirror_clear(user, sid, fname)
            remaining_files = [
                t["filename"] for t in self._section_topology_files(user, sid)
            ]
            self._topology_order_write(user, sid, remaining_files, remaining_files)
            self._send_json({
                "ok": True,
                "section_id": sid,
                "deleted_count": len(deleted),
                "deleted": deleted,
                "remaining": self._section_topology_files(user, sid),
            })
            return True
        # Register a legacy<->multi-user mapping for a single topology
        # file. Called by topology-file-ops.js right after the frontend
        # migration helper imports a legacy file into /api/domains. This
        # lets the /save, /rename, /delete-file, /delete handlers mirror
        # owner changes into the multi-user DB so shared recipients see
        # them on their next fetch.
        if path.startswith("/api/sections/") and path.endswith("/_mirror-register"):
            sid = path.split("/")[3]
            fname = (data.get("filename") or "").strip()
            did = (data.get("domain_id") or "").strip()
            tid = (data.get("topology_id") or "").strip()
            if not fname or not did or not tid:
                self._send_json(
                    {"error": "filename, domain_id and topology_id are required"},
                    400,
                )
                return True
            if not fname.lower().endswith(".json"):
                fname = fname + ".json"
            _mirror_set(user, sid, fname, did, tid)
            self._send_json({"ok": True})
            return True
        if path.startswith("/api/sections/") and path.endswith("/save"):
            sid = path.split("/")[3]
            name = data.get("name", "").strip()
            topo = data.get("topology", {})
            force_save = bool(data.get("force"))
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            conflict_debug_requested = bool(
                data.get("conflict_debug")
                or data.get("debug_conflict")
                or query.get("conflict_debug")
            )
            if not name:
                self._send_json({"error": "Name required"}, 400)
                return True
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            sdir = self._section_dir(user, sid)
            os.makedirs(sdir, exist_ok=True)
            if bool(data.get("avoid_duplicate")) and not force_save:
                base_safe = safe or "topology"
                candidate = base_safe
                idx = 2
                while os.path.exists(os.path.join(sdir, candidate + ".json")):
                    candidate = f"{base_safe}-{idx}"
                    idx += 1
                    if idx > 999:
                        candidate = f"{base_safe}-{int(time.time())}"
                        break
                if candidate != safe:
                    safe = candidate
                    name = candidate
                    if isinstance(topo, dict):
                        meta = topo.setdefault("metadata", {})
                        if isinstance(meta, dict):
                            meta["name"] = name
            fpath = os.path.join(sdir, safe + ".json")
            is_new_topology_file = not os.path.isfile(fpath)
            if is_new_topology_file:
                existing_topologies = self._section_topology_files(user, sid)
                if len(existing_topologies) >= DOMAIN_TOPOLOGY_LIMIT:
                    self._send_json(self._section_limit_payload(user, sid), 409)
                    return True
            # Stale-save guard: if this file has a multi-user mirror AND
            # someone wrote to that row AFTER our last legacy save, refuse
            # to overwrite unless the client sends `force: true`. The
            # canonical copy is the mirror row; the legacy file on disk is
            # just the owner's local cache, so newer mirror content can mean
            # a recipient has made changes we don't have yet.
            #
            # 2026-04-26 refinement: do NOT fire the guard for owner-only
            # mirror rows. A topology can have a mirror mapping simply
            # because it was imported into the multi-user DB; if there are no
            # write collaborators and the last DB writer is still the owner,
            # the DB>disk delta is mirror bookkeeping, not a real peer-write
            # risk. We still conflict when a write-recipient exists OR the
            # last writer recorded in the topology event log is not the owner
            # (including historical writes by someone whose share was later
            # revoked).
            mapping = _mirror_get(user, sid, safe + ".json")
            skipped_conflict_debug = None
            if mapping and not force_save:
                store = _mirror_user_store()
                if store is not None:
                    try:
                        meta = store.get_topology_meta(
                            user, mapping["domain_id"], mapping["topology_id"],
                        )
                    except Exception:
                        meta = None
                    if meta and meta.get("updated_at") and os.path.isfile(fpath):
                        try:
                            disk_mtime = os.path.getmtime(fpath)
                            # updated_at is ISO-8601 UTC from user_store.
                            db_ts = _epoch_from_iso(meta.get("updated_at"))
                            if db_ts is None:
                                raise ValueError(f"invalid updated_at={meta.get('updated_at')!r}")
                            # 5 s skew tolerates the normal race where our
                            # own previous mirror-save lands a tick after
                            # the disk write. Only flag meaningfully newer
                            # DB state (~ an actual peer write).
                            if db_ts > disk_mtime + _STALE_SAVE_SKEW_SECONDS:
                                write_collabs = int(meta.get("write_share_recipient_count") or 0)
                                last_actor = (meta.get("last_actor") or "").strip()
                                last_actor_is_other = bool(last_actor and last_actor != user)
                                if last_actor_is_other:
                                    reason = "last_writer_is_collaborator"
                                elif write_collabs > 0:
                                    reason = "active_write_collaborator"
                                else:
                                    reason = "owner_only_mirror_row"
                                debug = _stale_save_conflict_payload(
                                    user, sid, safe + ".json", mapping, meta,
                                    disk_mtime, db_ts, reason,
                                )
                                if write_collabs <= 0 and not last_actor_is_other:
                                    skipped_conflict_debug = debug
                                    print(
                                        "[stale-save-check] skipped owner-only "
                                        f"{sid}/{safe}.json delta={debug.get('delta_seconds')}s "
                                        f"db={meta.get('updated_at')} disk={debug.get('disk_mtime')}"
                                    )
                                else:
                                    last_writer = debug.get("last_writer") or {}
                                    self._send_json({
                                        "error": (
                                            "This topology was updated by another "
                                            "user while you had it open. Reload to "
                                            "see their changes, or save again to "
                                            "overwrite."
                                        ),
                                        "conflict": True,
                                        "current_updated_at": meta["updated_at"],
                                        "filename": safe + ".json",
                                        "last_writer": last_writer,
                                        "last_actor": last_writer.get("username") or "",
                                        "last_actor_display_name": (
                                            last_writer.get("display_name") or ""
                                        ),
                                        "conflict_reason": reason,
                                        "conflict_debug": debug,
                                    }, 409)
                                    return True
                        except Exception as exc:
                            print(f"[stale-save-check] {sid}/{safe}.json: {exc}")
            with open(fpath, "w") as f:
                json.dump(topo, f, indent=2)
            # Mirror-on-save: if this legacy file has already been migrated
            # into the multi-user DB (i.e. it has been shared at least once),
            # push the same content so shared recipients see the update on
            # their next fetch. This is owner-side only; recipients hit the
            # /api/domains/.../save path which already enforces write perms.
            mirror_updated_at = None
            if mapping:
                store = _mirror_user_store()
                if store is not None:
                    try:
                        actor_display = user
                        try:
                            user_meta = store.get_user(user)
                            actor_display = (
                                (user_meta or {}).get("display_name")
                                or user
                            )
                        except Exception:
                            actor_display = user
                        result = store.save_topology(
                            user,
                            mapping["domain_id"],
                            name,
                            topo,
                            topology_id=mapping["topology_id"],
                            actor=user,
                            actor_display_name=actor_display,
                        )
                        if isinstance(result, dict):
                            mirror_updated_at = result.get("updated_at")
                        # Broadcast to every open tab so the recipient's
                        # Topologies dropdown refreshes without F5.
                        _sse_publish_mirror_event(
                            user, mapping, "save",
                            {"name": name, "updated_at": mirror_updated_at},
                        )
                    except Exception as exc:
                        print(f"[mirror-save] {sid}/{safe}.json -> {mapping}: {exc}")
            resp_body = {"ok": True, "filename": safe + ".json", "name": name}
            if mirror_updated_at:
                resp_body["mirror_updated_at"] = mirror_updated_at
            if conflict_debug_requested and skipped_conflict_debug:
                resp_body["conflict_debug"] = skipped_conflict_debug
            self._send_json(resp_body)
            return True
        if path.startswith("/api/sections/") and path.endswith("/delete"):
            sid = path.split("/")[3]
            if sid in BUILTIN_SECTION_IDS:
                self._send_json(
                    {"error": "This is a built-in domain and cannot be deleted"},
                    400,
                )
                return True
            sdir = self._section_dir(user, sid)
            topo_files = []
            if os.path.isdir(sdir):
                topo_files = [
                    f for f in os.listdir(sdir)
                    if f.endswith(".json") and not f.startswith("_")
                ]
            if topo_files:
                self._send_json(
                    {
                        "error": (
                            f"Domain contains {len(topo_files)} topology file(s). "
                            "Move or delete individual topologies before deleting the domain."
                        ),
                        "topology_count": len(topo_files),
                    },
                    409,
                )
                return True
            sections = self._sections_read(user)
            sections = [s for s in sections if s.get("id") != sid]
            self._sections_write(user, sections)
            # Mirror-on-delete-section: before we blow away the directory,
            # take every mapped topology down from the multi-user DB and,
            # if the multi-user domain was auto-created for mirroring and
            # has no remaining topologies, delete the domain too so stale
            # empty shells don't accumulate.
            mapping_all = _mirror_read_all(user, sid)
            affected_domains = set()
            store = _mirror_user_store()
            if mapping_all and store is not None:
                for _fname, m in list(mapping_all.items()):
                    try:
                        _sse_publish_mirror_event(
                            user, m, "delete",
                            {"filename": _fname, "reason": "section-deleted"},
                        )
                        store.delete_topology(
                            user, m["domain_id"], m["topology_id"],
                        )
                        affected_domains.add(m["domain_id"])
                    except Exception as exc:
                        print(
                            f"[mirror-delete-section] {sid}/{_fname} "
                            f"({m}): {exc}"
                        )
                for did in affected_domains:
                    try:
                        remaining = store.list_topologies(user, did)
                        if not remaining:
                            store.delete_domain(user, did)
                    except Exception as exc:
                        print(
                            f"[mirror-delete-section] cleanup domain {did}: {exc}"
                        )
            _mirror_clear_section(user, sid)
            import shutil
            if os.path.isdir(sdir):
                shutil.rmtree(sdir)
            self._send_json({"ok": True})
            return True
        if path == "/api/sections/update":
            sections = self._sections_read(user)
            updated = data
            upd_name = (updated.get("name") or "").strip()
            upd_id = updated.get("id")
            old_sec = next((s for s in sections if s.get("id") == upd_id), None)
            old_name = (old_sec.get("name") or "") if old_sec else ""
            if upd_id in BUILTIN_SECTION_IDS:
                builtin_def = next((b for b in BUILTIN_SECTIONS if b["id"] == upd_id), {})
                if upd_name.lower() != (builtin_def.get("name") or "").lower():
                    self._send_json(
                        {"error": "Cannot rename a built-in domain"},
                        400,
                    )
                    return True
                updated["name"] = builtin_def.get("name") or updated.get("name")
                updated["builtin"] = True
            if upd_name.lower() == "dnaas" and old_name.lower() != "dnaas":
                self._send_json({"error": "\"DNAAS\" is a reserved domain name"}, 400)
                return True
            if any(s.get("id") != upd_id and (s.get("name") or "").lower() == upd_name.lower() for s in sections):
                self._send_json({"error": f"Domain \"{upd_name}\" already exists"}, 400)
                return True
            sections = [updated if s.get("id") == upd_id else s for s in sections]
            self._sections_write(user, sections)
            self._send_json({"ok": True})
            return True
        # Rename a topology file within a section
        if "/topologies/" in path and path.endswith("/rename"):
            parts = path.split("/")
            sid, fname = parts[3], parts[5]
            new_name = data.get("name", "").strip()
            if not new_name:
                self._send_json({"error": "Name required"}, 400)
                return True
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in new_name)
            sdir = self._section_dir(user, sid)
            old_path = os.path.join(sdir, fname)
            new_path = os.path.join(sdir, safe + ".json")
            if not os.path.isfile(old_path):
                self._send_json({"error": "Not found"}, 404)
                return True
            if os.path.isfile(new_path) and old_path != new_path:
                self._send_json({"error": "Name already exists"}, 400)
                return True
            os.rename(old_path, new_path)
            # Mirror-on-rename: keep the multi-user DB row + its mapping in
            # sync. Clear the old key and re-register under the new filename
            # even if the user just changed letter casing.
            mapping = _mirror_get(user, sid, fname)
            if mapping:
                _mirror_clear(user, sid, fname)
                _mirror_set(
                    user, sid, safe + ".json",
                    mapping["domain_id"], mapping["topology_id"],
                )
                store = _mirror_user_store()
                if store is not None:
                    try:
                        store.rename_topology(
                            user,
                            mapping["domain_id"],
                            mapping["topology_id"],
                            new_name,
                        )
                        _sse_publish_mirror_event(
                            user, mapping, "rename",
                            {"old_filename": fname, "new_filename": safe + ".json", "new_name": new_name},
                        )
                    except Exception as exc:
                        print(
                            f"[mirror-rename] {sid}/{fname} -> {safe}.json "
                            f"({mapping}): {exc}"
                        )
            self._send_json({"ok": True, "filename": safe + ".json"})
            return True
        # Delete a single topology file within a section
        if "/topologies/" in path and path.endswith("/delete-file"):
            parts = path.split("/")
            sid, fname = parts[3], parts[5]
            fpath = os.path.join(self._section_dir(user, sid), fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
                # Mirror-on-delete-file: drop the multi-user row too so
                # shared recipients stop seeing a file the owner deleted
                # locally. delete_topology also cascades share rows.
                mapping = _mirror_get(user, sid, fname)
                if mapping:
                    # Broadcast BEFORE we drop the row so the event still
                    # knows which recipients to notify (otherwise the share
                    # rows are gone by the time we ask).
                    _sse_publish_mirror_event(
                        user, mapping, "delete",
                        {"filename": fname},
                    )
                    store = _mirror_user_store()
                    if store is not None:
                        try:
                            store.delete_topology(
                                user,
                                mapping["domain_id"],
                                mapping["topology_id"],
                            )
                        except Exception as exc:
                            print(
                                f"[mirror-delete-file] {sid}/{fname} "
                                f"({mapping}): {exc}"
                            )
                    _mirror_clear(user, sid, fname)
                self._send_json({"ok": True})
            else:
                self._send_json({"error": "Not found"}, 404)
            return True
        # Move a topology file from one section to another
        if "/topologies/" in path and path.endswith("/move"):
            from urllib.parse import unquote
            import shutil
            parts = path.split("/")
            if len(parts) < 7:
                self._send_json({"error": "Invalid move path"}, 400)
                return True
            src_sid, fname = parts[3], unquote(parts[5])
            dest_sid = data.get("target_section_id", "").strip()
            if not dest_sid:
                self._send_json({"error": "target_section_id required"}, 400)
                return True
            if not fname.endswith(".json"):
                fname = fname + ".json"
            fname = os.path.basename(fname)
            src_dir = self._section_dir(user, src_sid)
            src_path = os.path.join(src_dir, fname)
            print(f"[MOVE] {fname}: {src_sid} -> {dest_sid} (user={user})")
            if not os.path.isfile(src_path):
                avail = os.listdir(src_dir) if os.path.isdir(src_dir) else []
                print(f"[MOVE] Not found: {src_path}  Available: {avail}")
                self._send_json({"error": f"Source file not found: {fname}"}, 404)
                return True
            dest_dir = self._section_dir(user, dest_sid)
            os.makedirs(dest_dir, exist_ok=True)
            if src_sid != dest_sid and len(self._section_topology_files(user, dest_sid)) >= DOMAIN_TOPOLOGY_LIMIT:
                self._send_json(self._section_limit_payload(user, dest_sid), 409)
                return True
            dest_path = os.path.join(dest_dir, fname)
            if os.path.isfile(dest_path):
                base, ext = os.path.splitext(fname)
                dest_path = os.path.join(dest_dir, base + "_moved" + ext)
            try:
                src_order_before = self._topology_order_read(
                    user, src_sid,
                    sorted(f for f in os.listdir(src_dir) if f.endswith(".json"))
                )
                dest_order_before = self._topology_order_read(
                    user, dest_sid,
                    sorted(f for f in os.listdir(dest_dir) if f.endswith(".json"))
                )
                shutil.move(src_path, dest_path)
                dest_name = os.path.basename(dest_path)
                src_existing_after = sorted(f for f in os.listdir(src_dir) if f.endswith(".json")) if os.path.isdir(src_dir) else []
                dest_existing_after = sorted(f for f in os.listdir(dest_dir) if f.endswith(".json"))
                self._topology_order_write(
                    user, src_sid,
                    [f for f in src_order_before if f != fname],
                    src_existing_after,
                )
                target_order = data.get("target_order")
                if isinstance(target_order, list) and target_order:
                    normalized_target = []
                    for raw in target_order:
                        target_name = str(raw or "").strip()
                        if not target_name:
                            continue
                        if not target_name.lower().endswith(".json"):
                            target_name = target_name + ".json"
                        target_name = os.path.basename(target_name)
                        normalized_target.append(dest_name if target_name == fname else target_name)
                else:
                    normalized_target = [f for f in dest_order_before if f != dest_name] + [dest_name]
                self._topology_order_write(user, dest_sid, normalized_target, dest_existing_after)
                print(f"[MOVE] OK: {src_path} → {dest_path}")
                self._send_json({"ok": True, "filename": dest_name})
            except Exception as e:
                print(f"[MOVE] Error: {e}")
                self._send_json({"error": str(e)}, 500)
            return True
        return None

    def _serve_debug_dnos_file(self, filename):
        """Serve a single .topology.json file."""
        if ".." in filename or "/" in filename or "\\" in filename:
            self.send_error(400, "Invalid filename")
            return
        path = os.path.join(BUG_EVIDENCE_DIR, filename)
        if not os.path.isfile(path):
            self.send_error(404, "File not found")
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self._send_json(data)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _migrate_bug_topologies(self, body):
        """One-shot migration of legacy ~/SCALER/FLOWSPEC_VPN/bug_evidence/*.topology.json
        files into a user's sections-API section.

        HISTORY: This endpoint was originally wired into the frontend's
        `_ensureBugsSection` startup flow so every page load pulled the
        global bug_evidence catalog into the calling user's __bugs dir.
        That turned a one-shot import into a permanent auto-copy and
        leaked yarel's historical bug evidence into every other user's
        BUGS dropdown (2026-04-21 multi-user leak incident). The
        frontend call site is now removed; this endpoint survives only
        so the LEGACY_SECTIONS_OWNERS (default ``yor`` / ``yarel``)
        can trigger the import manually from the browser if the
        bug_evidence catalog ever needs re-seeding. Every other user
        is refused.
        """
        user = self._require_auth()
        if not user:
            return
        if user not in LEGACY_SECTIONS_OWNERS:
            return self._send_json({
                "ok": False,
                "error": (
                    "bug_evidence auto-migration is disabled for non-owner users "
                    "to preserve per-user isolation. Bugs must be created via "
                    "/api/bugs/from-jira or saved explicitly by the user."
                ),
                "migrated": 0,
            }, 403)
        data = json.loads(body) if body else {}
        section_id = data.get("section_id", "")
        if not section_id:
            return self._send_json({"error": "section_id required"}, 400)
        sdir = self._section_dir(user, section_id)
        os.makedirs(sdir, exist_ok=True)
        migrated = 0
        if os.path.isdir(BUG_EVIDENCE_DIR):
            for f in os.listdir(BUG_EVIDENCE_DIR):
                if f.endswith(".topology.json"):
                    src = os.path.join(BUG_EVIDENCE_DIR, f)
                    dest_name = f.replace(".topology.json", ".json")
                    dest = os.path.join(sdir, dest_name)
                    if not os.path.isfile(dest):
                        import shutil
                        shutil.copy2(src, dest)
                        migrated += 1
        return self._send_json({"ok": True, "migrated": migrated})

    # --- Bug topology generation -----------------------------------------
    #
    # The "Create Bug Topology" GUI flow lets a user paste a Jira SW-XXXXX
    # number and (optionally) a title/summary/devices. The backend fetches
    # the actual Jira ticket via the user's stored credentials, parses
    # devices/IPs/VRFs/route/symptom out of the description and comments,
    # and synthesizes a /debug-dnos-style topology JSON. If the user has
    # not yet configured Jira creds, the dialog falls back to a
    # placeholder built from whatever the user typed in the form.
    #
    # Two flows in one endpoint:
    #
    #   POST /api/bugs/from-jira { sw_id, [...] }
    #     1. fetch Jira issue (if creds present)
    #     2. parse -> devices, vrfs, route, symptom
    #     3. merge with anything the user typed
    #     4. build topology JSON
    #     5. save under ~/.topology_users/<user>/sections/__bugs/<safe>.json
    #     6. return { ok, section_id, filename, name, sw_id, source }
    def _handle_bug_topology_create(self, body):
        user = self._require_auth()
        if not user:
            return
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        sw_id = (data.get("sw_id") or "").strip()
        if not sw_id:
            return self._send_json({"error": "sw_id is required (e.g. SW-243977)"}, 400)
        sw_normalized = self._normalize_sw_id(sw_id)
        if not sw_normalized:
            return self._send_json(
                {"error": "sw_id must look like SW-XXXXX or BUG-XXX"}, 400
            )
        # Caller-provided overrides (always win over Jira-derived values).
        user_title = (data.get("title") or "").strip()
        user_summary = (data.get("summary") or "").strip()
        user_devices = data.get("devices") or []
        if not isinstance(user_devices, list):
            user_devices = []
        force_placeholder = bool(data.get("force_placeholder"))

        # Caller can opt in to non-bug ticket types after seeing the warning.
        force_non_bug = bool(data.get("force_non_bug"))

        # Pull from Jira when (a) user has creds AND (b) caller didn't
        # explicitly opt out. Failures degrade gracefully to a placeholder
        # with a `source: "placeholder"` tag in the response so the GUI can
        # tell the user "couldn't reach Jira -- here's the empty shell".
        jira_inputs = None
        jira_error = None
        source = "placeholder"
        issue_type = ""
        is_bug_like = False
        if not force_placeholder:
            cfg = self._jira_config_read(user)
            if not cfg:
                jira_error = "no-config"
            else:
                try:
                    issue = self._jira_fetch_issue(cfg, sw_normalized)
                    issue_type, is_bug_like = self._classify_issue_type(issue)
                    # Type gate: refuse to build a topology from a non-bug
                    # ticket unless the caller explicitly forced it. We
                    # have NOT saved anything yet -- the user gets a clean
                    # "this isn't a bug" rejection they can act on.
                    if issue_type and not is_bug_like and not force_non_bug:
                        return self._send_json({
                            "error": (
                                f"{sw_normalized} is a {issue_type}, not a Bug. "
                                "Bug topologies are only created from Bug-like "
                                "tickets. Set 'force_non_bug' to override."
                            ),
                            "code": "not-a-bug",
                            "sw_id": sw_normalized,
                            "issue_type": issue_type,
                        }, 422)
                    jira_inputs = self._jira_parse_to_inputs(issue, sw_normalized)
                    source = "jira"
                except Exception as e:
                    jira_error = str(e)

        # Merge user overrides on top of Jira inputs (user wins).
        title = user_title or (jira_inputs or {}).get("title", "")
        summary = user_summary or (jira_inputs or {}).get("summary", "")
        devices = user_devices or (jira_inputs or {}).get("devices") or []
        vrfs = (jira_inputs or {}).get("vrfs") or []
        route = (jira_inputs or {}).get("route") or {}
        failure_device = (jira_inputs or {}).get("failure_device") or ""
        ticket_url = (jira_inputs or {}).get("ticket_url") or ""

        topology = self._build_bug_topology_json(
            sw_normalized,
            title=title,
            summary=summary,
            devices=devices,
            vrfs=vrfs,
            route=route,
            failure_device=failure_device,
            ticket_url=ticket_url,
            source=source,
            issue_type=issue_type,
        )
        # Make sure the built-in section directory exists.
        self._sections_read(user)
        sdir = self._section_dir(user, "__bugs")
        os.makedirs(sdir, exist_ok=True)
        if len(self._section_topology_files(user, "__bugs")) >= DOMAIN_TOPOLOGY_LIMIT:
            self._send_json(self._section_limit_payload(user, "__bugs"), 409)
            return
        base_name = sw_normalized + (f" - {title}" if title else "")
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_name)
        # Avoid clobbering an existing topology with the same SW: append _2,_3...
        candidate = safe
        suffix = 1
        while os.path.isfile(os.path.join(sdir, candidate + ".json")):
            suffix += 1
            candidate = f"{safe}_{suffix}"
        fname = candidate + ".json"
        with open(os.path.join(sdir, fname), "w") as f:
            json.dump(topology, f, indent=2)
        resp = {
            "ok": True,
            "section_id": "__bugs",
            "filename": fname,
            "name": candidate,
            "sw_id": sw_normalized,
            "source": source,
            "issue_type": issue_type,
            "is_bug_like": is_bug_like,
            "forced_non_bug": (bool(issue_type) and not is_bug_like and force_non_bug),
        }
        if jira_error:
            resp["jira_error"] = jira_error
        if jira_inputs:
            resp["jira_summary"] = jira_inputs.get("summary", "")
            resp["jira_title"] = jira_inputs.get("title", "")
            resp["jira_ticket_url"] = jira_inputs.get("ticket_url", "")
            resp["devices_count"] = len(jira_inputs.get("devices") or [])
            resp["vrfs_count"] = len(jira_inputs.get("vrfs") or [])
        return self._send_json(resp)

    # --- Jira credentials store ------------------------------------------
    #
    # Per-user, stored alongside the user's other workspace files. The
    # API token is sensitive (it grants full Jira access on behalf of the
    # user), so we never echo it back through the GET endpoint -- only the
    # base URL + email + a `configured` flag are returned.
    def _jira_config_path(self, username):
        if not username:
            return None
        user_dir = _ensure_user_workspace(username) or _user_xray_dir(username)
        if not user_dir:
            return None
        return os.path.join(user_dir, "jira_config.json")

    def _jira_config_read(self, username):
        path = self._jira_config_path(username)
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path) as f:
                cfg = json.load(f)
        except Exception:
            return None
        if not cfg.get("base_url") or not cfg.get("email") or not cfg.get("api_token"):
            return None
        return cfg

    def _jira_config_write(self, username, cfg):
        path = self._jira_config_path(username)
        if not path:
            raise RuntimeError("No per-user workspace available")
        # 0600 -- token is a secret.
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def _jira_config_delete(self, username):
        path = self._jira_config_path(username)
        if path and os.path.isfile(path):
            os.remove(path)

    def _handle_jira_config_get(self):
        user = self._require_auth()
        if not user:
            return
        cfg = self._jira_config_read(user)
        if not cfg:
            return self._send_json({"configured": False})
        # Surface a short, non-sensitive "hint" for the token so the UI can
        # reassure the user that a token IS saved without echoing the secret.
        # Convention: first 4 chars + "..." + last 4 chars of the token
        # string. ATATT tokens are long enough that 4+4 leaks nothing
        # actionable (you already need the whole string to auth).
        token = cfg.get("api_token", "") or ""
        if len(token) >= 12:
            token_hint = f"{token[:4]}...{token[-4:]}"
        elif token:
            token_hint = "****"
        else:
            token_hint = ""
        # `token_len` lets the UI show "192 chars saved" so the user can tell
        # at a glance whether the expected token is there without us ever
        # returning the plaintext.
        token_len = len(token)
        # Best-effort filesystem timestamp so the UI can show "Last updated
        # 2h ago". Falls back to 0 on any error (permission, missing file).
        saved_at = 0
        try:
            path = self._jira_config_path(user)
            if path and os.path.isfile(path):
                saved_at = int(os.path.getmtime(path))
        except OSError:
            saved_at = 0
        return self._send_json({
            "configured": True,
            "base_url": cfg.get("base_url", ""),
            "email": cfg.get("email", ""),
            "token_hint": token_hint,
            "token_len": token_len,
            "saved_at": saved_at,
        })

    def _handle_jira_config_put(self, body):
        user = self._require_auth()
        if not user:
            return
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        base_url = (data.get("base_url") or "").strip().rstrip("/")
        email = (data.get("email") or "").strip()
        token = (data.get("api_token") or "").strip()
        # Re-use the previously saved token when the caller explicitly chose
        # to keep it (token left blank in the UI). This is the main UX win
        # of the 2026-04-20g pass: the user can edit URL/email without
        # retyping the long API token, and they stop thinking "my token was
        # wiped" when the form opens with an empty token field.
        if not token:
            existing = self._jira_config_read(user) or {}
            prev_token = (existing.get("api_token") or "").strip()
            if prev_token:
                token = prev_token
        if not base_url or not email or not token:
            return self._send_json(
                {"error": "base_url, email and api_token are all required"}, 400
            )
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            return self._send_json(
                {"error": "base_url must start with http:// or https://"}, 400
            )
        # Optional smoke test: hit /myself to validate creds before saving.
        if not data.get("skip_validate"):
            try:
                self._jira_request(
                    {"base_url": base_url, "email": email, "api_token": token},
                    "/rest/api/3/myself",
                )
            except Exception as e:
                return self._send_json(
                    {"error": f"Jira credentials rejected: {e}"}, 401
                )
        try:
            self._jira_config_write(user, {
                "base_url": base_url,
                "email": email,
                "api_token": token,
            })
        except Exception as e:
            return self._send_json({"error": f"Failed to save: {e}"}, 500)
        # Return the same shape as GET so the UI can refresh the "Token
        # saved" chip (hint + len + timestamp) without a second roundtrip.
        if len(token) >= 12:
            token_hint = f"{token[:4]}...{token[-4:]}"
        else:
            token_hint = "****"
        saved_at = 0
        try:
            path = self._jira_config_path(user)
            if path and os.path.isfile(path):
                saved_at = int(os.path.getmtime(path))
        except OSError:
            saved_at = 0
        return self._send_json({
            "ok": True,
            "configured": True,
            "base_url": base_url,
            "email": email,
            "token_hint": token_hint,
            "token_len": len(token),
            "saved_at": saved_at,
        })

    def _handle_jira_config_delete(self):
        user = self._require_auth()
        if not user:
            return
        self._jira_config_delete(user)
        return self._send_json({"ok": True, "configured": False})

    # --- AI assistant credentials store ----------------------------------
    #
    # Byte-for-byte mirror of the Jira config pattern above. Each user has
    # one file at ~/.topology_users/<user>/ai_config.json (mode 0600)
    # holding {provider, model, api_key, base_url?}. The GET endpoint
    # NEVER echoes the api_key back -- only a masked hint + length + saved
    # timestamp. This keeps the frontend capable of showing "Key saved
    # 2h ago (sk-an...aB3)" without ever exposing the secret to a browser
    # console, session backup, or screenshot.
    #
    # All three handlers require a valid JWT via _require_auth(). No
    # shared / global file exists -- if the user has no config yet the
    # GET returns {"configured": False} and every AI route subsequently
    # responds 401 "AI assistant not configured" so the UI can surface
    # the inline config form.
    def _ai_config_path(self, username):
        if not username:
            return None
        user_dir = _ensure_user_workspace(username) or _user_xray_dir(username)
        if not user_dir:
            return None
        return os.path.join(user_dir, "ai_config.json")

    def _ai_config_read(self, username):
        path = self._ai_config_path(username)
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path) as f:
                cfg = json.load(f)
        except Exception:
            return None
        if not cfg.get("provider") or not cfg.get("api_key"):
            return None
        return cfg

    def _ai_config_write(self, username, cfg):
        path = self._ai_config_path(username)
        if not path:
            raise RuntimeError("No per-user workspace available")
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def _ai_config_delete(self, username):
        path = self._ai_config_path(username)
        if path and os.path.isfile(path):
            os.remove(path)

    @staticmethod
    def _ai_mask_key(token):
        """Return a short, non-sensitive hint for the stored API key.
        We echo 4 + 4 characters max -- enough for the user to recognize
        "the key I pasted last Tuesday" without leaking the secret.
        The "__server_shared__" placeholder (Gemini shared-key deploy
        mode) is a sentinel, not a real key -- surface that directly so
        the GUI banner reads naturally instead of "__se...red__".
        """
        token = token or ""
        if token == "__server_shared__":
            return "(shared server key)"
        if len(token) >= 12:
            return f"{token[:4]}...{token[-4:]}"
        if token:
            return "****"
        return ""

    def _handle_ai_config_get(self):
        user = self._require_auth()
        if not user:
            return
        # Expose whether the server has a deploy-wide Gemini key set so
        # the GUI's Quick-start hero can advertise "Use Gemini (free,
        # no setup)" when true and fall back to the local-Ollama hero
        # when false. Never echo the actual key value -- just a bool.
        shared_gemini = bool(os.environ.get("GEMINI_API_KEY", "").strip())
        cfg = self._ai_config_read(user) or {}
        stored_provider = (cfg.get("provider") or "").strip().lower()
        stored_api_key = cfg.get("api_key", "") or ""
        # Deploy-wide Gemini force-override. When the operator has
        # exported GEMINI_API_KEY, every user sees Gemini in the GUI
        # regardless of what's stored in their per-user config. The
        # single exception is the user who has explicitly saved
        # `provider=gemini` with their own personal AIza key -- we
        # let them keep their own key visible in the hint. This
        # matches the symmetrical override in ai/service.py's
        # resolve_client_for_user so the GUI display and the actual
        # LLM call stay consistent. The stored config is NOT rewritten
        # here: removing GEMINI_API_KEY instantly restores each user's
        # previous provider/model without a migration step.
        user_has_personal_gemini = (
            stored_provider == "gemini"
            and stored_api_key not in ("", "__server_shared__")
        )
        forced = shared_gemini and not user_has_personal_gemini
        saved_at = 0
        try:
            path = self._ai_config_path(user)
            if path and os.path.isfile(path):
                saved_at = int(os.path.getmtime(path))
        except OSError:
            saved_at = 0
        stored_tone = (cfg.get("tone") or "").strip().lower()
        if stored_tone not in ("senior", "junior"):
            stored_tone = "senior"
        if forced:
            # Preserve a stored Gemini model choice (e.g. gemini-2.5-pro)
            # so users who picked a specific Gemini variant keep it;
            # fall back to the canonical default otherwise.
            forced_model = ""
            if stored_provider == "gemini":
                forced_model = (cfg.get("model") or "").strip()
            if not forced_model:
                forced_model = "gemini-2.5-flash"
            return self._send_json({
                "configured": True,
                "provider": "gemini",
                "model": forced_model,
                "base_url": "",
                "token_hint": "(shared server key)",
                "token_len": 0,
                "saved_at": saved_at,
                "shared_gemini": True,
                "forced": True,
                "tone": stored_tone,
            })
        if not cfg:
            return self._send_json({
                "configured": False,
                "shared_gemini": shared_gemini,
                "forced": False,
                "tone": "senior",
            })
        return self._send_json({
            "configured": True,
            "provider": cfg.get("provider", ""),
            "model": cfg.get("model", ""),
            "base_url": cfg.get("base_url", ""),
            "token_hint": self._ai_mask_key(stored_api_key),
            "token_len": len(stored_api_key),
            "saved_at": saved_at,
            "shared_gemini": shared_gemini,
            "forced": False,
            "tone": stored_tone,
        })

    def _handle_ai_config_put(self, body):
        user = self._require_auth()
        if not user:
            return
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        provider = (data.get("provider") or "").strip().lower()
        model = (data.get("model") or "").strip()
        base_url = (data.get("base_url") or "").strip().rstrip("/")
        api_key = (data.get("api_key") or "").strip()
        # 2026-04-24r -- assistant personality. "senior" (default) keeps
        # the terse, DNOS-CLI-ready tone we ship today. "junior" expands
        # explanations, lists alternatives, and spells out acronyms on
        # first use. Any other string is ignored to keep the prompt
        # preamble deterministic.
        tone = (data.get("tone") or "").strip().lower()
        if tone not in ("senior", "junior"):
            tone = ""
        # Providers the server knows how to build a client for. Must stay
        # in sync with ai/service.py::resolve_client_for_user and with
        # PROVIDER_DEFAULTS. Ollama is special-cased below because its
        # local runtime doesn't need a key; Gemini is special-cased
        # because a server-wide GEMINI_API_KEY env var (set at deploy
        # time) lets every user use Gemini with an empty personal key.
        _ALLOWED = {"anthropic", "openai", "groq", "ollama", "gemini"}
        if provider not in _ALLOWED:
            return self._send_json(
                {"error": "provider must be one of: " + ", ".join(sorted(_ALLOWED))}, 400,
            )
        # Deploy-wide Gemini force-override: when the operator has set
        # GEMINI_API_KEY, this deployment is locked to Gemini. We reject
        # saves that pick a different provider so the user gets a clear
        # error ("Locked to Gemini by server admin") instead of a silent
        # save-then-invisibly-overridden experience. Gemini saves still
        # work normally, including picking a specific Gemini model or
        # pasting a personal AIza key that wins over the shared one.
        if provider != "gemini" and os.environ.get("GEMINI_API_KEY", "").strip():
            return self._send_json(
                {
                    "error": (
                        "This deployment is locked to Gemini via a shared "
                        "server key (GEMINI_API_KEY). Pick Gemini, or ask "
                        "your server admin to unset GEMINI_API_KEY to "
                        "re-enable other providers."
                    ),
                    "forced": True,
                }, 409,
            )
        # Reuse previously saved key when the caller explicitly left it
        # blank (same UX as the Jira editor -- no need to retype the
        # secret when tweaking model / base URL).
        if not api_key:
            existing = self._ai_config_read(user) or {}
            prev = (existing.get("api_key") or "").strip()
            if prev and (existing.get("provider") or "").lower() == provider:
                api_key = prev
        # Ollama ignores the Authorization header entirely -- the local
        # runtime has no concept of per-user auth. Stash a placeholder
        # so the on-disk config still has the required field and so
        # nothing downstream chokes on an empty string. The UI reflects
        # this by showing "not required for Local (Ollama)" in the key
        # field.
        if not api_key and provider == "ollama":
            api_key = "ollama"
        # Shared-key deployment knob: when the operator exports
        # GEMINI_API_KEY=AIza... in the server's environment, every user
        # can save provider=gemini with a blank key. The key itself is
        # NOT written to the user's on-disk config (which stays mode
        # 0600 per-user); resolve_client_for_user in ai/service.py reads
        # the env var at request time so rotating the shared key only
        # needs a service restart, not a config rewrite per user.
        if not api_key and provider == "gemini":
            shared_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
            if shared_gemini:
                api_key = "__server_shared__"
        if not api_key:
            return self._send_json({"error": "api_key is required"}, 400)
        if base_url and not (base_url.startswith("http://") or base_url.startswith("https://")):
            return self._send_json(
                {"error": "base_url must start with http:// or https://"}, 400,
            )
        # Default model if caller didn't pick one -- keeps first-time setup
        # friction low. We use the same defaults the UI shows.
        if not model:
            try:
                from ai.service import default_model_for
                model = default_model_for(provider) or ""
            except Exception:
                model = ""
        try:
            # Preserve previously saved tone when the caller doesn't
            # send one (provider-only saves from the settings panel
            # should not silently blow away the personality pick).
            if not tone:
                existing = self._ai_config_read(user) or {}
                tone = (existing.get("tone") or "").strip().lower()
                if tone not in ("senior", "junior"):
                    tone = "senior"
            self._ai_config_write(user, {
                "provider": provider,
                "model": model,
                "base_url": base_url,
                "api_key": api_key,
                "tone": tone,
            })
        except Exception as e:
            return self._send_json({"error": f"Failed to save: {e}"}, 500)
        saved_at = 0
        try:
            path = self._ai_config_path(user)
            if path and os.path.isfile(path):
                saved_at = int(os.path.getmtime(path))
        except OSError:
            saved_at = 0
        _shared = bool(os.environ.get("GEMINI_API_KEY", "").strip())
        # `forced` is True whenever the resolver / GET would override
        # this config to Gemini, so the frontend can surface the
        # "Locked to Gemini" banner immediately after a save instead
        # of waiting for the next GET to reveal the override.
        _forced = _shared and not (
            provider == "gemini" and api_key not in ("", "__server_shared__")
        )
        return self._send_json({
            "ok": True,
            "configured": True,
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "token_hint": self._ai_mask_key(api_key),
            "token_len": len(api_key),
            "saved_at": saved_at,
            "shared_gemini": _shared,
            "forced": _forced,
            "tone": tone,
        })

    def _handle_ai_config_delete(self):
        user = self._require_auth()
        if not user:
            return
        self._ai_config_delete(user)
        return self._send_json({"ok": True, "configured": False})

    def _handle_ai_ollama_models(self):
        """List models actually installed on the local Ollama runtime.

        Why this exists: the UI used to render a hardcoded model list
        (`llama3.1:8b-instruct`, `llama3.3:70b-instruct`, ...). If the
        admin hadn't run `ollama pull` for that exact tag, picking one
        would produce a "model not found" chat error at first send.
        Querying `/api/tags` lets the UI show ONLY what's really on
        disk, so there's nothing to mis-pick.

        Auth is still required so we don't expose local server
        inventory to anonymous callers -- it is information-light but
        there is no reason to leak it either.
        """
        user = self._require_auth()
        if not user:
            return
        try:
            import urllib.request as _ur
            req = _ur.Request("http://127.0.0.1:11434/api/tags",
                              headers={"Accept": "application/json"})
            with _ur.urlopen(req, timeout=3) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            # Keep the failure shape simple so the UI just has to branch
            # on `ok`. The common cases are "Ollama not installed",
            # "service down", or "port busy" -- we bundle all of them
            # as unreachable and surface the string for debugging.
            return self._send_json({
                "ok": False,
                "installed": False,
                "error": f"Ollama runtime not reachable at localhost:11434 ({exc})",
                "models": [],
            }, 200)
        raw = payload.get("models") or []
        models = []
        for m in raw:
            name = (m.get("name") or "").strip()
            if not name:
                continue
            size_bytes = int(m.get("size") or 0)
            details = m.get("details") or {}
            models.append({
                "id": name,
                "size_mb": round(size_bytes / (1024 * 1024), 1) if size_bytes else 0,
                "family": (details.get("family") or "").lower(),
                "parameter_size": details.get("parameter_size") or "",
                "quantization_level": details.get("quantization_level") or "",
            })
        models.sort(key=lambda r: r["id"])
        return self._send_json({
            "ok": True,
            "installed": True,
            "models": models,
            "count": len(models),
        })

    # --- AI chat + topology generation ----------------------------------
    #
    # Two thin routes share the same plumbing:
    #   - /api/ai/chat             : Q&A or small canvas edits (text only
    #                                in Phase A; tool_use wiring is ready
    #                                for Phase B's edit/focus tools).
    #   - /api/ai/topology/generate: always emits the `create_topology`
    #                                tool; response carries a validated
    #                                topology payload + the saved file's
    #                                section_id + filename.
    #
    # Both routes:
    #   1. _require_auth() -> username.
    #   2. resolve_client_for_user(username) -> LlmClient (or 401 if the
    #      user has not configured a key yet).
    #   3. _build_ai_system_prompt(username, ctx) -> knowledge digest +
    #      live context summary.
    #   4. client.chat(messages, tools=..., ...) -> normalized response.
    #
    # Everything persists under ~/.topology_users/<user>/ via the shared
    # section helpers (`__ai` domain).
    def _ai_build_messages(self, data):
        """Turn an incoming {messages:[{role,content}], message?:str} into
        a pair (system_extras, chat_messages) where:
          - system_extras: optional free-text block appended to the system prompt
          - chat_messages: [{role: user|assistant, content: str}, ...]
        """
        messages = data.get("messages")
        single = (data.get("message") or "").strip()
        if isinstance(messages, list) and messages:
            chat_messages = []
            # 2026-04-24r -- bumped 20 -> 40 so mid-session follow-ups
            # ("that fabric we just made") keep working. Each turn is
            # capped at `MAX_CONTENT_BYTES` server-side, so 40 turns
            # still fit comfortably in every supported provider's
            # context window. SQLite retains the full transcript.
            for m in messages[-40:]:
                if not isinstance(m, dict):
                    continue
                role = (m.get("role") or "").strip()
                content = m.get("content")
                if role not in ("user", "assistant") or not isinstance(content, str):
                    continue
                content = content.strip()
                if content:
                    chat_messages.append({"role": role, "content": content})
            return "", chat_messages
        if single:
            return "", [{"role": "user", "content": single}]
        return "", []

    def _build_ai_system_prompt(self, username, canvas_snapshot):
        """Compose the system prompt for an AI turn.

        Layout:
          1. Knowledge digest (static, ~5 KB).
          2. Live per-user / per-canvas context block (~<6 KB), JSON.
          3. Hard rules (tool use contract).
        """
        if not _ai_available or _ai_module is None:
            raise RuntimeError("AI assistant module not available")
        from ai.service import load_knowledge_digest
        from ai.context import build_live_context
        knowledge = load_knowledge_digest() or ""
        ctx = build_live_context(username, canvas_snapshot)
        try:
            ctx_json = json.dumps(ctx, separators=(",", ":"))
        except Exception:
            ctx_json = "{}"
        # 2026-04-24r -- surface the one-line narrative canvas summary
        # ABOVE the JSON block. Even small models consistently use this
        # line ("Canvas has 3 PEs, 2 Ps, 6 links on 'fabric'.") to
        # pick the right follow-up action; the structured JSON below
        # stays authoritative for exact ids / coords / labels.
        canvas_prose = ""
        try:
            cur = (ctx or {}).get("current") or {}
            prose = (cur.get("summary") or "").strip()
            if prose:
                canvas_prose = f"**Canvas now:** {prose}\n\n"
        except Exception:
            canvas_prose = ""
        # 2026-04-24r -- assistant tone preamble. Inserted first so a
        # cheap/small model uses it as its top priority; the hard rules
        # still come last (where tool-use must be respected).
        tone_preamble = ""
        try:
            _cfg = self._ai_config_read(username) or {}
            _tone = (_cfg.get("tone") or "").strip().lower()
            if _tone == "junior":
                tone_preamble = (
                    "## Tone\n\n"
                    "You are speaking with a junior network engineer. Spell "
                    "out acronyms on first use (iBGP = internal BGP, RR = "
                    "route reflector, ...). When you propose a design, briefly "
                    "list one credible alternative and say why you picked the "
                    "one you did. Prefer short paragraphs over dense bullet "
                    "lists. Never dump more than 6 bullets at once.\n\n"
                )
            else:
                tone_preamble = (
                    "## Tone\n\n"
                    "You are speaking with a senior DNOS engineer. Be terse. "
                    "Use standard abbreviations (iBGP, eBGP, RR, VRF, SID) "
                    "without expansion. Skip the hand-holding, skip "
                    "introductions. When asked 'why', give the trade-off "
                    "in one line. Prefer compact bullet lists and exact "
                    "DNOS CLI syntax when relevant.\n\n"
                )
        except Exception:
            tone_preamble = ""
        # Splice in a tiny catalog of the blueprint library so the model
        # knows the names it can pass to load_blueprint without having
        # to call list_blueprints({}) first. The full metadata is still
        # available via list_blueprints -- this is just a hint so the
        # model picks the right blueprint on turn 1 when it's obvious.
        blueprint_catalog = ""
        try:
            from ai.blueprints import blueprint_summary_for_prompt
            summary = blueprint_summary_for_prompt(username=username)
            if summary:
                blueprint_catalog = (
                    "\n\n## Blueprint library (call `load_blueprint` to fetch)\n\n"
                    f"{summary}\n\n"
                    "Use `list_blueprints` for filter search (protocol/scale/tags/query)."
                )
        except Exception:
            pass
        rules = (
            "Hard rules for tool use:\n"
            "- For professional protocol topologies of ANY kind "
            "(BGP, OSPF, ISIS, MPLS-L3VPN, EVPN-VXLAN, SR, Clos, campus, "
            "DCI, DNAAS, multicast, DC fabric, metro ring, traffic "
            "engineering, QoS/DiffServ/HQoS, HA/VRRP/BFD, IPsec/GRE/"
            "DMVPN site-to-site VPN, L2VPN/VPLS/VPWS, STP/RSTP/MSTP, "
            "FlowSpec/RTBH/DDoS, RPKI peering, BNG/PPPoE broadband, "
            "5G xHaul/CSR mobile, NAT/CGNAT, routing-policy, "
            "telemetry/gNMI), ALWAYS `list_blueprints` + `load_blueprint` "
            "first, then ADAPT the returned objects into `create_topology`."
            " The blueprints carry the correct per-protocol colors, AS "
            "/ area grouping shapes, and RD/RT/VRF text boxes that your "
            "free-form output lacks.\n"
            "- CONCEPT SEARCH is supported: when the user's word is not a "
            "literal protocol, pass it straight to `list_blueprints("
            "protocol=<concept>)` or `list_blueprints(query=<free text>)`."
            " The loader expands every concept through an alias map. "
            "Examples of concepts that WILL resolve: multicast, dc, "
            "fabric, overlay, underlay, te, metro, dci, qos, ha, vpn, "
            "ipsec, nat, stp, l2vpn, security, flowspec, rpki, broadband,"
            " bng, mobile, 5g, xhaul, telemetry, gnmi, ecmp, dualstack, "
            "sdwan. NEVER answer 'I couldn't find any blueprints for X' "
            "before trying the concept search.\n"
            "- COMPOSE when no exact match exists. 'Multicast on MPLS' = "
            "load `mvpn-mpls-2pe`. 'IGP with multicast' = load an OSPF/"
            "ISIS blueprint, add PIM-enabled links on top. 'EVPN fabric "
            "with multicast' = load `2spine-4leaf-anycast-gw` + IGMP "
            "snooping on VTEPs. 'MPLS L3VPN with QoS' = load "
            "`mpls-l3vpn/2pe-1ce-basic` + QoS class annotations from "
            "`qos/qos-diffserv-pe`. 'Campus with HA' = campus blueprint "
            "+ VRRP overlay. Explain the composition briefly first.\n"
            "- TOPOLOGY QUALITY CONTRACT: generated topologies must be "
            "detailed but simplified. Match the user's exact protocol, "
            "scale, site count, vendor/role words, and requested intent. "
            "For an unspecified scale, use 5-10 devices; only go larger "
            "when the user asks. Every whole-topology output should include "
            "semantic linkType/color/style, clear role labels, AS/site/area/"
            "tenant grouping shapes when applicable, and 2-5 concise text "
            "callouts explaining the key control-plane or service flow. "
            "Avoid one giant title as the only explanation, and avoid "
            "overcrowding the canvas with paragraph-sized text boxes. "
            "Text callouts must be short chips, placed outside device icons "
            "and away from each other; never stack multiple text objects at "
            "the same x/y or over a router label.\n"
            "- PROTOCOL-SPECIFIC DETAIL: if the user names a protocol "
            "(MSDP, MVPN, EVPN, OSPF, ISIS, RSVP-TE, FlowSpec, BNG, etc.), "
            "show the minimum moving parts that make that protocol real: "
            "speakers/controllers, route/session direction, source and "
            "receiver/customer roles, and boundary points. Use arrows and "
            "short labels for the traffic/control-plane direction.\n"
            "- INTENT RECOGNITION (match verb + object, do NOT ask for "
            "clarification):\n"
            "  * 'make it redundant' / 'dual-home' / 'add HA' = clone "
            "target device, mirror its links, add a VRRP overlay + BFD.\n"
            "  * 'make it dual-stack' / 'add IPv6' = append IPv6 "
            "addresses to device labels, note dual-stack on each link.\n"
            "  * 'scale to N' / 'double the leaves' = clone tier, "
            "rewire to preserve fabric rules, grow grouping shapes.\n"
            "  * 'convert X to Y' / 'replace LDP with SR' = swap "
            "linkType on matching links, keep devices / shapes intact.\n"
            "  * 'group by X' / 'color by tenant' = add labelled "
            "rectangle/ellipse shapes around each group (8% fill).\n"
            "  * 'add to every X' / 'label every /31' = emit ONE "
            "`apply_canvas_edits` with one edit per matching device.\n"
            "  * 'why X vs Y' / 'explain' = plain-text answer, no "
            "tool call.\n"
            "  * 'mirror to a DR site' / 'clone to second region' = "
            "duplicate all devices with -dr suffix, offset +1200px, "
            "fresh IP/ASN scheme, wrap in 'DR Site' shape, add DCI links.\n"
            "  * 'troubleshoot why X isn't working' = if canvas-visible "
            "(missing link/IP/mismatch) point it out; if needs live "
            "state, say 'paste show-output and I'll read it'.\n"
            "- Call `create_topology` when the user asks to create / "
            "build / generate / make / draw a WHOLE topology from scratch.\n"
            "- Call `apply_canvas_edits` when the user asks to ADD / "
            "REMOVE / CONNECT / MOVE / RENAME objects on the CURRENT "
            "canvas. Prefer this for incremental changes. Set `role` on "
            "new devices (spine/leaf/pe/ce/rr/...) instead of guessing x/y.\n"
            "- TOPOLOGY-GENERATOR ENRICHMENT (intent='topology-enrich' or "
            "the user just clicked 'AI enrich'): the canvas already "
            "carries devices and links produced by the deterministic "
            "generator. Do NOT call `create_topology` -- that would wipe "
            "the canvas. Instead emit ONE `apply_canvas_edits` batch "
            "that ADDS detail on top: `style` ops to assign protocol "
            "colors per linkType (iBGP blue dashed, eBGP orange arrow, "
            "OSPF green, ISIS purple, MPLS red, EVPN teal dashed-wide, "
            "DNAAS orange) and to stamp link-table fields "
            "`interface1`/`interface2`/`vlan`/`bd`/`linkDetails` on "
            "links that have real interface or VLAN data; `add_shape` "
            "ops with fillOpacity 0.06-0.12 for AS / area / VRF / BD "
            "grouping (rectangles for AS/site, ellipses for OSPF area); "
            "`add_text` ops for AS numbers, RD/RT, VRF names, dual-"
            "stack callouts; and `relabel`/`style` ops to nudge "
            "device colors per role. Keep every existing device and "
            "link intact -- enrichment is additive, never destructive.\n"
            "- For every other question (explanations, tips, reviews of "
            "existing objects, troubleshooting), respond in plain text.\n"
            "- Never echo a raw topology JSON in plain text -- use a tool.\n"
            "- Keep text replies short: 1-3 paragraphs or a compact bullet list."
        )
        return (
            f"{tone_preamble}"
            f"{knowledge}"
            f"{blueprint_catalog}\n\n"
            f"## Live context (read-only, refreshed every turn)\n\n"
            f"{canvas_prose}"
            f"```json\n{ctx_json}\n```\n\n"
            f"{rules}"
        )

    # --- 429 / rate-limit helper ----------------------------------------
    #
    # Hosted providers (Gemini free tier, Groq, OpenAI free / shared key,
    # ...) routinely return 429 for a few seconds after a heavy turn.
    # A single automatic retry -- respecting whatever `retry-after` hint
    # the provider buried in the response body -- eliminates ~80% of
    # the "Rate limit hit on Gemini" red cards users see after quick
    # back-to-back prompts, WITHOUT risking an infinite loop: we retry
    # EXACTLY ONCE and then surface the original error if it repeats.
    # 2026-04-24k -- raised from 10 s to 30 s after user hit a
    # Gemini free-tier 429 that kept recurring on the first two
    # retry attempts (10 s wasn't enough to clear the 60 s rolling
    # quota window). 30 s fits inside the `default_timeout = 60`
    # budget for hosted providers and is small enough that a
    # legitimately stuck call still fails fast.
    _AI_RATE_RETRY_MAX_WAIT_S = 30
    _AI_RATE_RETRY_MIN_WAIT_S = 1   # give the provider a moment even
                                     # when it didn't return a hint

    # 2026-04-24t -- per-provider model fallback ladders.
    #
    # Google's free-tier quotas are enforced PER MODEL (each flash variant
    # has its own 20 req/day / 1M TPM bucket). When the user hit their
    # daily cap on `gemini-2.5-flash`, the old pipeline raised
    # insufficient_quota and ALL subsequent turns showed a red card even
    # though a sibling model (e.g. `gemini-flash-latest` or
    # `gemini-2.5-flash-lite`) still had plenty of quota on the same key.
    # The ladder below is walked once the primary model has exhausted its
    # retry attempts; each step swaps `client.model` and reissues the
    # call exactly once. The "-latest" aliases are FIRST because Google
    # auto-routes them to whichever specific version has capacity, which
    # side-steps per-model rate limits the cleanest. Original model is
    # restored after the chat returns so subsequent turns start from the
    # user-chosen model again (we never rewrite the stored config).
    #
    # Each entry is a list[str] of model IDs to try in order. Kind is the
    # failure classification that triggers a fallback.
    _AI_MODEL_FALLBACKS = {
        "gemini": [
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-3.1-flash-lite-preview",
        ],
    }
    # Kinds that should trigger a model swap (quota / overload / rate).
    # These are distinct from auth/context errors where a model change
    # wouldn't help. insufficient_quota is the most common trigger: the
    # user's Gemini free-tier daily cap burned through on one model but
    # sibling models on the same key still have capacity.
    _AI_MODEL_FALLBACK_KINDS = (
        "insufficient_quota",
        "rate_limited",
        "upstream_overloaded",
    )

    @staticmethod
    def _parse_retry_after_seconds(details):
        """Extract a seconds-to-wait value from an LLM provider's 429
        response body.

        Covers the two common formats:
          * Groq / OpenAI: ``"Please try again in 1.615s"`` /
            ``"try again in 45 seconds"``.
          * Anthropic / Gemini: they put it in the `retry-after` HTTP
            header which we don't capture today, so we fall back to
            MIN_WAIT. (If you decide to thread the full HTTPError
            through, plug the header in here.)
        Returns None when no hint was found -- caller decides whether
        to use MIN_WAIT or to skip the retry entirely.
        """
        if not details:
            return None
        try:
            # 2026-04-24k -- broadened from `try\s+again\s+in` only to
            # ALSO catch Gemini's phrasing `"Please retry in 10.6s"`
            # and the structured `google.rpc.RetryInfo` field
            # `"retryDelay": "10s"`. Before this fix the regex missed
            # both Gemini formats and fell back to MIN_WAIT (1 s), so
            # we retried too fast against a provider that had just
            # told us exactly how long to wait.
            m = re.search(
                r"(?:try\s+again|retry)\s+in\s+([0-9]+(?:\.[0-9]+)?)\s*(s|sec|seconds?)?",
                details,
                flags=re.IGNORECASE,
            )
            if m:
                return float(m.group(1))
            # Structured RetryInfo: `"retryDelay": "10s"` (google.rpc).
            m = re.search(
                r'"retryDelay"\s*:\s*"([0-9]+(?:\.[0-9]+)?)\s*s"',
                details,
            )
            if m:
                return float(m.group(1))
        except Exception:
            pass
        return None

    def _ai_chat_with_rate_retry(self, client, messages, **chat_kwargs):
        """Call ``client.chat`` with automatic backoff-retries on
        transient upstream errors.

        Returns ``(raw_response, retry_info)`` where ``retry_info`` is
        either ``None`` (no retry needed) or
        ``{"wait_s": <float>, "provider": <str>, "attempts": <int>,
          "kind": <str>}`` so the caller can surface a "⚡ auto-
        recovered from X" chip in the UI.

        2026-04-24h -- broadened from "single retry on 429" to "up to
        three retries on rate_limited / upstream_overloaded /
        cf_bot_blocked" after reports that Gemini's ``gemini-2.5-flash``
        endpoint was flapping between 200 and 503 UNAVAILABLE
        ("This model is currently experiencing high demand. Spikes
        in demand are usually temporary."). One retry was not enough
        -- a second 503 within 1-2 s is common during a spike and
        was surfacing to the user as a red card that they had to
        click "retry" on manually. Three attempts with exponential
        backoff covers the common ~5 s overload window without
        pushing total wall-clock above the user-visible budget.

        The retry loop uses the same kwargs except ``timeout`` which
        we trim by the time we slept so we never extend the user-facing
        wall-clock past the original budget. Anything classified as a
        permanent error (api_key_rejected / insufficient_quota /
        model_not_found / context_overflow / timeout / unreachable /
        upstream_error) bubbles up unchanged on the FIRST occurrence.
        """
        from ai.service import LlmError
        RETRYABLE_KINDS = ("rate_limited", "upstream_overloaded", "cf_bot_blocked")
        # 3 total attempts: 1 initial + up to 2 retries.
        MAX_ATTEMPTS = 3
        provider = (getattr(client, "provider_name", "") or "").lower()
        original_model = getattr(client, "model", "") or ""
        # Derive the fallback ladder now so we can restore the client to
        # its original state in `finally` regardless of which branch the
        # fallback loop exits on. We SKIP the user's current model to
        # avoid a wasted retry against the same bucket we just exhausted.
        fallback_chain = [
            m for m in (self._AI_MODEL_FALLBACKS.get(provider) or [])
            if m and m != original_model
        ]
        model_path = []  # type: list  # models we actually attempted
        last_exc = None
        last_retry_info = None
        try:
            for step_idx, model_name in enumerate([original_model] + fallback_chain):
                # Step 0 is the user-selected model. Steps 1+ are fallbacks
                # and get marked in retry_info.fallback so the UI can pop
                # a small "answered by <model> (your <chosen> was out of
                # quota)" chip -- silent swaps erode trust.
                client.model = model_name
                model_path.append(model_name)
                slept_total = 0.0
                kw = dict(chat_kwargs)
                original_timeout = int(kw.get("timeout") or 60)
                step_fatal_exc = None  # type: ignore[assignment]
                for attempt in range(1, MAX_ATTEMPTS + 1):
                    try:
                        raw = client.chat(messages, **kw)
                        if step_idx == 0 and attempt == 1 and last_retry_info is None:
                            # Fully clean happy path.
                            return raw, None
                        # Either we retried on the same model, or we
                        # swapped models. Either way, surface it.
                        retry_info = {
                            "wait_s": round(slept_total, 2),
                            "provider": provider,
                            "attempts": attempt,
                            "kind": getattr(last_exc, "kind", "") if last_exc else "",
                        }
                        if step_idx > 0:
                            # Model-fallback metadata lets the frontend
                            # render a different chip ("answered by X
                            # because your Y was quota-exhausted")
                            # instead of the generic retry pill.
                            retry_info["fallback"] = {
                                "from_model": original_model,
                                "to_model": model_name,
                                "tried_models": list(model_path),
                                "reason_kind": getattr(last_exc, "kind", "") if last_exc else "",
                            }
                        return raw, retry_info
                    except LlmError as exc:
                        last_exc = exc
                        kind = getattr(exc, "kind", "") or ""
                        if kind not in RETRYABLE_KINDS:
                            # Non-transient failure on this model. If it's
                            # a quota / fallback-eligible kind AND we have
                            # sibling models left, jump to the next model
                            # immediately (no backoff -- the new model
                            # has its own bucket). Otherwise raise.
                            if (
                                kind in self._AI_MODEL_FALLBACK_KINDS
                                and step_idx < len(fallback_chain)
                            ):
                                step_fatal_exc = exc
                                break  # outer loop moves to next model
                            raise
                        if attempt >= MAX_ATTEMPTS:
                            # Exhausted retries on THIS model for a
                            # retryable kind. Move to the next fallback
                            # model if available; otherwise re-raise.
                            if (
                                kind in self._AI_MODEL_FALLBACK_KINDS
                                and step_idx < len(fallback_chain)
                            ):
                                step_fatal_exc = exc
                                break
                            raise
                        # Same-model retry path.
                        hint_s = self._parse_retry_after_seconds(getattr(exc, "details", ""))
                        if hint_s is not None:
                            wait_s = max(self._AI_RATE_RETRY_MIN_WAIT_S,
                                         min(hint_s + 0.25, self._AI_RATE_RETRY_MAX_WAIT_S))
                        else:
                            wait_s = min(self._AI_RATE_RETRY_MAX_WAIT_S,
                                         self._AI_RATE_RETRY_MIN_WAIT_S * (2 ** (attempt - 1)))
                        try:
                            _record_audit(
                                "ai_rate_retry",
                                username=None,
                                detail={
                                    "attempt": attempt,
                                    "wait_s": round(wait_s, 2),
                                    "kind": kind,
                                    "provider": provider,
                                    "model": model_name,
                                },
                            )
                        except Exception:
                            pass
                        time.sleep(wait_s)
                        slept_total += wait_s
                        kw["timeout"] = max(5, original_timeout - int(slept_total) - 1)
                if step_fatal_exc is not None:
                    # Log the model swap so operators can see the ladder
                    # in motion. If every sibling also fails, the final
                    # raise at the bottom surfaces the LAST model's
                    # error to the user.
                    try:
                        _record_audit(
                            "ai_model_fallback",
                            username=None,
                            detail={
                                "from_model": model_name,
                                "kind": getattr(step_fatal_exc, "kind", ""),
                                "provider": provider,
                                "next_model": (
                                    fallback_chain[step_idx]
                                    if step_idx < len(fallback_chain) else None
                                ),
                            },
                        )
                    except Exception:
                        pass
                    last_retry_info = {
                        "swapped_from": model_name,
                        "kind": getattr(step_fatal_exc, "kind", ""),
                    }
                    continue
            # Fell through without a successful return and without re-
            # raising: every ladder step either raised or hit a fallback
            # branch. Re-raise the last error so the frontend renders
            # the proper error card.
            if last_exc is not None:
                raise last_exc
            raise RuntimeError("AI retry loop exited without return; this is a bug")
        finally:
            # Always restore the original model so the next turn starts
            # from the user's chosen model. Otherwise a successful
            # fallback would silently "sticky" the fallback model on
            # the client instance for the remainder of the request.
            try:
                client.model = original_model
            except Exception:
                pass

    # --- AI blueprint tool resolution ----------------------------------
    #
    # The blueprint library (topology/ai/blueprints/) ships read-only
    # reference topologies. The AI assistant discovers them via
    # `list_blueprints` and fetches them via `load_blueprint`. Both tools
    # are resolved SERVER-SIDE inside the chat turn: we run the lookup,
    # feed the result back into the conversation, and let the model
    # continue until it emits a terminal tool (create_topology /
    # apply_canvas_edits) or plain text.
    #
    # Provider-specific message reconstruction is confined to
    # `_ai_append_tool_turn` below; the loop itself is provider-agnostic.
    _AI_BLUEPRINT_TOOLS = ("list_blueprints", "load_blueprint")
    _AI_MAX_BLUEPRINT_ITERATIONS = 3

    # ---- Topology clarify preflight (broad prompt -> chips / instant) ---
    # Machine-routed chip values for instant standard blueprints. Kind /
    # custom chips use natural-language values so the transcript stays
    # readable for the model on the next turn.
    _AI_TOPO_DEFAULT_PREFIX = "__AI_TOPO__/default/"
    _AI_TOPO_DEFAULT_BLUEPRINT_STEM: Dict[str, str] = {
        "bgp": "ibgp-rr-hub-spoke-6",
        "evpn": "2spine-4leaf-anycast-gw",
        "mpls": "2pe-1ce-basic",
        "ospf": "single-area-5",
        "isis": "pure-l2-backbone",
        "clos": "3stage-2x4",
    }

    def _ai_is_broad_topology_prompt(self, text: str) -> bool:
        """True when the user asks for a new topology without enough detail.

        Broad examples: 'generate a BGP topology', 'make an EVPN fabric'.
        Specific examples (return False): counts (2 spine 4 leaf), RR /
        full-mesh / transit wording, AS numbers, etc.
        """
        if not text or not isinstance(text, str):
            return False
        raw = text.strip()
        if raw.startswith("__AI_TOPO__/"):
            return False
        t = raw.lower()
        if len(t) > 2000:
            return False
        # Q&A / explainers are never generation preflight.
        if re.search(
            r"\b(how\s+do|how\s+does|what\s+is|what\s+are|explain|why|"
            r"tutorial|documentation|docs?)\b",
            t,
        ):
            return False
        # DNOS-style config asks without a diagram noun -- do not hijack.
        if re.search(
            r"\b(config|configuration|cli|syntax|command|knob|set |"
            r"delete |commit)\b",
            t,
        ) and not re.search(
            r"\b(topolog|diagram|fabric|canvas|lab)\b",
            t,
        ):
            return False
        # Enough design detail already present -> skip clarify.
        if re.search(
            r"\b(\d+\s*(x\s*)?(spine|leaf|router|routers|tor|pe|ce|"
            r"rack|node|nodes|site|sites|asbr|abr)\b|"
            r"route\s*reflector|\brrs?\b|full\s*mesh|hub[\s-]?spoke|"
            r"route\s*server|transit|confederation|"
            r"as\s*\d{2,5}|asn\s*\d{2,5}|"
            r"clos\s*\d|\d+\s*spine|\d+\s*leaf)\b",
            t,
        ):
            return False
        has_gen = bool(
            re.search(
                r"\b(generate|create|make|draw|build|design|"
                r"give me|show me|i want|i need|want a|need a|sketch)\b",
                t,
            )
        )
        has_topo_ctx = bool(
            re.search(
                r"\b(topolog(y|ies)|network\s+diagram|diagram|canvas|"
                r"fabric|lab(\s+setup)?|dc\s+fabric|data\s*center)\b",
                t,
            )
        )
        has_proto = bool(
            re.search(
                r"\b(bgp|ibgp|ebgp|evpn|vxlan|mpls|ospf|is-?is|isis|"
                r"pim|ldp|l3vpn|sr[\s-]?mpls|segment\s+routing|"
                r"clos|leaf[\s-]?spine|igp|wan)\b",
                t,
            )
        )
        if not has_proto:
            return False
        if not has_gen and not (has_topo_ctx and len(t) < 200):
            return False
        return True

    def _ai_broad_topology_family(self, text: str) -> str:
        """Return a coarse protocol/style bucket for question + defaults."""
        t = (text or "").lower()
        if re.search(r"\b(evpn|vxlan)\b", t):
            return "evpn"
        if re.search(r"\b(mpls|l3vpn|ldp|rsvp)\b", t):
            return "mpls"
        if re.search(r"\bospf\b", t):
            return "ospf"
        if re.search(r"\bis-?is\b|\bisis\b", t):
            return "isis"
        if re.search(r"\b(clos|leaf[\s-]?spine|data\s*center|datacenter|dc)\b", t):
            return "clos"
        if re.search(r"\b(bgp|ibgp|ebgp)\b", t):
            return "bgp"
        return "generic"

    def _ai_topology_preflight_question(self, family: str) -> Dict[str, Any]:
        """ask_user_question args for ``family`` (2-5 options, allow_free_text)."""
        fam = (family or "generic").strip().lower()
        if fam == "bgp":
            return {
                "question": (
                    "Which BGP style should I build? Pick a shortcut or add "
                    "details below."
                ),
                "options": [
                    {
                        "label": "Standard BGP lab",
                        "value": f"{self._AI_TOPO_DEFAULT_PREFIX}bgp",
                    },
                    {
                        "label": "iBGP route reflector",
                        "value": (
                            "Generate an iBGP route-reflector topology with "
                            "redundant RRs and several PE/CE spokes; include "
                            "session roles in labels."
                        ),
                    },
                    {
                        "label": "eBGP edge/transit",
                        "value": (
                            "Generate an eBGP multi-AS edge or transit topology "
                            "with clear AS boundaries and peering points."
                        ),
                    },
                    {
                        "label": "EVPN/VXLAN fabric",
                        "value": (
                            "Generate an EVPN/VXLAN fabric topology with "
                            "spine–leaf and anycast gateway roles."
                        ),
                    },
                    {
                        "label": "Something else…",
                        "value": (
                            "Custom topology: describe the BGP scenario, scale "
                            "(router counts / sites), AS numbers, and roles "
                            "you want next."
                        ),
                    },
                ],
                "allow_free_text": True,
            }
        if fam == "evpn":
            return {
                "question": (
                    "What kind of EVPN/VXLAN diagram should I generate?"
                ),
                "options": [
                    {
                        "label": "Standard EVPN lab",
                        "value": f"{self._AI_TOPO_DEFAULT_PREFIX}evpn",
                    },
                    {
                        "label": "Multi-tenant fabric",
                        "value": (
                            "Generate a multi-tenant EVPN/VXLAN topology with "
                            "distinct VNIs/tenants and anycast gateways."
                        ),
                    },
                    {
                        "label": "DCI / WAN extension",
                        "value": (
                            "Generate an EVPN-based DCI or WAN extension "
                            "topology between sites."
                        ),
                    },
                    {
                        "label": "Something else…",
                        "value": (
                            "Custom topology: describe EVPN use case, VNI/BD "
                            "needs, and scale for the next turn."
                        ),
                    },
                ],
                "allow_free_text": True,
            }
        if fam == "mpls":
            return {
                "question": "Which MPLS/L3VPN style fits best?",
                "options": [
                    {
                        "label": "Standard MPLS L3VPN lab",
                        "value": f"{self._AI_TOPO_DEFAULT_PREFIX}mpls",
                    },
                    {
                        "label": "Multi-site VPN",
                        "value": (
                            "Generate a multi-site MPLS L3VPN topology with "
                            "several PEs and central services."
                        ),
                    },
                    {
                        "label": "TE / SR-MPLS",
                        "value": (
                            "Generate an MPLS topology emphasizing TE or "
                            "segment-routing paths and PE/P roles."
                        ),
                    },
                    {
                        "label": "Something else…",
                        "value": (
                            "Custom topology: describe MPLS services, PE/CE "
                            "counts, and sites for the next turn."
                        ),
                    },
                ],
                "allow_free_text": True,
            }
        if fam == "ospf":
            return {
                "question": "What OSPF scenario should I draw?",
                "options": [
                    {
                        "label": "Standard single-area lab",
                        "value": f"{self._AI_TOPO_DEFAULT_PREFIX}ospf",
                    },
                    {
                        "label": "Multi-area hierarchy",
                        "value": (
                            "Generate a multi-area OSPF topology with ABRs "
                            "and clear area boundaries."
                        ),
                    },
                    {
                        "label": "Something else…",
                        "value": (
                            "Custom topology: describe OSPF areas, router "
                            "counts, and external connectivity for the next turn."
                        ),
                    },
                ],
                "allow_free_text": True,
            }
        if fam == "isis":
            return {
                "question": "What IS-IS layout should I use?",
                "options": [
                    {
                        "label": "Standard IS-IS backbone lab",
                        "value": f"{self._AI_TOPO_DEFAULT_PREFIX}isis",
                    },
                    {
                        "label": "Multi-level (L1/L2)",
                        "value": (
                            "Generate an IS-IS topology with L1/L2 boundaries "
                            "and route leaking between levels."
                        ),
                    },
                    {
                        "label": "Something else…",
                        "value": (
                            "Custom topology: describe IS-IS levels, sites, "
                            "and router roles for the next turn."
                        ),
                    },
                ],
                "allow_free_text": True,
            }
        if fam == "clos":
            return {
                "question": "What data-center fabric detail do you want?",
                "options": [
                    {
                        "label": "Standard 3-stage Clos",
                        "value": f"{self._AI_TOPO_DEFAULT_PREFIX}clos",
                    },
                    {
                        "label": "EVPN/VXLAN overlay",
                        "value": (
                            "Generate a leaf-spine Clos fabric with EVPN/VXLAN "
                            "overlay and anycast gateways."
                        ),
                    },
                    {
                        "label": "Something else…",
                        "value": (
                            "Custom topology: specify spine/leaf counts, "
                            "overlay protocol, and tenant needs for the next turn."
                        ),
                    },
                ],
                "allow_free_text": True,
            }
        # generic / unknown protocol bucket
        return {
            "question": (
                "What style of reference topology should I generate?"
            ),
            "options": [
                {
                    "label": "Standard 3-stage Clos",
                    "value": f"{self._AI_TOPO_DEFAULT_PREFIX}clos",
                },
                {
                    "label": "BGP WAN/edge",
                    "value": (
                        "Generate a BGP-centric WAN or edge topology with "
                        "clear peering and AS boundaries."
                    ),
                },
                {
                    "label": "EVPN/VXLAN fabric",
                    "value": (
                        "Generate an EVPN/VXLAN spine–leaf fabric topology."
                    ),
                },
                {
                    "label": "Something else…",
                    "value": (
                        "Custom topology: name the protocols, scale, and "
                        "sites you want in your next message."
                    ),
                },
            ],
            "allow_free_text": True,
        }

    def _ai_topology_preflight_instant_blueprint(
        self,
        *,
        user: str,
        family_key: str,
        conv_store,
        conversation_id,
        active_conv,
        data,
        client,
    ) -> Optional[Dict[str, Any]]:
        """Build a create_topology pending_placement response or None."""
        try:
            from ai.blueprints import load_blueprint as _load_bp
            from ai.context import normalize_topology_payload as _norm_topo
        except Exception as exc:
            try:
                print(f"[ai] topology preflight blueprint imports failed: {exc}")
            except Exception:
                pass
            return None
        fam = (family_key or "").strip().lower()
        stem = self._AI_TOPO_DEFAULT_BLUEPRINT_STEM.get(fam)
        if not stem:
            return None
        bp = _load_bp(stem, username=user or "")
        if not bp or not isinstance(bp.get("objects"), list):
            return None
        safe_name = (bp.get("name") or stem).strip() or stem
        args = {
            "name": safe_name,
            "objects": bp.get("objects") or [],
            "layout_hint": (bp.get("layout_hint") or "auto").strip() or "auto",
            "summary": (bp.get("summary") or f"Standard {fam.upper()} lab blueprint").strip(),
            "realism_scale": (bp.get("scale") or "medium").strip().lower(),
        }
        if args["realism_scale"] not in {"small", "medium", "large", "enterprise"}:
            args["realism_scale"] = "medium"
        try:
            topology = _norm_topo(args)
        except ValueError as ve:
            try:
                print(f"[ai] topology preflight normalize failed: {ve}")
            except Exception:
                pass
            return None
        meta = topology.get("metadata") or {}
        suggested = (meta.get("name") or safe_name).strip() or safe_name
        tool_calls = [{
            "name": "create_topology",
            "status": "pending_placement",
            "topology": topology,
            "display_name": suggested,
            "suggested_name": suggested,
        }]
        return {
            "ok": True,
            "text": (
                f"Loaded the standard {fam.upper()} blueprint — pick where "
                "to place it on disk."
            ),
            "tool_calls": tool_calls,
            "model": getattr(client, "model", "") or "",
            "provider": getattr(client, "provider_name", "") or "",
            "usage": {},
            "stop_reason": "preflight_instant_blueprint",
            "preflight": "instant_blueprint",
        }

    def _ai_persist_assistant_chat_turn(
        self,
        user,
        conv_store,
        conversation_id,
        resp: Dict[str, Any],
        *,
        active_conv,
        retry_info=None,
    ):
        """Append assistant message + refresh turn_count (non-fatal)."""
        if conv_store is None or not conversation_id:
            return
        try:
            conv_store.append_message(
                user,
                conversation_id,
                "assistant",
                resp.get("text") or "",
                tool_calls=resp.get("tool_calls") or None,
                retry_info=retry_info,
            )
            refreshed = conv_store.get_conversation(
                user, conversation_id, include_messages=False,
            )
            if refreshed and "conversation" in resp:
                resp["conversation"]["turn_count"] = refreshed.get("turn_count")
                resp["conversation"]["updated_at"] = refreshed.get("updated_at")
        except Exception as exc:
            try:
                print(f"[ai] persist assistant msg failed: {exc}")
            except Exception:
                pass

    def _ai_topology_preflight_handle(
        self,
        *,
        user,
        last_user_message: str,
        canvas,
        conv_store,
        conversation_id,
        active_conv,
        data,
        client,
    ) -> bool:
        """Return True when this request was fully handled (response sent)."""
        msg = (last_user_message or "").strip()
        if not msg:
            return False
        # Instant standard blueprint (chip from prior clarify turn).
        if msg.startswith(self._AI_TOPO_DEFAULT_PREFIX):
            fam = msg[len(self._AI_TOPO_DEFAULT_PREFIX):].strip().lower()
            fam = fam.split()[0] if fam else ""
            resp_body = self._ai_topology_preflight_instant_blueprint(
                user=user,
                family_key=fam,
                conv_store=conv_store,
                conversation_id=conversation_id,
                active_conv=active_conv,
                data=data,
                client=client,
            )
            if not resp_body:
                return False
            if active_conv and conversation_id:
                resp_body["conversation_id"] = conversation_id
                resp_body["conversation"] = {
                    "id": active_conv.get("id"),
                    "title": active_conv.get("title"),
                    "topology_domain": active_conv.get("topology_domain"),
                    "topology_id": active_conv.get("topology_id"),
                    "turn_count": active_conv.get("turn_count"),
                }
            self._ai_persist_assistant_chat_turn(
                user, conv_store, conversation_id, resp_body,
                active_conv=active_conv, retry_info=None,
            )
            self._send_json(resp_body)
            return True
        if not self._ai_is_broad_topology_prompt(msg):
            return False
        family = self._ai_broad_topology_family(msg)
        qargs = self._ai_topology_preflight_question(family)
        q = (qargs.get("question") or "").strip()
        raw_opts = qargs.get("options") or []
        opts_out: List[Dict[str, str]] = []
        if isinstance(raw_opts, list):
            for o in raw_opts[:5]:
                if not isinstance(o, dict):
                    continue
                lbl = (o.get("label") or "").strip()
                val = (o.get("value") or "").strip() or lbl
                if lbl:
                    opts_out.append({"label": lbl[:40], "value": val[:600]})
        if not q or len(opts_out) < 2:
            return False
        resp_body = {
            "ok": True,
            "text": (
                "Quick check before I generate — pick the closest match "
                "or type more detail."
            ),
            "tool_calls": [{
                "name": "ask_user_question",
                "status": "question",
                "question": q[:400],
                "options": opts_out,
                "allow_free_text": bool(qargs.get("allow_free_text")),
            }],
            "model": getattr(client, "model", "") or "",
            "provider": getattr(client, "provider_name", "") or "",
            "usage": {},
            "stop_reason": "topology_clarify_preflight",
            "preflight": "topology_clarify",
        }
        if active_conv and conversation_id:
            resp_body["conversation_id"] = conversation_id
            resp_body["conversation"] = {
                "id": active_conv.get("id"),
                "title": active_conv.get("title"),
                "topology_domain": active_conv.get("topology_domain"),
                "topology_id": active_conv.get("topology_id"),
                "turn_count": active_conv.get("turn_count"),
            }
        self._ai_persist_assistant_chat_turn(
            user, conv_store, conversation_id, resp_body,
            active_conv=active_conv, retry_info=None,
        )
        self._send_json(resp_body)
        return True

    def _ai_execute_blueprint_tool(self, username, name, args):
        """Run a blueprint lookup tool server-side. Returns a JSON-ready dict.

        Both `list_blueprints` and `load_blueprint` are strictly
        read-only: failures are surfaced as
        `{"ok": False, "error": ...}` so the model can recover without
        aborting the turn.
        """
        try:
            from ai.blueprints import list_blueprints as _list_bp, load_blueprint as _load_bp
        except Exception as exc:
            return {"ok": False, "error": f"blueprints module broken: {exc}"}
        if name == "list_blueprints":
            protocol = (args.get("protocol") or "").strip() or None
            scale = (args.get("scale") or "").strip() or None
            tags = args.get("tags") or None
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            query = (args.get("query") or "").strip() or None
            try:
                limit = int(args.get("limit") or 60)
            except Exception:
                limit = 60
            try:
                entries = _list_bp(
                    username=username,
                    protocol=protocol,
                    scale=scale,
                    tags=tags,
                    query=query,
                    limit=limit,
                )
            except Exception as exc:
                return {"ok": False, "error": f"list_blueprints failed: {exc}"}
            # Drop the internal path from each entry before handing it to
            # the model -- it doesn't need filesystem details.
            safe = []
            for m in entries:
                safe.append({
                    k: v for k, v in m.items() if k != "path"
                })
            return {"ok": True, "count": len(safe), "blueprints": safe}
        if name == "load_blueprint":
            bp_name = (args.get("name") or "").strip()
            if not bp_name:
                return {"ok": False, "error": "load_blueprint requires a 'name' argument"}
            try:
                payload = _load_bp(bp_name, username=username)
            except Exception as exc:
                return {"ok": False, "error": f"load_blueprint failed: {exc}"}
            if not payload:
                return {"ok": False, "error": f"Blueprint {bp_name!r} not found"}
            return {"ok": True, "name": bp_name, "blueprint": payload}
        return {"ok": False, "error": f"Unknown blueprint tool: {name}"}

    @staticmethod
    def _ai_append_tool_turn(provider_name, messages, tool_calls, tool_results):
        """Append one round-trip of assistant tool_use + user tool_result.

        Reconstructs the provider's native wire format so the next
        `client.chat(messages, ...)` call sees a well-formed conversation.
        ``tool_calls`` is the list we got back from
        ``LlmClient._normalize_response`` (`[{name, args, id}]`);
        ``tool_results`` is a parallel list of server-executed dicts.
        """
        if not tool_calls:
            return
        provider = (provider_name or "").lower()
        if provider == "gemini":
            # Gemini's OpenAI-compatible endpoint rejects replayed synthetic
            # functionCall history for thinking models unless Google's
            # hidden thought_signature is present. The compatibility response
            # does not expose that signature, so feed server-side blueprint
            # lookups back as plain context instead of as assistant/tool
            # messages. The model still has the lookup JSON and can continue
            # with load_blueprint/create_topology normally.
            chunks = [
                "Server-executed blueprint lookup results follow. Use these "
                "results as authoritative context for the next step; do not "
                "repeat the same lookup unless you need different filters."
            ]
            for tc, res in zip(tool_calls, tool_results):
                try:
                    args_txt = json.dumps(tc.get("args") or {})
                except Exception:
                    args_txt = "{}"
                try:
                    res_txt = json.dumps(res)[:24000]
                except Exception:
                    res_txt = json.dumps({"ok": False, "error": "tool result could not be serialized"})
                chunks.append(
                    "\nTool: {name}\nArguments: {args}\nResult JSON:\n{result}".format(
                        name=tc.get("name") or "",
                        args=args_txt,
                        result=res_txt,
                    )
                )
            messages.append({"role": "user", "content": "\n".join(chunks)})
            return
        if provider == "anthropic":
            # Claude: assistant message with tool_use blocks, user reply
            # with matching tool_result blocks.
            assistant_content = []
            for tc in tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc.get("id") or tc.get("name") or "",
                    "name": tc.get("name") or "",
                    "input": tc.get("args") or {},
                })
            messages.append({"role": "assistant", "content": assistant_content})
            user_content = []
            for tc, res in zip(tool_calls, tool_results):
                user_content.append({
                    "type": "tool_result",
                    "tool_use_id": tc.get("id") or tc.get("name") or "",
                    "content": json.dumps(res)[:24000],
                })
            messages.append({"role": "user", "content": user_content})
            return
        # OpenAI / Groq / Ollama -- all OpenAI-compatible.
        openai_tool_calls = []
        for tc in tool_calls:
            openai_tool_calls.append({
                "id": tc.get("id") or tc.get("name") or "",
                "type": "function",
                "function": {
                    "name": tc.get("name") or "",
                    "arguments": json.dumps(tc.get("args") or {}),
                },
            })
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": openai_tool_calls,
        })
        for tc, res in zip(tool_calls, tool_results):
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id") or tc.get("name") or "",
                "content": json.dumps(res)[:24000],
            })

    @staticmethod
    def _ai_default_tool_reply(tool_calls, blueprint_preview=None):
        """Return a concise assistant sentence for tool-only model replies."""
        names = [(tc.get("name") or "") for tc in (tool_calls or [])]
        consulted = blueprint_preview or []
        consulted_txt = ""
        if consulted:
            consulted_txt = f" after consulting {len(consulted)} blueprint"
            consulted_txt += "" if len(consulted) == 1 else "s"
        if "create_topology" in names:
            return (
                "I prepared a topology matched to your request"
                f"{consulted_txt}. It keeps the layout simplified while adding "
                "role labels, protocol links, grouping boundaries, and key callouts. "
                "Choose where to place it below."
            )
        if "apply_canvas_edits" in names:
            return (
                "I prepared canvas edits for the current topology"
                f"{consulted_txt}. The changes are applied below and can be undone "
                "from the receipt card."
            )
        if "propose_canvas_edits" in names:
            return (
                "I prepared a preview of the canvas changes"
                f"{consulted_txt}. Review the proposed edits below before applying them."
            )
        if "ask_user_question" in names:
            return "I need one detail to tailor this correctly. Pick an option below."
        return "I completed the requested AI action. Review the card below for details."

    # --- AI conversation endpoints -------------------------------------
    #
    # Per-user multi-conversation storage:
    #
    #   GET    /api/ai/conversations                  list own (exclude archived)
    #   GET    /api/ai/conversations?archived=1       include archived
    #   POST   /api/ai/conversations                  create new (optional title / topology pin)
    #   GET    /api/ai/conversations/<id>             fetch full transcript
    #   PATCH  /api/ai/conversations/<id>             rename / archive / pin
    #   DELETE /api/ai/conversations/<id>             remove (messages cascade)
    #
    # Admin audit (admin role OR deployment owner):
    #
    #   GET    /api/admin/ai/conversations?user=X              list user's chats
    #   GET    /api/admin/ai/conversations/<id>?user=X         read full transcript
    #
    # All endpoints return JSON. The frontend maintains a localStorage
    # cache keyed on the JWT subject so the drawer paints instantly
    # while the fresh server snapshot lands in the background.

    def _parse_qs_single(self, name):
        """Return the first value of a query-string key, or empty string."""
        try:
            q = urllib.parse.urlparse(self.path).query
            return urllib.parse.parse_qs(q).get(name, [""])[0]
        except Exception:
            return ""

    def _handle_ai_conversations_list(self):
        user = self._require_auth()
        if not user:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        include_archived = self._parse_qs_single("archived") in ("1", "true", "yes")
        topo_domain = self._parse_qs_single("topology_domain") or None
        topo_id = self._parse_qs_single("topology_id") or None
        try:
            convs = store.list_conversations(
                user,
                include_archived=include_archived,
                topology_domain=topo_domain,
                topology_id=topo_id,
            )
        except Exception as exc:
            return self._send_json({"error": f"list failed: {exc}"}, 500)
        return self._send_json({"ok": True, "conversations": convs})

    def _handle_ai_conversations_get(self, conv_id):
        user = self._require_auth()
        if not user:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        conv = store.get_conversation(user, conv_id, include_messages=True)
        if not conv:
            return self._send_json({"error": "not found"}, 404)
        return self._send_json({"ok": True, "conversation": conv})

    def _handle_ai_conversations_create(self, body):
        user = self._require_auth()
        if not user:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "invalid JSON body"}, 400)
        title = (data.get("title") or "").strip() or None
        topo_domain = data.get("topology_domain") or None
        topo_id = data.get("topology_id") or None
        provider = data.get("provider") or None
        model = data.get("model") or None
        try:
            conv = store.create_conversation(
                user,
                title=title,
                topology_domain=topo_domain,
                topology_id=topo_id,
                provider=provider,
                model=model,
            )
        except RuntimeError as exc:
            return self._send_json({"error": str(exc)}, 409)
        except Exception as exc:
            return self._send_json({"error": f"create failed: {exc}"}, 500)
        return self._send_json({"ok": True, "conversation": conv}, 201)

    def _handle_ai_conversations_patch(self, conv_id, body):
        user = self._require_auth()
        if not user:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "invalid JSON body"}, 400)
        # Apply each provided field; we update them one by one so a
        # partial patch (just the title, just the archived flag, etc.)
        # is never accidentally overwritten.
        conv = store.get_conversation(user, conv_id, include_messages=False)
        if not conv:
            return self._send_json({"error": "not found"}, 404)
        if "title" in data:
            conv = store.rename_conversation(user, conv_id, str(data["title"]))
        if "archived" in data:
            conv = store.set_archived(user, conv_id, bool(data["archived"]))
        if "pinned" in data:
            conv = store.set_pinned(user, conv_id, bool(data["pinned"]))
        if ("topology_domain" in data) or ("topology_id" in data):
            conv = store.set_topology_pin(
                user, conv_id,
                data.get("topology_domain"),
                data.get("topology_id"),
            )
        return self._send_json({"ok": True, "conversation": conv})

    def _handle_ai_conversations_delete(self, conv_id):
        user = self._require_auth()
        if not user:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        if not store.delete_conversation(user, conv_id):
            return self._send_json({"error": "not found"}, 404)
        return self._send_json({"ok": True, "deleted": conv_id})

    def _handle_admin_ai_conversations_list(self):
        caller, _role = self._require_admin()
        if not caller:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        target = self._parse_qs_single("user")
        if not target:
            return self._send_json({"error": "user query param required"}, 400)
        include_archived = self._parse_qs_single("archived") not in ("0", "false", "no")
        try:
            convs = store.admin_list_conversations(
                target,
                include_archived=include_archived,
            )
            stats = store.user_stats(target)
        except Exception as exc:
            return self._send_json({"error": f"admin list failed: {exc}"}, 500)
        try:
            _record_audit(
                "ai_admin_list_conversations",
                username=caller,
                detail={"target": target, "count": len(convs)},
            )
        except Exception:
            pass
        return self._send_json({
            "ok": True,
            "target_user": target,
            "conversations": convs,
            "stats": stats,
        })

    def _handle_admin_ai_conversations_get(self, conv_id):
        caller, _role = self._require_admin()
        if not caller:
            return
        store = _conversation_store()
        if store is None:
            return self._send_json({"error": "conversation store unavailable"}, 503)
        target = self._parse_qs_single("user")
        if not target:
            return self._send_json({"error": "user query param required"}, 400)
        conv = store.admin_get_conversation(target, conv_id)
        if not conv:
            return self._send_json({"error": "not found"}, 404)
        try:
            _record_audit(
                "ai_admin_read_conversation",
                username=caller,
                detail={"target": target, "conv": conv_id,
                        "turns": conv.get("turn_count")},
            )
        except Exception:
            pass
        return self._send_json({
            "ok": True,
            "target_user": target,
            "conversation": conv,
        })

    # --- DNOS-grounded chat turn --------------------------------------
    #
    # Called by ``_handle_ai_chat`` when the lexical intent classifier
    # in ``ai.dnos_config_grounding`` decides the user is asking for
    # DNOS configuration syntax. Returns ``None`` to fall through to
    # the normal topology AI path; otherwise returns the value of
    # ``self._send_json(...)`` (which is what the HTTP handler expects).
    def _handle_ai_dnos_grounded_turn(
        self,
        *,
        user,
        client,
        conv_store,
        conversation_id,
        active_conv,
        data,
        messages,
        intent,
        build_search_query,
        search_dnos_docs,
        build_grounded_system_prompt,
        parse_dnos_block,
        validate_dnos_text,
        serialize_sources,
    ):
        from ai.service import LlmError
        # 1. Build the search query and pull DNOS evidence ---------------
        try:
            query = build_search_query(intent)
        except Exception:
            query = intent.query or ""
        try:
            evidence = search_dnos_docs(
                query,
                limit=int(data.get("dnos_evidence_limit") or 6),
                use_mcp=bool(data.get("dnos_use_mcp", True)),
                mcp_timeout=int(data.get("dnos_mcp_timeout") or 8),
            )
        except Exception as exc:
            try:
                print(f"[ai/dnos] evidence search failed: {exc}")
            except Exception:
                pass
            evidence = []
        if not evidence:
            # No grounded evidence -- per the contract we MUST NOT let
            # the model invent DNOS syntax. Surface a helpful error
            # card. The frontend renders ``dnos_error`` as a notice.
            resp = {
                "ok": True,
                "text": (
                    "I could not find verified DNOS documentation for that "
                    "request, so I am not going to invent a config. Please "
                    "rephrase with a more specific hierarchy "
                    "(e.g. 'BGP neighbor address-family', "
                    "'EVPN VPWS interface', 'OSPF area 0')."
                ),
                "tool_calls": [],
                "model": getattr(client, "model", ""),
                "provider": getattr(client, "provider_name", ""),
                "usage": {},
                "stop_reason": "no_dnos_evidence",
                "dnos_grounded": True,
                "dnos_intent": {
                    "is_config_intent": True,
                    "confidence": intent.confidence,
                    "reason": intent.reason,
                    "query": query,
                },
                "dnos_sources": [],
                "dnos_error": {
                    "kind": "no_verified_source",
                    "message": "No matching DNOS documentation snippet found.",
                },
            }
            self._dnos_persist_assistant_turn(
                user, conv_store, conversation_id, resp,
            )
            return self._send_json(resp)
        # 2. Call the LLM with a strict, tool-less system prompt ----------
        try:
            grounded_system = build_grounded_system_prompt(evidence)
        except Exception as exc:
            try:
                print(f"[ai/dnos] grounded prompt build failed: {exc}")
            except Exception:
                pass
            return None
        provider_name = (getattr(client, "provider_name", "") or "").lower()
        default_timeout = 60
        if provider_name == "ollama":
            default_timeout = 240
        # We pass the entire user-side history so the model has
        # context (e.g. "in addition to that, add the route-policy"
        # follow-ups). System prompt is fully replaced with the
        # grounded one -- the topology rules do NOT apply here.
        full_messages = [{"role": "system", "content": grounded_system}] + messages
        try:
            raw, retry_info = self._ai_chat_with_rate_retry(
                client,
                full_messages,
                tools=None,  # absolutely no tool access in grounded mode
                max_tokens=int(data.get("max_tokens") or 1500),
                temperature=float(data.get("temperature") or 0.0),
                timeout=int(data.get("timeout") or default_timeout),
            )
        except LlmError as e:
            return self._send_json({
                "error": str(e),
                "code": "upstream",
                "kind": getattr(e, "kind", "upstream_error"),
                "details": getattr(e, "details", "") or "",
                "provider": provider_name,
                "dnos_grounded": True,
            }, e.status_code)
        except Exception as e:
            return self._send_json({
                "error": f"DNOS grounded AI call failed: {e}",
                "dnos_grounded": True,
            }, 500)
        text_out = (raw.get("text") or "").strip()
        # 3. Handle the "no source" sentinel and reject empty replies ----
        if not text_out or text_out == "NO_VERIFIED_DNOS_SOURCE":
            resp = {
                "ok": True,
                "text": (
                    "I could not ground the requested config in the "
                    "DNOS documentation I retrieved. Please rephrase "
                    "with a more specific hierarchy or attach the "
                    "exact knob you need."
                ),
                "tool_calls": [],
                "model": raw.get("model"),
                "provider": raw.get("provider") or provider_name,
                "usage": raw.get("usage") or {},
                "stop_reason": "no_grounded_match",
                "dnos_grounded": True,
                "dnos_intent": {
                    "is_config_intent": True,
                    "confidence": intent.confidence,
                    "reason": intent.reason,
                    "query": query,
                },
                "dnos_sources": serialize_sources(evidence),
                "dnos_error": {
                    "kind": "no_grounded_match",
                    "message": "Model could not ground a config in retrieved DNOS docs.",
                },
            }
            if retry_info:
                resp["retried"] = retry_info
            self._dnos_persist_assistant_turn(
                user, conv_store, conversation_id, resp,
            )
            return self._send_json(resp)
        # 4. Extract the CLI body and validate it ------------------------
        try:
            cli_body = parse_dnos_block(text_out)
        except Exception:
            cli_body = ""
        if not cli_body:
            resp = {
                "ok": True,
                "text": (
                    "The model produced text but no DNOS CLI block. "
                    "Please retry with a slightly more specific request."
                ),
                "tool_calls": [],
                "model": raw.get("model"),
                "provider": raw.get("provider") or provider_name,
                "usage": raw.get("usage") or {},
                "stop_reason": "no_cli_block",
                "dnos_grounded": True,
                "dnos_intent": {
                    "is_config_intent": True,
                    "confidence": intent.confidence,
                    "reason": intent.reason,
                    "query": query,
                },
                "dnos_sources": serialize_sources(evidence),
                "dnos_error": {
                    "kind": "no_cli_block",
                    "message": "AI reply did not contain a parsable DNOS CLI block.",
                    "raw_text": text_out[:600],
                },
            }
            if retry_info:
                resp["retried"] = retry_info
            self._dnos_persist_assistant_turn(
                user, conv_store, conversation_id, resp,
            )
            return self._send_json(resp)
        try:
            validation = validate_dnos_text(cli_body)
        except Exception as exc:
            validation = {"ok": True, "issues": [], "validator_error": str(exc)}
        # 5. Build the wire response ------------------------------------
        # The visible bubble shows ONLY the validated CLI block -- per
        # the user's "no frontend-made DNOS syntax" rule, the chat
        # produces the body and the frontend renders it as a code/pre.
        # Sources travel out-of-band as a chip card.
        wire_text = "```dnos\n" + cli_body.strip() + "\n```"
        resp = {
            "ok": True,
            "text": wire_text,
            "tool_calls": [],
            "model": raw.get("model"),
            "provider": raw.get("provider") or provider_name,
            "usage": raw.get("usage") or {},
            "stop_reason": raw.get("stop_reason"),
            "dnos_grounded": True,
            "dnos_intent": {
                "is_config_intent": True,
                "confidence": intent.confidence,
                "reason": intent.reason,
                "query": query,
            },
            "dnos_sources": serialize_sources(evidence),
            "dnos_validation": validation,
            "dnos_config": cli_body,
        }
        if retry_info:
            resp["retried"] = retry_info
        if active_conv and conversation_id:
            resp["conversation_id"] = conversation_id
            resp["conversation"] = {
                "id": active_conv.get("id"),
                "title": active_conv.get("title"),
                "topology_domain": active_conv.get("topology_domain"),
                "topology_id": active_conv.get("topology_id"),
                "turn_count": active_conv.get("turn_count"),
            }
        self._dnos_persist_assistant_turn(
            user, conv_store, conversation_id, resp,
        )
        return self._send_json(resp)

    def _dnos_persist_assistant_turn(
        self, user, conv_store, conversation_id, resp,
    ):
        """Append the grounded assistant turn to the per-user conversation
        store. Mirrors the persistence in ``_handle_ai_chat`` -- failures
        are non-fatal so the response still ships.
        """
        if conv_store is None or not conversation_id:
            return
        try:
            conv_store.append_message(
                user,
                conversation_id,
                "assistant",
                resp.get("text") or "",
                tool_calls=resp.get("tool_calls") or None,
                retry_info=resp.get("retried"),
            )
            refreshed = conv_store.get_conversation(
                user, conversation_id, include_messages=False,
            )
            if refreshed and "conversation" in resp:
                resp["conversation"]["turn_count"] = refreshed.get("turn_count")
                resp["conversation"]["updated_at"] = refreshed.get("updated_at")
        except Exception as exc:
            try:
                print(f"[ai/dnos] persist assistant turn failed: {exc}")
            except Exception:
                pass

    def _handle_ai_chat(self, body):
        user = self._require_auth()
        if not user:
            return
        if not _ensure_ai_module():
            return self._send_json(
                {"error": f"AI assistant module unavailable: {_ai_import_error}"}, 503,
            )
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        _extras, messages = self._ai_build_messages(data)
        if not messages:
            return self._send_json({"error": "message or messages[] is required"}, 400)
        canvas = data.get("canvas") or {}
        try:
            from ai.service import resolve_client_for_user, LlmError
            from ai.context import (
                TOPOLOGY_TOOL_SCHEMA,
                CANVAS_EDITS_TOOL_SCHEMA,
                LIST_BLUEPRINTS_TOOL_SCHEMA,
                LOAD_BLUEPRINT_TOOL_SCHEMA,
            )
        except Exception as e:
            return self._send_json({"error": f"AI module broken: {e}"}, 500)
        try:
            client = resolve_client_for_user(user)
        except LlmError as e:
            return self._send_json(
                {"error": str(e), "code": "not-configured"}, e.status_code,
            )
        # ---- Conversation persistence (admin-auditable per-user store) -
        #
        # If the client passes a `conversation_id` we append this turn to
        # it. If not, we auto-create a conversation titled after the
        # first user message so the drawer can list it immediately. A
        # stale id from localStorage (DB wiped, etc.) silently falls
        # back to creating a fresh conversation instead of 404-ing.
        conv_store = _conversation_store()
        conversation_id = (data.get("conversation_id") or "").strip() or None
        last_user_message = ""
        for m in reversed(messages):
            if (m.get("role") or "") == "user":
                last_user_message = (m.get("content") or "").strip()
                break
        active_conv = None
        if conv_store is not None:
            try:
                if conversation_id:
                    active_conv = conv_store.get_conversation(
                        user, conversation_id, include_messages=False,
                    )
                if not active_conv:
                    title = conv_store.auto_title(last_user_message)
                    topo_domain = (data.get("topology_domain") or "") or None
                    topo_id = (data.get("topology_id") or "") or None
                    active_conv = conv_store.create_conversation(
                        user,
                        title=title,
                        topology_domain=topo_domain,
                        topology_id=topo_id,
                        provider=getattr(client, "provider_name", None),
                        model=getattr(client, "model", None),
                    )
                    conversation_id = active_conv["id"]
                if last_user_message:
                    try:
                        conv_store.append_message(
                            user, conversation_id, "user", last_user_message,
                        )
                    except Exception as exc:
                        # Non-fatal: we log and continue. A write error
                        # here must not break the conversation flow.
                        try:
                            print(f"[ai] persist user msg failed: {exc}")
                        except Exception:
                            pass
            except Exception as exc:
                # Store failure never aborts the chat -- chat works just
                # like today, but without persistence until the DB is fixed.
                try:
                    print(f"[ai] conversation bootstrap failed: {exc}")
                except Exception:
                    pass
                active_conv = None
                conversation_id = None
        # ---- DNOS configuration intent gate ----------------------------
        #
        # When the latest user turn is asking for DNOS CLI syntax / a
        # config snippet, we short-circuit the normal topology path and
        # run a strict backend-only flow that mirrors Scaler GUI:
        #   1. Search Network Mapper `search_cli_docs` + local RST tree.
        #   2. If we cannot ground the answer, return an error card --
        #      we do NOT let the model invent DNOS keywords.
        #   3. Otherwise call the LLM with a locked system prompt that
        #      embeds the evidence and forbids tool calls.
        #   4. Validate the produced CLI text via cli_validator.
        #   5. Echo the evidence back as `dnos_sources` so the drawer
        #      shows a "Verified from DNOS docs" chip.
        # See ``ai/dnos_config_grounding.py`` for the search + intent
        # classifier; the flow below wires it into the chat handler.
        try:
            from ai.dnos_config_grounding import (
                detect_config_intent,
                build_search_query,
                search_dnos_docs,
                build_grounded_system_prompt,
                parse_dnos_block,
                validate_dnos_text,
                serialize_sources,
            )
        except Exception as exc:
            # Module-level import failure should not break normal chat;
            # log once and fall through to the standard path.
            try:
                print(f"[ai] dnos_config_grounding unavailable: {exc}")
            except Exception:
                pass
            detect_config_intent = None  # type: ignore[assignment]
        config_intent = None
        if detect_config_intent is not None:
            try:
                config_intent = detect_config_intent(messages, canvas=canvas)
            except Exception as exc:
                try:
                    print(f"[ai] dnos intent detection failed: {exc}")
                except Exception:
                    pass
                config_intent = None
        if config_intent is not None and config_intent.is_config_intent:
            grounded_resp = self._handle_ai_dnos_grounded_turn(
                user=user,
                client=client,
                conv_store=conv_store,
                conversation_id=conversation_id,
                active_conv=active_conv,
                data=data,
                messages=messages,
                intent=config_intent,
                build_search_query=build_search_query,
                search_dnos_docs=search_dnos_docs,
                build_grounded_system_prompt=build_grounded_system_prompt,
                parse_dnos_block=parse_dnos_block,
                validate_dnos_text=validate_dnos_text,
                serialize_sources=serialize_sources,
            )
            if grounded_resp is not None:
                return grounded_resp
            # Grounded flow chose to defer (e.g. internal error); fall
            # through to the standard path so the user still gets a
            # response rather than a broken chat turn.
        # ---- Broad topology clarify / instant-default preflight ----------
        #
        # Short-circuit vague "generate a BGP topology" style prompts to
        # an ask_user_question card, or serve a standard blueprint when
        # the user picked the instant-default chip -- all before the LLM.
        if self._ai_topology_preflight_handle(
            user=user,
            last_user_message=last_user_message,
            canvas=canvas,
            conv_store=conv_store,
            conversation_id=conversation_id,
            active_conv=active_conv,
            data=data,
            client=client,
        ):
            return
        system_prompt = self._build_ai_system_prompt(user, canvas)
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        # Local CPU inference (Ollama on this host is our only local provider
        # today) can take 60-180s for a cold tool-calling round-trip even on
        # a small 3B model. A 60s timeout produced spurious 504s while the
        # model was still legitimately generating -- raise it specifically
        # for local providers. Hosted providers keep the tight 60s default
        # to surface real quota/network issues quickly.
        provider_name = getattr(client, "provider_name", "") or ""
        default_timeout = 60
        if provider_name == "ollama":
            default_timeout = 240
        try:
            # All four tools are advertised. The system prompt (see
            # _build_ai_system_prompt + knowledge.md) steers selection:
            # list_blueprints / load_blueprint are read-only lookups
            # resolved server-side in the loop below; create_topology
            # (full-topology generation) and apply_canvas_edits
            # (incremental live edits) are terminal tools returned
            # to the frontend.
            # 2026-04-24r -- two new interactive tools added alongside
            # the terminal ones. `ask_user_question` lets the model ask
            # a short disambiguation question (chip picker in the UI);
            # `propose_canvas_edits` lets it show a diff preview for
            # irreversible / bulk edits. Both are safe no-ops if the
            # frontend doesn't render them (they fall through to the
            # generic tool card).
            from ai.context import (
                ASK_USER_QUESTION_TOOL_SCHEMA,
                PROPOSE_CANVAS_EDITS_TOOL_SCHEMA,
            )
            turn_tools = [
                TOPOLOGY_TOOL_SCHEMA,
                CANVAS_EDITS_TOOL_SCHEMA,
                PROPOSE_CANVAS_EDITS_TOOL_SCHEMA,
                ASK_USER_QUESTION_TOOL_SCHEMA,
                LIST_BLUEPRINTS_TOOL_SCHEMA,
                LOAD_BLUEPRINT_TOOL_SCHEMA,
            ]
            raw, retry_info = self._ai_chat_with_rate_retry(
                client,
                full_messages,
                tools=turn_tools,
                max_tokens=int(data.get("max_tokens") or 4096),
                temperature=float(data.get("temperature") or 0.2),
                timeout=int(data.get("timeout") or default_timeout),
            )
            # Blueprint-resolution loop: while the model only called
            # read-only lookup tools, run them server-side and feed
            # the results back. Stops when the model either emits a
            # terminal tool (create_topology / apply_canvas_edits) or
            # plain text, or when we hit the iteration cap so a
            # runaway "call list_blueprints forever" never pins a
            # provider budget. `blueprint_preview` is surfaced to the
            # frontend so users can see which blueprints the assistant
            # consulted (rendered as a small "consulted N blueprints"
            # chip under the reply).
            blueprint_preview = []
            iteration = 0
            while iteration < self._AI_MAX_BLUEPRINT_ITERATIONS:
                raw_tool_calls = raw.get("tool_calls") or []
                lookup_calls = [
                    tc for tc in raw_tool_calls
                    if (tc.get("name") or "") in self._AI_BLUEPRINT_TOOLS
                ]
                if not lookup_calls:
                    break
                # Execute every lookup call in order so results align
                # positionally with `lookup_calls` when we append them.
                results = []
                for tc in lookup_calls:
                    res = self._ai_execute_blueprint_tool(
                        user, tc.get("name") or "", tc.get("args") or {},
                    )
                    results.append(res)
                    blueprint_preview.append({
                        "name": tc.get("name") or "",
                        "args": tc.get("args") or {},
                        "ok": bool(res.get("ok")),
                        # Don't echo the full blueprint payload back
                        # to the frontend -- the UI only needs to
                        # know WHICH blueprint was consulted. The
                        # actual JSON is already in the model's
                        # conversation context.
                        "summary": (
                            res.get("name")
                            or (f"{res.get('count', 0)} blueprint(s)" if res.get("ok") else res.get("error", ""))
                        ),
                    })
                self._ai_append_tool_turn(
                    getattr(client, "provider_name", "") or "",
                    full_messages,
                    lookup_calls,
                    results,
                )
                iteration += 1
                raw, _ = self._ai_chat_with_rate_retry(
                    client,
                    full_messages,
                    tools=turn_tools,
                    max_tokens=int(data.get("max_tokens") or 4096),
                    temperature=float(data.get("temperature") or 0.2),
                    timeout=int(data.get("timeout") or default_timeout),
                )
            # Make the chat UI deterministic: a successful provider call
            # should never leave the user with an empty bubble. Tool-only
            # replies get a concise deterministic sentence; fully empty
            # replies get one text-only retry from the same model.
            if not (raw.get("text") or "").strip():
                final_calls = raw.get("tool_calls") or []
                if final_calls:
                    raw["text"] = self._ai_default_tool_reply(final_calls, blueprint_preview)
                else:
                    try:
                        fallback_messages = list(full_messages) + [{
                            "role": "user",
                            "content": (
                                "Your previous response was empty and did not call a usable tool. "
                                "Answer the user's latest request now in 1-3 concise sentences. "
                                "If you cannot act, say exactly what you need next."
                            ),
                        }]
                        raw_text, _fallback_retry = self._ai_chat_with_rate_retry(
                            client,
                            fallback_messages,
                            tools=None,
                            max_tokens=512,
                            temperature=float(data.get("temperature") or 0.2),
                            timeout=min(int(data.get("timeout") or default_timeout), 30),
                        )
                        if (raw_text.get("text") or "").strip():
                            raw["text"] = raw_text.get("text", "")
                            raw["model"] = raw_text.get("model") or raw.get("model")
                            raw["provider"] = raw_text.get("provider") or raw.get("provider")
                    except Exception:
                        pass
                    if not (raw.get("text") or "").strip():
                        raw["text"] = (
                            "I could not produce a usable AI response for that turn. "
                            "Please retry or add one more detail about what you want changed."
                        )
        except LlmError as e:
            # Forward the classified kind + raw details so the chat UI can
            # render a targeted card (billing banner with a "Top up" CTA
            # for insufficient_quota, a retry chip for rate_limited, etc.).
            # `code` remains "upstream" for back-compat with the old
            # frontend path; `kind` is the new, specific tag.
            return self._send_json({
                "error": str(e),
                "code": "upstream",
                "kind": getattr(e, "kind", "upstream_error"),
                "details": getattr(e, "details", "") or "",
                "provider": (client.provider_name if hasattr(client, "provider_name") else ""),
            }, e.status_code)
        except Exception as e:
            return self._send_json({"error": f"AI call failed: {e}"}, 500)
        resp = {
            "ok": True,
            "text": raw.get("text", ""),
            "tool_calls": [],
            "model": raw.get("model"),
            "provider": raw.get("provider"),
            "usage": raw.get("usage") or {},
            "stop_reason": raw.get("stop_reason"),
        }
        if retry_info:
            # Frontend renders a subtle "auto-recovered from rate limit"
            # pill under the reply. See topology-ai.js::_renderRetryChip.
            resp["retried"] = retry_info
        if blueprint_preview:
            # Small chip under the reply: "Consulted N blueprints".
            resp["blueprints_consulted"] = blueprint_preview
        if active_conv and conversation_id:
            # Echo the conversation metadata back so the client can wire
            # up a freshly-created id on first turn. The title may have
            # just been auto-derived from the user message -- surfacing
            # it here means the client updates its sidebar without a
            # separate GET /api/ai/conversations call.
            resp["conversation_id"] = conversation_id
            resp["conversation"] = {
                "id": active_conv.get("id"),
                "title": active_conv.get("title"),
                "topology_domain": active_conv.get("topology_domain"),
                "topology_id": active_conv.get("topology_id"),
                "turn_count": active_conv.get("turn_count"),
            }
        # Handle tool calls. create_topology is now returned as a
        # "pending_placement" card -- the frontend prompts the user to
        # pick an existing domain or create a new one before we persist
        # anything. The old behaviour auto-saved every generation to a
        # hidden `__ai` domain, which nobody wanted (users had to move
        # files out of it manually every time). apply_canvas_edits is
        # passed through as-is -- the frontend (topology-ai.js ::
        # _applyCanvasEdits) mutates the in-memory canvas and relies on
        # the normal auto-save path to persist the result. Everything
        # else passes through as a "preview" tool suggestion (no
        # side-effects) so unknown tools never silently corrupt state.
        from ai.context import normalize_topology_payload
        for tc in raw.get("tool_calls") or []:
            name = tc.get("name") or ""
            args = tc.get("args") or {}
            if name == "create_topology":
                try:
                    topology = normalize_topology_payload(args)
                except ValueError as ve:
                    resp["tool_calls"].append({
                        "name": name,
                        "status": "rejected",
                        "error": str(ve),
                    })
                    continue
                # Suggest a filesystem-safe topology name from the
                # topology metadata; fall back to a stable default.
                meta = topology.get("metadata") or {}
                suggested = (meta.get("name") or "ai-topology").strip() or "ai-topology"
                resp["tool_calls"].append({
                    "name": name,
                    "status": "pending_placement",
                    "topology": topology,
                    "display_name": suggested,
                    "suggested_name": suggested,
                })
            elif name == "apply_canvas_edits":
                # Light server-side validation: reject payloads with no
                # usable edits so the frontend doesn't waste a render.
                # Anything deeper (id existence, coord sanity) is the
                # frontend's job -- it has the live canvas state.
                edits_in = args.get("edits") if isinstance(args, dict) else None
                if not isinstance(edits_in, list) or not edits_in:
                    resp["tool_calls"].append({
                        "name": name,
                        "status": "rejected",
                        "error": "apply_canvas_edits requires a non-empty edits[] array",
                    })
                    continue
                # Pass the normalized args through to the client. We
                # deliberately keep the wire format small (no server
                # fill-in of x/y) so the client's auto-layout has full
                # latitude.
                resp["tool_calls"].append({
                    "name": name,
                    "status": "apply",
                    "summary": (args.get("summary") or "").strip(),
                    "edits": edits_in,
                })
            elif name == "propose_canvas_edits":
                # 2026-04-24r -- preview-only twin of apply_canvas_edits.
                # Same validation, but status=="preview" so the frontend
                # renders a diff card with Apply / Tweak / Cancel instead
                # of mutating the canvas immediately.
                edits_in = args.get("edits") if isinstance(args, dict) else None
                if not isinstance(edits_in, list) or not edits_in:
                    resp["tool_calls"].append({
                        "name": name,
                        "status": "rejected",
                        "error": "propose_canvas_edits requires a non-empty edits[] array",
                    })
                    continue
                resp["tool_calls"].append({
                    "name": name,
                    "status": "propose",
                    "summary": (args.get("summary") or "").strip(),
                    "edits": edits_in,
                })
            elif name == "ask_user_question":
                # 2026-04-24r -- frontend renders as chip picker.
                # Validate shape so a malformed call doesn't hang the UI
                # waiting for a nonexistent question card.
                q = (args.get("question") or "").strip() if isinstance(args, dict) else ""
                raw_opts = args.get("options") if isinstance(args, dict) else None
                opts = []
                if isinstance(raw_opts, list):
                    for o in raw_opts[:5]:
                        if not isinstance(o, dict):
                            continue
                        lbl = (o.get("label") or "").strip()
                        val = (o.get("value") or "").strip() or lbl
                        if lbl:
                            opts.append({"label": lbl[:40], "value": val[:600]})
                if not q or len(opts) < 2:
                    resp["tool_calls"].append({
                        "name": name,
                        "status": "rejected",
                        "error": "ask_user_question requires a question and >=2 options",
                    })
                    continue
                resp["tool_calls"].append({
                    "name": name,
                    "status": "question",
                    "question": q[:400],
                    "options": opts,
                    "allow_free_text": bool(args.get("allow_free_text")),
                })
            else:
                resp["tool_calls"].append({
                    "name": name,
                    "status": "preview",
                    "args": args,
                })
        # Persist the assistant turn last so tool_calls + retry_info
        # captured above flow straight into the transcript store.
        # Failures here are non-fatal: the response still ships.
        self._ai_persist_assistant_chat_turn(
            user,
            conv_store,
            conversation_id,
            resp,
            active_conv=active_conv,
            retry_info=retry_info,
        )
        return self._send_json(resp)

    def _handle_ai_topology_generate(self, body):
        """Dedicated endpoint that FORCES a create_topology tool call.

        Same plumbing as /api/ai/chat but we short-circuit the
        conversation: we wrap the user's description as a single user
        message and bias the system prompt so the model always emits the
        tool. Useful for the "quick create" chip in the drawer that skips
        the Q&A loop.
        """
        user = self._require_auth()
        if not user:
            return
        if not _ensure_ai_module():
            return self._send_json(
                {"error": f"AI assistant module unavailable: {_ai_import_error}"}, 503,
            )
        try:
            data = json.loads(body) if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        description = (data.get("description") or data.get("message") or "").strip()
        if not description:
            return self._send_json(
                {"error": "description is required (free-form topology prompt)"}, 400,
            )
        canvas = data.get("canvas") or {}
        try:
            from ai.service import resolve_client_for_user, LlmError
            from ai.context import (
                TOPOLOGY_TOOL_SCHEMA,
                LIST_BLUEPRINTS_TOOL_SCHEMA,
                LOAD_BLUEPRINT_TOOL_SCHEMA,
                normalize_topology_payload,
            )
        except Exception as e:
            return self._send_json({"error": f"AI module broken: {e}"}, 500)
        try:
            client = resolve_client_for_user(user)
        except LlmError as e:
            return self._send_json(
                {"error": str(e), "code": "not-configured"}, e.status_code,
            )
        system_prompt = (
            self._build_ai_system_prompt(user, canvas)
            + "\n\nThe user is asking for a NEW topology. You MUST respond "
              "by calling the create_topology tool. Do not ask questions."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ]
        # Same rationale as _handle_ai_chat: local Ollama on CPU hosts needs
        # a longer ceiling. Topology generation in particular is tool-call
        # heavy (a single round-trip must emit the full create_topology
        # JSON) so first-token latency dominates.
        gen_provider = getattr(client, "provider_name", "") or ""
        gen_timeout = 90
        if gen_provider == "ollama":
            gen_timeout = 300
        try:
            # Quick-create also gets the blueprint-lookup tools so the
            # model can grab an authoritative protocol topology before
            # emitting create_topology. Same server-side resolution
            # loop as /api/ai/chat.
            gen_tools = [
                TOPOLOGY_TOOL_SCHEMA,
                LIST_BLUEPRINTS_TOOL_SCHEMA,
                LOAD_BLUEPRINT_TOOL_SCHEMA,
            ]
            raw, _retry_info = self._ai_chat_with_rate_retry(
                client,
                messages,
                tools=gen_tools,
                max_tokens=int(data.get("max_tokens") or 6144),
                temperature=float(data.get("temperature") or 0.2),
                timeout=int(data.get("timeout") or gen_timeout),
            )
            gen_iter = 0
            while gen_iter < self._AI_MAX_BLUEPRINT_ITERATIONS:
                raw_tc = raw.get("tool_calls") or []
                lookup = [
                    tc for tc in raw_tc
                    if (tc.get("name") or "") in self._AI_BLUEPRINT_TOOLS
                ]
                if not lookup:
                    break
                results = [
                    self._ai_execute_blueprint_tool(
                        user, tc.get("name") or "", tc.get("args") or {},
                    )
                    for tc in lookup
                ]
                self._ai_append_tool_turn(
                    getattr(client, "provider_name", "") or "",
                    messages,
                    lookup,
                    results,
                )
                gen_iter += 1
                raw, _ = self._ai_chat_with_rate_retry(
                    client,
                    messages,
                    tools=gen_tools,
                    max_tokens=int(data.get("max_tokens") or 6144),
                    temperature=float(data.get("temperature") or 0.2),
                    timeout=int(data.get("timeout") or gen_timeout),
                )
        except LlmError as e:
            return self._send_json({
                "error": str(e),
                "code": "upstream",
                "kind": getattr(e, "kind", "upstream_error"),
                "details": getattr(e, "details", "") or "",
                "provider": (client.provider_name if hasattr(client, "provider_name") else ""),
            }, e.status_code)
        except Exception as e:
            return self._send_json({"error": f"AI call failed: {e}"}, 500)
        tool_calls = raw.get("tool_calls") or []
        if not tool_calls:
            return self._send_json({
                "error": "Model did not emit a create_topology call",
                "text": raw.get("text", ""),
                "code": "no-tool-call",
            }, 502)
        # Take the first create_topology call; ignore any stray tools.
        args = None
        for tc in tool_calls:
            if (tc.get("name") or "") == "create_topology":
                args = tc.get("args") or {}
                break
        if args is None:
            return self._send_json({
                "error": "Model called an unexpected tool",
                "tool_calls": tool_calls,
                "code": "wrong-tool",
            }, 502)
        try:
            topology = normalize_topology_payload(args)
        except ValueError as ve:
            return self._send_json({
                "error": f"Generated topology is invalid: {ve}",
                "code": "bad-topology",
            }, 422)
        # No auto-save. The frontend's "quick-create" chip now renders a
        # domain picker identical to the chat-driven flow; the user
        # decides where the topology lands. We return the normalized
        # topology + suggested filesystem-safe name so the picker can
        # pre-fill its input without the caller having to re-derive it.
        metadata = topology.get("metadata") or {}
        suggested = (metadata.get("name") or "ai-topology").strip() or "ai-topology"
        return self._send_json({
            "ok": True,
            "status": "pending_placement",
            "suggested_name": suggested,
            "display_name": suggested,
            "topology": topology,
            "text": raw.get("text", ""),
            "model": raw.get("model"),
            "provider": raw.get("provider"),
            "usage": raw.get("usage") or {},
        })

    # Historical helper kept for binary compatibility: older entry
    # points (or any out-of-tree callers) may still invoke it. It writes
    # to the built-in `__ai` domain using the same conventions as
    # _handle_bug_topology_create. The in-tree AI chat / generate paths
    # no longer call it -- those now emit a pending_placement payload
    # and let the user decide where the topology lands.
    def _ai_save_generated_topology(self, username, topology):
        """Persist an AI-generated topology under the user's built-in
        `__ai` domain and return the saved metadata.

        Kept only for backward compatibility with older clients / tests.
        New code should let the frontend's domain picker route saves
        through ``POST /api/sections/<sid>/save``.
        """
        self._sections_read(username)  # ensures __ai is injected
        sdir = self._section_dir(username, "__ai")
        os.makedirs(sdir, exist_ok=True)
        metadata = topology.get("metadata") or {}
        base_name = (metadata.get("name") or "ai-topology").strip() or "ai-topology"
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_name)
        candidate = safe
        suffix = 1
        while os.path.isfile(os.path.join(sdir, candidate + ".json")):
            suffix += 1
            candidate = f"{safe}_{suffix}"
        fname = candidate + ".json"
        with open(os.path.join(sdir, fname), "w") as f:
            json.dump(topology, f, indent=2)
        return {"section_id": "__ai", "filename": fname, "name": candidate}

    # --- Jira fetcher ----------------------------------------------------
    @staticmethod
    def _jira_request(cfg, rel_url, timeout=15):
        """GET <base_url><rel_url> with HTTP Basic Auth (email:token).
        Returns parsed JSON or raises Exception on any error.
        """
        import base64
        base = cfg["base_url"].rstrip("/")
        url = base + rel_url
        cred = base64.b64encode(f"{cfg['email']}:{cfg['api_token']}".encode()).decode()
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {cred}",
            "Accept": "application/json",
            "User-Agent": "DriveNets-Topology-Studio/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")[:200]
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} {e.reason} ({body})")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Cannot reach Jira: {e.reason}")

    def _jira_fetch_issue(self, cfg, sw_id):
        """Fetch issue + first page of comments. Returns the merged dict.
        We always include `issuetype` so the caller can enforce the "must
        be a bug-like ticket" check before building a topology.
        """
        issue = self._jira_request(
            cfg,
            f"/rest/api/3/issue/{sw_id}?fields=summary,description,labels,"
            f"components,status,priority,issuetype"
        )
        try:
            comments = self._jira_request(
                cfg,
                f"/rest/api/3/issue/{sw_id}/comment?maxResults=20&orderBy=created"
            )
            issue["_comments"] = comments.get("comments", []) if isinstance(comments, dict) else []
        except Exception:
            issue["_comments"] = []
        return issue

    @staticmethod
    def _classify_issue_type(issue):
        """Return (issue_type_name, is_bug_like) from a Jira issue dict.

        is_bug_like is True iff the issuetype.name maps to BUG_LIKE_ISSUE_TYPES
        (case-insensitive) OR contains the substring "bug" / "defect" anywhere
        (handles custom workflows like "Production Bug" / "Customer Defect").
        Unknown / missing issue type is treated as NOT bug-like so the caller
        can ask the user to confirm.
        """
        fields = (issue or {}).get("fields") or {}
        itype = fields.get("issuetype") or {}
        name = (itype.get("name") or "").strip()
        if not name:
            return "", False
        lname = name.lower()
        if lname in BUG_LIKE_ISSUE_TYPES:
            return name, True
        if "bug" in lname or "defect" in lname:
            return name, True
        return name, False

    # --- Jira ticket parser ----------------------------------------------
    @staticmethod
    def _adf_to_text(node, out=None):
        """Walk Atlassian Document Format -> plain text. Best-effort, never raises."""
        if out is None:
            out = []
        if not isinstance(node, dict):
            return "".join(out)
        nt = node.get("type")
        if nt == "text":
            out.append(node.get("text", ""))
        for child in node.get("content", []) or []:
            Handler._adf_to_text(child, out)
        # Block boundaries -> newline so headings/paragraphs separate.
        if nt in ("paragraph", "heading", "listItem", "codeBlock", "blockquote",
                   "tableRow", "tableCell", "tableHeader", "rule"):
            out.append("\n")
        return "".join(out)

    def _jira_parse_to_inputs(self, issue, sw_id):
        """Distill the Jira ticket down to the inputs the topology builder
        consumes: devices, vrfs, route, symptom, failure-device hint."""
        import re
        fields = issue.get("fields") or {}
        title = (fields.get("summary") or "").strip()
        # Description can be ADF (dict) or plain string depending on Jira version.
        desc_field = fields.get("description")
        if isinstance(desc_field, dict):
            description = self._adf_to_text(desc_field)
        elif isinstance(desc_field, str):
            description = desc_field
        else:
            description = ""
        # Concatenate all comments (also possibly ADF).
        comments_text = []
        for c in issue.get("_comments", []) or []:
            body = c.get("body")
            if isinstance(body, dict):
                comments_text.append(self._adf_to_text(body))
            elif isinstance(body, str):
                comments_text.append(body)
        full_text = "\n".join([title, description] + comments_text)

        # 1) Devices: PE-N, RR-XXX-N, P-N, CE-N, ExaBGP, Spirent, FortiGate.
        device_patterns = [
            r"\b(PE-\d+)\b",
            r"\b(RR-[A-Z]+-?\d*)\b",
            r"\b(P-\d+)\b",
            r"\b(CE-\d+)\b",
            r"\b(ExaBGP)\b",
            r"\b(Spirent)\b",
            r"\b(FortiGate)\b",
            r"\b(NCC-\d+)\b",
            r"\b(NCP-\d+)\b",
        ]
        seen = []
        seen_lower = set()
        for pat in device_patterns:
            for m in re.finditer(pat, full_text):
                name = m.group(1)
                key = name.lower()
                if key not in seen_lower:
                    seen_lower.add(key)
                    seen.append(name)
        # Order: source-y devices on the left, RR on the right.
        def _device_rank(name):
            n = name.lower()
            if n.startswith("exa") or n.startswith("spirent") or n.startswith("ce-"):
                return 0
            if n.startswith("pe-"):
                return 1
            if n.startswith("p-"):
                return 2
            if n.startswith("rr-"):
                return 3
            if n.startswith("ncc-") or n.startswith("ncp-"):
                return 4
            return 5
        seen.sort(key=_device_rank)

        # 2) Per-device IPs (look for "PE-1 (1.1.1.1)" or "PE-1: 1.1.1.1").
        ip_re = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b")
        device_records = []
        for name in seen:
            ip = ""
            for pat in [
                rf"\b{re.escape(name)}\s*[:\s]\s*\(?({ip_re.pattern.strip('()')})\)?",
                rf"{re.escape(name)}\s*\(\s*({ip_re.pattern.strip('()')})\s*\)",
            ]:
                m = re.search(pat, full_text, re.IGNORECASE)
                if m:
                    ip = m.group(1)
                    break
            visual = "server" if name.lower() in ("exabgp", "spirent", "fortigate") else "classic"
            color = ("#e67e22" if visual == "server"
                     else "#9b59b6" if name.lower().startswith("rr-")
                     else "#2ecc71" if name.lower().startswith("ce-")
                     else "#3498db")
            device_records.append({
                "label": name,
                "ip": ip,
                "color": color,
                "visualStyle": visual,
            })
        if not device_records:
            # No identifiable devices -> single placeholder so the canvas
            # still loads cleanly. The user can rename it.
            device_records.append({"label": "Device", "color": "#3498db", "visualStyle": "classic"})

        # 3) VRFs: "VRF NAME", "vrf NAME", optional RD/RT after.
        vrfs = []
        for m in re.finditer(r"\bVRF[\s_-]+([A-Z][A-Z0-9_-]{1,24})\b", full_text):
            vrf_name = m.group(1)
            if vrf_name.upper() in ("NAME", "INSTANCE", "TYPE"):
                continue
            window = full_text[m.start():m.start() + 240]
            rd_m = re.search(r"\bRD\s*[:=]?\s*((?:\d{1,3}\.){3}\d{1,3}:\d+|\d+:\d+)", window)
            rt_m = re.search(r"\bRT\s*[:=]?\s*(\d+:\d+)", window)
            entry = {"name": vrf_name}
            if rd_m: entry["rd"] = rd_m.group(1)
            if rt_m: entry["rt"] = rt_m.group(1)
            # Avoid duplicate VRFs.
            if not any(v["name"] == vrf_name for v in vrfs):
                vrfs.append(entry)

        # 4) Route info: dst prefix + action keyword (redirect-ip / redirect-vrf / drop).
        route = {}
        m = re.search(r"\b(dst|destination|prefix)\s*[:=]?\s*((?:\d{1,3}\.){3}\d{1,3}/\d+)", full_text, re.IGNORECASE)
        if m:
            route["dst"] = m.group(2)
        m = re.search(r"\b(src|source)\s*[:=]?\s*((?:\d{1,3}\.){3}\d{1,3}/\d+)", full_text, re.IGNORECASE)
        if m:
            route["src"] = m.group(2)
        m = re.search(r"\bredirect-ip\s+((?:\d{1,3}\.){3}\d{1,3})\b", full_text, re.IGNORECASE)
        if m:
            route["action"] = f"redirect-ip {m.group(1)}"
        else:
            m = re.search(r"\b(redirect-vrf|drop|rate-limit\s+\d+)\b", full_text, re.IGNORECASE)
            if m:
                route["action"] = m.group(1)

        # 5) Failure device hint (look for "fails on PE-1" / "broken on RR-X" / etc.).
        failure_device = ""
        m = re.search(
            r"\b(?:fails?|broken|crashes|stuck|drops?|never (?:becomes?|reaches?)) (?:on|at|in)?\s*"
            r"(PE-\d+|RR-[A-Z]+-?\d*|P-\d+|CE-\d+|ExaBGP)",
            full_text, re.IGNORECASE,
        )
        if m:
            failure_device = m.group(1)
        elif device_records:
            # Default to the centermost PE-like device.
            for d in device_records:
                if d["label"].lower().startswith("pe-"):
                    failure_device = d["label"]
                    break
            if not failure_device:
                failure_device = device_records[-1]["label"]

        # 6) Symptom (<= 3 lines): take the title + first 2 non-trivial lines of the description.
        symptom_lines = [title] if title else []
        for line in description.splitlines():
            stripped = line.strip("-* \t")
            if not stripped or len(stripped) < 12:
                continue
            if stripped.lower().startswith(("steps", "reproduce", "expected", "actual", "environment")):
                continue
            symptom_lines.append(stripped[:120])
            if len(symptom_lines) >= 3:
                break
        summary = "\n".join(symptom_lines).strip()

        # 7) Ticket URL for one-click reference.
        base = ""
        # The fetcher knows the base_url, but we don't pass it here -- so
        # synthesize from the issue's `self` field.
        self_url = issue.get("self", "")
        if self_url:
            m = re.match(r"^(https?://[^/]+)", self_url)
            if m:
                base = m.group(1)
        ticket_url = f"{base}/browse/{sw_id}" if base else ""

        return {
            "title": title,
            "summary": summary,
            "devices": device_records,
            "vrfs": vrfs,
            "route": route,
            "failure_device": failure_device,
            "ticket_url": ticket_url,
        }

    @staticmethod
    def _normalize_sw_id(raw):
        import re
        if not raw:
            return ""
        r = raw.strip().upper().replace(" ", "")
        m = re.match(r"^(SW|BUG|DPI|FR|EPM)-?(\d+)$", r)
        if not m:
            return ""
        return f"{m.group(1)}-{m.group(2)}"

    @staticmethod
    def _build_bug_topology_json(sw_id, title="", summary="", devices=None,
                                  vrfs=None, route=None, failure_device="",
                                  ticket_url="", source="placeholder",
                                  issue_type=""):
        """Build a /debug-dnos-style topology JSON.

        Design goals (2026-05-13 pass):
          - MORE VISUAL, LESS TEXT. The canvas is the picture; text
            supports it. We keep exactly the words the user cannot
            infer from the picture: the SW id, a one-line title, the
            device labels, and a short symptom line.
          - SYMMETRIC ARROW PATHS. Bug diagrams default to a centered
            left-to-right chain with arrowed links, so the failure flow
            is obvious before reading any text.
          - READABLE ON THE DARK GRID. Every text block that sits over
            the canvas body has a solid panel behind it
            (showBackground=true with a ~0.88 alpha fill). Previously
            the header floated as plain red text and washed out on a
            dark canvas.
          - CONSISTENT AXES. Title/URL top, compact symptom and route
            cards above the centered path, devices on the horizontal
            mid-line, cross on the failing device, optional VRF chips
            above their PEs.

        Inputs (all optional except sw_id):
          - title           short ticket title (top header)
          - summary         <=2-line symptom (route-info box on the left)
          - devices         [{ label, ip, color, visualStyle }, ...]
          - vrfs            [{ name, rd, rt }, ...] -- one panel per PE
          - route           { dst, src, action } -- route-info box content
          - failure_device  device label that gets the red cross marker
          - ticket_url      surfaced as a clickable link chip under the header
          - source          "jira" | "placeholder" (recorded in metadata)
          - issue_type      Jira issuetype.name ("Bug", "Defect", ...);
                            "" when not fetched

        Layout (left -> right):
          source / CE / tool -> PE / RR / downstream, centered around
          the canvas midpoint.
        """
        devices = list(devices or [])
        vrfs = list(vrfs or [])
        route = dict(route or {})
        objs = []
        device_id_counter = 0
        link_id_counter = 0
        text_id_counter = 0
        shape_id_counter = 0

        # Reusable style presets. Every "info" text block over the canvas
        # body gets a filled translucent panel so the text stays
        # readable on the dark grid. We pair each panel color with a
        # matching accent color for the text itself.
        PANEL_HEADER_BG = "rgba(192, 57, 43, 0.88)"     # solid red panel
        PANEL_URL_BG = "rgba(52, 73, 94, 0.85)"         # dark slate chip
        PANEL_SUMMARY_BG = "rgba(42, 33, 22, 0.90)"     # warm dark card
        PANEL_ROUTE_BG = "rgba(22, 40, 60, 0.90)"       # cool dark card
        PANEL_VRF_BG = "rgba(45, 30, 55, 0.88)"         # violet tinted chip
        BORDER_HEADER = "rgba(231, 76, 60, 0.85)"
        BORDER_URL = "rgba(93, 173, 226, 0.70)"
        BORDER_SUMMARY = "rgba(230, 126, 34, 0.55)"
        BORDER_ROUTE = "rgba(93, 173, 226, 0.60)"
        BORDER_VRF = "rgba(187, 143, 206, 0.60)"

        # --- 1) HEADER BAR -------------------------------------------------
        # SW-id + short title on one compact panel. No more bare red text
        # floating over the grid.
        header_line = f"BUG  {sw_id}"
        if title:
            # Trim so the header stays one or two lines max; agents can
            # lengthen it via enrichment later if they want to.
            short_title = title.strip().splitlines()[0]
            if len(short_title) > 82:
                short_title = short_title[:79] + "..."
            header_line += f"\n{short_title}"
        objs.append({
            "id": f"text_{text_id_counter}",
            "type": "text",
            "x": 520,
            "y": 72,
            "text": header_line,
            "fontSize": 14,
            "color": "#ffffff",
            "showBackground": True,
            "backgroundColor": PANEL_HEADER_BG,
            "backgroundOpacity": 92,
            "backgroundPadding": 10,
            "showBorder": True,
            "borderColor": BORDER_HEADER,
            "borderWidth": 1,
        })
        text_id_counter += 1

        # --- 1b) TICKET URL CHIP ------------------------------------------
        # Small dark panel directly beneath the header. Keeps the link
        # clickable visually without adding three extra lines of noise.
        if ticket_url:
            objs.append({
                "id": f"text_{text_id_counter}",
                "type": "text",
                "x": 520,
                "y": 108,
                "text": ticket_url,
                "fontSize": 10,
                "color": "#9bd0f5",
                "showBackground": True,
                "backgroundColor": PANEL_URL_BG,
                "backgroundOpacity": 85,
                "backgroundPadding": 6,
                "showBorder": True,
                "borderColor": BORDER_URL,
                "borderWidth": 1,
            })
            text_id_counter += 1

        # --- 2) DEVICES ---------------------------------------------------
        # Role-aware coloring: CE green, PE blue, RR purple, "failure"
        # override to red when the user hints which device is broken.
        # This carries meaning in the picture instead of prose.
        if not devices:
            devices = [{"label": "Device", "color": "#3498db", "visualStyle": "classic"}]
        n = len(devices)
        col_gap = 260
        center_x = 560
        first_x = center_x - ((max(n, 1) - 1) * col_gap / 2)
        device_y = 360
        device_radius = 38
        device_records = []

        def _role_color(lbl, idx, total):
            lbl_l = (lbl or "").lower()
            if lbl_l.startswith("ce") or "spirent" in lbl_l or "exa" in lbl_l:
                return "#2ecc71"  # green for client/traffic source
            if lbl_l.startswith("rr") or "route-reflector" in lbl_l or "reflector" in lbl_l:
                return "#9b59b6"  # purple for RR
            if lbl_l.startswith("pe"):
                return "#3498db"  # blue for PE
            if idx == 0:
                return "#2ecc71"
            if idx == total - 1 and total > 2:
                return "#9b59b6"
            return "#3498db"

        for idx, dev in enumerate(devices):
            x = round(first_x + idx * col_gap)
            label = (dev.get("label") or f"Node-{idx+1}")[:32]
            color = dev.get("color") or _role_color(label, idx, n)
            visual = dev.get("visualStyle") or "classic"
            device_type = dev.get("deviceType") or "router"
            if device_type not in ("router", "switch"):
                device_type = "router"
            objs.append({
                "id": f"device_{device_id_counter}",
                "type": "device",
                "deviceType": device_type,
                "x": x,
                "y": device_y,
                "radius": device_radius,
                "color": color,
                "label": label,
                "locked": False,
                "visualStyle": visual,
            })
            device_records.append({
                "id": f"device_{device_id_counter}",
                "x": x,
                "y": device_y,
                "label": label,
            })
            device_id_counter += 1
            ip = (dev.get("ip") or "").strip()
            if ip:
                objs.append({
                    "id": f"text_{text_id_counter}",
                    "type": "text",
                    "x": x,
                    "y": device_y + device_radius + 26,
                    "text": ip,
                    "fontSize": 10,
                    "color": "#d0d5db",
                    "showBackground": True,
                    "backgroundColor": "rgba(30, 35, 45, 0.78)",
                    "backgroundOpacity": 80,
                    "backgroundPadding": 4,
                })
                text_id_counter += 1

        # --- 2b) VRF CHIPS ------------------------------------------------
        # One chip per VRF, hovered above the PE it belongs to. We shrink
        # the old "VRF/RD/RT" three-line block to a compact two-line chip
        # so it reads like a badge rather than a paragraph.
        pe_records = [d for d in device_records if d.get("label", "").lower().startswith("pe-")]
        if not pe_records:
            pe_records = device_records
        for v_idx, vrf in enumerate(vrfs):
            if not pe_records:
                break
            target = pe_records[v_idx % len(pe_records)]
            name = vrf.get("name", "UNKNOWN")
            rd = vrf.get("rd") or ""
            rt = vrf.get("rt") or ""
            # Compact: "VRF name" on top, "RD x  RT y" on one line below
            bottom = []
            if rd:
                bottom.append(f"RD {rd}")
            if rt:
                bottom.append(f"RT {rt}")
            chip_lines = [f"VRF {name}"]
            if bottom:
                chip_lines.append("  ".join(bottom))
            objs.append({
                "id": f"text_{text_id_counter}",
                "type": "text",
                "x": target["x"],
                "y": device_y - device_radius - 70
                     - (v_idx // max(len(pe_records), 1)) * 56,
                "text": "\n".join(chip_lines),
                "fontSize": 10,
                "color": "#e8d4f2",
                "showBackground": True,
                "backgroundColor": PANEL_VRF_BG,
                "backgroundOpacity": 88,
                "backgroundPadding": 7,
                "showBorder": True,
                "borderColor": BORDER_VRF,
                "borderWidth": 1,
            })
            text_id_counter += 1

        # --- 3) LINKS -----------------------------------------------------
        # Arrowed links carry the flow direction, so the path is readable
        # even with minimal captions. Keep labels out of the generator;
        # enrichment can add one or two link-attached labels when needed.
        for i in range(len(device_records) - 1):
            a = device_records[i]
            b = device_records[i + 1]
            link_id = f"link_{link_id_counter}"
            objs.append({
                "id": link_id,
                "type": "link",
                "originType": "QL",
                "device1": a["id"],
                "device2": b["id"],
                "start": {"x": a["x"] + device_radius, "y": a["y"]},
                "end": {"x": b["x"] - device_radius, "y": b["y"]},
                "color": "#85c1e9",
                "style": "arrow",
                "width": 3,
            })
            link_id_counter += 1

        # --- 4) SUMMARY CARD ----------------------------------------------
        # Before: "Bug Summary:" / "Issue Summary:" headers plus a long
        # paragraph. Now: a single "Symptom" chip with <=2 lines (~120
        # chars max). Long prose lives in metadata.bug_summary for
        # traceability; it does not belong on the canvas.
        if summary:
            s = " ".join(summary.strip().split())  # collapse whitespace
            # Keep it tight: one sentence + trailing ellipsis if longer.
            if len(s) > 120:
                s = s[:117] + "..."
            card_text = f"Symptom\n{s}"
        else:
            card_text = (
                "Symptom\n"
                f"Placeholder -- ask the agent \"/bug-topology {sw_id}\" to enrich."
            )
        objs.append({
            "id": f"text_{text_id_counter}",
            "type": "text",
            "x": center_x - 230,
            "y": 200,
            "text": card_text,
            "fontSize": 11,
            "color": "#f5cba7",
            "showBackground": True,
            "backgroundColor": PANEL_SUMMARY_BG,
            "backgroundOpacity": 90,
            "backgroundPadding": 9,
            "showBorder": True,
            "borderColor": BORDER_SUMMARY,
            "borderWidth": 1,
        })
        text_id_counter += 1

        # --- 4b) ROUTE CARD (right side) ----------------------------------
        route_lines = []
        if route.get("dst"):
            route_lines.append(f"dst  {route['dst']}")
        if route.get("src"):
            route_lines.append(f"src  {route['src']}")
        if route.get("action"):
            route_lines.append(f"act  {route['action']}")
        if route_lines:
            right_x = center_x + 230
            objs.append({
                "id": f"text_{text_id_counter}",
                "type": "text",
                "x": right_x,
                "y": 200,
                "text": "Route\n" + "\n".join(route_lines),
                "fontSize": 11,
                "color": "#aed6f1",
                "showBackground": True,
                "backgroundColor": PANEL_ROUTE_BG,
                "backgroundOpacity": 90,
                "backgroundPadding": 9,
                "showBorder": True,
                "borderColor": BORDER_ROUTE,
                "borderWidth": 1,
            })
            text_id_counter += 1

        # --- 5) FAILURE MARKER -------------------------------------------
        # One red cross is enough for the generated baseline. Extra callouts
        # belong in later enrichment, not the first-pass bug topology.
        target_record = device_records[0]
        target_idx = 0
        if failure_device:
            for di, d in enumerate(device_records):
                if d.get("label", "").lower() == failure_device.lower():
                    target_record = d
                    target_idx = di
                    break
        objs.append({
            "id": f"shape_{shape_id_counter}",
            "type": "shape",
            "shapeType": "cross",
            "x": target_record["x"] + device_radius + 12,
            "y": target_record["y"] - device_radius - 10,
            "width": 28,
            "height": 28,
            "rotation": 0,
            "fillColor": "#e74c3c",
            "fillOpacity": 1.0,
            "fillEnabled": True,
            "strokeColor": "#c0392b",
            "strokeWidth": 2,
            "strokeEnabled": True,
        })
        shape_id_counter += 1

        # --- 6) LAYERED PACKET (auto, only when we have something to say) -
        # When the bug topology has a route hint OR a vrf with RT/RD, emit
        # a single layered packet chip attached to the link approaching the
        # failure_device. The chip shows L2 / VLAN-or-MPLS / L3 / L4 /
        # Payload rows, with empty rows hidden (visible=false) so the
        # frontend renders a compact card. Operators can toggle layers
        # back on or rename them via the packet popup.
        packet_id_counter = 0
        wants_packet = bool(route.get("dst") or route.get("src") or route.get("action") or vrfs)
        if wants_packet and len(device_records) >= 2:
            def _norm_name(value):
                return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

            def _packet_summary_from_route():
                text = " ".join(str(v) for v in (
                    route.get("protocol"),
                    route.get("action"),
                    route.get("type"),
                    title,
                    summary,
                ) if v)
                text_l = text.lower()
                if "flowspec" in text_l or "flow spec" in text_l:
                    return "FLOWSPEC"
                if "evpn" in text_l and ("rt-2" in text_l or "rt2" in text_l or "mac" in text_l):
                    return "EVPN RT-2"
                if "vpls-pw" in text_l or "vpls pw" in text_l or "vpws" in text_l:
                    return "VPLS PW"
                if "bgp" in text_l or "route" in text_l or "update" in text_l:
                    return "BGP UPD"
                if vrfs:
                    return "VRF FLOW"
                return "FRAME"

            def _packet_direction_for_link(anchor_idx):
                left = device_records[anchor_idx]
                right = device_records[anchor_idx + 1]
                left_names = {_norm_name(left.get(k)) for k in ("id", "label", "hostname", "name")}
                right_names = {_norm_name(right.get(k)) for k in ("id", "label", "hostname", "name")}
                src_hint = _norm_name(route.get("src_device") or route.get("source_device") or route.get("from_device") or route.get("fromDevice"))
                dst_hint = _norm_name(route.get("dst_device") or route.get("target_device") or route.get("to_device") or route.get("toDevice"))
                if src_hint or dst_hint:
                    if (src_hint and src_hint in left_names) or (dst_hint and dst_hint in right_names):
                        return "forward"
                    if (src_hint and src_hint in right_names) or (dst_hint and dst_hint in left_names):
                        return "backward"
                # Default bug topology flow points toward the failure device.
                return "forward" if anchor_idx + 1 == target_idx else "backward"

            # Anchor: the link arriving at the failure device. If the
            # failure device is the first node, use the first outbound link
            # instead so the packet still sits on the path.
            anchor_link_idx = max(0, target_idx - 1)
            anchor_link_idx = min(anchor_link_idx, len(device_records) - 2)
            anchor_link_id = f"link_{anchor_link_idx}"
            l3_src = (route.get("src") or "").strip()
            l3_dst = (route.get("dst") or "").strip()
            action = (route.get("action") or "").strip()
            # Pick MPLS / VLAN content from the first VRF when present.
            vlan_text = ""
            mpls_text = ""
            if vrfs:
                first_vrf = vrfs[0]
                rt = (first_vrf.get("rt") or "").strip()
                rd = (first_vrf.get("rd") or "").strip()
                if rd or rt:
                    mpls_text = "label=auto"
                    if rt:
                        mpls_text += f"  RT {rt}"
                    if rd:
                        mpls_text += f"  RD {rd}"
            l4_text = ""
            if action:
                # Surface drop/forward verdict on L4 row so the packet
                # explains the failure inline.
                l4_text = f"verdict={action}"
            payload_text = ""
            if summary:
                short_payload = " ".join(summary.strip().split())
                if len(short_payload) > 60:
                    short_payload = short_payload[:57] + "..."
                payload_text = short_payload
            layers = [
                {
                    "id": "L2",
                    "label": "L2",
                    "text": "Ethernet (src/dst MAC)",
                    "color": "#5dade2",
                    "visible": True,
                },
                {
                    "id": "VLAN",
                    "label": "VLAN",
                    "text": vlan_text,
                    "color": "#48c9b0",
                    "visible": bool(vlan_text),
                },
                {
                    "id": "MPLS",
                    "label": "MPLS",
                    "text": mpls_text,
                    "color": "#bb8fce",
                    "visible": bool(mpls_text),
                },
                {
                    "id": "L3",
                    "label": "L3",
                    "text": (
                        f"src {l3_src or '?'}  ->  dst {l3_dst or '?'}"
                        if (l3_src or l3_dst) else ""
                    ),
                    "color": "#f5b041",
                    "visible": bool(l3_src or l3_dst),
                },
                {
                    "id": "L4",
                    "label": "L4",
                    "text": l4_text,
                    "color": "#e59866",
                    "visible": bool(l4_text),
                },
                {
                    "id": "PAYLOAD",
                    "label": "Payload",
                    "text": payload_text,
                    "color": "#85c1e9",
                    "visible": bool(payload_text),
                },
            ]
            objs.append({
                "id": f"packet_{packet_id_counter}",
                "type": "packet",
                "linkId": anchor_link_id,
                "linkAttachT": 0.5,
                # x/y will be recomputed by updatePacketPosition once the
                # frontend loads, but seed sensible coordinates so older
                # clients that ignore the attachment still draw something
                # near the path.
                "x": (target_record["x"] - device_radius - 80),
                "y": (device_y - 90),
                "title": "Frame",
                "summary": _packet_summary_from_route(),
                "direction": _packet_direction_for_link(anchor_link_idx),
                "collapsed": False,
                "layers": layers,
                "locked": False,
            })
            packet_id_counter += 1

        return {
            "version": "1.0",
            "objects": objs,
            "metadata": {
                "deviceIdCounter": device_id_counter,
                "linkIdCounter": link_id_counter,
                "textIdCounter": text_id_counter,
                "shapeIdCounter": shape_id_counter,
                "packetIdCounter": packet_id_counter,
                "description": f"Bug topology for {sw_id}",
                "sw_id": sw_id,
                "bug_title": title,
                "bug_summary": summary,
                "bug_source": source,
                "bug_issue_type": issue_type,
                "bug_ticket_url": ticket_url,
                "bug_failure_device": failure_device,
                "bug_route": route,
                "bug_vrfs": vrfs,
                "generated_by": "topology/serve.py:_build_bug_topology_json",
            },
        }

    def _xray_user(self):
        """Return (username, role) for the current request, or (None, None)
        when no JWT was supplied. Captures + config are scoped on this."""
        auth = self.headers.get("Authorization", "")
        return _extract_jwt_username(auth), _extract_jwt_role(auth)

    def _require_xray_user(self):
        """For mutating XRAY ops: require an authenticated user. Returns
        (username, role) or sends 401 + None."""
        auth = self.headers.get("Authorization", "")
        username = _extract_jwt_username(auth)
        if not username:
            self._send_json({"error": "Authentication required"}, 401)
            return None, None
        return username, _extract_jwt_role(auth)

    def _capture_owned(self, capture_id):
        """Look up a capture, returning (entry, owner_ok). Admin role
        always passes the owner check.

        Unauthenticated requests are NEVER granted access -- not even to
        legacy `_owner=""` captures, since their pcaps may live in shared
        directories and could expose another user's traffic.
        """
        entry = XRAY_CAPTURES.get(capture_id)
        if not entry:
            return None, False
        username, role = self._xray_user()
        if not username:
            return entry, False
        if role == "admin":
            return entry, True
        owner = entry.get("_owner") or ""
        if not owner:
            return entry, owner == username
        return entry, owner == username

    # Two classes of credentials live in xray_config.json:
    #
    # 1. SHARED service accounts (same value for every user, like an SSH key
    #    the whole lab uses). DUT default `dnroot/dnroot` and the DNAAS
    #    fabric service account `sisaev/Drive1234!` belong here -- they are
    #    NOT personal data; they are DriveNets-wide lab defaults.
    # 2. PER-USER personal data (the user's own Mac VPN IP, their personal
    #    SSH user/password to that Mac, the Wireshark path on their own
    #    laptop, their personal Arista lab account). These MUST stay blank
    #    until the user fills them in -- never seeded from another user.
    _XRAY_SHARED_SAFE_KEYS = ("script_path", "decoder_path")
    _XRAY_SHARED_SAFE_CREDS = ("device_user", "device_password")
    _XRAY_SHARED_DNAAS = ("user", "password")

    def _xray_default_config(self):
        """Empty-but-bootable XRAY config for a brand-new user.

        Pre-filled with shared lab defaults only:
          - DUT user/pass (`dnroot/dnroot`)
          - DNAAS fabric service account (`sisaev/Drive1234!`) -- shared lab
            credential used by every user; safe to default.
          - Script paths from the global config.

        Personal fields (Mac IP/user/password, Wireshark path, Arista lab
        account) stay blank so each user enters their own.
        """
        cfg = {
            "version": 2,
            "mac": {
                "user": "",
                "password": "",
                "ip_vpn": "",
                "ip_office": "",
                "wireshark_path": "",
                "pcap_directory": "",
            },
            "credentials": {
                "device_user": "dnroot",
                "device_password": "dnroot",
                "arista_user": "",
                "arista_password": "",
            },
            "dnaas_credentials": {
                "user": "sisaev",
                "password": "Drive1234!",
            },
            "client": {},
            "setup_complete": False,
        }
        # Pull script paths and shared service accounts from the global config
        # if present, so a site can override the bundled defaults centrally
        # (e.g. swap to a different DUT user) without editing every user file.
        try:
            with open(XRAY_CONFIG_PATH, "r") as f:
                global_cfg = json.load(f)
            for k in self._XRAY_SHARED_SAFE_KEYS:
                if global_cfg.get(k):
                    cfg[k] = global_cfg[k]
            global_creds = global_cfg.get("credentials", {})
            for k in self._XRAY_SHARED_SAFE_CREDS:
                if global_creds.get(k):
                    cfg["credentials"][k] = global_creds[k]
            global_dnaas = global_cfg.get("dnaas_credentials", {})
            for k in self._XRAY_SHARED_DNAAS:
                if global_dnaas.get(k):
                    cfg["dnaas_credentials"][k] = global_dnaas[k]
        except Exception:
            pass
        return cfg

    def _xray_config_read(self):
        """Per-user XRAY config (no cross-user leakage, ever).

        - Authenticated user: returns only `~/.topology_users/<u>/xray.json`
          merged onto safe defaults. Brand-new users get blank Mac / Arista
          creds and shared DUT/DNAAS service accounts -- never another
          user's secrets.
        - Unauthenticated request: returns safe defaults ONLY (shared
          service accounts + blank personal fields). The global
          `~/.xray_config.json` is NEVER returned to anonymous callers
          because it may contain a previous owner's personal Mac creds
          left over from legacy single-user mode.
        """
        username, _ = self._xray_user()
        cfg = self._xray_default_config()
        if not username:
            return cfg
        path = _user_xray_config_path(username)
        try:
            with open(path, "r") as f:
                user_cfg = json.load(f)
            for k, v in user_cfg.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k] = {**cfg[k], **v}
                else:
                    cfg[k] = v
        except Exception:
            pass
        return cfg

    def _xray_config_write(self, data):
        """Persist XRAY config in the caller's per-user file.

        Refuses to write when the caller is unauthenticated -- otherwise
        an anonymous request could overwrite the global file that other
        anonymous callers might still read in legacy installs.
        Returns True on success, False if the caller had no JWT.
        """
        username, _ = self._xray_user()
        if not username:
            return False
        path = _user_xray_config_path(username)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except OSError:
            pass
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return True

    def _handle_device_sync(self, device_id):
        """Sync (fetch) running config from device. Proxies to scaler_bridge when available."""
        try:
            url = SCALER_BRIDGE_API + f"/api/config/{urllib.parse.quote(device_id)}/sync"
            req = urllib.request.Request(url, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return self._send_json(data)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else "{}"
            try:
                err_data = json.loads(err_body)
                return self._send_json({"detail": err_data.get("detail", str(e))}, e.code)
            except Exception:
                return self._send_json({"detail": str(e)}, e.code)
        except Exception as e:
            return self._send_json({"detail": f"Scaler bridge unavailable: {e}"}, 503)

    # Mac-verification TTL: after this many seconds a previous `verify-mac`
    # success no longer counts and the user must re-verify before another
    # mac-output capture can start. Protects against stale VPN/IP changes.
    _XRAY_MAC_VERIFY_TTL_SECONDS = 30 * 60

    # Labels that identify a DNAAS fabric device (LEAF/SPINE/NCM/NCF/...).
    # Mirrors the JS list in topology-dnaas.js::isRouter -- both must stay
    # in sync (test_xray_dnaas_pov_gate_unit.py asserts this).
    #
    # CONTRACT: a DNAAS fabric device is NOT a valid POV for normal cp/dp
    # tcpdump captures: the live_capture.py path SSHes into a DNOS shell
    # and runs `tcpdump`, which is wrong for DNAAS leaves (they expect the
    # mirror-via-uplink flow, hence the dedicated `dnaas-dp` mode that
    # uses `--dnaas-leaf-host` + the shared sisaev service account).
    # Refusing here is defense-in-depth -- the frontend popup also
    # disables the DNAAS POV button, but a direct API call must still
    # be rejected.
    _DNAAS_LABEL_KEYWORDS = (
        "DNAAS", "LEAF", "SPINE", "FABRIC", "TOR",
        "AGGREGATION", "AGG-", "CORE-", "-LEAF", "-SPINE",
        "NCM", "NCF",
    )

    @classmethod
    def _is_dnaas_device_label(cls, label):
        """True if a device label matches one of the DNAAS fabric patterns."""
        if not label:
            return False
        upper = str(label).upper()
        return any(kw in upper for kw in cls._DNAAS_LABEL_KEYWORDS)

    def _xray_build_capture_filter(self, params):
        """Merge explicit XRAY BPF with row-derived VLAN/IP filters."""
        parts = []
        explicit = (params.get("capture_filter") or "").strip()
        if explicit:
            parts.append(f"({explicit})")
        capture_intf = str(
            params.get("capture_interface") or params.get("interface") or ""
        ).strip()
        # If tcpdump/packet-capture is already attached to a VLAN
        # sub-interface (bundle-100.12, geX.Y, ...), the VLAN tag is often
        # stripped at that capture point. Adding BPF `vlan 12` then drops
        # every packet and produces an empty pcap.
        suppress_vlan = bool(re.search(r"\.\d+(?:$|:)", capture_intf))
        if params.get("auto_vlan_filter") and not suppress_vlan:
            outer = str(params.get("vlan_outer") or params.get("vlanOuter") or "").strip()
            inner = str(params.get("vlan_inner") or params.get("vlanInner") or "").strip()
            if outer.isdigit():
                parts.append(f"vlan {outer}")
            if inner.isdigit():
                parts.append(f"vlan {inner}")
        if params.get("auto_ip_filter"):
            ip = str(params.get("ip") or params.get("ip_address") or params.get("ipAddress") or "").strip()
            if "/" in ip:
                ip = ip.split("/", 1)[0].strip()
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip) or ":" in ip:
                parts.append(f"host {ip}")
        return " and ".join(parts)

    @staticmethod
    def _xray_is_ipv4(value):
        return bool(re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", str(value or "").strip()))

    @staticmethod
    def _xray_inventory_key(value):
        return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

    def _xray_load_device_inventory_index(self):
        """Return alias -> inventory entry from the SCALER device DB.

        XRAY only reads this shared lab inventory to resolve DNAAS display
        labels (for example DNAAS-LEAF-B10 / B10) into SSH targets. Capture
        state, config, and pcaps remain per-user.
        """
        index = {}
        try:
            with open(XRAY_SCALER_DEVICES_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return index
        devices = raw.get("devices") if isinstance(raw, dict) else raw
        if not isinstance(devices, list):
            return index
        for entry in devices:
            if not isinstance(entry, dict):
                continue
            names = [
                entry.get("id"),
                entry.get("hostname"),
                entry.get("name"),
                entry.get("serial"),
                entry.get("serial_number"),
                entry.get("ip"),
                entry.get("mgmt_ip"),
                entry.get("management_ip"),
            ]
            aliases = entry.get("aliases")
            if isinstance(aliases, list):
                names.extend(aliases)
            for name in names:
                key = self._xray_inventory_key(name)
                if key:
                    index[key] = entry
        return index

    def _xray_inventory_entry_host(self, entry):
        if not isinstance(entry, dict):
            return ""
        for field in ("mgmt_ip", "management_ip", "ip", "ssh_host", "host"):
            host = str(entry.get(field) or "").split("/")[0].strip()
            if self._xray_is_ipv4(host):
                return host
        return ""

    def _xray_resolve_inventory_host(self, *names):
        index = self._xray_load_device_inventory_index()
        for raw in names:
            name = str(raw or "").strip()
            if not name:
                continue
            if self._xray_is_ipv4(name):
                return name
            entry = index.get(self._xray_inventory_key(name))
            host = self._xray_inventory_entry_host(entry)
            if host:
                return host
        return ""

    def _xray_resolve_device_host(self, *names):
        """Resolve labels/aliases/IPs for XRAY helper SSH targets."""
        resolved = self._xray_resolve_inventory_host(*names)
        if resolved:
            return resolved
        return self._xray_discover_mgmt_ip(*names)

    def _xray_discover_mgmt_ip(self, *names):
        """Resolve a topology label/serial to a DUT management IP."""
        seen = set()
        for raw in names:
            name = str(raw or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            try:
                url = (
                    DISCOVERY_API
                    + f"/api/device/{urllib.parse.quote(name)}/management-interfaces"
                )
                with urllib.request.urlopen(url, timeout=10) as resp:
                    mgmt = json.loads(resp.read())
                first_ip = ""
                for iface in mgmt.get("interfaces", []):
                    for addr in iface.get("ipv4_addresses", []):
                        ip = str(addr).split("/")[0].strip()
                        if not ip:
                            continue
                        first_ip = first_ip or ip
                        if "mgmt0" in str(iface.get("name", "")).lower():
                            return ip
                if first_ip:
                    return first_ip
            except Exception:
                continue
        return ""

    def _xray_resolve_dut_host(self, params):
        """Prefer a real SSH address over display labels before live_capture."""
        explicit = str(params.get("dut_host") or "").strip()
        if explicit and self._xray_is_ipv4(explicit):
            return explicit
        device_name = str(params.get("device") or "").strip()
        resolved = self._xray_resolve_device_host(explicit, device_name)
        if resolved:
            return resolved
        return explicit

    @staticmethod
    def _xray_parse_mirror_preflight_outputs(desc_output, sessions_output, config_output):
        """Return free DNAAS mirror destination candidates from read-only CLI output."""
        iface_re = re.compile(r"\b((?:ge|hu|ce|qsfp)\d*-\d+/\d+/\d+(?:\.\d+)?)\b")
        candidate_words = re.compile(r"(port[_ -]?mirroring|for[_ -]?port[_ -]?mirror|mirror)", re.IGNORECASE)
        candidates = []
        for line in (desc_output or "").splitlines():
            if not candidate_words.search(line):
                continue
            match = iface_re.search(line)
            if not match:
                continue
            iface = match.group(1)
            if "." in iface:
                continue
            if iface not in candidates:
                candidates.append(iface)

        active_destinations = []
        for match in re.finditer(r"Destination interface:\s*(\S+)", sessions_output or "", re.IGNORECASE):
            dest = match.group(1).strip().rstrip(",")
            if dest and dest not in active_destinations:
                active_destinations.append(dest)

        configured_subifs = {}
        for iface in candidates:
            subif_re = re.compile(rf"\binterfaces\s+{re.escape(iface)}\.(\d+)\b")
            configured_subifs[iface] = sorted(set(subif_re.findall(config_output or "")), key=lambda x: int(x))

        busy = [iface for iface in candidates if iface in active_destinations]
        blocked_by_subinterfaces = [
            {"interface": iface, "subinterfaces": configured_subifs.get(iface, [])}
            for iface in candidates
            if configured_subifs.get(iface)
        ]
        blocked_set = {row["interface"] for row in blocked_by_subinterfaces}
        free = [
            iface for iface in candidates
            if iface not in active_destinations and iface not in blocked_set
        ]
        return {
            "available": bool(free),
            "chosen": free[0] if free else "",
            "candidates": candidates,
            "free": free,
            "busy": busy,
            "blocked_by_subinterfaces": blocked_by_subinterfaces,
            "active_destinations": active_destinations,
            "reason": (
                f"Free mirror destination: {free[0]}"
                if free else
                "No free physical DNAAS mirror destination found from show interfaces description, port-mirroring sessions, and interface config"
            ),
        }

    def _xray_run_leaf_show_commands(self, host, username, password, commands, timeout=10):
        import paramiko
        import socket
        import time as _time

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host,
                username=username,
                password=password,
                timeout=timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            shell = client.invoke_shell(width=240, height=60)
            shell.settimeout(timeout)
            _time.sleep(1.0)
            while shell.recv_ready():
                shell.recv(65535)

            def run_cmd(cmd):
                shell.send(cmd.rstrip() + "\n")
                output = ""
                end = _time.time() + timeout
                idle_since = None
                while _time.time() < end:
                    if shell.recv_ready():
                        output += shell.recv(65535).decode("utf-8", errors="ignore")
                        idle_since = None
                        if output.rstrip():
                            last = output.rstrip().splitlines()[-1].strip()
                            if last.endswith("#") or last.endswith(">"):
                                break
                    else:
                        if output and idle_since is None:
                            idle_since = _time.time()
                        elif output and (_time.time() - idle_since) > 0.8:
                            break
                        _time.sleep(0.1)
                return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", output)

            return {cmd: run_cmd(cmd) for cmd in commands}
        except (socket.timeout, paramiko.SSHException, OSError) as e:
            raise RuntimeError(f"Cannot read DNAAS leaf mirror config from {host}: {e}") from e
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _xray_resolve_spine_from_lldp(self, lldp_output):
        index = self._xray_load_device_inventory_index()
        for line in (lldp_output or "").splitlines():
            for token in re.split(r"[\s|,;]+", line):
                clean = token.strip().strip("()[]{}<>")
                if not clean:
                    continue
                entry = index.get(self._xray_inventory_key(clean))
                if not entry:
                    continue
                identity = " ".join(str(entry.get(k) or "") for k in (
                    "hostname", "id", "platform", "device_class", "fabric_role"
                )).upper()
                if "SPINE" not in identity:
                    continue
                host = self._xray_inventory_entry_host(entry)
                if host:
                    return {
                        "spine_host": host,
                        "spine_label": entry.get("hostname") or entry.get("id") or clean,
                    }
        return {}

    def _xray_dnaas_mirror_preflight(self, params):
        cfg = self._xray_config_read()
        dnaas_creds = cfg.get("dnaas_credentials") or {}
        leaf_label = str(params.get("leaf_label") or params.get("dnaas_leaf_label") or "").strip()
        raw_host = str(params.get("leaf_host") or params.get("dnaas_leaf_host") or leaf_label).strip()
        if not raw_host:
            return {"available": False, "error": "DNAAS leaf host is required"}
        host = self._xray_resolve_device_host(raw_host, leaf_label)
        if not host:
            return {
                "available": False,
                "error": f"Could not resolve DNAAS leaf host '{raw_host}' from inventory or discovery",
                "leaf_label": leaf_label or raw_host,
            }
        user = (dnaas_creds.get("user") or "sisaev").strip()
        password = dnaas_creds.get("password") or "Drive1234!"
        commands = [
            "show interfaces description | no-more",
            "show services port-mirroring sessions | no-more",
            "show config interfaces | flatten",
        ]
        outputs = self._xray_run_leaf_show_commands(host, user, password, commands)
        result = self._xray_parse_mirror_preflight_outputs(
            outputs.get(commands[0], ""),
            outputs.get(commands[1], ""),
            outputs.get(commands[2], ""),
        )
        result["leaf_host"] = host
        result["leaf_label"] = leaf_label or raw_host
        requested_spine = str(params.get("spine_host") or params.get("dnaas_spine_host") or "").strip()
        resolved_spine = self._xray_resolve_device_host(requested_spine)
        if resolved_spine:
            result["spine_host"] = resolved_spine
            result["spine_label"] = requested_spine
        elif result.get("chosen"):
            # DNOS documented LLDP detail syntax is `show lldp neighbors <interface>`.
            lldp_cmd = f"show lldp neighbors {result['chosen']} | no-more"
            try:
                lldp = self._xray_run_leaf_show_commands(host, user, password, [lldp_cmd])
                result["lldp_command"] = lldp_cmd
                result.update(self._xray_resolve_spine_from_lldp(lldp.get(lldp_cmd, "")))
            except Exception as e:
                result["spine_warning"] = f"Could not resolve DNAAS spine from leaf LLDP: {e}"
        return result

    def _xray_run(self, params):
        cfg = self._xray_config_read()
        username, _role = self._xray_user()
        script = cfg.get("script_path", os.path.expanduser("~/live_capture.py"))
        creds = cfg.get("credentials", {})
        mac = cfg.get("mac", {})

        # Backend gate: refuse a DNAAS fabric device as the capture POV
        # for cp/dp/auto modes. dnaas-dp is the right knob for DNAAS leaves
        # (it calls a different code path that talks to the leaf via the
        # shared service account and mirrors via the uplink). cp/dp on a
        # leaf would just hang in a tcpdump call against a shell that
        # isn't there. See `_DNAAS_LABEL_KEYWORDS` for the patterns.
        requested_mode = (params.get("mode") or "").strip()
        device_label = (params.get("device") or "").strip()
        if self._is_dnaas_device_label(device_label) and requested_mode != "dnaas-dp":
            return {"error": (
                f"'{device_label}' is a DNAAS fabric device and cannot be "
                f"the capture POV in '{requested_mode or 'cp'}' mode. Switch "
                f"to DP (DNAAS) mode, or pick a non-DNAAS endpoint as the POV."
            )}

        # Backend gate: mac/mac-live captures require a recent successful
        # verify-mac for the *current* mac.ip_vpn. This is defense-in-depth
        # even if the frontend button lock is bypassed (direct API call,
        # scripted client, buggy JS, etc). See DEVELOPMENT_GUIDELINES.md
        # "XRAY packet capture" section for the contract.
        requested_output = (params.get("output") or "").strip()
        needs_mac = requested_output in ("mac", "mac-live") or requested_mode == "dp"
        if needs_mac:
            current_ip = (mac.get("ip_vpn") or "").strip()
            verified_ip = (mac.get("verified_ip") or "").strip()
            verified_at = mac.get("verified_at")
            if not current_ip:
                return {"error": "No Mac workstation IP configured. Set it in XRAY settings and click 'Verify Workstation'."}
            if not verified_ip or verified_ip != current_ip:
                return {"error": f"Mac workstation not verified for IP {current_ip}. Click 'Verify Workstation' in XRAY settings first."}
            try:
                age_s = time.time() - float(verified_at)
            except (TypeError, ValueError):
                return {"error": "Mac verification record is invalid. Click 'Verify Workstation' in XRAY settings to re-verify."}
            if age_s > self._XRAY_MAC_VERIFY_TTL_SECONDS:
                mins = int(self._XRAY_MAC_VERIFY_TTL_SECONDS / 60)
                return {"error": f"Mac verification expired (>{mins} min). Click 'Verify Workstation' in XRAY settings to re-verify."}

        if requested_mode == "dnaas-dp":
            preflight = self._xray_dnaas_mirror_preflight({
                "leaf_host": params.get("dnaas_leaf_host") or "",
                "leaf_label": params.get("dnaas_leaf_label") or "",
                "spine_host": params.get("dnaas_spine_host") or "",
            })
            if not preflight.get("available"):
                return {"error": preflight.get("reason") or preflight.get("error") or "No free DNAAS mirror destination is available"}
            params["dnaas_leaf_host"] = preflight["leaf_host"]
            if preflight.get("leaf_label"):
                params["dnaas_leaf_label"] = preflight["leaf_label"]
            if preflight.get("spine_host"):
                params["dnaas_spine_host"] = preflight["spine_host"]
            if not params.get("dnaas_mirror_uplink") and preflight.get("chosen"):
                params["dnaas_mirror_uplink"] = preflight["chosen"]

        capture_id = str(uuid.uuid4())[:8]
        cmd = ["python3", script, "-m", params.get("mode", "cp")]
        cmd += ["-s", params.get("interface", "any")]
        cmd += ["-t", str(params.get("duration", 10))]
        cmd += ["-y"]
        cmd += ["--session-name", f"XRAY_{capture_id}"]
        if params.get("device"):
            cmd += ["--device-label", str(params.get("device"))]

        # Direction: ingress, egress, both
        direction = params.get("direction", "both")
        if direction in ("ingress", "egress", "both"):
            cmd += ["-d", direction]

        # Capture filter (BPF). Row-aware Link Table capture can request
        # automatic VLAN/IP predicates; keep explicit user filters intact.
        capture_filter = self._xray_build_capture_filter(params)
        if capture_filter:
            cmd += ["--capture-filter", capture_filter]

        # Device host -- explicit verified IP/host or inventory-resolved label.
        # Frontend state can contain display labels (for example RR-SA-2) in
        # sshConfig.host; never pass those blindly to live_capture.py because
        # Paramiko will treat them as DNS names and fail with socket.gaierror.
        dut_host = self._xray_resolve_dut_host(params)
        if dut_host:
            cmd += ["--dut-host", dut_host]

        if creds.get("device_user"):
            cmd += ["--dut-user", creds["device_user"]]
        if creds.get("device_password"):
            cmd += ["--dut-pass", creds["device_password"]]

        out_mode = params.get("output", "mac")
        if out_mode in ("mac", "mac-live"):
            cmd += ["-o", out_mode]
            if mac.get("ip_vpn"):
                cmd += ["--mac-host", mac["ip_vpn"]]
            if mac.get("user"):
                cmd += ["--mac-user", mac["user"]]
            if mac.get("password"):
                cmd += ["--mac-pass", mac["password"]]
            if mac.get("wireshark_path"):
                cmd += ["--wireshark-path", mac["wireshark_path"]]
            if mac.get("pcap_directory"):
                cmd += ["--mac-directory", mac["pcap_directory"]]
        elif out_mode == "pcap":
            cmd += ["-o", "pcap"]
        else:
            cmd += ["-o", "auto"]

        # DP mode extras
        if params.get("mode") == "dp":
            if params.get("arista_host"):
                cmd += ["--arista-host", params["arista_host"]]
            if params.get("arista_src_port"):
                cmd += ["--arista-src-port", params["arista_src_port"]]
            if creds.get("arista_user"):
                cmd += ["--arista-user", creds["arista_user"]]
            if creds.get("arista_password"):
                cmd += ["--arista-pass", creds["arista_password"]]

        # DNAAS-DP mode: DNAAS leaves use a shared lab service account
        # (sisaev / Drive1234!). Per-user override is supported but rare --
        # we default to the shared account that _xray_default_config seeds.
        if params.get("mode") == "dnaas-dp":
            dnaas_creds = cfg.get("dnaas_credentials") or {}
            leaf_user = (dnaas_creds.get("user") or "sisaev").strip()
            leaf_pass = dnaas_creds.get("password") or "Drive1234!"
            if params.get("dnaas_leaf_host"):
                cmd += ["--dnaas-leaf-host", params["dnaas_leaf_host"]]
            if params.get("dnaas_leaf_source_port"):
                cmd += ["--dnaas-leaf-source-port", params["dnaas_leaf_source_port"]]
            if params.get("dnaas_mirror_uplink"):
                cmd += ["--dnaas-mirror-uplink", params["dnaas_mirror_uplink"]]
            if params.get("dnaas_spine_host"):
                cmd += ["--dnaas-spine-host", params["dnaas_spine_host"]]
            cmd += ["--dnaas-leaf-user", leaf_user]
            cmd += ["--dnaas-leaf-pass", leaf_pass]
            cmd += ["--dnaas-spine-user", leaf_user]
            cmd += ["--dnaas-spine-pass", leaf_pass]

        retain_pcap = should_retain_pcap(username)
        cleanup_pcap = params.get("cleanup_server_pcap", True) and out_mode == "mac"
        needs_mac_delivery = out_mode in ("mac", "mac-live")
        try:
            requested_duration = int(params.get("duration", 0) or 0)
        except (TypeError, ValueError):
            requested_duration = 0

        # Per-user captures dir: tell live_capture exactly where to land the
        # pcap (-f) so different users never see each other's files. Without
        # this, every pcap lands in the server's CWD, mixing users together.
        captures_dir = _user_captures_dir(username)
        ts = time.strftime("%Y%m%d_%H%M%S")
        pcap_filename = (
            params.get("pcap_filename")
            or f"{username or 'global'}_{capture_id}_{ts}.pcap"
        )
        pcap_target = os.path.join(captures_dir, pcap_filename)
        cmd += ["-f", pcap_target]

        entry = {
            "status": "running",
            "output_lines": [],
            "pcap_path": None,
            "error": None,
            "process": None,
            "_owner": username or "",
            "_started_at": time.time(),
            "_target_pcap": pcap_target,
            "_output_mode": out_mode,
            "_retain_pcap": retain_pcap,
            "_pcap_ephemeral": not retain_pcap,
            "_requested_duration": requested_duration,
            "mac_delivery_status": "pending" if needs_mac_delivery else "not_required",
            "mac_delivery_step": "queued" if needs_mac_delivery else "not_required",
        }
        XRAY_CAPTURES[capture_id] = entry

        def run():
            def _last_meaningful_output() -> str:
                lines = [
                    str(line).strip()
                    for line in entry.get("output_lines", [])[-30:]
                    if str(line).strip()
                ]
                priority = [
                    line for line in lines
                    if re.search(r"\b(fatal|error|failed|exception|permission denied|unknown word|timeout|timed out|no route|unreachable)\b", line, re.I)
                ]
                useful = priority[-4:] or lines[-6:]
                return " | ".join(useful)

            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                entry["process"] = proc
                mac_delivered = False
                for line in proc.stdout:
                    entry["output_lines"].append(line.rstrip())
                    if len(entry["output_lines"]) > 200:
                        entry["output_lines"] = entry["output_lines"][-100:]
                    lower_line = line.lower()
                    if (
                        "pcap saved" in lower_line
                        or "saved locally" in lower_line
                        or "wrote" in lower_line
                        or "writing pcap to" in lower_line
                        or "pcap retrieved" in lower_line
                    ):
                        for token in line.split():
                            clean_token = token.strip().strip(":,;()[]")
                            clean_token = re.sub(r"\x1b\[[0-9;]*m", "", clean_token)
                            if clean_token.endswith(".pcap"):
                                entry["pcap_path"] = clean_token
                    if "MAC_DELIVERY_FAILED" in line:
                        entry["mac_delivery_failed"] = True
                        entry["mac_delivery_status"] = "failed"
                        entry["mac_delivery_step"] = "failed"
                    if any(marker in lower_line for marker in (
                        "connecting to mac",
                        "opening wireshark on mac",
                        "auto-scp to mac",
                        "deploy mac helper",
                    )):
                        if entry.get("mac_delivery_status") == "pending":
                            entry["mac_delivery_status"] = "in_progress"
                    # Granular sub-steps so the popup can render a fine-grained
                    # progress strip rather than one generic "Delivering..." line.
                    # Order is loosely chronological; a later step never regresses
                    # to an earlier step (`_PROMOTE` map below).
                    if "connecting to mac for sftp" in lower_line:
                        _xray_promote_step(entry, "sftp_connecting")
                    elif "mac verified at" in lower_line:
                        _xray_promote_step(entry, "mac_verified")
                    if "pcap delivered to mac" in lower_line:
                        _xray_promote_step(entry, "sftp_done")
                    if "opening wireshark on mac" in lower_line:
                        _xray_promote_step(entry, "opening_wireshark")
                    if "pcap saved locally:" in lower_line or "saved locally:" in lower_line:
                        for token in line.split():
                            clean_token = token.strip().strip(":,;()[]")
                            clean_token = re.sub(r"\x1b\[[0-9;]*m", "", clean_token)
                            if clean_token.endswith(".pcap"):
                                entry["local_pcap_path"] = clean_token
                    if "wireshark opened on mac" in lower_line or "delivered to mac" in lower_line or "opened in wireshark" in lower_line:
                        mac_delivered = True
                        entry["mac_delivery_status"] = "delivered"
                        _xray_promote_step(entry, "opened")
                    if out_mode == "mac-live" and (
                        "mac helper deployed" in lower_line
                        or "live streaming:" in lower_line
                        or "tcpdump started on" in lower_line
                    ):
                        mac_delivered = True
                        entry["mac_delivery_status"] = "delivered"
                        _xray_promote_step(entry, "opened")
                    ll = lower_line
                    if ("ssh" in ll or "scp" in ll or "sshpass" in ll) and ("refused" in ll or "unreachable" in ll or "timed out" in ll or "no route" in ll or "permission denied" in ll):
                        entry["mac_delivery_failed"] = True
                        entry["mac_delivery_status"] = "failed"
                    if "connection reset" in ll or "broken pipe" in ll:
                        entry.setdefault("mac_delivery_failed", True)
                        entry["mac_delivery_status"] = "failed"
                proc.wait()
                if not entry.get("pcap_path") and os.path.isfile(entry.get("_target_pcap", "")):
                    entry["pcap_path"] = entry.get("_target_pcap")
                elapsed = max(0.0, time.time() - float(entry.get("_started_at") or time.time()))
                early_exit = (
                    proc.returncode == 0
                    and requested_duration > 0
                    and elapsed < max(1.0, requested_duration - 2)
                )
                if early_exit:
                    entry["error"] = (
                        f"Capture exited after {elapsed:.1f}s before requested "
                        f"{requested_duration}s duration"
                    )
                    if needs_mac_delivery and not mac_delivered:
                        entry["mac_delivery_failed"] = True
                        entry["mac_delivery_status"] = "failed"
                if needs_mac_delivery and proc.returncode == 0 and not mac_delivered and not entry.get("mac_delivery_failed"):
                    saved_pcap = entry.get("local_pcap_path") or entry.get("pcap_path")
                    if saved_pcap and os.path.isfile(saved_pcap):
                        entry["mac_delivery_status"] = "unconfirmed"
                        entry["mac_delivery_unconfirmed"] = True
                    else:
                        entry["mac_delivery_failed"] = True
                        entry["mac_delivery_status"] = "failed"
                        entry["error"] = "Capture finished but Mac delivery was not confirmed"
                entry["status"] = "completed" if proc.returncode == 0 and not early_exit else "error"
                if proc.returncode != 0:
                    detail = _last_meaningful_output()
                    entry["error"] = f"Exit code {proc.returncode}" + (f": {detail}" if detail else "")
                    if not mac_delivered:
                        entry["mac_delivery_failed"] = True
                        entry["mac_delivery_status"] = "failed"
                if not retain_pcap:
                    if (
                        (mac_delivered and not entry.get("mac_delivery_failed"))
                        or entry.get("status") == "error"
                        or entry.get("mac_delivery_failed")
                    ):
                        _xray_cleanup_capture_pcaps(entry, "ephemeral_capture_finished")
                    else:
                        _xray_schedule_ephemeral_cleanup(entry, "ephemeral_awaiting_download")
                elif cleanup_pcap and mac_delivered and not entry.get("mac_delivery_failed"):
                    for p in [entry.get("pcap_path"), entry.get("local_pcap_path")]:
                        if p and os.path.isfile(p):
                            try:
                                os.remove(p)
                                entry["server_pcap_cleaned"] = True
                            except OSError:
                                pass
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
            finally:
                entry["process"] = None

        t = threading.Thread(target=run, daemon=True)
        t.start()
        return capture_id

    # ---------------------------------------------------------------
    # Admin + Owner tier endpoints (2026-04-22)
    # ---------------------------------------------------------------
    # Tightly scoped helpers for the new user-menu panels. Three gates:
    #   _require_admin()      -> user must have role == 'admin' or be owner
    #   _require_owner()      -> user must pass _is_owner_user()
    #   _require_auth_role()  -> any logged-in user is fine (tuple variant)
    # NOTE: do NOT shadow the legacy `_require_auth()` defined earlier on
    # this class (it returns a bare username string and is used by ~20
    # legacy callers). The admin/owner gates below use a distinct helper
    # so both shapes can coexist safely.
    # Owner-tier endpoints are intentionally conservative:
    #   /api/owner/restart is a no-op unless ALLOW_OWNER_RESTART=1 is set,
    #   /api/owner/reset-configs rewrites only per-user AI + Jira configs
    #     (topologies/domains/sections are NEVER touched), and
    #   /api/owner/impersonate only returns a token bearing the caller's
    #     own role (impersonation is cosmetic "view-as" on the frontend,
    #     not a real session swap, so it can't be abused for privilege
    #     escalation).
    # ---------------------------------------------------------------
    def _require_auth_role(self):
        """Return (username, role) for any logged-in caller; 401 and (None, None)
        when no JWT is present.

        Distinct from the legacy `_require_auth()` on this class which
        returns only the username string -- do not unify the two without
        auditing every legacy caller first."""
        auth = self.headers.get("Authorization", "")
        username = _extract_jwt_username(auth)
        if not username:
            self._send_json({"error": "Authentication required"}, 401)
            return None, None
        return username, _extract_jwt_role(auth)

    def _require_admin(self):
        """Return (username, role) when the caller is admin OR owner.
        Sends 401/403 + (None, None) on failure."""
        username, role = self._require_auth_role()
        if not username:
            return None, None
        if role == "admin":
            return username, role
        if _is_owner_user(username):
            return username, role
        self._send_json({"error": "Admin role required"}, 403)
        return None, None

    def _require_owner(self):
        """Return (username, role) when the caller is the deployment owner.
        Sends 401/403 + (None, None) on failure."""
        username, role = self._require_auth_role()
        if not username:
            return None, None
        if _is_owner_user(username):
            return username, role
        self._send_json({"error": "Owner-only endpoint"}, 403)
        return None, None

    def _handle_admin_diagnostics(self):
        """Return a compact snapshot used by the Server Diagnostics dialog.

        Admin-only. Builds its data from the monitor thread's shared state
        (`_child_procs`, `_child_start_times`) so diagnostics are fast and
        never shell out. Adds a /api/health echo for convenience.
        """
        username, _role = self._require_admin()
        if not username:
            return
        now = time.time()
        svcs = {}
        try:
            for name, proc in _child_procs.items():
                started = _child_start_times.get(name, 0.0)
                alive = bool(proc and (proc.poll() is None))
                svcs[name] = {
                    "alive": alive,
                    "pid": getattr(proc, "pid", None),
                    "uptime_sec": max(0, int(now - started)) if started else 0,
                    "health_fail_count": _health_fail_count.get(name, 0),
                }
        except Exception as e:
            svcs["_error"] = str(e)

        memory = {}
        try:
            import resource  # Unix only
            usage = resource.getrusage(resource.RUSAGE_SELF)
            memory = {
                "maxrss_kb": usage.ru_maxrss,
                "user_time_sec": round(usage.ru_utime, 2),
                "system_time_sec": round(usage.ru_stime, 2),
            }
        except Exception:
            pass

        topology_users_count = 0
        topology_dirs = 0
        try:
            base = TOPOLOGY_USERS_BASE
            if os.path.isdir(base):
                for name in os.listdir(base):
                    udir = os.path.join(base, name)
                    if os.path.isdir(udir):
                        topology_users_count += 1
                        tdir = os.path.join(udir, "topologies")
                        if os.path.isdir(tdir):
                            topology_dirs += len([f for f in os.listdir(tdir) if f.endswith(".json")])
        except Exception:
            pass

        # Best-effort peek at /api/health for the full service map.
        health = {}
        try:
            with urllib.request.urlopen("http://127.0.0.1:" + str(PORT) + "/api/health", timeout=1) as r:
                health = json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            pass

        return self._send_json({
            "now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "server_port": PORT,
            "services": svcs,
            "memory": memory,
            "topology_users_count": topology_users_count,
            "topology_files_count": topology_dirs,
            "health": health,
            "gemini_shared_key_set": bool(os.environ.get("GEMINI_API_KEY")),
            "owner_username_override": os.environ.get("OWNER_USERNAME", ""),
        })

    def _handle_admin_shared_key_status(self):
        """Report whether the GEMINI_API_KEY shared key is active.

        Counts (a) whether the env var is set, (b) its masked tail, and
        (c) how many per-user AI configs exist (so an admin can tell at
        a glance how many users would be force-overridden). Does NOT
        leak the key value or any other user's personal data."""
        username, _role = self._require_admin()
        if not username:
            return
        key = os.environ.get("GEMINI_API_KEY") or ""
        masked = ""
        if key:
            if len(key) <= 8:
                masked = "*" * len(key)
            else:
                masked = key[:3] + "*" * (len(key) - 7) + key[-4:]
        per_user_configs = 0
        try:
            base = TOPOLOGY_USERS_BASE
            if os.path.isdir(base):
                for name in os.listdir(base):
                    cfg = os.path.join(base, name, "ai_config.json")
                    if os.path.isfile(cfg):
                        per_user_configs += 1
        except Exception:
            pass
        return self._send_json({
            "enabled": bool(key),
            "masked_key": masked,
            "per_user_configs_count": per_user_configs,
            "env_var": "GEMINI_API_KEY",
        })

    def _handle_admin_audit(self):
        """Return the last ~200 audit events. Admin-only."""
        username, _role = self._require_admin()
        if not username:
            return
        with _ADMIN_AUDIT_LOCK:
            events = list(_ADMIN_AUDIT_RING[-_ADMIN_AUDIT_MAX:])
        events.reverse()  # newest first
        return self._send_json({"events": events, "count": len(events)})

    def _handle_admin_broadcast(self, body):
        """Post a broadcast toast that every logged-in user picks up via
        /api/admin/announcements polling."""
        username, _role = self._require_admin()
        if not username:
            return
        try:
            data = json.loads(body or b"{}") if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        message = (data.get("message") or "").strip()
        if not message:
            return self._send_json({"error": "message is required"}, 400)
        if len(message) > 280:
            return self._send_json({"error": "message is too long (280 char max)"}, 400)
        level = (data.get("level") or "info").strip().lower()
        if level not in ("info", "warn", "success", "error"):
            level = "info"
        ttl = int(data.get("ttl_sec") or 120)
        ttl = max(5, min(1800, ttl))  # 5s..30min
        entry = {
            "id": str(uuid.uuid4()),
            "message": message[:280],
            "level": level,
            "ts": time.time(),
            "expires_at": time.time() + ttl,
            "sender": username,
        }
        with _ANNOUNCEMENTS_LOCK:
            _ANNOUNCEMENTS.append(entry)
            if len(_ANNOUNCEMENTS) > _ANNOUNCEMENTS_MAX:
                del _ANNOUNCEMENTS[: len(_ANNOUNCEMENTS) - _ANNOUNCEMENTS_MAX]
        _record_audit("broadcast_sent", username, {"message": message[:80], "level": level})
        return self._send_json({"ok": True, "announcement": entry})

    def _handle_announcements_get(self):
        """Return currently-active announcements for the polling client.

        Accessible to any authenticated user (no admin gate) because
        everyone receives the broadcast toasts. Only non-expired entries
        are returned."""
        username, _role = self._require_auth_role()
        if not username:
            return
        now = time.time()
        with _ANNOUNCEMENTS_LOCK:
            live = [a for a in _ANNOUNCEMENTS if a.get("expires_at", 0) > now]
        return self._send_json({"announcements": live, "count": len(live)})

    def _handle_feature_flags_get(self):
        """Return feature flags. Admin-only (regular users don't need to
        see the raw flag map; their toggles are read by other code)."""
        username, _role = self._require_admin()
        if not username:
            return
        return self._send_json({"flags": _load_feature_flags(), "defaults": dict(_FEATURE_FLAGS_DEFAULTS)})

    def _handle_feature_flags_put(self, body):
        """Merge-update feature flags. Unknown keys are ignored so the API
        surface is stable even if the admin UI drifts from the server."""
        username, _role = self._require_admin()
        if not username:
            return
        try:
            data = json.loads(body or b"{}") if body else {}
        except Exception:
            return self._send_json({"error": "Invalid JSON body"}, 400)
        flags = _load_feature_flags()
        applied = {}
        for k, v in (data.get("flags") or {}).items():
            if k in _FEATURE_FLAGS_DEFAULTS:
                flags[k] = bool(v)
                applied[k] = bool(v)
        _save_feature_flags(flags)
        _record_audit("feature_flags_updated", username, {"applied": applied})
        return self._send_json({"ok": True, "flags": flags, "applied": applied})

    def _handle_admin_reload_knowledge(self):
        """Hot-reload the AI knowledge digest (ai/knowledge.md) without
        restarting the server. Works by calling the ai module's reload
        hook if available; otherwise returns a helpful stub."""
        username, _role = self._require_admin()
        if not username:
            return
        if not _ensure_ai_module():
            return self._send_json({"error": "AI module not loaded"}, 503)
        # Try a few likely entry points so this keeps working even if the
        # ai module grows a different reload name. Safe: only calls them
        # when they exist; never executes arbitrary code. The hook can
        # return a dict of stats (bytes, mtime, path) which we forward
        # straight to the admin UI so the toast shows real data.
        tried = []
        for name in ("reload_knowledge", "reload_digest", "refresh_knowledge"):
            fn = getattr(_ai_module, name, None)
            if callable(fn):
                try:
                    result = fn()
                    tried.append({"name": name, "ok": True})
                    _record_audit("knowledge_reloaded", username, {"via": name})
                    payload = {"ok": True, "reloaded_via": name}
                    if isinstance(result, dict):
                        # Pass through known stats so the admin toast can
                        # report "reloaded 12,345 chars" instead of "ok".
                        for k in ("path", "mtime", "size", "length"):
                            if k in result:
                                payload[k] = result[k]
                    return self._send_json(payload)
                except Exception as e:
                    tried.append({"name": name, "ok": False, "error": str(e)})
        return self._send_json({
            "ok": False,
            "error": "No reload hook available in ai module",
            "tried": tried,
        }, 501)

    # ---------- AI blueprint library -------------------------------------
    #
    # These three endpoints power the AI assistant's new `list_blueprints`
    # and `load_blueprint` tools, and the admin "Reload AI Blueprints"
    # button. Blueprints are JSON files under `ai/blueprints/` with
    # per-user overrides under `~/.topology_users/<user>/ai_blueprints/`.
    # See topology/ai/blueprints.py for the loader and
    # topology/ai/blueprints/INDEX.md for the catalog.
    def _handle_ai_blueprints_list(self):
        user = self._require_auth()
        if not user:
            return
        if not _ensure_ai_module():
            return self._send_json({"error": "AI module not loaded"}, 503)
        try:
            from ai.blueprints import list_blueprints as _list_bp
        except Exception as e:  # pragma: no cover -- defensive
            return self._send_json({"error": f"blueprints module broken: {e}"}, 500)
        qs = self._parse_qs_single
        protocol = qs("protocol") or ""
        scale = qs("scale") or ""
        tags_raw = qs("tags") or ""
        query = qs("q") or qs("query") or ""
        try:
            limit = int(qs("limit") or 200)
        except Exception:
            limit = 200
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        try:
            entries = _list_bp(
                username=user,
                protocol=protocol or None,
                scale=scale or None,
                tags=tags or None,
                query=query or None,
                limit=limit,
            )
        except Exception as e:
            return self._send_json({"error": f"list_blueprints failed: {e}"}, 500)
        return self._send_json({"ok": True, "blueprints": entries,
                                "count": len(entries)})

    def _handle_ai_blueprint_get(self, name):
        user = self._require_auth()
        if not user:
            return
        if not _ensure_ai_module():
            return self._send_json({"error": "AI module not loaded"}, 503)
        try:
            from ai.blueprints import load_blueprint as _load_bp
        except Exception as e:  # pragma: no cover -- defensive
            return self._send_json({"error": f"blueprints module broken: {e}"}, 500)
        try:
            payload = _load_bp(name, username=user)
        except Exception as e:
            return self._send_json({"error": f"load_blueprint failed: {e}"}, 500)
        if not payload:
            return self._send_json({"error": f"Blueprint {name!r} not found"}, 404)
        return self._send_json({"ok": True, "name": name, "blueprint": payload})

    def _handle_admin_reload_blueprints(self):
        """Hot-reload the AI blueprint library. Admin only."""
        username, _role = self._require_admin()
        if not username:
            return
        if not _ensure_ai_module():
            return self._send_json({"error": "AI module not loaded"}, 503)
        try:
            from ai.blueprints import reload_blueprints as _reload_bp
        except Exception as e:
            return self._send_json({"error": f"blueprints module broken: {e}"}, 500)
        try:
            stats = _reload_bp(username=username)
        except Exception as e:
            return self._send_json({"error": f"reload_blueprints failed: {e}"}, 500)
        try:
            _record_audit("blueprints_reloaded", username, stats if isinstance(stats, dict) else {})
        except Exception:
            pass
        payload = {"ok": True}
        if isinstance(stats, dict):
            payload.update(stats)
        return self._send_json(payload)

    def _handle_owner_reset_configs(self, body):
        """OWNER ONLY. Wipe per-user ai_config.json / jira_config.json so
        the next request falls back to the shared defaults + the Gemini
        force-override. Topologies / sections / domains are NOT touched."""
        username, _role = self._require_owner()
        if not username:
            return
        try:
            data = json.loads(body or b"{}") if body else {}
        except Exception:
            data = {}
        confirm = str(data.get("confirm", "")).strip().upper()
        # Explicit word-match so a mis-click can't nuke everything.
        if confirm != "RESET":
            return self._send_json({
                "error": "Confirmation required",
                "hint": "POST with body {\"confirm\": \"RESET\"}",
            }, 400)
        removed = []
        try:
            base = TOPOLOGY_USERS_BASE
            if os.path.isdir(base):
                for name in os.listdir(base):
                    udir = os.path.join(base, name)
                    if not os.path.isdir(udir):
                        continue
                    for fname in ("ai_config.json", "jira.json"):
                        fpath = os.path.join(udir, fname)
                        if os.path.isfile(fpath):
                            try:
                                os.remove(fpath)
                                removed.append(os.path.join(name, fname))
                            except OSError:
                                pass
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)
        _record_audit("configs_reset", username, {"count": len(removed)})
        return self._send_json({"ok": True, "removed": removed, "count": len(removed)})

    def _handle_owner_restart(self, body):
        """OWNER ONLY. Gated by ALLOW_OWNER_RESTART=1 env var (off by
        default). When enabled, flips a flag the monitor thread watches
        and exits the process -- systemd / pm2 etc. will bring it back
        up. When disabled, explains the requirement without restarting."""
        username, _role = self._require_owner()
        if not username:
            return
        allowed = os.environ.get("ALLOW_OWNER_RESTART", "").strip() in ("1", "true", "yes", "on")
        if not allowed:
            return self._send_json({
                "error": "Server restart is disabled on this deployment",
                "hint": "Set ALLOW_OWNER_RESTART=1 in the server environment to enable",
                "enabled": False,
            }, 403)
        _record_audit("server_restart_requested", username, {"source": "owner_menu"})
        # Reply BEFORE exiting so the client gets a clean 200.
        self._send_json({
            "ok": True,
            "message": "Server is restarting. Your session will reconnect automatically once it's back.",
        })
        def _kick():
            # Small delay so the response actually flushes.
            time.sleep(0.4)
            try:
                os._exit(0)
            except Exception:
                pass
        threading.Thread(target=_kick, daemon=True).start()
        return None

    def _handle_owner_impersonate(self, body):
        """OWNER ONLY. Returns the metadata the frontend needs to render
        the UI *as if* it were another user (cosmetic view-as mode).

        Note: this does NOT issue a new JWT. The requesting owner's
        token is what continues to authenticate API calls; the frontend
        simply swaps the displayed avatar / name / pill so the owner can
        preview how a teammate sees the app. That keeps the endpoint
        safe -- it cannot be abused to act on behalf of someone else."""
        username, _role = self._require_owner()
        if not username:
            return
        try:
            data = json.loads(body or b"{}") if body else {}
        except Exception:
            data = {}
        target = (data.get("username") or "").strip()
        if not target:
            return self._send_json({"error": "username is required"}, 400)
        # Look up the target's display info via the same user store
        # that /api/auth/users uses; unknown users fail closed.
        try:
            from api.auth.user_store import user_store
            full = user_store.get_user(target)
        except Exception:
            full = None
        if not full:
            return self._send_json({"error": f"User '{target}' not found"}, 404)
        _record_audit("impersonate", username, {"target": target})
        return self._send_json({
            "ok": True,
            "viewer": {"username": username, "owner": True},
            "target": {
                "username": full["username"],
                "display_name": full["display_name"],
                "role": full["role"],
            },
            "note": "View-as preview only; API calls still run as the owner.",
        })

    # -------------------------------------------------------------
    # Owner-only "view-as" workspace browser (2026-04-22).
    #
    # These endpoints let the deployment owner inspect another user's
    # topology workspace (domains + saved topologies) without having to
    # log in as them. They are strictly READ-ONLY: no write / delete
    # paths exist here, so there's no privilege-escalation surface even
    # if someone managed to call them with an owner token. Every access
    # is recorded in the audit log so we can review who looked at whose
    # data after the fact.
    #
    # Path shapes:
    #   GET /api/owner/view-as/<username>/summary
    #   GET /api/owner/view-as/<username>/domains
    #   GET /api/owner/view-as/<username>/domains/<domain_id>/topologies
    #   GET /api/owner/view-as/<username>/domains/<domain_id>/topologies/<topology_id>
    #
    # All payloads are shaped to match what /api/domains/* already
    # returns for the signed-in user, so the frontend can re-use the
    # same renderer code with a different base URL.
    # -------------------------------------------------------------
    def _view_as_parse(self, path):
        """Return (target_username, tail_segments) or (None, []) on a
        malformed path. Also 404s unknown users up-front so the caller
        handlers can just early-return on None."""
        prefix = "/api/owner/view-as/"
        if not path.startswith(prefix):
            return None, []
        remainder = path[len(prefix):]
        parts = [p for p in remainder.split("/") if p]
        if not parts:
            return None, []
        target = urllib.parse.unquote(parts[0])
        # Block obvious traversal / empty names -- the user_store only
        # accepts alphanumerics + [._-] but belt-and-suspenders here.
        if not target or ".." in target or "/" in target or "\\" in target:
            return None, []
        try:
            from api.auth.user_store import user_store as _us
            if not _us.get_user(target):
                self._send_json({"error": f"User '{target}' not found"}, 404)
                return None, []
        except Exception as e:
            self._send_json({"error": f"user_store unavailable: {e}"}, 503)
            return None, []
        return target, parts[1:]

    def _handle_owner_view_as_summary(self, target):
        """Tiny dossier about the target user: display name, role,
        total domains, total topologies, last-login. Useful for the
        header row of the workspace browser in the frontend."""
        try:
            from api.auth.user_store import user_store as _us
            u = _us.get_user(target) or {}
            domains = _us.list_domains(target)
            total_topos = 0
            for d in domains:
                total_topos += int(d.get("topology_count") or 0)
            return self._send_json({
                "ok": True,
                "target": {
                    "username": u.get("username", target),
                    "display_name": u.get("display_name", target),
                    "role": u.get("role", "engineer"),
                    "email": u.get("email", ""),
                    "created_at": u.get("created_at", ""),
                    "last_login": u.get("last_login", ""),
                },
                "domain_count": len(domains),
                "topology_count": total_topos,
            })
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)

    def _handle_owner_view_as_domains(self, target):
        """List the target user's domains. Shape mirrors /api/domains
        (minus the sharing overlays, which only matter for the signed-in
        user's own perspective)."""
        try:
            from api.auth.user_store import user_store as _us
            domains = _us.list_domains(target)
            # Drop sharing overlays that only make sense for the signed-in
            # user; "view as" is a read-only external look, so we don't
            # want to surface "shared with me" rows for the target.
            out = [d for d in domains if not d.get("is_shared_with_me_domain")
                                        and not d.get("is_shared")]
            return self._send_json({"domains": out, "count": len(out)})
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)

    def _handle_owner_view_as_topologies(self, target, domain_id):
        try:
            from api.auth.user_store import user_store as _us
            rows = _us.list_topologies(target, domain_id)
            return self._send_json({"topologies": rows, "count": len(rows)})
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)

    def _handle_owner_view_as_topology_load(self, target, domain_id, topology_id):
        """Return the full saved topology payload for the target user.
        Read-only: the frontend loads this onto the canvas and should
        refuse any downstream "save" call until the viewer exits
        view-as mode."""
        try:
            from api.auth.user_store import user_store as _us
            row = _us.load_topology(target, domain_id, topology_id)
            if not row:
                return self._send_json({"error": "Topology not found"}, 404)
            return self._send_json(row)
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)

    def _do_GET_api_routes(self):
        path = self.path.split("?")[0]
        # SSE event stream: intercepted BEFORE the scaler-bridge proxy so
        # the stream is handled in-process (we need serve.py's local
        # subscriber registry for fan-out from mirror-save handlers).
        if path == "/api/topologies/events":
            return self._handle_sse_topology_events()
        if path.startswith("/mcp/"):
            if path.endswith("/sse") or path == "/mcp/sse":
                return self._proxy_sse_stream()
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/integration/cursor/"):
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/auth/") or path == "/api/domains" or path.startswith("/api/domains/"):
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/dnaas/") or path.startswith("/api/network-mapper/"):
            return self._proxy_to_discovery("GET")
        if path.startswith("/api/config/push/progress/"):
            return self._proxy_sse_stream()
        if path.startswith("/api/topology-generator/"):
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/link-telemetry/"):
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/config/") or path.startswith("/api/operations/") or path.startswith("/api/wizard/") or path.startswith("/api/mirror/"):
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/ssh-pool/"):
            return self._proxy_to_scaler_bridge("GET")
        if path == "/api/ssh/check-port":
            return self._proxy_to_scaler_bridge("GET")
        if path == "/api/events/status":
            return self._proxy_to_scaler_bridge("GET")
        # Auto-monitor (Phase 2 MVP) read endpoints.
        if path == "/api/devices/monitored" or path.startswith("/api/devices/monitored/"):
            return self._proxy_to_scaler_bridge("GET")
        if path == "/api/health":
            return self._handle_health()
        if path == "/api/monitor/health":
            return self._handle_monitor_health()
        if path == "/debug-dnos-topologies/list.json":
            self._serve_debug_dnos_list()
            return
        if path.startswith("/debug-dnos-topologies/") and path.endswith(".json"):
            filename = path.split("/")[-1]
            return self._serve_debug_dnos_file(filename)
        if path == "/api/devices/" or path == "/api/devices":
            devices = []
            try:
                url = DISCOVERY_API + "/api/devices/list"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read())
                    devices = data.get("devices", [])
            except Exception:
                pass
            try:
                inv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device_inventory.json")
                if os.path.exists(inv_path):
                    import re
                    dev_map = {(d.get("hostname") or d.get("id") or "").lower(): d for d in devices}
                    with open(inv_path) as f:
                        inv = json.load(f)
                    for key, dev in inv.get("devices", {}).items():
                        hostname = dev.get("hostname", key)
                        ip_from_key = key if re.match(r"^\d+\.\d+\.\d+\.\d+", key) else ""
                        ip = (dev.get("mgmt_ip") or ip_from_key or "").split("/")[0]
                        hkey = hostname.lower()
                        existing = dev_map.get(hkey)
                        if existing:
                            if ip and not existing.get("ip"):
                                existing["ip"] = ip
                                existing["mgmt_ip"] = ip
                            if not existing.get("serial") and dev.get("serial"):
                                existing["serial"] = dev.get("serial")
                            if not existing.get("system_type") and dev.get("system_type"):
                                existing["system_type"] = dev.get("system_type")
                                existing["platform"] = dev.get("system_type")
                        else:
                            entry = {
                                "id": hostname, "name": hostname, "hostname": hostname,
                                "ip": ip, "mgmt_ip": ip,
                                "serial": dev.get("serial", ""),
                                "system_type": dev.get("system_type", ""),
                                "platform": dev.get("system_type", "NCP"),
                                "source": "inventory_cache",
                            }
                            devices.append(entry)
                            dev_map[hkey] = entry
            except Exception:
                pass
            scaler_configs = os.path.join(os.path.expanduser("~"), "SCALER", "db", "configs")
            if os.path.isdir(scaler_configs):
                import re as _re
                dev_by_name = {d.get("hostname", "").lower(): d for d in devices}
                for dirname in os.listdir(scaler_configs):
                    ops = os.path.join(scaler_configs, dirname, "operational.json")
                    if not os.path.isfile(ops):
                        continue
                    try:
                        try:
                            from routes._ops_writer import read_ops as _r
                            from pathlib import Path as _P
                            o = _r(_P(ops))
                        except Exception:
                            with open(ops) as f:
                                o = json.load(f)
                        raw_mgmt = (o.get("mgmt_ip") or "").split("/")[0]
                        raw_ssh = o.get("ssh_host") or ""
                        ip = raw_mgmt if raw_mgmt and _re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_mgmt) else (raw_ssh if _re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_ssh) else raw_mgmt or "")
                        serial = o.get("serial_number", "")
                        op_sys_type = (o.get("system_type") or o.get("deploy_system_type") or "").strip()
                        existing = dev_by_name.get(dirname.lower())
                        if existing:
                            if not existing.get("ip") and ip:
                                existing["ip"] = ip
                                existing["mgmt_ip"] = ip
                            # operational.json is authoritative for system_type (overrides stale device_inventory)
                            if op_sys_type:
                                existing["system_type"] = op_sys_type
                                existing["platform"] = op_sys_type
                        if not existing:
                            for d in devices:
                                if serial and d.get("serial", "").lower() == serial.lower():
                                    if op_sys_type:
                                        d["system_type"] = op_sys_type
                                        d["platform"] = op_sys_type
                                    if not d.get("ip") and ip:
                                        d["ip"] = ip
                                        d["mgmt_ip"] = ip
                                    break
                            else:
                                entry = {
                                    "id": dirname, "name": dirname, "hostname": dirname,
                                    "ip": ip, "mgmt_ip": ip, "serial": serial, "source": "scaler_cache",
                                }
                                if op_sys_type:
                                    entry["system_type"] = op_sys_type
                                    entry["platform"] = op_sys_type
                                if dirname.lower() not in dev_by_name:
                                    devices.append(entry)
                                    dev_by_name[dirname.lower()] = entry
                    except Exception:
                        continue
            return self._send_json({"devices": devices, "count": len(devices)})
        if path == "/api/devices/watched" or path == "/api/devices/events/recent":
            return self._proxy_to_scaler_bridge("GET")
        if path.startswith("/api/devices/") and len(path) > len("/api/devices/"):
            device_id = path.split("/api/devices/")[1].split("/")[0]
            device_id = urllib.parse.unquote(device_id)
            action = path.split(device_id + "/")[1].split("/")[0] if (device_id + "/") in path else None
            if action in ("context", "git-commit", "mode-probe", "stack-fast"):
                return self._proxy_to_scaler_bridge("GET")
            if action == "resolve":
                return self._proxy_to_scaler_bridge("GET")
            if action in ("watchers", "events", "user-prefs"):
                return self._proxy_to_scaler_bridge("GET")
            if action in ("test", "sync"):
                return self._send_json({"status": "ok", "message": f"{action} not available"})
            try:
                url = DISCOVERY_API + f"/api/device/{urllib.parse.quote(device_id)}/resolve"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                    return self._send_json({
                        "id": device_id,
                        "hostname": data.get("hostname", device_id),
                        "ip": data.get("mgmt_ip", ""),
                        "serial": data.get("serial", ""),
                        "source": data.get("source", ""),
                        "username": "dnroot",
                        "password": "dnroot"
                    })
            except Exception:
                try:
                    fallback_url = SCALER_BRIDGE_API + f"/api/devices/{urllib.parse.quote(device_id)}/resolve"
                    req = urllib.request.Request(fallback_url)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = json.loads(resp.read())
                        return self._send_json({
                            "id": data.get("id", device_id),
                            "hostname": data.get("hostname", device_id),
                            "ip": data.get("ip", "") or data.get("mgmt_ip", ""),
                            "serial": data.get("serial", ""),
                            "source": data.get("source", "scaler_bridge"),
                            "username": data.get("username", "dnroot"),
                            "password": data.get("password", "dnroot")
                        })
                except Exception:
                    return self._send_json({"error": f"Device not found: {device_id}"}, 404)
        if path.startswith("/api/sections"):
            result = self._handle_sections_get(path)
            if result is not None:
                return
        if path == "/api/users/me/jira-config":
            return self._handle_jira_config_get()
        if path == "/api/users/me/ai-config":
            return self._handle_ai_config_get()
        if path == "/api/ai/ollama/models":
            return self._handle_ai_ollama_models()
        # Blueprint library (authoritative protocol-topology examples the
        # AI assistant consults before emitting create_topology). Listed
        # before the conversations routes so the string match is cheap.
        if path == "/api/ai/blueprints":
            return self._handle_ai_blueprints_list()
        if path.startswith("/api/ai/blueprints/"):
            name = path[len("/api/ai/blueprints/"):].strip("/")
            if name:
                return self._handle_ai_blueprint_get(urllib.parse.unquote(name))
        # Per-user AI conversations. See _handle_ai_conversations_* for
        # the full method-by-method breakdown.
        if path == "/api/ai/conversations":
            return self._handle_ai_conversations_list()
        if path.startswith("/api/ai/conversations/"):
            conv_id = path[len("/api/ai/conversations/"):].strip("/")
            if conv_id:
                return self._handle_ai_conversations_get(conv_id)
        if path == "/api/admin/ai/conversations":
            return self._handle_admin_ai_conversations_list()
        if path.startswith("/api/admin/ai/conversations/"):
            conv_id = path[len("/api/admin/ai/conversations/"):].strip("/")
            if conv_id:
                return self._handle_admin_ai_conversations_get(conv_id)
        # Admin + owner GET endpoints used by the user-menu dropdown
        # (diagnostics / shared-key / audit / feature-flags /
        # announcements). The announcement feed is readable by ANY
        # authenticated user since every user receives the broadcasts.
        if path == "/api/admin/diagnostics":
            return self._handle_admin_diagnostics()
        if path == "/api/admin/shared-key-status":
            return self._handle_admin_shared_key_status()
        if path == "/api/admin/audit":
            return self._handle_admin_audit()
        if path == "/api/admin/feature-flags":
            return self._handle_feature_flags_get()
        if path == "/api/admin/announcements":
            return self._handle_announcements_get()
        # Owner-only view-as workspace browser (read-only).
        #
        # We route BEFORE the /api/xray and other generic prefixes so a
        # target username containing something unusual can never shadow
        # an unrelated API path. The owner gate fires first -- if the
        # caller isn't the deployment owner, nothing else matters.
        if path.startswith("/api/owner/view-as/"):
            username, _role = self._require_owner()
            if not username:
                return
            target, parts = self._view_as_parse(path)
            if not target:
                return
            _record_audit("view_as", username, {"target": target, "path": path})
            # /api/owner/view-as/<user>/summary
            if len(parts) == 1 and parts[0] == "summary":
                return self._handle_owner_view_as_summary(target)
            # /api/owner/view-as/<user>/domains
            if len(parts) == 1 and parts[0] == "domains":
                return self._handle_owner_view_as_domains(target)
            # /api/owner/view-as/<user>/domains/<id>/topologies[/<tid>]
            if len(parts) >= 3 and parts[0] == "domains" and parts[2] == "topologies":
                domain_id = urllib.parse.unquote(parts[1])
                if len(parts) == 3:
                    return self._handle_owner_view_as_topologies(target, domain_id)
                if len(parts) == 4:
                    topology_id = urllib.parse.unquote(parts[3])
                    return self._handle_owner_view_as_topology_load(target, domain_id, topology_id)
            return self._send_json({"error": "Unknown view-as subpath"}, 404)
        if path == "/api/xray/config":
            # Reading config now ALWAYS returns safe defaults for unauth callers
            # (no leak of legacy global file). Authenticated users get their own.
            return self._send_json(self._xray_config_read())
        if path.startswith("/api/xray/status/"):
            username, _role = self._require_xray_user()
            if not username:
                return
            cid = path.split("/")[-1]
            entry, owned = self._capture_owned(cid)
            if not entry:
                return self._send_json({"error": "Not found"}, 404)
            if not owned:
                return self._send_json({"error": "Not authorized for this capture"}, 403)
            resp = {
                "status": entry["status"],
                "output_lines": entry["output_lines"][-20:],
                "pcap_path": entry["pcap_path"],
                "error": entry["error"],
                "output_mode": entry.get("_output_mode", ""),
                "mac_delivery_status": entry.get("mac_delivery_status", "not_required"),
                "mac_delivery_step": entry.get("mac_delivery_step", "queued"),
                "pcap_ephemeral": bool(entry.get("_pcap_ephemeral")),
                "server_pcap_cleaned": bool(entry.get("server_pcap_cleaned")),
                "pcap_cleanup_reason": entry.get("pcap_cleanup_reason", ""),
            }
            if entry.get("_pcap_cleanup_deadline"):
                resp["pcap_cleanup_deadline"] = entry.get("_pcap_cleanup_deadline")
            if entry.get("mac_delivery_failed"):
                resp["mac_delivery_failed"] = True
            if entry.get("mac_delivery_unconfirmed"):
                resp["mac_delivery_unconfirmed"] = True
            if entry.get("mac_delivery_failed") or entry.get("mac_delivery_unconfirmed"):
                resp["local_pcap_path"] = entry.get("local_pcap_path", entry["pcap_path"])
            return self._send_json(resp)
        if path.startswith("/api/xray/download/"):
            username, _role = self._require_xray_user()
            if not username:
                return
            cid = path.split("/")[-1]
            entry, owned = self._capture_owned(cid)
            if not entry:
                self.send_error(404, "Capture not found")
                return
            if not owned:
                self.send_error(403, "Not authorized for this capture")
                return
            pcap_path = entry.get("local_pcap_path") or entry.get("pcap_path")
            if not pcap_path or not os.path.isfile(pcap_path):
                self.send_error(404, "Pcap file not found")
                return
            try:
                with open(pcap_path, "rb") as f:
                    data = f.read()
                fname = os.path.basename(pcap_path)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.tcpdump.pcap")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except OSError as e:
                self.send_error(500, str(e))
            finally:
                if not should_retain_pcap(username):
                    _xray_cleanup_capture_pcaps(entry, "ephemeral_download_served")
            return
        if path == "/api/xray/captures":
            # List captures owned by the current user (admin sees all).
            username, role = self._require_xray_user()
            if not username:
                return
            owned = []
            for cid, entry in list(XRAY_CAPTURES.items()):
                if role == "admin" or (entry.get("_owner") or "") == username:
                    owned.append({
                        "id": cid,
                        "status": entry.get("status"),
                        "owner": entry.get("_owner") or "",
                        "started_at": entry.get("_started_at"),
                        "pcap_path": entry.get("pcap_path"),
                        "local_pcap_path": entry.get("local_pcap_path"),
                        "pcap_ephemeral": bool(entry.get("_pcap_ephemeral")),
                        "server_pcap_cleaned": bool(entry.get("server_pcap_cleaned")),
                        "error": entry.get("error"),
                    })
            return self._send_json({"captures": owned, "count": len(owned)})
        if path.startswith("/api/"):
            return self._send_json({"detail": f"No handler for GET {path}"}, 404)
        self._serve_static_gzipped()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        if "/move" in self.path:
            print(f"[POST /move] path={self.path} content_length={content_length} body={body}")
        path = self.path.split("?")[0]
        if path == "/api/monitor/announce-restart":
            return self._handle_announce_restart(body)
        if path.startswith("/mcp/") or path.startswith("/api/integration/cursor/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/auth/") or path == "/api/domains" or path.startswith("/api/domains/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/dnaas/") or path.startswith("/api/network-mapper/"):
            return self._proxy_to_discovery("POST", body)
        if path.startswith("/api/topology-generator/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/link-telemetry/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/config/") or path.startswith("/api/operations/") or path.startswith("/api/wizard/") or path.startswith("/api/mirror/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/ssh-pool/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/probe":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/discover-console":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/pdu-power":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/console-scan":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/discover-ncc-mgmt":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/clear-ghost-ip":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/ssh/verify-identity":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/devices/discover":
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/devices/watch-heartbeat":
            return self._proxy_to_scaler_bridge("POST", body)
        # Auto-monitor (Phase 2 MVP) -- verify-and-register fans out into
        # the shared registry + per-user reference + dispatch to the
        # SCALER mirror + Network Mapper. See
        # topology/docs/AUTO_MONITOR_ON_ATTACH.md.
        if path == "/api/devices/verify-and-register":
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/devices/monitored/") and path.endswith("/attach"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/devices/") and len(path) > len("/api/devices/"):
            parts = path[len("/api/devices/"):].rstrip("/").split("/")
            device_id = urllib.parse.unquote(parts[0]) if parts else ""
            action = parts[1] if len(parts) > 1 else None
            if device_id and action in (
                "test",
                "set-hostname",
                "stack-live",
                "system-type",
                # verify-credentials is the SSH-dialog "Save" path that
                # piggy-backs on /api/ssh/verify-identity + /api/ssh/probe.
                # Owned by routes/devices.py on the scaler-bridge process,
                # so we just forward the POST. Without this entry the
                # topology server returns 404 for every Save click and
                # the dialog's verify step looks broken for every user.
                "verify-credentials",
            ):
                return self._proxy_to_scaler_bridge("POST", body)
            if device_id and action in ("watch", "unwatch"):
                return self._proxy_to_scaler_bridge("POST", body)
            if device_id and action == "sync":
                return self._handle_device_sync(device_id)
        if path == "/api/devices/" or path == "/api/devices":
            return self._send_json({"status": "ok", "message": "Device registered locally"})
        if path == "/debug-dnos-topologies/save":
            return self._save_debug_dnos_file(body)
        if path == "/debug-dnos-topologies/rename":
            data = json.loads(body) if body else {}
            old_name = data.get("old_filename", "")
            new_name = data.get("name", "").strip()
            if not new_name or not old_name:
                return self._send_json({"error": "Name required"}, 400)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in new_name)
            old_path = os.path.join(BUG_EVIDENCE_DIR, old_name)
            new_path = os.path.join(BUG_EVIDENCE_DIR, safe + ".topology.json")
            if not os.path.isfile(old_path):
                return self._send_json({"error": "Not found"}, 404)
            if os.path.isfile(new_path) and old_path != new_path:
                return self._send_json({"error": "Name already exists"}, 400)
            os.rename(old_path, new_path)
            return self._send_json({"ok": True, "filename": safe + ".topology.json"})
        if path == "/debug-dnos-topologies/delete-file":
            data = json.loads(body) if body else {}
            fname = data.get("filename", "")
            if not fname:
                return self._send_json({"error": "Filename required"}, 400)
            fpath = os.path.join(BUG_EVIDENCE_DIR, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
                return self._send_json({"ok": True})
            return self._send_json({"error": "Not found"}, 404)
        if path == "/api/migrate-bug-topologies":
            return self._migrate_bug_topologies(body)
        if path == "/api/bugs/from-jira":
            return self._handle_bug_topology_create(body)
        if path == "/api/ai/chat":
            return self._handle_ai_chat(body)
        if path == "/api/ai/topology/generate":
            return self._handle_ai_topology_generate(body)
        if path == "/api/ai/conversations":
            return self._handle_ai_conversations_create(body)
        if path.startswith("/api/sections"):
            result = self._handle_sections_post(path, body)
            if result is not None:
                return
        if path == "/api/xray/run":
            # Mutating XRAY action -> require an authenticated user so each
            # capture is owned and each pcap lands in the user's captures dir.
            # Previously this only short-circuited when the caller sent a
            # *malformed* Authorization header; an anonymous call (no header
            # at all) fell through to _xray_run after _require_xray_user had
            # already sent the 401, doing wasted server work that the user
            # could never see. Always return on missing username.
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                params = json.loads(body) if body else {}
                result = self._xray_run(params)
                # _xray_run returns a dict {"error": "..."} for validation failures
                # (e.g. missing per-user DNAAS creds, DNAAS device picked as
                # POV in cp/dp mode) or a string capture_id on success.
                if isinstance(result, dict) and result.get("error"):
                    return self._send_json(result, 400)
                return self._send_json({"capture_id": result})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path == "/api/xray/dnaas-mirror-preflight":
            # Read-only but per-user: the DNAAS leaf credentials live in the
            # caller's xray.json, so unauthenticated callers must not reach
            # this endpoint and must not learn another user's lab creds.
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                params = json.loads(body) if body else {}
                result = self._xray_dnaas_mirror_preflight(params)
                return self._send_json(result, 200 if result.get("available") else 409)
            except Exception as e:
                return self._send_json({"available": False, "error": str(e)}, 500)
        if path == "/api/xray/redeliver":
            # Per-user gate: only an authenticated user may request a
            # re-deliver of a pcap to their Mac. The pcap-path realpath
            # check below already prevents one user from touching another
            # user's captures, but we need the JWT first to know who the
            # caller is (and to refuse anonymous re-delivers outright).
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                data = json.loads(body) if body else {}
                pcap_path = data.get("pcap_path", "").strip()
                new_mac_ip = data.get("mac_ip", "").strip()
                if not pcap_path or not os.path.isfile(pcap_path):
                    return self._send_json({"error": f"pcap not found: {pcap_path}"}, 400)
                if not new_mac_ip:
                    return self._send_json({"error": "mac_ip required"}, 400)
                # Per-user pcap path enforcement: when the caller is auth'd we
                # only accept pcap paths inside the caller's captures dir (or
                # admin-only access to the global dir). Prevents one user from
                # redelivering another user's pcap.
                username, role = self._xray_user()
                if username and role != "admin":
                    user_root = os.path.realpath(_user_captures_dir(username))
                    real_pcap = os.path.realpath(pcap_path)
                    if not real_pcap.startswith(user_root + os.sep):
                        return self._send_json({"error": "pcap is not in your captures directory"}, 403)
                cfg = self._xray_config_read()
                if "mac" not in cfg:
                    cfg["mac"] = {}
                cfg["mac"]["ip_vpn"] = new_mac_ip
                self._xray_config_write(cfg)
                mac = cfg["mac"]
                import sys
                sys.path.insert(0, os.path.expanduser("~"))
                from xray.common import _scp_pcap_to_mac
                try:
                    ok = _scp_pcap_to_mac(
                        pcap_path,
                        mac_user=mac.get("user", os.environ.get("USER", "dn")),
                        mac_pass=mac.get("password", ""),
                        mac_host=new_mac_ip,
                        wireshark_path=mac.get("wireshark_path"),
                        mac_directory=mac.get("pcap_directory"),
                    )
                finally:
                    if not should_retain_pcap(username):
                        _xray_cleanup_capture_pcaps({
                            "_owner": username,
                            "pcap_path": pcap_path,
                            "_target_pcap": pcap_path,
                        }, "ephemeral_redeliver_attempt")
                if ok:
                    return self._send_json({"ok": True})
                else:
                    return self._send_json({"error": "Mac delivery failed -- check IP/credentials"}, 500)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path.startswith("/api/xray/stop/"):
            username, _role = self._require_xray_user()
            if not username:
                return
            cid = path.split("/")[-1]
            entry, owned = self._capture_owned(cid)
            if not entry:
                return self._send_json({"error": "Not found"}, 404)
            if not owned:
                return self._send_json({"error": "Not authorized for this capture"}, 403)
            if entry.get("process"):
                try:
                    entry["process"].terminate()
                except Exception:
                    pass
                entry["status"] = "stopped"
            return self._send_json({"ok": True})
        if path == "/api/xray/verify-mac":
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                data = json.loads(body) if body else {}
                cfg = self._xray_config_read()
                mac_cfg = cfg.get("mac", {}) or {}
                mac_ip = (data.get("ip") or mac_cfg.get("ip_vpn") or "").strip()
                mac_user = (data.get("user") or mac_cfg.get("user") or os.environ.get("USER", "dn")).strip()
                mac_pass = data.get("password")
                if mac_pass is None:
                    mac_pass = mac_cfg.get("password", "")
                if not mac_ip:
                    return self._send_json({"reachable": False, "ip": "", "error": "No Mac IP configured"})
                if not mac_user:
                    return self._send_json({
                        "reachable": False,
                        "ssh": False,
                        "ip": mac_ip,
                        "cause": "missing_user",
                        "error": "No Mac username configured"
                    })
                if not mac_pass:
                    return self._send_json({
                        "reachable": False,
                        "ssh": False,
                        "ip": mac_ip,
                        "cause": "missing_password",
                        "error": "No Mac password configured. Enter the Mac login password, then verify again."
                    })
                env = os.environ.copy()
                env["SSHPASS"] = mac_pass
                def _mac_verify_error(result):
                    stderr = (result.stderr or "").strip()
                    stdout = (result.stdout or "").strip()
                    text = f"{stderr}\n{stdout}".lower()
                    if result.returncode == 127 or ("sshpass" in text and "not found" in text):
                        return "missing_sshpass", "sshpass is not installed on this server. Install XRAY dependencies first."
                    if result.returncode == 5 or "permission denied" in text or "authentication failed" in text:
                        return "auth_failed", (
                            f"Authentication failed for {mac_user}@{mac_ip}. "
                            "Wrong Mac username/password, or Remote Login does not allow this user."
                        )
                    if "connection refused" in text:
                        return "ssh_refused", "Mac is reachable but SSH was refused. Enable Remote Login on the Mac."
                    if "no route to host" in text or "network is unreachable" in text:
                        return "network_unreachable", "Network path to the Mac is unreachable. Check VPN/IP connectivity."
                    if "could not resolve hostname" in text or "name or service not known" in text:
                        return "bad_host", "Mac host/IP could not be resolved. Check the configured Mac IP."
                    if "operation timed out" in text or "connection timed out" in text:
                        return "ssh_timeout", "SSH timed out. Check the Mac IP, VPN route, firewall, and Remote Login."
                    return "ssh_failed", stderr or stdout or "SSH verification failed. Check Mac IP, Remote Login, username, and password."
                try:
                    result = subprocess.run(
                        [
                            "sshpass", "-e", "ssh",
                            "-o", "StrictHostKeyChecking=no",
                            "-o", "ConnectTimeout=5",
                            "-o", "LogLevel=ERROR",
                            f"{mac_user}@{mac_ip}",
                            "echo ok",
                        ],
                        env=env, capture_output=True, text=True, timeout=10
                    )
                    reachable = result.returncode == 0 and "ok" in result.stdout
                    verified_at = None
                    cause = None
                    error = None
                    if reachable:
                        # Persist proof-of-verification in the caller's per-user
                        # xray.json so the capture gate in _xray_run can trust it.
                        verified_at = time.time()
                        cfg.setdefault("mac", {})
                        cfg["mac"]["verified_ip"] = mac_ip
                        cfg["mac"]["verified_at"] = verified_at
                        cfg["mac"]["verified_by"] = username
                        try:
                            self._xray_config_write(cfg)
                        except Exception:
                            # Worst case: user has to re-verify -- non-fatal.
                            pass
                    else:
                        cause, error = _mac_verify_error(result)
                    return self._send_json({
                        "reachable": reachable,
                        "ssh": reachable,
                        "ip": mac_ip,
                        "verified_at": verified_at,
                        "verified_ip": mac_ip if reachable else None,
                        "cause": cause,
                        "error": error
                    })
                except subprocess.TimeoutExpired:
                    return self._send_json({
                        "reachable": False,
                        "ssh": False,
                        "ip": mac_ip,
                        "cause": "ssh_timeout",
                        "error": "SSH timed out. Check the Mac IP, VPN route, firewall, and Remote Login."
                    })
                except FileNotFoundError:
                    return self._send_json({
                        "reachable": False,
                        "ssh": False,
                        "ip": mac_ip,
                        "cause": "missing_sshpass",
                        "error": "sshpass is not installed on this server. Install XRAY dependencies first."
                    })
            except Exception as e:
                return self._send_json({"reachable": False, "ssh": False, "ip": "", "cause": "verify_failed", "error": str(e)})
        if path == "/api/xray/config":
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                data = json.loads(body) if body else {}
                cfg = self._xray_config_read()
                # If the caller changes mac.ip_vpn, invalidate the previous
                # verification so they are forced to re-verify before the
                # next mac-output capture (see _xray_run gate).
                try:
                    incoming_mac = data.get("mac") if isinstance(data, dict) else None
                    if isinstance(incoming_mac, dict) and "ip_vpn" in incoming_mac:
                        new_ip = (incoming_mac.get("ip_vpn") or "").strip()
                        old_ip = ((cfg.get("mac") or {}).get("ip_vpn") or "").strip()
                        if new_ip != old_ip:
                            mac_sec = cfg.setdefault("mac", {})
                            mac_sec.pop("verified_ip", None)
                            mac_sec.pop("verified_at", None)
                            mac_sec.pop("verified_by", None)
                except Exception:
                    pass
                for k, v in data.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k] = {**cfg[k], **v}
                    else:
                        cfg[k] = v
                if not self._xray_config_write(cfg):
                    return self._send_json({"error": "Authentication required"}, 401)
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path == "/api/ssh/clear-hostkey":
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                data = json.loads(body) if body else {}
                # Accept either:
                #   { "host": "foo" }                              -- legacy single-target
                #   { "hosts": ["foo", "1.2.3.4", "foo-short"] }   -- batch
                # Both forms map into a deduplicated list. GI/recovery callers
                # should pass BOTH the NCC DNS hostname AND the NCC/cluster mgmt
                # IPs, because the user's known_hosts may store either form
                # depending on how they first connected.
                raw_hosts = []
                if isinstance(data.get("hosts"), list):
                    raw_hosts = data["hosts"]
                elif data.get("host"):
                    raw_hosts = [data["host"]]
                # sanitise + dedupe while preserving order
                seen = set()
                targets = []
                for h in raw_hosts:
                    if not isinstance(h, str):
                        continue
                    h = h.strip()
                    if not h or h in seen:
                        continue
                    if not all(c.isalnum() or c in ".-_:" for c in h):
                        continue
                    seen.add(h)
                    targets.append(h)
                if not targets:
                    return self._send_json({"error": "host(s) required"}, 400)

                # 1) Clear on server (best-effort; we mostly care about the Mac).
                server_results = []
                server_any_ok = False
                for h in targets:
                    try:
                        srv = subprocess.run(
                            ["ssh-keygen", "-R", h],
                            capture_output=True, text=True, timeout=5,
                        )
                        ok = srv.returncode == 0
                        server_any_ok = server_any_ok or ok
                        server_results.append({
                            "host": h, "ok": ok,
                            "output": (srv.stdout + srv.stderr).strip()[-200:],
                        })
                    except Exception as _e:
                        server_results.append({"host": h, "ok": False, "output": str(_e)})

                # 2) Clear on Mac via sshpass SSH.
                cfg = self._xray_config_read()
                mac = cfg.get("mac", {})
                mac_ip = mac.get("ip_vpn", "")
                mac_user = mac.get("user", os.environ.get("USER", "dn"))
                mac_pass = mac.get("password", "")
                mac_results = []
                mac_any_ok = False
                mac_msg = ""

                # Always build copy-paste commands so the UI can offer a
                # graceful fallback when the Mac is unreachable (stale VPN IP,
                # firewall, Remote Login disabled, etc.).
                _copy_cmds = " && ".join(f"ssh-keygen -R {h}" for h in targets)

                if mac_ip and mac_user:
                    env = os.environ.copy()
                    env["SSHPASS"] = mac_pass
                    # One SSH connection, chain all ssh-keygen -R calls so we
                    # don't pay the sshd handshake cost per-host.
                    chained = " ; ".join(f"ssh-keygen -R {h}" for h in targets)
                    try:
                        _cmd = (
                            f'sshpass -e ssh -o StrictHostKeyChecking=no '
                            f'-o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 '
                            f'-o LogLevel=ERROR {mac_user}@{mac_ip} '
                            f'"{chained} ; echo __OK__"'
                        )
                        result_mac = subprocess.run(
                            _cmd, shell=True, env=env,
                            capture_output=True, text=True, timeout=20
                        )
                        mac_any_ok = (result_mac.returncode == 0
                                      and "__OK__" in result_mac.stdout)
                        for h in targets:
                            mac_results.append({"host": h, "ok": mac_any_ok})
                        if mac_any_ok:
                            mac_msg = (
                                f"Cleared {len(targets)} host key(s) on Mac "
                                f"({mac_ip}) as {mac_user}"
                            )
                        else:
                            _err = (result_mac.stderr or "").strip()
                            mac_msg = f"Mac SSH failed: {_err[:200] or 'no stderr'}"
                    except subprocess.TimeoutExpired:
                        mac_msg = f"Mac SSH timed out ({mac_ip})"
                        for h in targets:
                            mac_results.append({"host": h, "ok": False})
                    except Exception as _e:
                        mac_msg = f"Mac SSH failed ({mac_ip}): {_e}"
                        for h in targets:
                            mac_results.append({"host": h, "ok": False})
                else:
                    mac_msg = ("Mac IP not configured -- run the copy-paste "
                               "command on your Mac terminal")
                    for h in targets:
                        mac_results.append({"host": h, "ok": False})

                return self._send_json({
                    "ok": server_any_ok or mac_any_ok,
                    "server_cleared": server_any_ok,
                    "mac_cleared": mac_any_ok,
                    "mac_ip": mac_ip,
                    "message": mac_msg,
                    "targets": targets,
                    "server_results": server_results,
                    "mac_results": mac_results,
                    # Copy-paste helper the UI can surface when Mac SSH fails
                    # or is not configured. Runs the same clears locally.
                    "copy_command": _copy_cmds,
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path == "/api/xray/verify-mac":
            username, _role = self._require_xray_user()
            if not username:
                return
            try:
                data = json.loads(body) if body else {}
                ip = data.get("ip", "").strip()
                if not ip:
                    return self._send_json({"reachable": False, "error": "IP required"})
                cfg = self._xray_config_read()
                mac = cfg.get("mac", {})
                user = (data.get("user") or "").strip() or mac.get("user") or os.environ.get("USER", "dn")
                password = (data.get("password") or "").strip() or mac.get("password", "")

                # Step 1: Ping check (network reachability)
                ping_ok = False
                try:
                    ping = subprocess.run(
                        ["ping", "-c", "1", "-W", "3", ip],
                        capture_output=True, text=True, timeout=5
                    )
                    ping_ok = ping.returncode == 0
                except Exception:
                    pass

                # Step 2: SSH auth check (identity verification)
                ssh_ok = False
                ssh_err = ""
                env = os.environ.copy()
                env["SSHPASS"] = password
                try:
                    result = subprocess.run(
                        ["sshpass", "-e", "ssh",
                         "-o", "ConnectTimeout=5",
                         "-o", "StrictHostKeyChecking=no",
                         "-o", "UserKnownHostsFile=/dev/null",
                         "-o", "LogLevel=ERROR",
                         f"{user}@{ip}", "echo ok"],
                        capture_output=True, text=True, timeout=12, env=env
                    )
                    ssh_ok = result.returncode == 0 and "ok" in result.stdout
                    if not ssh_ok:
                        ssh_err = result.stderr.strip() or f"SSH exit code {result.returncode}"
                except subprocess.TimeoutExpired:
                    ssh_err = "SSH timed out (12s)"
                except Exception as e:
                    ssh_err = str(e)

                if ssh_ok:
                    return self._send_json({"reachable": True, "ssh": True, "ping": ping_ok})
                elif ping_ok:
                    return self._send_json({
                        "reachable": False, "ping": True, "ssh": False,
                        "error": f"Mac is reachable (ping OK) but SSH failed: {ssh_err}. "
                                 "Enable 'Remote Login' in System Settings > General > Sharing on the Mac."
                    })
                else:
                    return self._send_json({
                        "reachable": False, "ping": False, "ssh": False,
                        "error": f"Mac not reachable at {ip} (ping + SSH both failed). Check VPN connection and IP."
                    })
            except Exception as e:
                return self._send_json({"reachable": False, "error": str(e)})
        # Admin + owner POST endpoints powering the user-menu dialogs.
        # Sharding them by /admin/ vs /owner/ prefix makes it obvious
        # which role is required for each route (see the `_require_*`
        # gates inside each handler for the actual enforcement).
        if path == "/api/admin/broadcast":
            return self._handle_admin_broadcast(body)
        if path == "/api/admin/reload-knowledge":
            return self._handle_admin_reload_knowledge()
        if path == "/api/admin/reload-blueprints":
            return self._handle_admin_reload_blueprints()
        if path == "/api/owner/reset-configs":
            return self._handle_owner_reset_configs(body)
        if path == "/api/owner/restart":
            return self._handle_owner_restart(body)
        if path == "/api/owner/impersonate":
            return self._handle_owner_impersonate(body)
        if path.startswith("/api/"):
            return self._send_json({"detail": f"No handler for POST {path}"}, 404)
        self.send_error(404, "Not found")

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        path = self.path.split("?")[0]
        if path.startswith("/api/integration/cursor/"):
            return self._proxy_to_scaler_bridge("PUT", body)
        if path.startswith("/api/auth/") or path == "/api/domains" or path.startswith("/api/domains/"):
            return self._proxy_to_scaler_bridge("PUT", body)
        if path == "/api/users/me/jira-config":
            return self._handle_jira_config_put(body)
        if path == "/api/users/me/ai-config":
            return self._handle_ai_config_put(body)
        # Admin PUT: feature-flags (partial merge semantics -- only
        # the flags present in the body are updated).
        if path == "/api/admin/feature-flags":
            return self._handle_feature_flags_put(body)
        if path.startswith("/api/devices/") and path.endswith("/user-prefs"):
            return self._proxy_to_scaler_bridge("PUT", body)
        if path.startswith("/api/"):
            return self._send_json({"detail": f"No handler for PUT {path}"}, 404)
        self.send_error(404, "Not found")

    def do_PATCH(self):
        """PATCH is used for partial-update endpoints (e.g. profile prefs).

        Without this method, Python's base HTTPServer returns a generic
        501 and the admin/customise UI breaks. We intentionally keep the
        routing list tiny -- only the /api/auth/ FastAPI routes exposed
        through the bridge need PATCH today.
        """
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        path = self.path.split("?")[0]
        if path.startswith("/api/integration/cursor/"):
            return self._proxy_to_scaler_bridge("PATCH", body)
        if path.startswith("/api/auth/") or path == "/api/domains" or path.startswith("/api/domains/"):
            return self._proxy_to_scaler_bridge("PATCH", body)
        if path.startswith("/api/ai/conversations/"):
            conv_id = path[len("/api/ai/conversations/"):].strip("/")
            if conv_id:
                return self._handle_ai_conversations_patch(conv_id, body)
        if path.startswith("/api/"):
            return self._send_json({"detail": f"No handler for PATCH {path}"}, 404)
        self.send_error(404, "Not found")

    def do_DELETE(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/integration/cursor/"):
            return self._proxy_to_scaler_bridge("DELETE")
        if path.startswith("/api/auth/") or path == "/api/domains" or path.startswith("/api/domains/"):
            return self._proxy_to_scaler_bridge("DELETE")
        if path == "/api/users/me/jira-config":
            return self._handle_jira_config_delete()
        if path == "/api/users/me/ai-config":
            return self._handle_ai_config_delete()
        if path.startswith("/api/ai/conversations/"):
            conv_id = path[len("/api/ai/conversations/"):].strip("/")
            if conv_id:
                return self._handle_ai_conversations_delete(conv_id)
        # Auto-monitor (Phase 2 MVP) -- detach reference. MUST be checked
        # BEFORE the generic /api/devices/<id> DELETE catch-all because
        # ``parts[0]`` is "monitored" (a literal segment) not a device id.
        if path.startswith("/api/devices/monitored/") and path.endswith("/attach"):
            return self._proxy_to_scaler_bridge("DELETE")
        if path.startswith("/api/devices/") and len(path) > len("/api/devices/"):
            parts = path[len("/api/devices/"):].rstrip("/").split("/")
            device_id = urllib.parse.unquote(parts[0]) if parts else ""
            if device_id:
                return self._handle_device_delete(device_id)
        if path.startswith("/api/"):
            return self._send_json({"detail": f"No handler for DELETE {path}"}, 404)
        self.send_error(404, "Not found")

    def _handle_device_delete(self, device_id):
        """Delete device from local cache. Stub until scaler_bridge - device list comes from discovery_api."""
        return self._send_json({"detail": "Delete not available - use scaler-wizard"}, 503)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def _start_discovery_api():
    """Auto-launch discovery_api.py on port 8765 if not already running."""
    discovery_script = os.path.join(DIRECTORY, "discovery_api.py")
    if not os.path.isfile(discovery_script):
        print(f"[WARN] discovery_api.py not found at {discovery_script}, skipping auto-start")
        return None

    # Check if already running
    try:
        req = urllib.request.Request(DISCOVERY_API + "/api/health", method="GET")
        urllib.request.urlopen(req, timeout=2)
        print("[OK] Discovery API already running on port 8765")
        return None
    except urllib.error.HTTPError:
        print("[OK] Discovery API already listening on port 8765")
        return None
    except Exception:
        pass

    print("[INFO] Starting discovery_api.py on port 8765...")
    try:
        log_path = os.environ.get("TOPOLOGY_DISCOVERY_LOG", "/tmp/discovery_api.log")
        log_file = open(log_path, "a", buffering=1)
        proc = subprocess.Popen(
            ["python3", "discovery_api.py"],
            cwd=DIRECTORY,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        log_file.close()
        # Give it a moment to bind
        time.sleep(1.5)
        if proc.poll() is not None:
            print(f"[ERROR] discovery_api.py exited immediately; see {log_path}")
            return None
        print(f"[OK] Discovery API started (pid {proc.pid})")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start discovery_api.py: {e}")
        return None


def _start_scaler_bridge():
    """Auto-launch scaler_bridge.py on port 8766 if not already running."""
    bridge_script = os.path.join(DIRECTORY, "scaler_bridge.py")
    if not os.path.isfile(bridge_script):
        print(f"[WARN] scaler_bridge.py not found at {bridge_script}, skipping auto-start")
        return None

    # Check if already running
    try:
        req = urllib.request.Request(SCALER_BRIDGE_API + "/api/health", method="GET")
        urllib.request.urlopen(req, timeout=2)
        print("[OK] Scaler bridge already running on port 8766")
        return None
    except urllib.error.HTTPError:
        print("[OK] Scaler bridge already listening on port 8766")
        return None
    except Exception:
        pass

    print("[INFO] Starting scaler_bridge.py on port 8766...")
    try:
        log_path = os.environ.get("TOPOLOGY_SCALER_BRIDGE_LOG", "/tmp/scaler_bridge.log")
        log_file = open(log_path, "a", buffering=1)
        # Keep the bridge process stable for long-lived MCP SSE sessions.
        # Uvicorn --reload restarts the child whenever watched files under
        # /home/dn/CURSOR change, which drops Cursor's /mcp/sse connection and
        # makes the Topology MCP appear to go down. serve.py's monitor handles
        # crash recovery; code deployments restart the stack explicitly.
        bridge_cmd = [
            "python3", "-m", "uvicorn", "scaler_bridge:app",
            "--host", "0.0.0.0", "--port", "8766", "--log-level", "warning",
        ]
        proc = subprocess.Popen(
            bridge_cmd,
            cwd=DIRECTORY,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        log_file.close()
        # Give it a moment to bind
        time.sleep(1.5)
        if proc.poll() is not None:
            print(f"[ERROR] scaler_bridge.py exited immediately; see {log_path}")
            return None
        print(f"[OK] Scaler bridge started (pid {proc.pid})")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start scaler_bridge.py: {e}")
        return None


def _service_monitor(stop_event):
    """Background thread: health-check children every 15s, restart on crash or file change."""
    global _child_procs, _child_start_times, _discovery_file_mtime, _health_fail_count, _restart_timestamps
    discovery_script = os.path.join(DIRECTORY, "discovery_api.py")
    crash_window = 120  # seconds
    max_restarts_in_window = 5

    def _health_ok(url, timeout=2):
        """True when the child is actually answering HTTP on `url`.

        History:
        - 2026-04-23: scaler_bridge auth middleware made /docs return 401.
          The monitor used to treat any 4xx/5xx as "dead" and restart-looped
          the healthy bridge. Fixed by accepting 4xx as "alive".
        - 2026-04-29: discovery_api (stdlib BaseHTTPRequestHandler) does
          NOT implement do_HEAD and returns 501 ("Unsupported method")
          for HEAD probes. 501 is 5xx, so the monitor decided
          discovery_api was dead and proc.terminate()d it every ~45s. That
          wiped the in-memory `jobs` dict, so every Multi-BD Discovery the
          user kicked off died with "Discovery job lost - server may have
          restarted" within a minute.

        Fix: probe with GET instead of HEAD. The discovery_api and
        scaler_bridge `/api/health` endpoints are both cheap GETs that
        return small JSON, and GET is the actual contract those handlers
        implement. Any HTTP response (2xx/3xx/4xx/5xx) means the child is
        alive and listening; only connection-level failures
        (refused / timeout / DNS) count as "dead".
        """
        try:
            req = urllib.request.Request(url, method="GET")
            urllib.request.urlopen(req, timeout=timeout)
            return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            return False

    def _restart_discovery():
        global _discovery_file_mtime
        with _monitor_lock:
            proc = _child_procs.get("discovery")
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        new_proc = _start_discovery_api()
        if new_proc:
            with _monitor_lock:
                _child_procs["discovery"] = new_proc
                _child_start_times["discovery"] = time.time()
                if os.path.isfile(discovery_script):
                    _discovery_file_mtime = os.path.getmtime(discovery_script)
                _health_fail_count["discovery"] = 0
                _restart_timestamps.append((time.time(), "discovery"))

    def _restart_bridge():
        with _monitor_lock:
            proc = _child_procs.get("bridge")
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        new_proc = _start_scaler_bridge()
        if new_proc:
            with _monitor_lock:
                _child_procs["bridge"] = new_proc
                _child_start_times["bridge"] = time.time()
                _health_fail_count["bridge"] = 0
                _restart_timestamps.append((time.time(), "bridge"))

    def _prune_restarts():
        now = time.time()
        with _monitor_lock:
            _restart_timestamps[:] = [(t, s) for t, s in _restart_timestamps if now - t < crash_window]

    def _restart_count(service):
        now = time.time()
        return sum(1 for t, s in _restart_timestamps if s == service and now - t < crash_window)

    while not stop_event.wait(15):
        _prune_restarts()

        # --- Discovery API (always health-check, even without a proc handle) ---
        proc = _child_procs.get("discovery")
        proc_alive = proc is not None and proc.poll() is None

        if proc is not None and proc.poll() is not None:
            print("[WARN] discovery_api died, restarting...")
            if _restart_count("discovery") < max_restarts_in_window:
                _restart_discovery()
            else:
                print("[ERROR] discovery_api crash loop detected, stopping restarts")
        elif not _health_ok(DISCOVERY_API + "/api/health"):
            _health_fail_count["discovery"] = _health_fail_count.get("discovery", 0) + 1
            if _health_fail_count["discovery"] >= 3:
                print("[WARN] discovery_api health check failed 3x, restarting...")
                _health_fail_count["discovery"] = 0
                if _restart_count("discovery") < max_restarts_in_window:
                    _restart_discovery()
        else:
            _health_fail_count["discovery"] = 0

        # File-change detection for discovery_api
        proc = _child_procs.get("discovery")
        if proc is not None and proc.poll() is None and os.path.isfile(discovery_script):
            mtime = os.path.getmtime(discovery_script)
            if mtime > _discovery_file_mtime and _discovery_file_mtime > 0:
                print("[INFO] discovery_api.py changed, restarting...")
                if _restart_count("discovery") < max_restarts_in_window:
                    _restart_discovery()

        # --- Scaler bridge (always health-check, even without a proc handle) ---
        proc = _child_procs.get("bridge")

        if proc is not None and proc.poll() is not None:
            print("[WARN] scaler_bridge died, restarting...")
            if _restart_count("bridge") < max_restarts_in_window:
                _restart_bridge()
            else:
                print("[ERROR] scaler_bridge crash loop detected, stopping restarts")
        elif not _health_ok(SCALER_BRIDGE_API + "/api/health"):
            _health_fail_count["bridge"] = _health_fail_count.get("bridge", 0) + 1
            if _health_fail_count["bridge"] >= 3:
                print("[WARN] scaler_bridge health check failed 3x, restarting...")
                _health_fail_count["bridge"] = 0
                if _restart_count("bridge") < max_restarts_in_window:
                    _restart_bridge()
        else:
            _health_fail_count["bridge"] = 0

 
HelloRequestHandler = Handler


if __name__ == "__main__":
    discovery_proc = _start_discovery_api()
    bridge_proc = _start_scaler_bridge()
    if discovery_proc is not None:
        _child_procs["discovery"] = discovery_proc
        _child_start_times["discovery"] = time.time()
        discovery_script = os.path.join(DIRECTORY, "discovery_api.py")
        if os.path.isfile(discovery_script):
            _discovery_file_mtime = os.path.getmtime(discovery_script)
    if bridge_proc is not None:
        _child_procs["bridge"] = bridge_proc
        _child_start_times["bridge"] = time.time()

    monitor_stop = threading.Event()
    monitor_thread = threading.Thread(target=_service_monitor, args=(monitor_stop,), daemon=True)
    monitor_thread.start()

    try:
        try:
            req = urllib.request.Request(DISCOVERY_API + "/api/health", method="GET")
            urllib.request.urlopen(req, timeout=3)
            print("[INFO] Health check: discovery_api (8765) reachable")
        except Exception as e:
            print(f"[WARN] Health check: discovery_api (8765) not reachable: {e}")
        try:
            req = urllib.request.Request(SCALER_BRIDGE_API + "/api/health", method="GET")
            urllib.request.urlopen(req, timeout=3)
            print("[INFO] Health check: scaler_bridge (8766) reachable")
        except Exception as e:
            print(f"[WARN] Health check: scaler_bridge (8766) not reachable: {e}")
        with ThreadedHTTPServer(("0.0.0.0", PORT), Handler) as httpd:
            print("[serve] live-link-telemetry proxy active")
            print(f"Serving at http://0.0.0.0:{PORT}")
            httpd.serve_forever()
    finally:
        monitor_stop.set()
        for name, proc in [("discovery_api", _child_procs.get("discovery")), ("scaler_bridge", _child_procs.get("bridge"))]:
            if proc is not None and proc.poll() is None:
                print(f"[INFO] Stopping {name}...")
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass






