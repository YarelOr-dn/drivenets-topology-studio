"""Shared helpers for scaler bridge routers (extracted from scaler_bridge)."""
from __future__ import annotations

import contextvars

from fastapi import HTTPException

from routes._state import _push_jobs, _push_jobs_lock

# Per-request JWT username, populated by the auth middleware in
# scaler_bridge.py. Defaults to "" so legacy single-user code paths keep
# returning the global XRAY credentials when no user is set.
current_app_user: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_app_user", default=""
)

__all__ = [
    "DEVICE_INVENTORY_JSON", "DISCOVERY_API", "INVENTORY_FILE",
    "LOCAL_CONSOLE_CSV", "LOCAL_PDU_CLI_CFG", "LOCAL_PDU_MAP",
    "SCALER_ROOT", "SSHConnectionPool", "XRAY_CONFIG_PATH",
    "ZOHAR_CACHE_TTL", "ZOHAR_CSV_REMOTE", "ZOHAR_DB_PASS",
    "ZOHAR_DB_SERVER", "ZOHAR_DB_USER", "ZOHAR_PDU_CLI_REMOTE",
    "ZOHAR_PDU_REMOTE",
    "_ACTIVE_BUILDS_PATH", "_ACTIVE_UPGRADES_PATH",
    "_INTERNAL_JOB_KEYS", "_KNOWN_CONSOLE_SERVERS",
    "_MAX_HISTORY_JOBS", "_MAX_TERMINAL_LINES_IN_HISTORY",
    "_PUSH_HISTORY_PATH",
    "_build_config_summary", "_build_device_identity", "_build_job_name",
    "_build_scaler_ops_index", "_cache_resolve",
    "_compute_wizard_suggestions", "_connect_virsh_console_sync",
    "_detect_cli_mode_from_buffer", "_discover_console",
    "_discover_ncc_mgmt_ip_sync", "_evict_stale_jobs_locked",
    "_fetch_all_operational_via_ssh", "_fetch_config_via_ssh",
    "_fetch_git_commit_via_ssh", "_fetch_stack_via_ssh",
    "_fetch_zohar_db", "_find_cached_config_by_ip",
    "_find_inventory_device", "_get_cached_config", "_get_credentials",
    "_invalidate_scaler_ops_cache", "_mark_device_ip_stale", "_is_scaler_ops_stale",
    "_get_device_context", "_get_known_console_servers",
    "_get_pdu_cli_type", "_iso_from_ts", "_load_push_history",
    "_lookup_zohar_console", "_lookup_zohar_pdu",
    "_open_virsh_ncc_shell_channel", "_parse_mgmt_ip_from_show_interfaces",
    "_resolve_active_ncc_host", "_seed_cluster_metadata_from_mappings",
    "_pdu_power_action", "_persist_job_if_done", "_probe_console_server",
    "_probe_single_port", "_recv_until", "_remove_active_build",
    "_remove_active_upgrade", "_resolve_config_dir", "_resolve_device",
    "_resolve_from_monitored_registry", "_resolve_mgmt_ip", "_sanitize_job", "_save_active_build",
    "_save_active_upgrade",     "_save_discovered_console",
    "_save_push_history", "_ssh_pool", "_strip_ansi",
    "current_app_user", "_user_xray_dir",
    "_classify_device_profile", "_load_lab_credentials", "_get_lab_credential_chain",
]

#!/usr/bin/env python3
"""
Scaler Bridge API - REST wrapper for scaler-wizard modules.

Exposes device config fetch, sync, and summary endpoints for the topology app.
Runs on port 8766. The main serve.py proxies /api/config/* to this service.

Usage:
    python3 scaler_bridge.py
    # Or: python3 -m uvicorn scaler_bridge:app --host 0.0.0.0 --port 8766
"""
import json
import logging
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Dict

# Single canonical reader for operational.json. Imports the salvage-aware
# read_ops at module load so every site here calls the same code path
# instead of hand-rolling json.loads + try/except. Saves us from the
# "one corrupt file silently truncates the cache" failure mode we hit
# on YOR_PE-1 (2026-04-26).
from routes._ops_writer import read_ops as _read_ops_safe

# Ensure SCALER is on path
SCALER_ROOT = Path(os.environ.get("SCALER_ROOT", str(Path.home() / "SCALER")))
if str(SCALER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCALER_ROOT))


def find_lab_devices_file() -> Path:
    """Resolve the curated devices.json path for the active lab profile.

    Resolution order (first hit wins):
      1. ``$SCALER_DEVICES_FILE`` -- explicit override (used by tests +
         lab_profile.py to point at a non-default profile's file).
      2. ``$SCALER_ROOT/db/devices.json`` -- the curated cache the
         existing 5-min ``extract_configs.sh`` cron reads.

    The auto-monitor mirror writer in ``monitored_dispatch.py`` writes
    to whichever path this returns. Tests MUST set
    ``SCALER_DEVICES_FILE`` so they never touch the live lab file.
    """
    override = os.environ.get("SCALER_DEVICES_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    return Path(SCALER_ROOT) / "db" / "devices.json"

import urllib.error
import urllib.parse
import urllib.request

DISCOVERY_API = os.environ.get("DISCOVERY_API", "http://localhost:8765")
XRAY_CONFIG_PATH = os.path.expanduser("~/.xray_config.json")


_discovery_breaker = {"failures": 0, "open_until": 0}

def _resolve_device(device_id: str) -> dict:
    """Resolve device to mgmt_ip via discovery_api.
    
    Circuit breaker: after 3 consecutive failures, skip for 30s to avoid
    10-second timeout blocking every context/stack call.
    """
    import time
    now = time.time()
    if _discovery_breaker["failures"] >= 3 and now < _discovery_breaker["open_until"]:
        raise ConnectionError("discovery_api circuit breaker open")
    url = f"{DISCOVERY_API}/api/device/{urllib.parse.quote(device_id)}/resolve"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            _discovery_breaker["failures"] = 0
            return json.loads(resp.read())
    except Exception:
        _discovery_breaker["failures"] += 1
        _discovery_breaker["open_until"] = now + 30
        raise


def _user_xray_dir(app_user: str) -> Path:
    """Return ~/.topology_users/<app_user>/ if it exists, else None."""
    if not app_user or app_user == "default":
        return None
    base = Path(os.environ.get("TOPOLOGY_USERS_BASE", str(Path.home() / ".topology_users")))
    user_dir = base / app_user
    return user_dir if user_dir.exists() else None


# ---------------------------------------------------------------------------
# Lab credential profiles
# ---------------------------------------------------------------------------
# DriveNets labs run several device classes that each accept different SSH
# credentials. The defaults below are SHARED service accounts (not personal),
# the same for every user of this app. They can be overridden centrally via
# ~/.xray_config.json (admin-managed) or per-user via ~/.topology_users/<u>/
# xray.json + devices.json. The hostname-routing picker below decides which
# profile to try FIRST for a given device; the discovery endpoints additionally
# perform an auto-fallback chain on auth failure so a misclassified device
# still gets discovered.

_LAB_PROFILE_DEFAULTS = {
    # Standard DNOS PE/P/RR routers and the catch-all default.
    "dut": {"user": "dnroot", "password": "dnroot"},
    # DNAAS fabric (LEAF/SPINE/SUPERSPINE) -- shared service account.
    "dnaas": {"user": "sisaev", "password": "Drive1234!"},
    # Arista lab switches.
    "arista": {"user": "dn", "password": "drive1234!"},
}

# Order tried by the auto-fallback chain when the first-pick profile fails.
# Most labs only need dut <-> dnaas, but arista is included so a mislabeled
# Arista box is still recoverable.
_LAB_PROFILE_FALLBACK_ORDER = ("dut", "dnaas", "arista")


def _classify_device_profile(device_id: str = "", hostname: str = "") -> str:
    """Pick the best-fit credential profile based on device naming.

    Returns one of: "dut" (default), "dnaas", "arista".

    Heuristic only -- the discovery endpoints still auto-fall-back through
    the other profiles if SSH auth fails, so a wrong classification just
    costs one extra connection attempt.
    """
    name = (device_id or hostname or "").upper()
    if not name:
        return "dut"
    # DNAAS fabric: LEAF, SPINE, SUPERSPINE, SS- (e.g. SS-13, B-14, D-16).
    # Single-letter-dash patterns like B-14, D-16 are the IL DNAAS naming.
    if any(tok in name for tok in ("LEAF", "SPINE", "SUPERSPINE", "DNAAS", "FABRIC")):
        return "dnaas"
    if name.startswith("SS-") or any(name.startswith(p) for p in ("B-", "D-", "C-")):
        # Conservative: only treat as DNAAS when the rest is a 1-3 digit ID
        # (B-14, D-16) -- avoids hijacking customer-named devices like B-CORE.
        try:
            tail = name.split("-", 1)[1]
            if tail.isdigit() and 1 <= len(tail) <= 3:
                return "dnaas"
        except IndexError:
            pass
    if "ARISTA" in name or name.startswith("EOS-") or "DCS-" in name:
        return "arista"
    return "dut"


def _load_lab_credentials() -> dict:
    """Load the shared lab credential profiles, falling back to defaults.

    Order:
      1. ~/.xray_config.json `credentials` (DUT) and `dnaas_credentials` --
         site-wide overrides managed by the app admin.
      2. _LAB_PROFILE_DEFAULTS -- bundled DriveNets-wide defaults.

    Per-user overrides are NOT loaded here (they live in xray.json /
    devices.json and are only consulted by `_get_credentials`).
    """
    profiles = {k: dict(v) for k, v in _LAB_PROFILE_DEFAULTS.items()}
    try:
        with open(XRAY_CONFIG_PATH) as f:
            cfg = json.load(f)
        dut = cfg.get("credentials", {}) or {}
        if dut.get("device_user") and dut.get("device_password"):
            profiles["dut"] = {"user": dut["device_user"], "password": dut["device_password"]}
        if dut.get("arista_user") and dut.get("arista_password"):
            profiles["arista"] = {"user": dut["arista_user"], "password": dut["arista_password"]}
        dnaas = cfg.get("dnaas_credentials", {}) or {}
        if dnaas.get("user") and dnaas.get("password"):
            profiles["dnaas"] = {"user": dnaas["user"], "password": dnaas["password"]}
    except Exception:
        pass
    return profiles


def _get_lab_credential_chain(device_id: str = "", hostname: str = "") -> list:
    """Return [(profile_name, user, password), ...] in the order to try.

    First element is the best-guess profile based on hostname; the rest are
    the alternates so callers can auto-retry on auth failure without a UI
    prompt. Used by the Discover endpoint and by the topology canvas SSH /
    LLDP discovery paths.
    """
    profiles = _load_lab_credentials()
    primary = _classify_device_profile(device_id=device_id, hostname=hostname)
    order = [primary] + [p for p in _LAB_PROFILE_FALLBACK_ORDER if p != primary]
    chain = []
    for name in order:
        prof = profiles.get(name)
        if prof and prof.get("user") and prof.get("password"):
            chain.append((name, prof["user"], prof["password"]))
    return chain


def _get_credentials(app_user: str = "", device_id: str = "", hostname: str = "") -> tuple:
    """Resolve device SSH credentials with per-user + device-class precedence.

    Priority (first match wins):
      1. ~/.topology_users/<app_user>/devices.json -> per-device-id override
      2. ~/.topology_users/<app_user>/devices.json -> "_default" entry
      3. ~/.topology_users/<app_user>/xray.json   -> credentials.device_user/_password
      4. Lab-credential profile picked from device hostname (DUT vs DNAAS vs Arista)
         using ~/.xray_config.json or the bundled defaults.
      5. ("dnroot", "dnroot") -> hard fallback.

    When called without arguments we transparently pick up the JWT username
    from the per-request ContextVar set by the auth middleware. Legacy
    callers that pass nothing therefore become per-user automatically as
    soon as multiuser is enabled.

    `device_id` / `hostname`: when supplied, lets us return DNAAS-style
    credentials for LEAF/SPINE devices instead of always defaulting to
    `dnroot/dnroot`. This fixes "API discovery fails on some devices"
    where the device is a DNAAS leaf but the legacy code only ever tried
    the DUT default.

    All exceptions are swallowed so SSH paths never break on a bad/missing file.
    """
    if not app_user:
        try:
            app_user = current_app_user.get() or ""
        except Exception:
            app_user = ""
    user_dir = _user_xray_dir(app_user)
    if user_dir is not None:
        # 1+2: per-user devices.json {device_id: {user, password}, "_default": {...}}
        devices_file = user_dir / "devices.json"
        if devices_file.exists():
            try:
                with open(devices_file) as f:
                    db = json.load(f)
                target = None
                if device_id and device_id in db:
                    target = db[device_id]
                elif "_default" in db:
                    target = db["_default"]
                if isinstance(target, dict):
                    u = target.get("user") or target.get("device_user")
                    p = target.get("password") or target.get("device_password")
                    if u and p:
                        return u, p
            except Exception:
                pass
        # 3: per-user xray.json (DUT creds only -- DNAAS/Arista come from
        # the shared lab profiles below so a per-user xray.json can't
        # accidentally hijack DNAAS auth for the whole app).
        xray_file = user_dir / "xray.json"
        if xray_file.exists():
            try:
                with open(xray_file) as f:
                    cfg = json.load(f)
                creds = cfg.get("credentials", {})
                u = creds.get("device_user")
                p = creds.get("device_password")
                # Only use the per-user DUT creds when the target IS a DUT.
                # For LEAF/SPINE we want the shared DNAAS service account.
                profile = _classify_device_profile(device_id=device_id, hostname=hostname)
                if u and p and profile == "dut":
                    return u, p
            except Exception:
                pass

    # 4: hostname-routed lab profile.
    chain = _get_lab_credential_chain(device_id=device_id, hostname=hostname)
    if chain:
        _, user, password = chain[0]
        return user, password

    # 5: hard fallback.
    return "dnroot", "dnroot"


class SSHConnectionPool:
    """Persistent SSH connection pool for faster operations.
    When enabled, reuses connections instead of connect/disconnect per request.
    Thread-safe; uses fresh invoke_shell() per use to avoid dirty channel state.
    Pool is keyed by (app_user, ip) so different app users get isolated connections.
    Pool enabled state is per-user: User A toggling off doesn't affect User B.

    Wave 6.3: ``_max_connections`` is env-tunable via ``TP_SSH_POOL_MAX``
    (default 200). At 100 concurrent users each touching 1-2 devices,
    50-entry LRU thrashed heavily -- users paid ~1-2s reconnect cost on
    cache misses. 200 removes the bottleneck for realistic lab loads.
    """
    def __init__(self):
        self._enabled_users = set()  # per-user opt-in (empty = nobody pooling)
        self._pool = {}  # "app_user@ip" -> { client, user, app_user, last_used, created_at }
        self._lock = threading.Lock()
        self._keepalive_thread = None
        self._stop_keepalive = threading.Event()
        self._max_idle_s = 300
        self._keepalive_s = 30
        try:
            self._max_connections = max(10, int(os.environ.get("TP_SSH_POOL_MAX", 200)))
        except (TypeError, ValueError):
            self._max_connections = 200

    @property
    def enabled(self):
        """True if any user has pooling enabled (backward compat for code that reads this)."""
        return bool(self._enabled_users)

    def _user_enabled(self, app_user: str) -> bool:
        return (app_user or "default") in self._enabled_users

    @staticmethod
    def _pool_key(ip: str, app_user: str = "default") -> str:
        return f"{app_user or 'default'}@{ip}"

    def toggle(self, on: bool, app_user: str = "default") -> dict:
        app_user = app_user or "default"
        with self._lock:
            if on:
                self._enabled_users.add(app_user)
                self._stop_keepalive.clear()
                if not self._keepalive_thread or not self._keepalive_thread.is_alive():
                    self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
                    self._keepalive_thread.start()
            else:
                self._enabled_users.discard(app_user)
                prefix = f"{app_user}@"
                to_close = [k for k in self._pool if k.startswith(prefix)]
                for key in to_close:
                    entry = self._pool.pop(key, None)
                    if entry:
                        try:
                            entry.get("client") and entry["client"].close()
                        except Exception:
                            pass
                if not self._pool and not self._enabled_users:
                    self._stop_keepalive.set()
                    if self._keepalive_thread and self._keepalive_thread.is_alive():
                        self._keepalive_thread.join(timeout=2)
                    self._keepalive_thread = None
            return {"enabled": self._user_enabled(app_user), "count": len(self._pool)}

    def get_client(self, ip: str, user: str, password: str, app_user: str = "default"):
        """Return a pooled or fresh SSHClient. If pool disabled for this user, caller must close.

        Wave 7.7: tracks ``in_use`` refcount per pool entry so the LRU
        evictor never tears down a connection that another thread is
        currently issuing commands against. Callers SHOULD bracket
        usage with ``get_client`` / ``release`` -- but even if they
        don't, the new logic only evicts entries with ``in_use == 0``,
        falling back to the oldest idle entry when the pool is full.
        """
        import paramiko
        ip = (ip or "").strip().split("/")[0]
        if not ip:
            return None
        key = self._pool_key(ip, app_user)
        with self._lock:
            if not self._user_enabled(app_user):
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=user, password=password, timeout=15,
                              look_for_keys=False, allow_agent=False)
                transport = client.get_transport()
                if transport:
                    transport.set_keepalive(self._keepalive_s)
                return client
            entry = self._pool.get(key)
            if entry:
                client = entry.get("client")
                if client and client.get_transport() and client.get_transport().is_active():
                    entry["last_used"] = time.monotonic()
                    entry["in_use"] = entry.get("in_use", 0) + 1
                    return client
                try:
                    client and client.close()
                except Exception:
                    pass
                del self._pool[key]
            if len(self._pool) >= self._max_connections:
                self._evict_lru()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=user, password=password, timeout=15,
                          look_for_keys=False, allow_agent=False)
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(self._keepalive_s)
            self._pool[key] = {
                "client": client, "user": user, "app_user": app_user,
                "last_used": time.monotonic(), "created_at": time.monotonic(),
                "in_use": 1,
            }
            return client

    def release(self, ip: str, app_user: str = "default"):
        """Mark connection as idle and decrement the in-use refcount.

        ``in_use`` cannot go negative (Wave 7.7 safety net): callers that
        release without a matching ``get_client`` should not wedge the
        LRU policy.
        """
        ip = (ip or "").strip().split("/")[0]
        key = self._pool_key(ip, app_user)
        with self._lock:
            entry = self._pool.get(key)
            if entry is not None:
                entry["last_used"] = time.monotonic()
                cur = int(entry.get("in_use", 0))
                entry["in_use"] = max(0, cur - 1)

    def evict(self, ip: str, app_user: str = None):
        """Force-close and remove connection. If app_user=None, evict all users for that ip."""
        ip = (ip or "").strip().split("/")[0]
        with self._lock:
            if app_user is not None:
                key = self._pool_key(ip, app_user)
                entry = self._pool.pop(key, None)
                if entry:
                    try:
                        entry.get("client") and entry["client"].close()
                    except Exception:
                        pass
            else:
                suffix = f"@{ip}"
                to_close = [k for k in self._pool if k.endswith(suffix)]
                for key in to_close:
                    entry = self._pool.pop(key, None)
                    if entry:
                        try:
                            entry.get("client") and entry["client"].close()
                        except Exception:
                            pass

    def _evict_lru(self):
        """Evict the least-recently-used IDLE connection.

        Wave 7.7 change: the previous implementation picked any LRU
        entry including one currently in use, which could tear down an
        SSH channel mid-command when the pool was full. We now only
        consider entries with ``in_use == 0``. If every entry is busy
        (rare: pool size >= concurrent callers), we leave the pool as
        is and the caller simply allocates a fresh un-pooled client --
        preferable to killing an in-flight operation.
        """
        if not self._pool:
            return
        idle = [
            (k, v) for k, v in self._pool.items()
            if int(v.get("in_use", 0)) == 0
        ]
        if not idle:
            # All pooled clients are checked out. Safer to grow beyond
            # the cap than to kill an in-flight command -- the
            # keepalive loop and explicit ``release`` path will prune
            # the oldest idle entry shortly.
            return
        lru_key = min(idle, key=lambda x: x[1]["last_used"])[0]
        entry = self._pool.pop(lru_key, None)
        if entry:
            try:
                entry.get("client") and entry["client"].close()
            except Exception:
                pass

    def _keepalive_loop(self):
        while not self._stop_keepalive.wait(self._keepalive_s):
            with self._lock:
                if not self.enabled:
                    break
                now = time.monotonic()
                to_remove = []
                for key, entry in self._pool.items():
                    # Wave 7.7: never evict an in-use connection from the
                    # keepalive loop. A caller may have been holding the
                    # client for longer than ``_max_idle_s`` while
                    # running a long show command or multi-step commit.
                    if int(entry.get("in_use", 0)) > 0:
                        continue
                    if now - entry["last_used"] > self._max_idle_s:
                        to_remove.append(key)
                    else:
                        client = entry.get("client")
                        if not client or not client.get_transport() or not client.get_transport().is_active():
                            to_remove.append(key)
                for key in to_remove:
                    entry = self._pool.pop(key, None)
                    if entry:
                        try:
                            entry.get("client") and entry["client"].close()
                        except Exception:
                            pass

    def status(self, app_user: str = None) -> dict:
        with self._lock:
            entries = []
            for key, e in self._pool.items():
                if app_user and not key.startswith(f"{app_user}@"):
                    continue
                client = e.get("client")
                active = bool(client and client.get_transport() and client.get_transport().is_active())
                ip_part = key.split("@", 1)[1] if "@" in key else key
                entries.append({"ip": ip_part, "app_user": e.get("app_user", "default"),
                               "active": active, "last_used": e.get("last_used", 0)})
            user_enabled = self._user_enabled(app_user) if app_user else self.enabled
            return {"enabled": user_enabled, "count": len(entries), "entries": entries}

    def health_stats(self) -> dict:
        """Aggregate pool stats for /api/health/concurrency (Wave 6.3).

        Returns capacity, current fill, per-user counts, and per-IP counts
        so operators can spot one user monopolizing pool slots or one
        device attracting many connections.

        Wave 7.7: also reports ``in_use`` totals so operators can see
        whether the pool is full-but-idle (happy) or full-and-hot
        (approaching saturation).
        """
        with self._lock:
            by_user: Dict[str, int] = {}
            by_ip: Dict[str, int] = {}
            active_count = 0
            in_use_total = 0
            by_user_in_use: Dict[str, int] = {}
            for key, e in self._pool.items():
                if "@" in key:
                    u, ip = key.split("@", 1)
                else:
                    u, ip = "default", key
                by_user[u] = by_user.get(u, 0) + 1
                by_ip[ip] = by_ip.get(ip, 0) + 1
                client = e.get("client")
                if client and client.get_transport() and client.get_transport().is_active():
                    active_count += 1
                iu = int(e.get("in_use", 0))
                if iu > 0:
                    in_use_total += iu
                    by_user_in_use[u] = by_user_in_use.get(u, 0) + iu
            users_enabled = sorted(self._enabled_users)
            return {
                "enabled_users": users_enabled,
                "max_connections": self._max_connections,
                "in_pool": len(self._pool),
                "active": active_count,
                "in_use": in_use_total,
                "in_use_by_user": by_user_in_use,
                "utilization": (len(self._pool) / self._max_connections
                                if self._max_connections > 0 else 0.0),
                "by_user": by_user,
                "by_ip": by_ip,
                "idle_timeout_s": self._max_idle_s,
            }


_ssh_pool = SSHConnectionPool()


_resolve_cache = {}
_scaler_ops_index = None
_scaler_ops_ip_map = None  # ip -> [entry] for fast IP-based lookups
_scaler_ops_index_ts = 0


def _build_scaler_ops_index():
    """Build an in-memory index of all SCALER operational.json files.
    Maps: serial, hostname, mgmt_ip, dir_name -> {ip, scaler_id, serial}
    Cached for 60 seconds.
    """
    global _scaler_ops_index, _scaler_ops_ip_map, _scaler_ops_index_ts
    import time
    now = time.time()
    if _scaler_ops_index and (now - _scaler_ops_index_ts) < 60:
        return _scaler_ops_index

    index = {}
    ip_map = {}
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_dir.exists():
        _scaler_ops_index = index
        _scaler_ops_ip_map = {}
        _scaler_ops_index_ts = now
        return index

    # Phase 0: Build a {hostname_or_alias.lower() -> serial} map from
    # console_mappings.json. This lets a stale placeholder dir (e.g.
    # YOR_PE-1/ with no serial and device_state=GI) inherit the chassis
    # serial from the port mapping in console_mappings, so it gets linked
    # to the serial-rich sibling (PE-1/ with state=DNOS) in Phase 2 and
    # cannot publish a ghost IP of its own into the index.
    cm_hostname_to_serial: dict[str, str] = {}
    try:
        cm_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
        if cm_path.exists():
            cm = json.loads(cm_path.read_text())
            # New multi-server format: console_servers[*].ports[*].serial_number
            for _srv in (cm.get("console_servers") or {}).values():
                for port_info in (_srv.get("ports") or {}).values():
                    sn = (port_info.get("serial_number") or "").strip()
                    if not sn:
                        continue
                    host_candidates = [port_info.get("hostname") or ""]
                    host_candidates += port_info.get("hostname_aliases") or []
                    for name in host_candidates:
                        key = (name or "").strip().lower()
                        if key:
                            cm_hostname_to_serial.setdefault(key, sn)
            # device_to_console short-cut
            for dev_name, mapping in (cm.get("device_to_console") or {}).items():
                sn = (mapping.get("serial_number") or "").strip()
                if sn and dev_name:
                    cm_hostname_to_serial.setdefault(dev_name.strip().lower(), sn)
    except Exception:
        # Never block the index build on a console-mapping read error.
        cm_hostname_to_serial = {}

    # Phase 1: Read all config directories and find the richest entry per serial
    serial_to_best = {}
    all_entries = []
    for dev_dir in configs_dir.iterdir():
        if not dev_dir.is_dir():
            continue
        ops_path = dev_dir / "operational.json"
        if not ops_path.exists():
            continue
        try:
            ops = _read_ops_safe(ops_path)
            raw_ssh = (ops.get("ssh_host") or "").strip().split("/")[0]
            raw_mgmt = (ops.get("mgmt_ip") or "").strip().split("/")[0]
            raw_ncc = (ops.get("ncc_mgmt_ip") or "").strip().split("/")[0]
            raw_kvm = (ops.get("kvm_host_ip") or "").strip().split("/")[0]
            is_ssh_ip = bool(raw_ssh and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_ssh))
            is_mgmt_ip = bool(raw_mgmt and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_mgmt))
            is_ncc_ip = bool(raw_ncc and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_ncc))
            dev_state = (ops.get("device_state") or "").upper()
            is_kvm_cluster = (ops.get("ncc_type") == "kvm")
            is_gi_like = dev_state in ("GI", "BASEOS_SHELL", "DEPLOYING", "UPGRADING", "RECOVERY")

            # Priority order for the dialable IP we publish to callers:
            #   1. KVM cluster in GI-like state: prefer the NCC VM's management
            #      IP (`ncc_mgmt_ip`). `mgmt_ip` on these records has been
            #      known to hold `kvm_host_ip` after a messy wizard refresh;
            #      dialing the hypervisor instead of the NCC is exactly how
            #      PE-4 ended up mis-classified as DNOS (hypervisor banner
            #      is unclassifiable -> under the old binary classifier it
            #      defaulted to DNOS). Never publish `kvm_host_ip` as the
            #      device's SSH target for a GI-like cluster.
            #   2. `ssh_host` if it looks like an IP -- that is the
            #      authoritative "last known good" SSH target written by
            #      `connect_for_upgrade` after an identity check.
            #   3. `mgmt_ip` if it looks like an IP and is NOT the KVM host.
            #   4. Fall back to whatever strings we have.
            if is_kvm_cluster and is_gi_like and is_ncc_ip:
                ip = raw_ncc
            elif is_ssh_ip and not (is_kvm_cluster and raw_kvm and raw_ssh == raw_kvm):
                ip = raw_ssh
            elif is_mgmt_ip and not (is_kvm_cluster and raw_kvm and raw_mgmt == raw_kvm):
                ip = raw_mgmt
            elif is_ncc_ip:
                ip = raw_ncc
            elif is_mgmt_ip:
                ip = raw_mgmt
            elif is_ssh_ip:
                ip = raw_ssh
            else:
                ip = raw_mgmt or raw_ssh
            serial = (ops.get("serial_number") or "").strip()
            hostname = (ops.get("hostname") or dev_dir.name).strip()
            has_state = bool(dev_state)
            has_version = bool(ops.get("dnos_version") or ops.get("dnos_url"))
            # Compute richness on the ORIGINAL contents (before any
            # console-mappings serial inheritance) so a serial-poor stale
            # placeholder dir can't outrank the serial-rich live dir.
            richness = (1 if has_state else 0) + (1 if has_version else 0) + (1 if serial else 0)

            # Inherit chassis serial from console_mappings.json when
            # operational.json doesn't have one (e.g. a stale placeholder
            # dir left over from a previous hostname). Links the entry to
            # the richest sibling in Phase 2 and prevents it from owning an
            # IP key that belongs to the live dir.
            if not serial and cm_hostname_to_serial:
                for key in (dev_dir.name, hostname):
                    k = (key or "").strip().lower()
                    if k and k in cm_hostname_to_serial:
                        serial = cm_hostname_to_serial[k]
                        break
            is_stale = bool(ops.get("_stale"))
            if is_stale:
                ip = ""
            entry = {
                "ip": ip,
                "scaler_id": dev_dir.name,
                "serial": serial,
                "hostname": hostname,
                "stale": is_stale,
            }
            all_entries.append((dev_dir.name, entry, richness, serial))

            if serial and serial != "N/A":
                prev = serial_to_best.get(serial)
                if prev is None or richness > prev[1]:
                    serial_to_best[serial] = (entry, richness)
        except Exception:
            continue

    # Phase 2: Build index, preferring the richest entry per serial
    for dir_name, entry, richness, serial in all_entries:
        if serial and serial in serial_to_best:
            best_entry = serial_to_best[serial][0]
            if best_entry["scaler_id"] != dir_name:
                entry = {**best_entry, "scaler_id": best_entry["scaler_id"]}

        index[dir_name.lower()] = entry
        hostname = entry.get("hostname", dir_name)
        if hostname and hostname.lower() not in index:
            index[hostname.lower()] = entry
        if serial:
            index[serial.lower()] = entry
        ip = entry.get("ip", "")
        if ip:
            index[ip] = entry
            if ip not in ip_map:
                ip_map[ip] = []
            if entry not in ip_map[ip]:
                ip_map[ip].append(entry)
        raw_ssh = entry.get("ssh_host", "")
        if raw_ssh and raw_ssh.lower() not in index:
            index[raw_ssh.lower()] = entry

    _scaler_ops_index = index
    _scaler_ops_ip_map = ip_map
    _scaler_ops_index_ts = now
    return index


def _resolve_config_dir(device_id: str) -> str:
    """Find the canonical config directory name for a device.

    Resolves through: exact match -> index lookup -> partial name match.
    Returns the directory name (e.g. 'PE-1') under SCALER_ROOT/db/configs/.
    Falls back to device_id if no match found.
    """
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"

    # IMPORTANT: use the corruption-tolerant ``read_ops`` so a single
    # malformed operational.json (legacy non-atomic write) doesn't
    # poison every caller. ``read_ops`` quarantines bad files and
    # returns ``{}`` rather than raising. Without this, the
    # device-mode resolver's persist step silently fails (we observed
    # this in the wild on YOR_PE-1 -- a 06:56 write left the file
    # with two concatenated objects, and every probe for 15h failed
    # to write through).
    from routes._ops_writer import read_ops as _safe_read_ops

    if (configs_dir / device_id / "operational.json").exists():
        ops = _safe_read_ops(configs_dir / device_id / "operational.json")
        if ops.get("device_state") or ops.get("dnos_version") or ops.get("serial_number"):
            # Canonicalize by chassis serial: even when the alias has its OWN
            # config dir (e.g. YOR_PE-1/ AND PE-1/ both exist for serial
            # WK31D7VV00023), collapse onto the single richest sibling dir that
            # shares the serial, so one physical device never splits its config
            # history across alias dirs. Without this, the /UPGRADE + monitor
            # flows save pre-config under whichever name resolved (hostname vs
            # id), and the global BGP session ended up under YOR_PE-1/ while the
            # services ended up under PE-1/ (root-caused 2026-06-24). The index
            # already maps serial -> richest scaler_id; we just honor it here
            # instead of returning the exact dir blindly.
            _sn = (ops.get("serial_number") or "").strip().lower()
            if _sn:
                _ent = _build_scaler_ops_index().get(_sn)
                _canon = (_ent or {}).get("scaler_id")
                if _canon and _canon != device_id and (configs_dir / _canon / "operational.json").exists():
                    return _canon
            return device_id

    idx = _build_scaler_ops_index()
    entry = idx.get(device_id.lower())
    if entry:
        sid = entry["scaler_id"]
        if (configs_dir / sid / "operational.json").exists():
            return sid

    norm = re.sub(r'[_\-\s]', '', device_id.lower())
    best_dir = None
    best_richness = -1
    for d in configs_dir.iterdir():
        if not d.is_dir() or not (d / "operational.json").exists():
            continue
        norm_d = re.sub(r'[_\-\s]', '', d.name.lower())
        if norm in norm_d or norm_d in norm:
            ops = _safe_read_ops(d / "operational.json")
            if ops:
                richness = sum(1 for k in ("device_state", "dnos_version", "serial_number") if ops.get(k))
                if richness > best_richness:
                    best_richness = richness
                    best_dir = d.name
            elif best_dir is None:
                # Empty/corrupt -- still record as a fallback candidate
                # so we don't return ``device_id`` unchanged when the
                # user just lost the contents of the only matching dir.
                best_dir = d.name

    return best_dir or best_dir or device_id


def _resolve_from_monitored_registry(device_id: str, ssh_host: str = "") -> tuple | None:
    """Resolve a user-attached device from the monitored backend registry.

    This is the post-onboarding source-of-truth bridge between the SSH dialog
    (`verify-and-register`) and the rest of the scaler APIs. It is scoped to
    the authenticated user when available so one user's registered lab device
    cannot satisfy another user's unresolved canvas label.
    """
    try:
        app_user = current_app_user.get() or ""
    except Exception:
        app_user = ""
    if not app_user or app_user == "default":
        return None

    try:
        from api import monitored_registry as reg
    except Exception:
        return None

    candidates = [
        (device_id or "").strip(),
        (ssh_host or "").strip().split("/")[0],
    ]
    candidates = [c for c in candidates if c]
    if not candidates:
        return None

    def _loose(value: str) -> str:
        return re.sub(r"[_\-\s.]", "", (value or "").strip().lower())

    candidate_exact = {c.lower() for c in candidates}
    candidate_loose = {_loose(c) for c in candidates if c}
    try:
        records = reg.list_devices(only_user=app_user)
    except Exception:
        return None

    for record in records:
        primary_ip = (record.get("management_ip") or "").strip()
        cluster_ips = [str(ip).strip() for ip in (record.get("cluster_ncc_ips") or []) if str(ip).strip()]
        identifiers = [
            record.get("hostname") or "",
            record.get("serial_number") or "",
            primary_ip,
            record.get("key") or "",
            *cluster_ips,
        ]
        exact = {str(v).strip().lower() for v in identifiers if str(v).strip()}
        loose = {_loose(str(v)) for v in identifiers if str(v).strip()}
        if not (candidate_exact & exact or candidate_loose & loose):
            continue

        # If the caller supplied a specific registered cluster member IP,
        # preserve that as the SSH target. Otherwise use the canonical
        # management IP recorded by verify-and-register.
        requested_ip = ""
        for c in candidates:
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", c) and c in cluster_ips + [primary_ip]:
                requested_ip = c
                break
        mgmt_ip = requested_ip or primary_ip
        if not mgmt_ip:
            continue
        scaler_id = (record.get("hostname") or device_id or "").strip() or mgmt_ip
        return (mgmt_ip, scaler_id, f"monitored_registry:{record.get('key') or mgmt_ip}")

    return None


def _resolve_mgmt_ip(device_id: str, ssh_host: str = "") -> tuple:
    """Central device IP resolution. Returns (mgmt_ip, scaler_device_id, resolved_via).

    Resolution chain (fast, uses cached SCALER index):
    1. ssh_host is an IP AND that IP is live in the SCALER ops index -> use it
       (happy path: the canvas already has the authoritative IP cached).
    2. ssh_host is an IP but NOT in the ops index -> the IP is potentially
       stale (ghost IP after an upgrade / redeploy). Keep it as a last-resort
       fallback, then continue down the chain so the serial / operational.json
       wins. This is the "SN is source of truth" rule.
    3. ssh_host is a serial/hostname -> match in SCALER ops index.
    4. device_id exact match in SCALER ops index.
    5. Current user's monitored backend registry (verify-and-register output).
    6. Discovery API _resolve_device().
    7. device_inventory.json fuzzy match.
    8. Partial name match in SCALER ops index (PE-1 in YOR_PE-1).
    9. If every fresh source fails AND we had a stale ssh_host IP from step 2,
       dial that IP as a last resort -- the device may simply not be
       registered in scaler yet.

    When a fresh path wins AFTER a stale ssh_host fallback was stashed,
    ``resolved_via`` is tagged ``sn_over_stale_ip:<old>-><new>:<inner_via>``
    so logs / UI can tell the caller that the canvas IP was overridden by
    a more authoritative source.

    Raises HTTPException(503) if no IP can be found and no stale fallback
    is available.
    """
    cache_key = f"{device_id}|{ssh_host}"
    if cache_key in _resolve_cache:
        cached = _resolve_cache[cache_key]
        import time
        if time.time() - cached[3] < 120:
            return cached[0], cached[1], cached[2]

    ssh = ssh_host.strip() if ssh_host else ""
    idx = _build_scaler_ops_index()

    is_ip = bool(ssh and re.match(r"^\d+\.\d+\.\d+\.\d+$", ssh))

    # When ssh_host is an IP we either use it directly (if live in the ops
    # index) or stash it as a last-resort fallback and fall through to the
    # device_id / serial / partial-match chain. Stashing avoids the old
    # short-circuit that dialled ghost IPs after a device was reimaged.
    stale_ip_fallback: tuple | None = None
    if is_ip:
        entry = idx.get(ssh)
        if entry and entry.get("scaler_id"):
            result = (ssh, entry["scaler_id"], f"ssh_ip_literal:{ssh}")
            _cache_resolve(cache_key, result)
            return result
        stale_ip_fallback = (ssh, device_id, f"ssh_ip_direct:{ssh}")

    def _tag_via(fresh_ip: str, inner_via: str) -> str:
        """Tag resolved_via when a fresh source overrides a stale canvas IP."""
        if stale_ip_fallback and fresh_ip and fresh_ip != stale_ip_fallback[0]:
            return f"sn_over_stale_ip:{stale_ip_fallback[0]}->{fresh_ip}:{inner_via}"
        return inner_via

    if ssh and not is_ip:
        entry = idx.get(ssh.lower())
        if entry and entry["ip"]:
            result = (entry["ip"], entry["scaler_id"], f"ssh_serial:{ssh}->{entry['scaler_id']}")
            _cache_resolve(cache_key, result)
            return result

    entry = idx.get(device_id.lower())
    if entry and entry["ip"]:
        via = _tag_via(entry["ip"], f"scaler_index:{device_id}")
        result = (entry["ip"], entry["scaler_id"], via)
        _cache_resolve(cache_key, result)
        return result

    monitored = _resolve_from_monitored_registry(device_id, ssh)
    if monitored:
        via = _tag_via(monitored[0], monitored[2])
        result = (monitored[0], monitored[1], via)
        _cache_resolve(cache_key, result)
        return result

    try:
        resolved = _resolve_device(device_id)
        ip = resolved.get("mgmt_ip", "").strip()
        if ip:
            idx_entry = idx.get(ip)
            sid = idx_entry["scaler_id"] if idx_entry else device_id
            via = _tag_via(ip, "discovery_api")
            result = (ip, sid, via)
            _cache_resolve(cache_key, result)
            return result
    except Exception:
        pass

    inv_dev = _find_inventory_device(device_id, ssh)
    if inv_dev is None:
        inv_dev = {}
    ip = (inv_dev.get("mgmt_ip") or inv_dev.get("ip") or "").strip().split("/")[0]
    if ip:
        idx_entry = idx.get(ip)
        sid = idx_entry["scaler_id"] if idx_entry else device_id
        via = _tag_via(ip, "device_inventory")
        result = (ip, sid, via)
        _cache_resolve(cache_key, result)
        return result

    norm_did = re.sub(r'[_\-\s]', '', device_id.lower())
    for key, entry in idx.items():
        if not entry["ip"]:
            continue
        norm_key = re.sub(r'[_\-\s]', '', key)
        if norm_did in norm_key or norm_key in norm_did:
            via = _tag_via(entry["ip"], f"partial:{key}")
            result = (entry["ip"], entry["scaler_id"], via)
            _cache_resolve(cache_key, result)
            return result

    # No fresh source resolved device_id. If the caller originally passed
    # an IP (even one not in our ops index), honour it as a last resort --
    # the device may simply not be registered in scaler yet.
    if stale_ip_fallback:
        _cache_resolve(cache_key, stale_ip_fallback)
        return stale_ip_fallback

    raise HTTPException(
        status_code=503,
        detail=f"Could not resolve IP for '{device_id}'"
               f"{' (ssh_host=' + ssh + ')' if ssh else ''}. "
               "Set SSH address (IP) on the canvas device (right-click > Set SSH)."
    )


def _cache_resolve(key, result):
    import time
    _resolve_cache[key] = (result[0], result[1], result[2], time.time())


# ---------------------------------------------------------------------------
# Ghost-IP reaper
# ---------------------------------------------------------------------------
# When a device is upgraded or re-imaged, the management IP it used to
# advertise is released. The IP can then be reassigned by the lab's DHCP /
# inventory to a completely different DUT. If we keep serving the old IP
# for the original device_id, the user clicks "SSH PE-4" and silently lands
# on R7-Natan_SIT -- a dangerous class of bug ("ghost IP").
#
# The reaper below is the single source of truth for "this IP is no longer
# reliable for this device". Callers mark the record stale, and every
# resolver (ops index, discovery, inventory) honours that flag. The reaper
# also evicts SSH pool entries and drops the scaler-ops index cache so the
# next resolve rebuilds from disk.


def _invalidate_scaler_ops_cache() -> None:
    """Force `_build_scaler_ops_index` to re-read disk on next call."""
    global _scaler_ops_index, _scaler_ops_ip_map, _scaler_ops_index_ts
    _scaler_ops_index = {}
    _scaler_ops_ip_map = {}
    _scaler_ops_index_ts = 0.0
    _resolve_cache.clear()


def _mark_device_ip_stale(
    scaler_id: str,
    stale_ip: str = "",
    reason: str = "",
    actual_hostname: str = "",
    acting_user: str = "",
    broadcast: bool = True,
) -> dict:
    """Mark a scaler-ops entry's mgmt_ip/ssh_host as stale (no hard delete).

    We keep the operational.json around for historical context (configs,
    discovery results, platform info) but flag the reachability fields as
    unreliable so every subsequent resolve falls through to the next
    source. The record is only resurrected when the scaler re-discovery
    pipeline writes a fresh mgmt_ip back.

    Side effects:
      * evicts any pooled SSH client for the stale IP
      * drops the in-memory scaler-ops index + resolve cache
      * best-effort prunes the legacy `scaler/db/devices.json` mirror so
        the older CLI library doesn't keep dialling the ghost IP either
      * when ``acting_user`` is provided, records an audit event in the
        shared ``device_state`` DB and (if ``broadcast`` is True) pushes a
        ``ghost_ip_reaped`` event over the WebSocket bus to every user
        watching this device. "acting_user" is blank only when invoked
        from standalone CLI paths (tests, cron); in those cases we still
        record the event but attribute it to ``"system"``.

    Returns a machine-readable summary that the API can forward to the UI:
        {
            "scaler_id": str,
            "device_id": str | None,   # best-effort canvas label
            "cleared_ip": str,
            "actual_hostname": str,
            "reason": str,
            "marked_stale_at": ISO-8601,
            "operational_updated": bool,
            "devices_json_updated": bool,
            "pool_evicted": list[str],
            "acting_user": str,
            "event_id": int | None,
            "broadcast_deliveries": dict[str, int],
        }
    """
    import time
    from datetime import datetime, timezone
    acting_user_clean = (acting_user or "").strip() or "system"
    summary = {
        "scaler_id": scaler_id or "",
        "device_id": None,
        "cleared_ip": (stale_ip or "").strip(),
        "actual_hostname": (actual_hostname or "").strip(),
        "reason": reason or "ghost_ip",
        "marked_stale_at": datetime.now(timezone.utc).isoformat(),
        "operational_updated": False,
        "devices_json_updated": False,
        "pool_evicted": [],
        "acting_user": acting_user_clean,
        "event_id": None,
        "broadcast_deliveries": {},
    }

    if not scaler_id:
        _invalidate_scaler_ops_cache()
        # The device-mode resolver caches by scaler_id; without one we
        # only have an IP. Best-effort: tell the resolver to flush
        # entries whose live mgmt_ip equals this stale IP. Cheap to
        # call -- if no entries match it's a no-op.
        if summary["cleared_ip"]:
            try:
                from routes._device_mode_resolver import (
                    invalidate_by_mgmt_ip as _devmode_invalidate_ip,
                )
                _devmode_invalidate_ip(summary["cleared_ip"])
            except Exception:
                pass
        if summary["cleared_ip"]:
            try:
                _ssh_pool.evict(summary["cleared_ip"])
                summary["pool_evicted"].append(summary["cleared_ip"])
            except Exception:
                pass
        # Best-effort: still record the event (without a canvas device
        # ID we can't fan out to watchers, but the raw IP eviction is
        # worth keeping in the audit trail).
        try:
            from api.device_state import device_state, EVENT_GHOST_IP_REAPED
            device_state.record_event(
                device_id=summary["cleared_ip"] or "unknown",
                event_type=EVENT_GHOST_IP_REAPED,
                actor_user=acting_user_clean,
                payload={
                    "cleared_ip": summary["cleared_ip"],
                    "reason": summary["reason"],
                    "scaler_id": None,
                },
            )
        except Exception:
            pass
        return summary

    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    if ops_path.exists():
        try:
            ops = _read_ops_safe(ops_path)
        except Exception:
            ops = {}
        prev_mgmt = (ops.get("mgmt_ip") or "").strip().split("/")[0]
        prev_ssh = (ops.get("ssh_host") or "").strip()
        # Keep originals under _stale_* so a human can inspect; clear the
        # live fields so resolvers see the record as address-less.
        ops["_stale"] = True
        ops["_stale_reason"] = summary["reason"]
        ops["_stale_at"] = summary["marked_stale_at"]
        if summary["actual_hostname"]:
            ops["_stale_remote_hostname"] = summary["actual_hostname"]
        if prev_mgmt and "_stale_last_mgmt_ip" not in ops:
            ops["_stale_last_mgmt_ip"] = prev_mgmt
        if prev_ssh and "_stale_last_ssh_host" not in ops:
            ops["_stale_last_ssh_host"] = prev_ssh
        ops["mgmt_ip"] = ""
        ops["ssh_host"] = ""
        # If the stale IP also appears as ncc_mgmt_ip, reap it too so the
        # cluster-recovery path doesn't silently reintroduce the ghost.
        cleared_ip_match = (summary["cleared_ip"] or prev_mgmt or prev_ssh).strip().split("/")[0]
        _nip = (ops.get("ncc_mgmt_ip") or "").strip()
        if _nip and cleared_ip_match and _nip == cleared_ip_match:
            if "_stale_last_ncc_mgmt_ip" not in ops:
                ops["_stale_last_ncc_mgmt_ip"] = _nip
            ops["ncc_mgmt_ip"] = ""
            ops["ncc_mgmt_verified_at"] = ""
        summary["device_id"] = (ops.get("hostname") or scaler_id).strip()
        # Append to an in-file ring-buffer so the operational.json itself
        # carries a short-lived audit trail even when the shared event DB
        # is rotated out. Keep the last 20 entries to bound growth.
        events_log = ops.get("_ghost_events")
        if not isinstance(events_log, list):
            events_log = []
        events_log.append({
            "at": summary["marked_stale_at"],
            "actor_user": acting_user_clean,
            "cleared_ip": cleared_ip_match or summary["cleared_ip"],
            "reason": summary["reason"],
            "actual_hostname": summary["actual_hostname"],
        })
        if len(events_log) > 20:
            events_log = events_log[-20:]
        ops["_ghost_events"] = events_log
        try:
            from ._ops_writer import update_ops as _update_ops_ghost

            def _mutate_ghost(d: dict, snapshot=ops) -> None:
                d.clear()
                d.update(snapshot)

            _ok_g, _ = _update_ops_ghost(ops_path, _mutate_ghost, create_if_missing=False)
            summary["operational_updated"] = bool(_ok_g)
        except Exception as exc:
            logging.getLogger(__name__).warning("[ghost-ip] failed to write %s: %s", ops_path, exc)
        # Prefer the canonical IP we just cleared if caller didn't specify one.
        if not summary["cleared_ip"]:
            summary["cleared_ip"] = prev_mgmt or prev_ssh

    # Evict SSH pool entries tied to the stale IP so the next attempt
    # re-opens a fresh channel instead of reusing the old client.
    stale_ip_clean = summary["cleared_ip"].strip().split("/")[0]
    if stale_ip_clean and re.match(r"^\d+\.\d+\.\d+\.\d+$", stale_ip_clean):
        try:
            _ssh_pool.evict(stale_ip_clean)
            summary["pool_evicted"].append(stale_ip_clean)
        except Exception:
            pass

    # Legacy flat devices.json -- used by the scaler CLI library. Strip
    # the IP so the CLI falls back to re-discovery instead of dialling
    # the ghost host.
    legacy_path = Path(SCALER_ROOT) / "db" / "devices.json"
    if legacy_path.exists():
        try:
            legacy = json.loads(legacy_path.read_text())
        except Exception:
            legacy = None
        if isinstance(legacy, dict) and isinstance(legacy.get("devices"), list):
            changed = False
            wanted_ids = {scaler_id.lower()}
            if summary["device_id"]:
                wanted_ids.add(summary["device_id"].lower())
            for entry in legacy["devices"]:
                if not isinstance(entry, dict):
                    continue
                ids = {
                    (entry.get("id") or "").lower(),
                    (entry.get("hostname") or "").lower(),
                }
                ids |= {a.lower() for a in (entry.get("aliases") or []) if isinstance(a, str)}
                entry_ip = (entry.get("ip") or "").strip()
                matches_id = bool(wanted_ids & ids)
                matches_ip = bool(stale_ip_clean and entry_ip == stale_ip_clean)
                if matches_id or matches_ip:
                    if entry.get("ip"):
                        entry["_stale_last_ip"] = entry["ip"]
                        entry["ip"] = ""
                    entry["_stale"] = True
                    entry["_stale_reason"] = summary["reason"]
                    entry["_stale_at"] = summary["marked_stale_at"]
                    changed = True
            if changed:
                try:
                    legacy_path.write_text(json.dumps(legacy, indent=2))
                    summary["devices_json_updated"] = True
                except Exception as exc:
                    logging.getLogger(__name__).warning("[ghost-ip] failed to rewrite %s: %s", legacy_path, exc)

    _invalidate_scaler_ops_cache()
    # Flush the live device-mode resolver entry so the next probe
    # re-walks discovery for this scaler_id.
    try:
        from routes._device_mode_resolver import invalidate as _devmode_invalidate
        _devmode_invalidate(scaler_id, scaler_id)
    except Exception:
        pass
    try:
        logging.getLogger(__name__).info(
            "[ghost-ip] reaped scaler_id=%s cleared_ip=%s actual=%s reason=%s "
            "ops=%s legacy=%s pool_evicted=%s user=%s",
            scaler_id, summary["cleared_ip"], summary["actual_hostname"],
            summary["reason"], summary["operational_updated"],
            summary["devices_json_updated"], summary["pool_evicted"],
            acting_user_clean,
        )
    except Exception:
        pass

    # -- Shared-state audit log + per-user broadcast -----------------------
    # Frontend watchers are keyed by the *canvas label* (what the user
    # types into the topology tool -- e.g. "PE-1"), but the scaler layer
    # often resolves that to a canonical hostname like "YOR_CL_PE-1" via
    # operational.json. Fan out to every known alias so a watcher who
    # added "PE-1" still gets events when the scaler normalises the id.
    alias_set = set()
    canonical_id = (summary.get("device_id") or "").strip()
    if canonical_id:
        alias_set.add(canonical_id)
    if scaler_id:
        alias_set.add(scaler_id.strip())
    # Case-insensitive duplicates shouldn't both register, but we keep
    # the original casing for display; device_state comparisons are
    # case-insensitive via list_watchers_for_device's SQL collation.
    alias_set = {a for a in alias_set if a}

    if alias_set:
        event_id = None
        try:
            from api.device_state import device_state, EVENT_GHOST_IP_REAPED
            # Record one authoritative audit row under the canonical id.
            record_id = canonical_id or scaler_id
            ev = device_state.record_event(
                device_id=record_id,
                event_type=EVENT_GHOST_IP_REAPED,
                actor_user=acting_user_clean,
                payload={
                    "scaler_id": scaler_id,
                    "cleared_ip": summary["cleared_ip"],
                    "actual_hostname": summary["actual_hostname"],
                    "reason": summary["reason"],
                    "marked_stale_at": summary["marked_stale_at"],
                    "operational_updated": summary["operational_updated"],
                    "devices_json_updated": summary["devices_json_updated"],
                    "pool_evicted": summary["pool_evicted"],
                    "aliases": sorted(alias_set),
                },
            )
            event_id = ev.get("id")
            summary["event_id"] = event_id
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "[ghost-ip] failed to record device_state event: %s", exc
            )

        if broadcast:
            from api.event_bus import event_bus
            payload = {
                "scaler_id": scaler_id,
                "cleared_ip": summary["cleared_ip"],
                "actual_hostname": summary["actual_hostname"],
                "reason": summary["reason"],
                "marked_stale_at": summary["marked_stale_at"],
                "actor_user": acting_user_clean,
                "event_id": event_id,
                "aliases": sorted(alias_set),
            }
            extra_users = (
                [acting_user_clean]
                if acting_user_clean and acting_user_clean != "system" else None
            )
            notified_users = set()
            for alias in alias_set:
                try:
                    # Each publish call broadcasts under a different
                    # device_id so frontend handlers that filter by id
                    # don't miss the one that matches their canvas.
                    event_bus.publish_to_device_watchers_sync(
                        device_id=alias,
                        event_type="ghost_ip_reaped",
                        payload=payload,
                        # Only include the actor once -- on the first
                        # alias -- so they don't get three copies of the
                        # same event when three aliases exist.
                        extra_users=extra_users if not notified_users else None,
                    )
                    notified_users.add(alias)
                except Exception as exc:
                    logging.getLogger(__name__).warning(
                        "[ghost-ip] broadcast publish failed alias=%s: %s", alias, exc
                    )

    return summary


def _is_scaler_ops_stale(entry: dict) -> bool:
    """True if the operational.json for this entry is flagged as stale."""
    if not isinstance(entry, dict):
        return False
    # `entry` is a thin dict built by `_build_scaler_ops_index`; it does
    # not carry the `_stale` flag directly. Resolve it from the on-disk
    # operational.json using scaler_id -- cheap because this runs only on
    # cache miss inside _resolve_mgmt_ip.
    scaler_id = (entry.get("scaler_id") or "").strip()
    if not scaler_id:
        return False
    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    if not ops_path.exists():
        return False
    try:
        ops = _read_ops_safe(ops_path)
    except Exception:
        return False
    return bool(ops.get("_stale"))


def _safe_set_mgmt_ip(ops_data: dict, candidate_ip: str, source: str = "") -> bool:
    """Guardrailed writer for the ``mgmt_ip`` / ``ssh_host`` fields.

    Historically any code path with an IP-shaped string would call
    ``ops_data['mgmt_ip'] = candidate_ip`` directly. This produced two
    recurring classes of bugs:

      * **Ghost resurrection** -- a previously-reaped IP would get
        written back by a Phase-2 probe that took it from the frontend
        cache, re-contaminating the DB after the reaper cleared it.
      * **KVM host impersonation** -- for KVM-NCC cluster devices in
        GI mode, the UI sometimes cached ``kvm_host_ip`` (e.g.
        ``100.64.6.6``) as the device SSH address. That address then
        leaked into ``mgmt_ip``, making every subsequent live probe
        SSH to the hypervisor instead of the NCC. The prompt banner
        on the hypervisor looked enough like a DNOS router prompt to
        trip the binary mode classifier and flip the DB to DNOS, even
        though the real device was in GI.

    This helper accepts ``candidate_ip`` only when ALL of the
    following hold:

      * ``candidate_ip`` is a valid dotted-quad (``a.b.c.d``)
      * ``candidate_ip`` is NOT the device's own ``kvm_host_ip`` for
        a KVM-NCC cluster (use ``ncc_mgmt_ip`` for that tier)
      * ``candidate_ip`` is NOT in the reaper's ``_stale_last_*``
        memory
      * ``ops_data['_stale']`` is not True (when the record is still
        quarantined, callers must re-prove identity via
        ``connect_for_upgrade`` before any IP can be trusted again)

    Returns ``True`` when the assignment was applied, ``False`` when
    the guard rejected the candidate. Rejections are logged to
    ``_mgmt_ip_rejections`` in the ops record (bounded ring buffer).
    """
    import logging as _logging
    import re as _re

    if not isinstance(ops_data, dict):
        return False
    candidate = (candidate_ip or "").strip().split("/")[0]
    if not candidate or not _re.match(r"^\d+\.\d+\.\d+\.\d+$", candidate):
        return False

    reject_reasons = []

    if ops_data.get("_stale") is True:
        reject_reasons.append("record_is_stale")

    for _k in ("_stale_last_mgmt_ip", "_stale_last_ssh_host", "_stale_last_ncc_mgmt_ip"):
        _v = (ops_data.get(_k) or "").strip().split("/")[0]
        if _v and _v == candidate:
            reject_reasons.append(f"matches_reaped_{_k}")

    if ops_data.get("ncc_type") == "kvm":
        _kvm_ip = (ops_data.get("kvm_host_ip") or "").strip().split("/")[0]
        _ncc_ip = (ops_data.get("ncc_mgmt_ip") or "").strip().split("/")[0]
        if _kvm_ip and candidate == _kvm_ip and (_ncc_ip and candidate != _ncc_ip):
            reject_reasons.append("candidate_is_kvm_host_ip")

    if reject_reasons:
        try:
            from datetime import datetime as _dt, timezone as _tz
            rejections = ops_data.get("_mgmt_ip_rejections")
            if not isinstance(rejections, list):
                rejections = []
            rejections.append({
                "at": _dt.now(_tz.utc).isoformat(),
                "candidate": candidate,
                "source": source or "unknown",
                "reasons": reject_reasons,
            })
            ops_data["_mgmt_ip_rejections"] = rejections[-20:]
        except Exception:
            pass
        _logging.info(
            "[safe_mgmt_ip] rejected %s from %s: %s",
            candidate, source or "?", ",".join(reject_reasons),
        )
        return False

    _prev_mgmt_ip = (ops_data.get("mgmt_ip") or "").strip().split("/")[0]
    ops_data["mgmt_ip"] = candidate
    _gi_state = (ops_data.get("device_state") or "").upper()
    _has_ncc_ip = (ops_data.get("ncc_mgmt_ip") or "").strip().split("/")[0]
    if _gi_state in ("GI", "BASEOS_SHELL", "RECOVERY") and _has_ncc_ip:
        ops_data["ssh_host"] = _has_ncc_ip
    else:
        ops_data["ssh_host"] = candidate

    # When the IP actually changes (post-deploy/post-delete-and-redeploy),
    # flush the live device-mode resolver cache for this device so the
    # next probe re-walks discovery instead of dialing the old address.
    # ``_resolve_cache`` is the bridge_helpers IP-resolver cache; we only
    # need to touch the device-mode resolver here.
    if candidate != _prev_mgmt_ip:
        _device_id_for_resolver = (
            ops_data.get("device_id")
            or ops_data.get("scaler_id")
            or ops_data.get("hostname")
            or ""
        )
        if _device_id_for_resolver:
            try:
                from routes._device_mode_resolver import invalidate as _devmode_invalidate
                _devmode_invalidate(_device_id_for_resolver, _device_id_for_resolver)
            except Exception:
                pass
    return True


def _fetch_config_via_ssh(device_id: str, mgmt_ip: str, user: str, password: str) -> str:
    """Fetch running config via SSH using scaler ConfigExtractor."""
    from scaler.models import Device
    from scaler.config_extractor import InteractiveExtractor

    device = Device(
        id=device_id,
        hostname=device_id,
        ip=mgmt_ip,
        username=user,
        password=Device.encode_password(password),
    )
    config_dir = Path(SCALER_ROOT) / "db" / "configs" / device_id
    config_dir.mkdir(parents=True, exist_ok=True)
    ops_file = config_dir / "operational.json"
    from routes._ops_writer import update_ops as _uops_fetch_cfg

    def _mut_fetch_cfg(d):
        _safe_set_mgmt_ip(d, mgmt_ip, source="_fetch_config_via_ssh")

    _uops_fetch_cfg(ops_file, _mut_fetch_cfg, create_if_missing=True)

    with InteractiveExtractor(device, timeout=180) as extractor:
        return extractor.get_running_config(fetch_lldp=False)


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from terminal output."""
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)


def _parse_lldp_table(raw: str) -> list:
    """Parse ``show lldp neighbor(s)`` output into canonical dicts.

    Handles both pipe-separated and space-aligned DNOS table formats.
    Returns list of ``{"local": ..., "neighbor": ..., "remote": ...}``.
    """
    neighbors: list[dict] = []
    in_table = False
    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if "Interface" in stripped and "Neighbor" in stripped:
            in_table = True
            continue
        if stripped.startswith("---") or "|-" in stripped or "-|" in stripped:
            continue
        if re.match(r"^[A-Za-z0-9_.-]+[#>]", stripped) or re.match(r"^[A-Za-z0-9_.-]+\(", stripped):
            in_table = False
            continue
        if not in_table:
            continue
        if "|" in stripped:
            parts = [p.strip() for p in stripped.split("|") if p.strip()]
        else:
            parts = re.split(r"\s{2,}", stripped)
        if len(parts) < 3:
            continue
        local_if, nbr_dev, nbr_port = parts[0], parts[1], parts[2]
        if not local_if or local_if.lower().startswith("interface"):
            continue
        if not nbr_dev or nbr_dev in ("Neighbor", "Neighbor System Name", "-", ""):
            continue
        neighbors.append({"local": local_if, "neighbor": nbr_dev, "remote": nbr_port})
    return neighbors


def _normalize_lldp_neighbor(n: dict) -> dict:
    """Convert any LLDP neighbor dict variant into canonical ``{local, neighbor, remote}``."""
    return {
        "local": (
            n.get("local")
            or n.get("local_interface")
            or n.get("interface")
            or ""
        ),
        "neighbor": (
            n.get("neighbor")
            or n.get("neighbor_name")
            or n.get("neighbor_device")
            or ""
        ),
        "remote": (
            n.get("remote")
            or n.get("neighbor_interface")
            or n.get("remote_port")
            or n.get("neighbor_port")
            or ""
        ),
    }


def _empty_protocol_ops() -> dict:
    return {
        "bgp_neighbors": [],
        "isis": {},
        "ospf": {},
        "ldp": {},
    }


def _has_protocol_ops(protocols: dict) -> bool:
    if not isinstance(protocols, dict):
        return False
    if protocols.get("bgp_neighbors"):
        return True
    for key in ("isis", "ospf", "ldp"):
        if protocols.get(key):
            return True
    return False


def _parse_protocol_operational_outputs(outputs: dict) -> dict:
    """Parse verified protocol operational commands for scaler monitor context."""
    protocols = _empty_protocol_ops()
    try:
        from telemetry.config_parser import (
            parse_bgp_summary,
            parse_isis_neighbors,
            parse_ldp_neighbors,
            parse_ospf_neighbors,
        )

        bgp = parse_bgp_summary(outputs.get("show bgp summary", ""))
        protocols["bgp_neighbors"] = [
            (nbr.model_dump() if hasattr(nbr, "model_dump") else nbr.dict())
            for nbr in bgp.values()
        ]
        protocols["isis"] = parse_isis_neighbors(outputs.get("show isis neighbors", ""))
        protocols["ospf"] = parse_ospf_neighbors(outputs.get("show ospf neighbors", ""))
        protocols["ldp"] = parse_ldp_neighbors(outputs.get("show ldp neighbors detail", ""))
    except Exception as exc:
        logging.info("[protocol-ops] parse failed: %s", exc)
    return protocols


def _parse_stack_table_lines(raw: str) -> list:
    """Parse ``show system stack`` table text into component dicts."""
    components = []
    for line in raw.split("\n"):
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7:
            continue
        name = parts[1]
        if not name or name.upper() in ("COMPONENT", "---", ""):
            continue
        if name.startswith("-"):
            continue
        components.append({
            "name": name,
            "hw_model": parts[2] if len(parts) > 2 else "-",
            "revert": parts[4] if len(parts) > 4 else "-",
            "current": parts[5] if len(parts) > 5 else "-",
            "target": parts[6] if len(parts) > 6 else "-",
        })
    return components


def _fetch_stack_via_ssh(mgmt_ip: str, user: str, password: str) -> list:
    """SSH to device, run 'show system stack | no-more', parse and return components."""
    from routes._device_comm import DeviceCommHelper

    comm = DeviceCommHelper()
    raw = comm.run_show_ip(mgmt_ip, user, password, "show system stack", timeout=60)
    if "[SSH ERROR]" in raw:
        return []
    return _parse_stack_table_lines(_strip_ansi(raw))


def _recv_until(channel, markers, timeout_s=15):
    """Read channel until any marker string is found in output, or timeout.
    Polls at 50ms intervals -- no wasted time on fixed sleeps."""
    import time
    buf = ""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if channel.recv_ready():
            buf += channel.recv(65535).decode("utf-8", errors="replace")
            for m in markers:
                if m in buf:
                    return buf
        time.sleep(0.05)
    return buf


def _fetch_git_commit_via_ssh(mgmt_ip: str, user: str, password: str,
                              scaler_device_id: str = "",
                              app_user: str = "default") -> str | None:
    """SSH to device, run start shell + cat /.gitcommit, return hash.
    Falls back to virsh console for cluster devices when direct SSH fails."""
    from scaler.dnos_session import DNOSSession

    try:
        client = _ssh_pool.get_client(mgmt_ip, user, password, app_user=app_user)
    except Exception:
        client = None
    if not client:
        if scaler_device_id:
            result = _fetch_ops_via_virsh_fallback(scaler_device_id, user, password)
            gc = result.get("git_commit")
            if gc:
                try:
                    _ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id / "operational.json"
                    from routes._ops_writer import update_ops as _uops_gc

                    def _mut_gc(d, _gc=gc, _stack=result.get("stack")):
                        d["git_commit"] = _gc
                        if _stack:
                            d["stack_components"] = _stack

                    _uops_gc(_ops_path, _mut_gc, create_if_missing=False)
                except Exception:
                    pass
            return gc
        return None
    _user_pooled = _ssh_pool._user_enabled(app_user)
    owns = not _user_pooled
    try:
        with DNOSSession(
            mgmt_ip, user, password, client=client, owns_client=owns,
        ) as sess:
            sess.send_raw("run start shell\r\n")
            sess.recv_until_markers(["assword"], timeout_s=8)
            sess.send_raw(password + "\r\n")
            shell_out = sess.recv_until_markers(
                ["root@", "$ ", "denied", "ERROR"], timeout_s=8,
            )
            if "denied" in shell_out.lower() or "ERROR" in shell_out:
                return None
            sess.send_raw("cat /.gitcommit\r\n")
            raw = _strip_ansi(sess.recv_until_markers(["#", "$ "], timeout_s=5))
            for line in raw.split("\n"):
                line = line.strip()
                if not line or line.startswith("cat ") or line.endswith("#") or line.endswith("$"):
                    continue
                if "No such file" in line or "Permission denied" in line:
                    continue
                m = re.match(r"^([a-fA-F0-9]{7,40}(?:-\S+)?)$", line)
                if m:
                    return m.group(1)
            return None
    except Exception:
        return None
    finally:
        if _user_pooled:
            _ssh_pool.release(mgmt_ip, app_user=app_user)
        elif owns:
            try:
                client.close()
            except Exception:
                pass


def _fetch_all_operational_via_ssh(mgmt_ip: str, user: str, password: str,
                                   scaler_device_id: str = "",
                                   app_user: str = "default") -> dict:
    """Single SSH session for LLDP + protocol states + stack + git_commit + device_state.
    Uses DNOSSession. Uses pool when enabled.
    Falls back to virsh console for cluster (KVM) devices when direct SSH fails.

    Diagnostics: every major step is logged with the ``[STACK-TIMING]`` tag
    so a slow refresh on a cluster device can be debugged by simply
    grepping the bridge log for that tag. Each line carries the device id
    + caller-visible step name + elapsed-ms-since-this-call-began so it
    is trivial to reconstruct where the time went.
    """
    import time as _time

    from scaler.connection_strategy import detect_device_mode
    from scaler.dnos_session import DNOSSession

    _t0 = _time.time()
    _tag = scaler_device_id or mgmt_ip

    def _step(label, t_start):
        elapsed_ms = int((_time.time() - t_start) * 1000)
        total_ms = int((_time.time() - _t0) * 1000)
        logging.info(
            "[STACK-TIMING] %s direct-ssh step=%s dt=%dms total=%dms",
            _tag, label, elapsed_ms, total_ms,
        )

    logging.info(
        "[STACK-TIMING] %s direct-ssh BEGIN mgmt_ip=%s app_user=%s",
        _tag, mgmt_ip, app_user,
    )

    result = {
        "lldp": [],
        "stack": [],
        "git_commit": None,
        "device_state": None,
        "protocols": _empty_protocol_ops(),
    }
    _t = _time.time()
    try:
        client = _ssh_pool.get_client(mgmt_ip, user, password, app_user=app_user)
    except Exception as exc:
        logging.info("[STACK-TIMING] %s ssh_pool.get_client raised: %s", _tag, exc)
        client = None
    _step("ssh_pool.get_client", _t)
    if not client:
        if scaler_device_id:
            logging.info(
                "[STACK-TIMING] %s direct-ssh -> falling back to virsh (no client)",
                _tag,
            )
            return _fetch_ops_via_virsh_fallback(scaler_device_id, user, password)
        logging.info("[STACK-TIMING] %s direct-ssh ABORT no client + no scaler_id", _tag)
        return result
    _user_pooled = _ssh_pool._user_enabled(app_user)
    owns = not _user_pooled
    try:
        with DNOSSession(
            mgmt_ip, user, password, client=client, owns_client=owns,
        ) as sess:
            _t = _time.time()
            sess.send_raw("\r\n")
            mode_buf = sess.recv_until_markers(["#", ">"], timeout_s=5)
            detected = detect_device_mode(mode_buf)
            if detected:
                result["device_state"] = detected
            _step(f"mode_probe({detected or 'unknown'})", _t)

            _t = _time.time()
            raw_lldp = sess.send_command("show lldp neighbors", timeout=10)
            result["lldp"] = _parse_lldp_table(_strip_ansi(raw_lldp))
            _step(f"show_lldp_neighbors(rows={len(result['lldp'])})", _t)

            protocol_outputs = {}
            for command in (
                "show bgp summary",
                "show isis neighbors",
                "show ospf neighbors",
                "show ldp neighbors detail",
            ):
                _t = _time.time()
                try:
                    protocol_outputs[command] = _strip_ansi(sess.send_command(command, timeout=12))
                except Exception as exc:
                    logging.info("[STACK-TIMING] %s %s raised: %s", _tag, command.replace(" ", "_"), exc)
                    protocol_outputs[command] = ""
                _step(command.replace(" ", "_"), _t)
            result["protocols"] = _parse_protocol_operational_outputs(protocol_outputs)

            _t = _time.time()
            raw_stack = sess.send_command("show system stack", timeout=10)
            result["stack"] = _parse_stack_table_lines(_strip_ansi(raw_stack))
            _step(f"show_system_stack(rows={len(result['stack'])})", _t)

            _t = _time.time()
            try:
                raw_sys = sess.send_command("show system", timeout=10)
                for line in _strip_ansi(raw_sys).split("\n"):
                    cols = line.split()
                    if len(cols) >= 5 and cols[1].lower() == "ncc" and cols[4].lower() == "active":
                        result["active_ncc_node"] = cols[0]
                        break
            except Exception as exc:
                logging.info("[STACK-TIMING] %s show_system raised: %s", _tag, exc)
            _step(f"show_system(active_ncc={result.get('active_ncc_node','')})", _t)

            _t = _time.time()
            sess.send_raw("run start shell\r\n")
            sess.recv_until_markers(["assword"], timeout_s=8)
            sess.send_raw(password + "\r\n")
            shell_out = sess.recv_until_markers(
                ["root@", "$ ", "denied", "ERROR"], timeout_s=8,
            )
            _step("run_start_shell", _t)
            if "denied" not in shell_out.lower() and "ERROR" not in shell_out:
                _t = _time.time()
                sess.send_raw("cat /.gitcommit\r\n")
                raw = _strip_ansi(sess.recv_until_markers(["#", "$ "], timeout_s=5))
                for line in raw.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("cat ") or line.endswith("#") or line.endswith("$"):
                        continue
                    if "No such file" in line or "Permission denied" in line:
                        continue
                    m = re.match(r"^([a-fA-F0-9]{7,40}(?:-\S+)?)$", line)
                    if m:
                        result["git_commit"] = m.group(1)
                        break
                _step(f"cat_gitcommit(={result.get('git_commit') or 'none'})", _t)

            logging.info(
                "[STACK-TIMING] %s direct-ssh END total=%dms stack=%d lldp=%d bgp=%d",
                _tag, int((_time.time() - _t0) * 1000),
                len(result["stack"]), len(result["lldp"]),
                len(result.get("protocols", {}).get("bgp_neighbors") or []),
            )
            return result
    except Exception as exc:
        logging.info(
            "[STACK-TIMING] %s direct-ssh EXCEPTION total=%dms err=%s",
            _tag, int((_time.time() - _t0) * 1000), exc,
        )
        return result
    finally:
        if _user_pooled:
            _ssh_pool.release(mgmt_ip, app_user=app_user)
        elif owns:
            try:
                client.close()
            except Exception:
                pass


def _fetch_stack_only_via_ssh(mgmt_ip: str, user: str, password: str,
                              scaler_device_id: str = "",
                              app_user: str = "default") -> dict:
    """Fast-path for the Stack dialog Refresh button.

    Only runs the two commands the dialog actually renders:
    ``show system stack | no-more`` and ``show system | no-more``. No
    LLDP, no shell-into-baseos for ``/.gitcommit``, no config pull.
    On a healthy active NCC this finishes in 4-8 s vs 15-25 s for
    :func:`_fetch_all_operational_via_ssh`, and stays well within the
    50-s frontend timeout even on a busy active NCC.

    The helper ALSO persists the freshly read state into
    ``operational.json`` so subsequent cached reads are also fresh:

      * ``stack_components``         (the list rendered in the dialog)
      * ``device_state``             (DNOS / GI / RECOVERY)
      * ``stack_fetched_at``         (ISO timestamp, for the "fresh"/
                                      "stale" badge in the dialog)
      * ``active_ncc_vm``            (for cluster devices, derived from
                                      ``show system``; lets the next
                                      virsh-fallback skip the standby
                                      dance)
      * ``active_ncc_last_good_at``  (refreshed timestamp for the LKG
                                      memo so even non-virsh refreshes
                                      keep the cluster's LKG warm)

    Background pollers and the full-context path keep handling LLDP,
    git_commit and system_type so the freshness guarantees of those
    fields are unchanged.

    Returns dict::

        {
            "stack":                [{name, hw_model, revert, current, target}, ...],
            "device_state":         "DNOS" | "GI" | "RECOVERY" | None,
            "active_ncc_node":      str | None,
            "stack_fetched_at":     ISO-8601 str,
            "raw_output":           str,           # only populated on parse failure
        }

    All major steps emit ``[STACK-TIMING]`` log lines so the bridge log
    is the single source of truth for refresh timings.
    """
    import time as _time
    from datetime import datetime as _dt, timezone as _tz

    from scaler.connection_strategy import detect_device_mode
    from scaler.dnos_session import DNOSSession

    _t0 = _time.time()
    _tag = scaler_device_id or mgmt_ip

    def _step(label, t_start):
        elapsed_ms = int((_time.time() - t_start) * 1000)
        total_ms = int((_time.time() - _t0) * 1000)
        logging.info(
            "[STACK-TIMING] %s stack-fast step=%s dt=%dms total=%dms",
            _tag, label, elapsed_ms, total_ms,
        )

    logging.info(
        "[STACK-TIMING] %s stack-fast BEGIN mgmt_ip=%s app_user=%s",
        _tag, mgmt_ip, app_user,
    )

    result = {
        "stack": [],
        "device_state": None,
        "active_ncc_node": None,
        "stack_fetched_at": "",
        "raw_output": "",
    }

    _t = _time.time()
    try:
        client = _ssh_pool.get_client(mgmt_ip, user, password, app_user=app_user)
    except Exception as exc:
        logging.info("[STACK-TIMING] %s stack-fast ssh_pool.get_client raised: %s", _tag, exc)
        client = None
    _step("ssh_pool.get_client", _t)
    if not client:
        logging.info("[STACK-TIMING] %s stack-fast ABORT no client", _tag)
        return result

    _user_pooled = _ssh_pool._user_enabled(app_user)
    owns = not _user_pooled
    raw_stack = ""
    raw_sys = ""
    try:
        with DNOSSession(
            mgmt_ip, user, password, client=client, owns_client=owns,
        ) as sess:
            _t = _time.time()
            sess.send_raw("\r\n")
            mode_buf = sess.recv_until_markers(["#", ">"], timeout_s=5)
            detected = detect_device_mode(mode_buf)
            if detected:
                result["device_state"] = detected
            _step(f"mode_probe({detected or 'unknown'})", _t)

            _t = _time.time()
            try:
                raw_stack = sess.send_command("show system stack", timeout=10)
                result["stack"] = _parse_stack_table_lines(_strip_ansi(raw_stack))
            except Exception as exc:
                logging.info("[STACK-TIMING] %s stack-fast show_system_stack raised: %s", _tag, exc)
            _step(f"show_system_stack(rows={len(result['stack'])})", _t)

            _t = _time.time()
            try:
                raw_sys = sess.send_command("show system", timeout=10)
                for line in _strip_ansi(raw_sys).split("\n"):
                    cols = line.split()
                    if len(cols) >= 5 and cols[1].lower() == "ncc" and cols[4].lower() == "active":
                        result["active_ncc_node"] = cols[0]
                        break
            except Exception as exc:
                logging.info("[STACK-TIMING] %s stack-fast show_system raised: %s", _tag, exc)
            _step(f"show_system(active_ncc={result.get('active_ncc_node') or ''})", _t)
    except Exception as exc:
        logging.info(
            "[STACK-TIMING] %s stack-fast EXCEPTION total=%dms err=%s",
            _tag, int((_time.time() - _t0) * 1000), exc,
        )
        if not result["stack"]:
            result["raw_output"] = (raw_stack or raw_sys or str(exc))[-2000:]
        return result
    finally:
        if _user_pooled:
            _ssh_pool.release(mgmt_ip, app_user=app_user)
        elif owns:
            try:
                client.close()
            except Exception:
                pass

    now_iso = _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result["stack_fetched_at"] = now_iso

    # ------------------------------------------------------------------
    # Persist into operational.json so the next cached read is fresh.
    # ------------------------------------------------------------------
    # We touch ONLY the four scalar fields the dialog cares about plus
    # the LKG memo. We deliberately do NOT touch lldp_neighbors or
    # git_commit -- those are the responsibility of the full-context
    # path / background poller, and overwriting them here with stale
    # values would regress freshness for the canvas.
    try:
        if scaler_device_id and result["stack"]:
            ops_path = (
                Path(SCALER_ROOT) / "db" / "configs"
                / scaler_device_id / "operational.json"
            )
            from routes._ops_writer import update_ops as _uops_stack_fast

            # Re-seed cluster metadata from console_mappings BEFORE we
            # persist. ``scaler-monitor`` rewrites operational.json
            # every ~5 minutes and -- when its source dataset doesn't
            # carry the cluster fields -- it wipes ``ncc_type`` /
            # ``ncc_vms`` / ``kvm_host*``. Without this re-seed our
            # LKG memo refresh below would be a no-op (the mutator
            # exits early when ``ncc_type != "kvm"``), wasting the
            # benefit of having SSH'd to the active NCC. Seeding
            # right before the write closes a 5-minute window where
            # virsh-fallback would otherwise have to start with the
            # wrong NCC.
            try:
                _seed_cluster_metadata_from_mappings(scaler_device_id)
            except Exception as exc:
                logging.info(
                    "[STACK-TIMING] %s stack-fast pre-seed raised: %s",
                    _tag, exc,
                )

            stack_components = list(result["stack"])
            device_state = result.get("device_state")
            active_ncc_node = result.get("active_ncc_node") or ""

            def _mut_stack_fast(d):
                # Stack table -- always write when we got rows.
                d["stack_components"] = stack_components
                d["stack_fetched_at"] = now_iso
                if device_state:
                    d["device_state"] = device_state
                # Cluster LKG refresh: only when the device is a KVM
                # cluster (ncc_type=kvm) AND we successfully resolved
                # an NCC name from `show system`. ``active_ncc_node``
                # is the device-internal name (ncc0/ncc1); the LKG
                # memo uses the VM hostname (kvm108-cl408d-ncc0/1) so
                # we need to bridge the two via the cluster_ncc_access
                # mapping that the bridge already keeps in sync.
                if d.get("ncc_type") != "kvm":
                    return
                ncc_vms = list(d.get("ncc_vms") or [])
                if not ncc_vms or not active_ncc_node:
                    # Even without NCC->VM mapping, refresh LKG when
                    # the existing active_ncc_vm is sane. A successful
                    # SSH to the VIP proves the cluster's currently
                    # stored active is still hosting DNOS, which is
                    # the only thing the LKG memo needs.
                    if d.get("active_ncc_vm") in ncc_vms:
                        d["active_ncc_last_good_at"] = now_iso
                    return
                # Map device-internal name -> VM hostname using the
                # convention DNOS reports `ncc0` / `ncc1` and the VM
                # hostnames end in `-ncc0` / `-ncc1`.
                want_suffix = "-" + active_ncc_node.lower()
                matched_vm = ""
                for vm in ncc_vms:
                    if vm.lower().endswith(want_suffix):
                        matched_vm = vm
                        break
                if matched_vm:
                    d["active_ncc_vm"] = matched_vm
                    d["active_ncc_source"] = "stack_fast"
                    d["active_ncc_last_good_at"] = now_iso
                elif d.get("active_ncc_vm") in ncc_vms:
                    # Couldn't map but the existing pointer is sane.
                    d["active_ncc_last_good_at"] = now_iso

            ok, _ = _uops_stack_fast(ops_path, _mut_stack_fast)
            logging.info(
                "[STACK-TIMING] %s stack-fast persisted ok=%s components=%d active=%s",
                _tag, ok, len(stack_components), active_ncc_node or "-",
            )
    except Exception as exc:
        logging.info("[STACK-TIMING] %s stack-fast persist raised: %s", _tag, exc)

    logging.info(
        "[STACK-TIMING] %s stack-fast END total=%dms stack=%d state=%s active=%s",
        _tag, int((_time.time() - _t0) * 1000),
        len(result["stack"]), result.get("device_state") or "-",
        result.get("active_ncc_node") or "-",
    )
    return result


def _fetch_ops_via_virsh_fallback(scaler_device_id: str, user: str, password: str) -> dict:
    """Fetch LLDP/stack/git_commit via virsh console when direct SSH is unavailable.
    Used for cluster (KVM) devices where the NCC doesn't accept direct SSH.
    Tries each NCC VM until one has an active CLI (handles stale active_ncc_vm).

    Diagnostics: every NCC iteration is wrapped with ``[STACK-TIMING]``
    log lines so a slow refresh (a wrong-NCC dance, a stalled
    show-command, etc.) is trivially diagnosable from the bridge log
    without re-running with a debugger attached.

    Active-NCC memoization: if ``operational.json`` records a
    ``active_ncc_last_good_at`` ISO timestamp newer than NCC_LKG_TTL_S
    seconds and the matching ``active_ncc_vm`` is in the NCC list, that
    NCC is the ONLY one tried. Fast path for clusters that flip rarely.
    Falls through to the full standby-dance only when the LKG is stale,
    missing, or the trusted NCC fails this attempt. Saves 10-15s on
    every cluster refresh once one warm-up has succeeded.
    """
    import time as _time
    from datetime import datetime, timezone

    from scaler.connection_strategy import detect_device_mode

    _t0 = _time.time()
    _tag = scaler_device_id

    def _step(label, t_start, ncc=""):
        elapsed_ms = int((_time.time() - t_start) * 1000)
        total_ms = int((_time.time() - _t0) * 1000)
        suffix = f" ncc={ncc}" if ncc else ""
        logging.info(
            "[STACK-TIMING] %s virsh step=%s%s dt=%dms total=%dms",
            _tag, label, suffix, elapsed_ms, total_ms,
        )

    logging.info("[STACK-TIMING] %s virsh BEGIN", _tag)

    result = {
        "lldp": [],
        "stack": [],
        "git_commit": None,
        "device_state": None,
        "protocols": _empty_protocol_ops(),
    }
    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id / "operational.json"
    if not ops_path.exists():
        logging.info("[STACK-TIMING] %s virsh ABORT: no operational.json", _tag)
        return result
    try:
        ops = _read_ops_safe(ops_path)
    except Exception as exc:
        logging.info("[STACK-TIMING] %s virsh ABORT: read_ops_safe raised: %s", _tag, exc)
        return result
    if ops.get("ncc_type") != "kvm":
        logging.info(
            "[STACK-TIMING] %s virsh ABORT: ncc_type=%s (not kvm)",
            _tag, ops.get("ncc_type"),
        )
        return result

    kvm_host = ops.get("kvm_host_ip") or ops.get("kvm_host") or ""
    kvm_creds = ops.get("kvm_host_credentials") or {}
    kvm_user = kvm_creds.get("username", "dn")
    kvm_pass = kvm_creds.get("password", "drive1234!")
    ncc_vms = ops.get("ncc_vms") or []
    stored_active = ops.get("active_ncc_vm") or ""
    last_good_at = ops.get("active_ncc_last_good_at") or ""

    if not kvm_host:
        logging.info("[STACK-TIMING] %s virsh ABORT: no kvm_host", _tag)
        return result

    # ------------------------------------------------------------------
    # Active-NCC memoization
    # ------------------------------------------------------------------
    # When a previous virsh probe landed on the active NCC AND succeeded
    # within NCC_LKG_TTL_S seconds, trust it and skip the standby-dance.
    # Cluster active NCC swaps are rare (manual switchover or HA event)
    # so a 5-minute window is conservative and saves ~10-15s every
    # cluster refresh once we've warmed up.
    NCC_LKG_TTL_S = 300  # 5 minutes
    lkg_fresh = False
    if last_good_at and stored_active and stored_active in ncc_vms:
        try:
            # Accept both Z-suffix and offset-aware ISO formats.
            ts = last_good_at.replace("Z", "+00:00")
            t_lkg = datetime.fromisoformat(ts)
            if t_lkg.tzinfo is None:
                t_lkg = t_lkg.replace(tzinfo=timezone.utc)
            age_s = (datetime.now(timezone.utc) - t_lkg).total_seconds()
            if 0 <= age_s <= NCC_LKG_TTL_S:
                lkg_fresh = True
                logging.info(
                    "[STACK-TIMING] %s virsh LKG fresh: active_ncc_vm=%s age=%.0fs <= %ds",
                    _tag, stored_active, age_s, NCC_LKG_TTL_S,
                )
        except Exception as exc:
            logging.info(
                "[STACK-TIMING] %s virsh LKG parse failed (%s); treating as stale",
                _tag, exc,
            )

    # Build ordered NCC list:
    #   * fresh LKG -> only the trusted active (cluster fast path)
    #   * else      -> stored_active first, then the other NCCs
    try_order = []
    if lkg_fresh:
        try_order = [stored_active]
    else:
        if stored_active and stored_active in ncc_vms:
            try_order.append(stored_active)
        for vm in ncc_vms:
            if vm not in try_order:
                try_order.append(vm)
    if not try_order:
        try_order = [""]

    logging.info(
        "[STACK-TIMING] %s virsh try_order=%s lkg_fresh=%s",
        _tag, try_order, lkg_fresh,
    )

    for ncc_vm in try_order:
        _t_ncc = _time.time()
        logging.info("[virsh-ops] Trying NCC %s for %s via KVM %s",
                     ncc_vm or "(auto)", scaler_device_id, kvm_host)
        ssh = None
        try:
            _t = _time.time()
            ssh, channel, buf = _open_virsh_ncc_shell_channel(
                kvm_host, kvm_user, kvm_pass, ncc_vms, ncc_vm
            )
            channel.settimeout(15)
            _step("open_virsh_console", _t, ncc=ncc_vm)

            initial_text = buf.decode("utf-8", errors="replace") if isinstance(buf, (bytes, bytearray)) else str(buf)
            last_line = initial_text.rstrip().split("\n")[-1].strip() if initial_text.rstrip() else ""
            if last_line.endswith("$") and "#" not in last_line:
                logging.info("[virsh-ops] NCC %s is in bash (standby?), skipping", ncc_vm)
                _step("standby_skip", _t_ncc, ncc=ncc_vm)
                ssh.close()
                ssh = None
                continue

            detected = detect_device_mode(initial_text)
            if detected:
                result["device_state"] = detected

            def _send_and_recv(ch, cmd, wait=10):
                ch.send(cmd + " | no-more\n")
                _time.sleep(1.5)
                out = b""
                deadline = _time.time() + wait
                while _time.time() < deadline:
                    if ch.recv_ready():
                        out += ch.recv(65535)
                    full_text = out.decode("utf-8", errors="replace")
                    lines = full_text.rstrip().split("\n")
                    last_line = lines[-1].strip() if lines else ""
                    if len(lines) > 2 and (last_line.endswith("#") or last_line.endswith(">")):
                        if "More" not in last_line:
                            _time.sleep(0.3)
                            if ch.recv_ready():
                                out += ch.recv(65535)
                            break
                    _time.sleep(0.3)
                return _strip_ansi(out.decode("utf-8", errors="replace"))

            _t = _time.time()
            raw_stack = _send_and_recv(channel, "show system stack", wait=12)
            result["stack"] = _parse_stack_table_lines(raw_stack)
            _step(f"show_system_stack(rows={len(result['stack'])})", _t, ncc=ncc_vm)

            if not result["stack"]:
                logging.info("[virsh-ops] No stack from NCC %s, trying next", ncc_vm)
                _step("empty_stack_skip", _t_ncc, ncc=ncc_vm)
                ssh.close()
                ssh = None
                continue

            if not result["device_state"]:
                detected = detect_device_mode(raw_stack)
                if detected:
                    result["device_state"] = detected

            _t = _time.time()
            raw_lldp = _send_and_recv(channel, "show lldp neighbors", wait=20)
            result["lldp"] = _parse_lldp_table(raw_lldp)
            _step(f"show_lldp_neighbors(rows={len(result['lldp'])})", _t, ncc=ncc_vm)

            protocol_outputs = {}
            for command in (
                "show bgp summary",
                "show isis neighbors",
                "show ospf neighbors",
                "show ldp neighbors detail",
            ):
                _t = _time.time()
                try:
                    protocol_outputs[command] = _send_and_recv(channel, command, wait=18)
                except Exception as exc:
                    logging.info("[virsh-ops] %s failed on %s: %s", command, ncc_vm, exc)
                    protocol_outputs[command] = ""
                _step(command.replace(" ", "_"), _t, ncc=ncc_vm)
            result["protocols"] = _parse_protocol_operational_outputs(protocol_outputs)

            _t = _time.time()
            try:
                channel.send("run start shell\r\n")
                _time.sleep(2)
                shell_buf = b""
                shell_deadline = _time.time() + 10
                while _time.time() < shell_deadline:
                    if channel.recv_ready():
                        shell_buf += channel.recv(65535)
                    shell_text = shell_buf.decode("utf-8", errors="replace").lower()
                    if "assword" in shell_text or "root@" in shell_text or "$ " in shell_text:
                        break
                    _time.sleep(0.3)
                shell_decoded = shell_buf.decode("utf-8", errors="replace").lower()
                if "assword" in shell_decoded:
                    cli_pass = password or "dnroot"
                    channel.send(cli_pass + "\r\n")
                    _time.sleep(2)
                    shell_buf2 = b""
                    sd2 = _time.time() + 8
                    while _time.time() < sd2:
                        if channel.recv_ready():
                            shell_buf2 += channel.recv(65535)
                        t2 = shell_buf2.decode("utf-8", errors="replace")
                        if "root@" in t2 or "$ " in t2:
                            break
                        _time.sleep(0.3)
                channel.send("cat /.gitcommit 2>/dev/null\r\n")
                _time.sleep(1.5)
                gc_buf = b""
                gc_deadline = _time.time() + 5
                while _time.time() < gc_deadline:
                    if channel.recv_ready():
                        gc_buf += channel.recv(65535)
                    gc_text = gc_buf.decode("utf-8", errors="replace")
                    if "root@" in gc_text or "$ " in gc_text or "#" in gc_text:
                        break
                    _time.sleep(0.3)
                gc_decoded = _strip_ansi(gc_buf.decode("utf-8", errors="replace"))
                for gc_line in gc_decoded.split("\n"):
                    gc_line = gc_line.strip()
                    if not gc_line or gc_line.startswith("cat ") or gc_line.endswith("#") or gc_line.endswith("$"):
                        continue
                    if "No such file" in gc_line or "Permission" in gc_line:
                        continue
                    gc_match = re.match(r"^([a-fA-F0-9]{7,40}(?:-\S+)?)$", gc_line)
                    if gc_match:
                        result["git_commit"] = gc_match.group(1)
                        break
                channel.send("exit\r\n")
                _time.sleep(0.5)
            except Exception as gc_err:
                logging.warning("[virsh-ops] git_commit fetch failed for %s: %s", scaler_device_id, gc_err)
            _step(f"shell_gitcommit(={result.get('git_commit') or 'none'})", _t, ncc=ncc_vm)

            # Update active_ncc_vm if it changed AND stamp a Last-Known-Good
            # timestamp so subsequent refreshes inside NCC_LKG_TTL_S can
            # take the cluster fast path (skip the standby-NCC dance).
            #
            # Tag the source as ``kvm_virsh_probe`` so downstream ctx
            # resolution in ``_get_device_context`` trusts this over the
            # port-22 scan -- the scan is unreliable in GI mode where
            # BOTH NCC VMs may have sshd up on baseos, so a simple port
            # check picks whichever one answered first rather than the
            # real active cluster member. Virsh console probe is
            # authoritative: only the active NCC's console gives the
            # GI CLI prompt; standby shows bash and "dncli" errors out.
            _ops_changed = False
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if ncc_vm and ncc_vm != stored_active:
                ops["active_ncc_vm"] = ncc_vm
                _ops_changed = True
            _prev_source = (ops.get("active_ncc_source") or "").strip()
            if ncc_vm and _prev_source != "kvm_virsh_probe":
                ops["active_ncc_source"] = "kvm_virsh_probe"
                _ops_changed = True
            # Always refresh the LKG stamp on success so the 5-minute
            # window slides with each successful refresh.
            ops["active_ncc_last_good_at"] = now_iso
            _ops_changed = True
            if _ops_changed:
                try:
                    from routes._ops_writer import update_ops as _uops_virsh

                    def _mut_virsh(d, _vm=ncc_vm, _now=now_iso):
                        if _vm:
                            d["active_ncc_vm"] = _vm
                            d["active_ncc_source"] = "kvm_virsh_probe"
                        d["active_ncc_last_good_at"] = _now

                    _uops_virsh(ops_path, _mut_virsh, create_if_missing=False)
                    logging.info(
                        "[virsh-ops] Updated active_ncc_vm=%s source=kvm_virsh_probe lkg=%s",
                        ncc_vm, now_iso,
                    )
                except Exception as exc:
                    logging.info(
                        "[STACK-TIMING] %s persist active_ncc failed: %s", _tag, exc,
                    )

            logging.info("[virsh-ops] Got %d LLDP, %d stack, git=%s from NCC %s for %s",
                         len(result["lldp"]), len(result["stack"]),
                         result.get("git_commit", "N/A"), ncc_vm, scaler_device_id)
            logging.info(
                "[STACK-TIMING] %s virsh END SUCCESS ncc=%s ncc_total=%dms total=%dms",
                _tag, ncc_vm, int((_time.time() - _t_ncc) * 1000),
                int((_time.time() - _t0) * 1000),
            )
            return result
        except Exception as e:
            logging.warning("[virsh-ops] NCC %s failed: %s", ncc_vm, e)
            _step(f"ncc_exception({type(e).__name__})", _t_ncc, ncc=ncc_vm)
            if ssh:
                try:
                    ssh.close()
                except Exception:
                    pass
            continue

    logging.warning("[virsh-ops] All NCC VMs failed for %s", scaler_device_id)
    logging.info(
        "[STACK-TIMING] %s virsh END FAIL total=%dms (all NCCs failed)",
        _tag, int((_time.time() - _t0) * 1000),
    )
    return result


def _get_cached_config(device_id: str) -> str | None:
    """Read cached running config from SCALER db."""
    config_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "running.txt"
    if config_path.exists():
        return config_path.read_text()
    return None


def _build_config_summary(config: str) -> dict:
    """Parse config and build structured summary using scaler parsers."""
    try:
        from scaler.wizard.parsers import (
            parse_existing_evpn_services,
            parse_existing_multihoming,
            parse_route_targets,
            get_lo0_ip_from_config,
            get_as_number_from_config,
            get_router_id_from_config,
        )
        from scaler.wizard.parsers import extract_lldp_section, extract_lacp_section
    except ImportError as e:
        return {"error": f"Parser import failed: {e}", "raw_lines": len(config.splitlines())}

    as_num = get_as_number_from_config(config)
    system_name = ""
    try:
        from scaler.wizard.parsers import extract_hierarchy_section
        sys_section = extract_hierarchy_section(config, "system")
        if sys_section:
            nm = re.search(r"^\s+name\s+(\S+)", sys_section, re.MULTILINE)
            if nm:
                system_name = nm.group(1)
    except Exception:
        pass
    summary = {
        "lines": len(config.splitlines()),
        "system_name": system_name,
        "hostname": system_name or "",
        "loopback0_ip": get_lo0_ip_from_config(config) or "",
        "as_number": str(as_num) if as_num is not None else "",
        "router_id": get_router_id_from_config(config) or "",
        "route_targets": list(parse_route_targets(config)),
        "evpn_services": {},
        "multihoming_interfaces": 0,
    }

    try:
        evpn = parse_existing_evpn_services(config)
        summary["evpn_services"] = {k: len(v) for k, v in evpn.items()}
    except Exception:
        pass

    try:
        mh = parse_existing_multihoming(config)
        summary["multihoming_interfaces"] = len(mh)
    except Exception:
        pass

    return summary

ZOHAR_DB_SERVER = "zkeiserman-dev"
ZOHAR_DB_USER = "dn"
ZOHAR_DB_PASS = "Drive1234!"
ZOHAR_CSV_REMOTE = "/home/dn/console_db/console_devices.csv"
ZOHAR_PDU_REMOTE = "/home/dn/console_db/pdu_mapping.json"
ZOHAR_PDU_CLI_REMOTE = "/home/dn/console_db/pdu_cli_config.json"
LOCAL_CONSOLE_CSV = "/tmp/console_devices_cache.csv"
LOCAL_PDU_MAP = "/tmp/pdu_mapping_cache.json"
LOCAL_PDU_CLI_CFG = "/tmp/pdu_cli_config_cache.json"
_zohar_db_fetched_at = 0.0
ZOHAR_CACHE_TTL = 3600


def _fetch_zohar_db(force: bool = False):
    """Fetch Zohar's console DB from zkeiserman-dev via SFTP. Caches for 1 hour."""
    global _zohar_db_fetched_at
    if not force and (time.time() - _zohar_db_fetched_at) < ZOHAR_CACHE_TTL:
        if os.path.exists(LOCAL_CONSOLE_CSV) and os.path.exists(LOCAL_PDU_MAP):
            return
    import paramiko as _pmk
    try:
        c = _pmk.SSHClient()
        c.set_missing_host_key_policy(_pmk.AutoAddPolicy())
        c.connect(ZOHAR_DB_SERVER, username=ZOHAR_DB_USER, password=ZOHAR_DB_PASS,
                  timeout=10, look_for_keys=False, allow_agent=False)
        sftp = c.open_sftp()
        try:
            sftp.get(ZOHAR_CSV_REMOTE, LOCAL_CONSOLE_CSV)
        except (FileNotFoundError, IOError):
            pass
        try:
            sftp.get(ZOHAR_PDU_REMOTE, LOCAL_PDU_MAP)
        except (FileNotFoundError, IOError):
            pass
        try:
            sftp.get(ZOHAR_PDU_CLI_REMOTE, LOCAL_PDU_CLI_CFG)
        except (FileNotFoundError, IOError):
            pass
        sftp.close()
        c.close()
        _zohar_db_fetched_at = time.time()
    except Exception as e:
        logging.warning(f"[ConsoleDB] Failed to fetch from {ZOHAR_DB_SERVER}: {e}")


def _lookup_zohar_console(serial: str) -> tuple:
    """Look up console server and port from Zohar's CSV by serial. Returns (server, port) or (None, None)."""
    import csv
    if not os.path.exists(LOCAL_CONSOLE_CSV):
        return None, None
    serial_upper = serial.strip().upper()
    with open(LOCAL_CONSOLE_CSV, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 3 and row[2].strip().upper() == serial_upper:
                return row[0].strip(), row[1].strip()
    return None, None


def _lookup_zohar_pdu(serial: str) -> list:
    """Look up PDU mapping from Zohar's DB. Returns list of {pdu, outlet} dicts or []."""
    if not os.path.exists(LOCAL_PDU_MAP):
        return []
    serial_upper = serial.strip().upper()
    try:
        with open(LOCAL_PDU_MAP) as f:
            data = json.load(f)
        entry = data.get(serial_upper)
        if not entry:
            return []
        if isinstance(entry, list):
            return entry
        return [entry]
    except Exception:
        return []


def _infer_console_ncp_target(serial: str = "", port_meta: dict = None) -> dict:
    """Best-effort cluster NCP label for serial-console mappings.

    Zohar/console mappings historically only say that a CL console reaches the
    data-plane NCP, not the NCC. Newer serials often end with ``-P<N>``; expose
    that as a serial hint, not a DNOS NCP slot. Interface names such as
    ``ge100-18/0/6`` use a different numbering namespace, so rendering
    ``-P3`` as ``NCP-3`` is too easy to misread as a live node identifier.
    """
    import re as _re
    port_meta = port_meta or {}
    for key in ("ncp", "ncp_id", "console_ncp", "console_reaches"):
        value = str(port_meta.get(key) or "").strip()
        if not value:
            continue
        if key in ("ncp", "ncp_id", "console_ncp") and value.isdigit():
            return {"label": f"NCP-{value}", "source": f"console_mapping.{key}"}
        m = _re.search(r'(?:NCP[-_\s]?|^P)(\d+)', value, _re.I)
        if m:
            return {"label": f"NCP-{m.group(1)}", "source": f"console_mapping.{key}"}
        if value.upper() == "NCP":
            break
    desc = str(port_meta.get("description") or port_meta.get("note") or "").strip()
    m = _re.search(r'NCP[-_\s]?(\d+)', desc, _re.I)
    if m:
        return {"label": f"NCP-{m.group(1)}", "source": "console_mapping.description"}
    serial = str(serial or "").strip().upper()
    m = _re.search(r'-P(\d+)$', serial)
    if m:
        return {"label": f"NCP data-plane (serial P{m.group(1)})", "source": "serial_suffix"}
    return {"label": "NCP data-plane (exact node not mapped)", "source": "generic_cluster_console"}


def _get_pdu_cli_type(pdu_host: str) -> str:
    """Return CLI type for PDU: 'dev_outlet' (newer) or 'ol' (legacy)."""
    pdu_host = pdu_host.strip().lower()
    if not pdu_host.startswith("pdu-"):
        pdu_host = "pdu-" + pdu_host
    try:
        if os.path.exists(LOCAL_PDU_CLI_CFG):
            with open(LOCAL_PDU_CLI_CFG) as f:
                cfg = json.load(f)
            for mode, hosts in cfg.items():
                if pdu_host in [x.lower() for x in hosts]:
                    return mode
    except Exception:
        pass
    return "dev_outlet"


def _discover_console(device_id: str, serial_number: str = "", ssh_host: str = "") -> dict:
    """Discover console path for a device.
    Priority: 1) console_mappings.json  2) Zohar's CSV DB  3) Device42 API.
    Returns { console_server, port, pdu_entries, source, serial_no }."""
    serial = (serial_number or "").strip().upper()
    result = {"source": None, "console_server": None, "port": None,
              "pdu_entries": [], "serial_no": serial or None}

    canonical_hostname: str = ""

    if not serial:
        for try_id in [device_id, ssh_host]:
            if not try_id:
                continue
            try:
                ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
                if ops_path.exists():
                    ops = _read_ops_safe(ops_path)
                    s = ops.get("serial_number") or ops.get("serial") or ""
                    if s:
                        serial = s.strip().upper()
                        result["serial_no"] = serial
                        canonical_hostname = try_id
                        break
            except Exception:
                continue

    # SN-as-source-of-truth fallback: if literal dir names didn't yield a serial
    # (e.g. label is "YOR-PE-1" but canonical dir is "PE-1"), resolve through
    # the canonical-dir resolver which handles aliases / partial matches.
    if not serial and device_id:
        try:
            canon = _resolve_config_dir(device_id)
            if canon:
                ops_path = Path(SCALER_ROOT) / "db" / "configs" / canon / "operational.json"
                if ops_path.exists():
                    ops = _read_ops_safe(ops_path)
                    s = ops.get("serial_number") or ops.get("serial") or ""
                    if s:
                        serial = s.strip().upper()
                        result["serial_no"] = serial
                        canonical_hostname = canon
                        result["resolved_via"] = f"sn_via_canonical_dir:{device_id}->{canon}"
        except Exception:
            pass

    # 1) Check console_mappings.json (local DB -- same source the probe uses)
    try:
        from scaler.connection_strategy import get_console_config_for_device
        # Include canonical_hostname so label variants (YOR-PE-1 vs YOR_PE-1, or
        # YOR-PE-1 -> PE-1) still match the console mappings.
        try_names = [device_id, canonical_hostname, ssh_host]
        seen = set()
        for try_name in try_names:
            if not try_name or try_name in seen:
                continue
            seen.add(try_name)
            cfg = get_console_config_for_device(try_name)
            if cfg and cfg.get("host"):
                cs_host = cfg["host"]
                cs_port = cfg.get("port")
                if "." not in cs_host and "dev.drivenets.net" not in cs_host:
                    cs_host = f"{cs_host}.dev.drivenets.net"
                result["console_server"] = cs_host
                result["port"] = str(cs_port) if cs_port else None
                result["source"] = cfg.get("_source", "console_mappings")
                if not result["serial_no"] and serial:
                    result["serial_no"] = serial
                break
    except Exception:
        pass

    # Also check serial_to_console in console_mappings.json
    if not result["console_server"] and serial:
        try:
            mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
            if mappings_path.exists():
                cm = json.loads(mappings_path.read_text())
                s2c = cm.get("serial_to_console", {})
                entry = s2c.get(serial) or s2c.get(serial.upper())
                if entry and entry.get("console_server"):
                    cs_host = entry["console_server"]
                    if "." not in cs_host:
                        cs_host = f"{cs_host}.dev.drivenets.net"
                    result["console_server"] = cs_host
                    result["port"] = str(entry.get("port", ""))
                    result["source"] = "console_mappings"
        except Exception:
            pass

    # 2) Zohar's CSV DB
    if not result["console_server"] and serial:
        try:
            _fetch_zohar_db()
        except Exception:
            pass
        cs, port = _lookup_zohar_console(serial)
        if cs:
            result["console_server"] = cs
            result["port"] = port
            result["source"] = "zohar_db"
            result["pdu_entries"] = _lookup_zohar_pdu(serial)

    # 3) Device42 API
    if not result["console_server"]:
        try:
            config_path = Path.home() / ".device42_config.json"
            if config_path.exists():
                cfg = json.loads(config_path.read_text())
                base_url = (cfg.get("url") or "https://device42.dev.drivenets.net").rstrip("/")
                user = cfg.get("username", "")
                password = cfg.get("password", "")
                if user and password:
                    import base64
                    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
                    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}
                    if serial:
                        url = f"{base_url}/api/1.0/devices/?serial_no={urllib.parse.quote(serial)}"
                    else:
                        url = f"{base_url}/api/1.0/devices/?name={urllib.parse.quote(device_id)}"
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        d42_data = json.loads(resp.read())
                    devs = d42_data.get("devices", [])
                    if devs:
                        dev = devs[0]
                        result["source"] = "device42"
                        if dev.get("serial_no"):
                            result["serial_no"] = dev["serial_no"]
                        ports = dev.get("ports", [])
                        for p_entry in (ports if isinstance(ports, list) else []):
                            if isinstance(p_entry, dict) and p_entry.get("type") == "console":
                                result["console_server"] = p_entry.get("remote_device") or p_entry.get("name")
                                result["port"] = p_entry.get("remote_port") or p_entry.get("port")
                                break
                        pdus = dev.get("pdus", [])
                        if pdus:
                            result["pdu_entries"] = [
                                {"pdu": (p.get("name") or p.get("ip") or ""), "outlet": str(p.get("outlet") or p.get("port") or "")}
                                for p in pdus if isinstance(p, dict)
                            ]
        except Exception:
            pass

    if not result["console_server"] and not result["serial_no"]:
        raise ValueError(f"No console mapping found for {device_id}. Provide a serial number or add to Zohar's DB.")

    # PDU mapping is keyed by serial and is useful regardless of where the
    # console path came from (local console_mappings, Zohar CSV, or Device42).
    # Keep it as an enrichment step so cached console mappings still surface
    # the PDU recovery action in the GUI.
    if result.get("serial_no") and not result.get("pdu_entries"):
        try:
            _fetch_zohar_db()
        except Exception:
            pass
        result["pdu_entries"] = _lookup_zohar_pdu(result["serial_no"])

    # Detect cluster devices: console reaches NCP (data plane), NOT NCC (control plane)
    if result["console_server"]:
        try:
            mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
            if mappings_path.exists():
                cm = json.loads(mappings_path.read_text())
                ncc_access = cm.get("cluster_ncc_access", {})
                console_servers = cm.get("console_servers", {})
                port_meta = {}
                try:
                    cs_key = str(result.get("console_server") or "").split(".")[0].lower()
                    port_key = str(result.get("port") or "")
                    for srv_name, srv_info in console_servers.items():
                        if str(srv_name).lower() == cs_key or str(srv_info.get("host", "")).split(".")[0].lower() == cs_key:
                            port_meta = (srv_info.get("ports") or {}).get(port_key) or {}
                            break
                except Exception:
                    port_meta = {}
                import re as _re
                norm_id = _re.sub(r'[_\-\s]', '', device_id.lower())
                for key in ncc_access:
                    norm_k = _re.sub(r'[_\-\s]', '', key.lower())
                    if norm_id == norm_k:
                        entry = ncc_access[key]
                        result["is_cluster"] = True
                        result["console_target"] = "NCP"
                        ncp_target = _infer_console_ncp_target(result.get("serial_no") or serial, port_meta)
                        result["console_target_label"] = ncp_target["label"]
                        result["console_target_source"] = ncp_target["source"]
                        kvm_host = entry.get("kvm_host", "")
                        ncc_vms = entry.get("ncc_vms", [])
                        result["cluster_note"] = (
                            f"This console reaches {result['console_target_label']} (data plane), "
                            f"NOT the NCC (control plane). "
                            f"For NCC access use Virsh Console via KVM host {kvm_host} "
                            f"or SSH to {', '.join(ncc_vms) if ncc_vms else 'the NCC VMs'}."
                        )
                        break
        except Exception:
            pass

    return result


# ---- Console port-scan fallback (ATEN SN9116CO) ----

_KNOWN_CONSOLE_SERVERS = None

def _get_known_console_servers() -> list:
    """Load known console servers from console_mappings.json + hardcoded defaults."""
    global _KNOWN_CONSOLE_SERVERS
    if _KNOWN_CONSOLE_SERVERS is not None:
        return _KNOWN_CONSOLE_SERVERS
    servers = []
    try:
        mp = Path(SCALER_ROOT) / "db" / "console_mappings.json"
        if mp.exists():
            data = json.loads(mp.read_text())
            for name, info in data.get("console_servers", {}).items():
                servers.append({
                    "name": name,
                    "host": info.get("host", f"{name}.dev.drivenets.net"),
                    "user": info.get("user", "dn"),
                    "password": info.get("password", "drive1234"),
                    "total_ports": info.get("total_ports", 16),
                    "rack_hint": info.get("rack_hint", ""),
                })
    except Exception:
        pass
    if not servers:
        for rack in ["b10", "b15", "d16"]:
            servers.append({
                "name": f"console-{rack}",
                "host": f"console-{rack}.dev.drivenets.net",
                "user": "dn", "password": "drive1234",
                "total_ports": 16, "rack_hint": rack.upper(),
            })
    _KNOWN_CONSOLE_SERVERS = servers
    return servers


def _probe_single_port(ssh_client, port_num: int, look_for: str = "", timeout_per_port: float = 6) -> dict:
    """Navigate ATEN menu to a port, read output, exit cleanly.
    Returns {port, output, hostname_guess, matched}."""
    import paramiko
    result = {"port": port_num, "output": "", "hostname_guess": "", "matched": False}
    try:
        chan = ssh_client.invoke_shell(width=200, height=50)
        chan.settimeout(timeout_per_port)
        time.sleep(1)
        if chan.recv_ready():
            chan.recv(8192)

        chan.send("3\r\n")
        time.sleep(1.5)
        if chan.recv_ready():
            chan.recv(8192)

        chan.send(f"{port_num}\r\n")
        time.sleep(2)
        chan.send("\x03")
        time.sleep(0.5)
        chan.send("\r\n")
        time.sleep(2)
        out = ""
        for _ in range(5):
            if chan.recv_ready():
                out += chan.recv(16384).decode("utf-8", errors="replace")
            time.sleep(0.3)
        result["output"] = out[-500:] if len(out) > 500 else out

        import re
        hostname = ""
        for line in out.splitlines():
            stripped = line.strip()
            m = re.match(r'^([A-Za-z0-9_\-]+)[\(#>$]', stripped)
            if m:
                hostname = m.group(1)
                break
            if "login:" in stripped:
                hostname = "_login_prompt_"
                break

        result["hostname_guess"] = hostname
        if look_for and hostname:
            lf = look_for.lower()
            if lf in hostname.lower() or hostname.lower() in lf:
                result["matched"] = True

        chan.send("\x07")
        time.sleep(0.5)
        chan.send("q\r\n")
        time.sleep(0.5)
        chan.close()
    except Exception as e:
        result["output"] = f"[probe error: {e}]"
        try:
            chan.close()
        except Exception:
            pass
    return result


def _probe_console_server(server: dict, look_for: str = "", skip_ports: list = None) -> list:
    """Probe all ports on a console server, looking for a specific device.
    Returns list of {port, hostname_guess, matched, output_snippet}."""
    import paramiko
    skip = set(skip_ports or [])
    found = []
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server["host"], username=server["user"],
                    password=server["password"], timeout=15,
                    look_for_keys=False, allow_agent=False)
        total = server.get("total_ports", 16)
        for p in range(1, total + 1):
            if p in skip:
                continue
            res = _probe_single_port(ssh, p, look_for)
            found.append({
                "port": p,
                "hostname_guess": res["hostname_guess"],
                "matched": res["matched"],
                "output_snippet": res["output"][:200],
            })
            if res["matched"]:
                break
        ssh.close()
    except Exception as e:
        found.append({"port": 0, "hostname_guess": "", "matched": False,
                       "output_snippet": f"[connection failed: {e}]"})
    return found


def _save_discovered_console(device_id: str, serial_number: str, server_name: str,
                              server_host: str, port: int):
    """Save a discovered console mapping to console_mappings.json."""
    mp = Path(SCALER_ROOT) / "db" / "console_mappings.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if mp.exists():
        try:
            data = json.loads(mp.read_text())
        except Exception:
            data = {}
    if "console_servers" not in data:
        data["console_servers"] = {}
    srv = data["console_servers"].get(server_name, {})
    if "ports" not in srv:
        srv["ports"] = {}
    srv.setdefault("host", server_host)
    srv["ports"][str(port)] = {
        "hostname": device_id,
        "serial_number": serial_number.upper() if serial_number else "",
        "last_verified": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "port_scan",
    }
    data["console_servers"][server_name] = srv
    if "device_to_console" not in data:
        data["device_to_console"] = {}
    data["device_to_console"][device_id] = {
        "console_server": server_name,
        "host": server_host,
        "port": port,
        "serial_number": serial_number.upper() if serial_number else "",
        "source": "port_scan",
        "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    mp.write_text(json.dumps(data, indent=2))


def _pdu_power_action(pdu_host: str, outlet: int, action: str = "reboot") -> dict:
    """Perform PDU power action via SSH. action: 'reboot' | 'off' | 'on' | 'status'.
    Returns { success, status_output, error? }."""
    import paramiko as _pmk
    pdu_host = pdu_host.strip().lower()
    if not pdu_host.startswith("pdu-"):
        pdu_host = "pdu-" + pdu_host
    cli_type = _get_pdu_cli_type(pdu_host)
    passwords = ["drive1234!", "drive1234"]
    last_err = None
    for pwd in passwords:
        try:
            client = _pmk.SSHClient()
            client.set_missing_host_key_policy(_pmk.AutoAddPolicy())
            client.connect(pdu_host, username="dn", password=pwd, timeout=15,
                           look_for_keys=False, allow_agent=False)
            shell = client.invoke_shell()
            time.sleep(2)
            if shell.recv_ready():
                shell.recv(10000)

            def _run(cmd, wait=2.5):
                shell.send(cmd + "\n")
                time.sleep(wait)
                out = b""
                for _ in range(15):
                    if shell.recv_ready():
                        out += shell.recv(5000)
                        time.sleep(0.2)
                    elif out:
                        break
                    else:
                        time.sleep(0.2)
                return out.decode("utf-8", errors="replace")

            def _off():
                if cli_type == "dev_outlet":
                    return _run(f"dev outlet 1 {outlet} off")
                return _run(f"olOff {outlet}")

            def _on():
                if cli_type == "dev_outlet":
                    return _run(f"dev outlet 1 {outlet} on")
                return _run(f"olOn {outlet}")

            def _status():
                if cli_type == "dev_outlet":
                    return _run(f"dev outlet 1 {outlet} get status")
                return _run(f"olStatus {outlet}")

            output_lines = []
            if action == "off":
                _off()
                time.sleep(1)
                st = _status()
                output_lines.append(f"OFF sent -> status: {st.strip()}")
            elif action == "on":
                _on()
                time.sleep(1)
                st = _status()
                output_lines.append(f"ON sent -> status: {st.strip()}")
            elif action == "status":
                st = _status()
                output_lines.append(f"Status: {st.strip()}")
            else:
                _off()
                time.sleep(2)
                st1 = _status()
                output_lines.append(f"OFF -> {st1.strip()}")
                time.sleep(3)
                _on()
                time.sleep(2)
                st2 = _status()
                output_lines.append(f"ON -> {st2.strip()}")

            client.get_transport().close()
            return {"success": True, "status_output": "\n".join(output_lines), "pdu_host": pdu_host, "outlet": outlet, "cli_type": cli_type}
        except _pmk.ssh_exception.AuthenticationException as e:
            last_err = str(e)
            continue
        except Exception as e:
            return {"success": False, "error": str(e), "pdu_host": pdu_host, "outlet": outlet}
    return {"success": False, "error": f"Auth failed on {pdu_host}: {last_err}", "pdu_host": pdu_host, "outlet": outlet}


def _open_virsh_ncc_shell_channel(kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list, active_ncc: str = None):
    """Blocking: SSH to KVM, virsh console to NCC, auto-login. Returns (ssh, channel, initial_buf).
    Caller must set channel.settimeout as needed (0 for streaming WS, >0 for discovery).
    """
    import paramiko
    import time

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(kvm_host, username=kvm_user, password=kvm_pass, timeout=20, allow_agent=False, look_for_keys=False)
    try:
        channel = ssh.invoke_shell(width=200, height=50)
    except Exception:
        ssh.close()
        raise
    channel.settimeout(30)
    time.sleep(1)

    def _drain(ch, wait=3):
        buf = b""
        deadline = time.time() + wait
        while time.time() < deadline:
            if ch.recv_ready():
                buf += ch.recv(65535)
                deadline = time.time() + 1
            time.sleep(0.2)
        return buf.decode("utf-8", errors="replace")

    _drain(channel, wait=2)

    if not active_ncc:
        channel.send("sudo virsh list --all\n")
        time.sleep(3)
        virsh_output = _drain(channel, wait=3)
        if "running" not in virsh_output.lower() and "Id" not in virsh_output:
            channel.send("virsh list --all\n")
            time.sleep(3)
            virsh_output = _drain(channel, wait=3)
        if ncc_vms:
            for line in virsh_output.split("\n"):
                line_lower = line.lower()
                if "running" in line_lower:
                    for vm_name in ncc_vms:
                        if vm_name in line:
                            active_ncc = vm_name
                            break
                if active_ncc:
                    break
        else:
            for line in virsh_output.split("\n"):
                parts = line.split()
                if len(parts) >= 3 and parts[-1].lower() == "running":
                    vm_candidate = parts[1] if parts[0].isdigit() else parts[0]
                    if "ncc" in vm_candidate.lower():
                        active_ncc = vm_candidate
                        break

    if not active_ncc:
        ssh.close()
        raise ValueError("No running NCC VM found")

    channel.send(f"sudo virsh console --force {active_ncc}\n")
    time.sleep(3)
    deadline = time.time() + 6
    buf = b""
    while time.time() < deadline:
        if channel.recv_ready():
            buf += channel.recv(65535)
            if b"Escape character" in buf:
                break
        time.sleep(0.3)
    time.sleep(0.5)
    channel.send("\n")
    time.sleep(2)
    if channel.recv_ready():
        buf += channel.recv(65535)
    text = buf.decode("utf-8", errors="replace").lower()
    last_line = text.rstrip().split("\n")[-1].strip() if text.rstrip() else ""

    def _try_login_from_login_prompt(ch, cred_pairs, buf_ref):
        """Handle 'login:' prompt -- send user, wait for password:, send pass."""
        for cred_user, cred_pass in cred_pairs:
            ch.send(f"{cred_user}\n".encode())
            time.sleep(1)
            login_buf = b""
            for _ in range(15):
                time.sleep(0.3)
                if ch.recv_ready():
                    login_buf += ch.recv(4096)
                lo = login_buf.decode("utf-8", errors="replace").lower()
                ll = lo.rstrip().split("\n")[-1].strip() if lo.rstrip() else ""
                if ll.endswith("password:") or ll.endswith("password :"):
                    ch.send(f"{cred_pass}\n".encode())
                    buf_ref[0] += login_buf
                    time.sleep(3)
                    post_buf = b""
                    if ch.recv_ready():
                        post_buf = ch.recv(65535)
                    buf_ref[0] += post_buf
                    post_text = post_buf.decode("utf-8", errors="replace").lower()
                    if "incorrect" in post_text or "login:" in post_text.rstrip().split("\n")[-1].strip():
                        logging.info(f"[virsh] {cred_user}/{cred_pass} rejected, trying next")
                        break
                    return True
                if "#" in ll or ">" in ll or "$" in ll:
                    buf_ref[0] += login_buf
                    return True
            else:
                continue
        return False

    def _try_login_from_password_prompt(ch, passwords, buf_ref):
        """Handle bare 'Password:' prompt (stale virsh --force detach)."""
        for pw in passwords:
            ch.send(f"{pw}\n".encode())
            time.sleep(3)
            post = b""
            if ch.recv_ready():
                post = ch.recv(65535)
            buf_ref[0] += post
            pt = post.decode("utf-8", errors="replace").lower()
            ll = pt.rstrip().split("\n")[-1].strip() if pt.rstrip() else ""
            if "#" in ll or ">" in ll or "$" in ll or "last login" in pt:
                return True
            if ll.endswith("login:") and "last login" not in ll:
                ok = _try_login_from_login_prompt(ch, [("dn", "drivenets"), ("dnroot", "dnroot")], buf_ref)
                if ok:
                    return True
        return False

    buf_ref = [buf]
    cred_pairs = [("dn", "drivenets"), ("dnroot", "dnroot")]

    if last_line.endswith("login:") and "last login" not in last_line:
        _try_login_from_login_prompt(channel, cred_pairs, buf_ref)
    elif last_line.endswith("password:") or last_line.endswith("password :"):
        _try_login_from_password_prompt(channel, ["drivenets", "dnroot", "drive1234!"], buf_ref)
    elif not any(c in last_line for c in ("#", ">", "$")):
        channel.send("\n")
        time.sleep(2)
        extra = b""
        if channel.recv_ready():
            extra = channel.recv(65535)
        buf_ref[0] += extra
        et = extra.decode("utf-8", errors="replace").lower()
        el = et.rstrip().split("\n")[-1].strip() if et.rstrip() else ""
        if el.endswith("login:") and "last login" not in el:
            _try_login_from_login_prompt(channel, cred_pairs, buf_ref)
        elif el.endswith("password:") or el.endswith("password :"):
            _try_login_from_password_prompt(channel, ["drivenets", "dnroot", "drive1234!"], buf_ref)

    buf = buf_ref[0]

    # If we landed on a BaseOS bash shell ($), auto-enter DNOS CLI via dncli
    final_text = buf.decode("utf-8", errors="replace") if isinstance(buf, (bytes, bytearray)) else str(buf)
    final_last = final_text.rstrip().split("\n")[-1].strip() if final_text.rstrip() else ""
    if final_last.endswith("$") and "#" not in final_last and ">" not in final_last:
        logging.info("[virsh] Detected BaseOS shell ($), entering DNOS CLI via dncli")
        channel.send("dncli\n")
        dncli_buf = b""
        dncli_deadline = time.time() + 12
        entered_cli = False
        while time.time() < dncli_deadline:
            time.sleep(0.5)
            if channel.recv_ready():
                dncli_buf += channel.recv(65535)
            dncli_text = dncli_buf.decode("utf-8", errors="replace").lower()
            dncli_last = dncli_text.rstrip().split("\n")[-1].strip() if dncli_text.rstrip() else ""
            if dncli_last.endswith("#") or dncli_last.endswith(">"):
                entered_cli = True
                break
            if "password" in dncli_last and ("sudo" in dncli_text or "password" in dncli_last):
                logging.info("[virsh] dncli requires sudo password, sending credentials")
                for pw in ["dnroot", "drivenets", "drive1234!"]:
                    channel.send(f"{pw}\n")
                    time.sleep(3)
                    if channel.recv_ready():
                        dncli_buf += channel.recv(65535)
                    dt = dncli_buf.decode("utf-8", errors="replace").lower()
                    dl = dt.rstrip().split("\n")[-1].strip() if dt.rstrip() else ""
                    if dl.endswith("#") or dl.endswith(">"):
                        entered_cli = True
                        break
                    if "sorry" in dt.split(pw.lower())[-1] if pw.lower() in dt else "":
                        continue
                    if dl.endswith("#") or dl.endswith(">"):
                        entered_cli = True
                        break
                break
        buf += dncli_buf
        if entered_cli:
            logging.info("[virsh] Successfully entered DNOS CLI via dncli")
        else:
            logging.warning("[virsh] dncli may not have entered CLI -- last output: %s",
                            dncli_buf.decode("utf-8", errors="replace")[-200:])

    return ssh, channel, buf


def _resolve_active_ncc_host(ncc_hosts: list, ncc_mgmt_ip: str = "", cached_active_ncc: str = "") -> dict:
    """Determine which NCC hostname is the *truly active* NCC.

    Strategy (ordered by reliability):
      1. **Port-22 reachability on the per-node IP.** In GI mode the
         active NCC runs ``gi-manager`` which listens on :22 on its
         per-node interface; the standby (or the NCC still in
         baseos boot) returns "Connection refused". In DNOS mode
         both NCCs have sshd up but only the active one owns the
         VIP, so this check still safely picks an active side.
         Port 22 is TCP-checked in parallel (300 ms per host).
      2. DNS match: if exactly one host resolves to ``ncc_mgmt_ip``,
         that host is the canonical active NCC. (VIP follows the
         active NCC -- this only works in healthy DNOS.)
      3. Cached: use ``cached_active_ncc`` when listed in ``ncc_hosts``.
      4. Fallback: ``ncc_hosts[0]``.

    Returns::

        {
            "active_ncc_host": <hostname>,
            "active_ncc_ip":   <ip|None>,    # per-node IP of active NCC
            "dns_map":         {host: ip},   # resolution per NCC
            "source":          "port22_alive"|"dns_match"|"cached"|"fallback"
        }

    Never raises -- failures degrade gracefully to cached/fallback.
    """
    import socket as _sock
    import concurrent.futures as _cf
    out = {
        "active_ncc_host": "",
        "active_ncc_ip": None,
        "dns_map": {},
        "source": "",
    }
    try:
        hosts = [h for h in (ncc_hosts or []) if isinstance(h, str) and h.strip()]
        if not hosts:
            return out
        mgmt_ip = (ncc_mgmt_ip or "").strip().split("/")[0]
        for h in hosts:
            try:
                ip = _sock.gethostbyname(h)
                out["dns_map"][h] = ip
            except Exception:
                out["dns_map"][h] = None

        # 1. Port-22 reachability on per-node IPs. This is authoritative
        #    in GI mode: only the NCC running gi-manager exposes sshd,
        #    the other returns "Connection refused". Probe in parallel
        #    with tight timeouts so the probe never blocks the UI.
        def _tcp_22_alive(ip: str) -> bool:
            if not ip:
                return False
            s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
            s.settimeout(1.2)
            try:
                s.connect((ip, 22))
                # Read a banner if any -- confirms sshd, not a mid-boot
                # TCP listener that hangs up.
                try:
                    s.settimeout(0.8)
                    banner = s.recv(64)
                    return bool(banner) and banner.startswith(b"SSH-")
                except Exception:
                    return True  # connected but no banner; still counts
            except Exception:
                return False
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        # VIP is NOT a valid answer in GI -- it answers with a baseos
        # sshd that rejects dnroot. Skip any host whose DNS-resolved IP
        # is the cluster mgmt VIP.
        ip_to_host = {}
        for h, ip in out["dns_map"].items():
            if ip and ip != mgmt_ip:
                ip_to_host[ip] = h
        alive_hosts = []
        if ip_to_host:
            try:
                with _cf.ThreadPoolExecutor(max_workers=min(4, len(ip_to_host))) as pool:
                    fut_map = {pool.submit(_tcp_22_alive, ip): (h, ip) for ip, h in ip_to_host.items()}
                    for fut in _cf.as_completed(fut_map, timeout=3.5):
                        h, ip = fut_map[fut]
                        try:
                            if fut.result():
                                alive_hosts.append((h, ip))
                        except Exception:
                            pass
            except Exception:
                pass
        if alive_hosts:
            cached = (cached_active_ncc or "").strip()
            # If the cached active host is alive, prefer it (avoids
            # flipping between NCCs when both are up).
            cached_alive = [(h, ip) for h, ip in alive_hosts if h == cached]
            winner = cached_alive[0] if cached_alive else alive_hosts[0]
            out["active_ncc_host"] = winner[0]
            out["active_ncc_ip"] = winner[1]
            out["source"] = "port22_alive"
            return out

        # 2. DNS-VIP match (healthy DNOS path).
        #
        # When exactly ONE NCC's hostname resolves to the cluster VIP,
        # that hostname is the active NCC -- the standby NCC's lab DNS
        # entry never points to the floating VIP. We use that signal to
        # identify the active NCC, but we do NOT report the VIP as
        # ``active_ncc_ip``: the frontend writes ``active_ncc_ip`` back
        # into the device's sticky-host slot and uses it as the iTerm
        # dispatch target. Sending iTerm to the VIP is exactly the bug
        # we're trying to avoid (some cluster VIP listeners reject
        # dnroot/dnroot, observed on YOR_CL_PE-4 27-Apr-2026), and it
        # also drives the visible "flip between active NCC and VIP"
        # behaviour because the SSH dialog row data-active-ncc shows
        # the NCC hostname while ``active_ncc_ip`` carries the VIP.
        #
        # Resolution: report the per-node IP of the OTHER NCC's DNS
        # entry as ``active_ncc_ip`` only when we can establish it
        # belongs to the active side. When DNS only gives us the VIP
        # (the standby NCC has no per-node A record), leave
        # ``active_ncc_ip`` empty so callers fall through to the
        # cached or kvm-probe path -- the frontend's stale-VIP guard
        # then has a non-equal ``_activeNccIp`` to compare ``host``
        # against and will route via active-NCC iTerm correctly.
        if mgmt_ip:
            matched = [h for h, ip in out["dns_map"].items() if ip and ip == mgmt_ip]
            if len(matched) == 1:
                out["active_ncc_host"] = matched[0]
                # Try to find a per-node IP for the matched host. Lab
                # DNS sometimes also provides ``<ncc-host>.<suffix>``
                # entries that resolve to the per-node IP rather than
                # the VIP -- the secondary lookup catches that. When
                # nothing better is available, leave ``active_ncc_ip``
                # as None so the frontend doesn't latch onto the VIP.
                _per_node_ip = None
                try:
                    _hostnames_to_try = [matched[0]]
                    if "." not in matched[0]:
                        # FQDN variants observed in our labs
                        _hostnames_to_try.extend([
                            matched[0] + ".lab",
                            matched[0] + ".dn",
                        ])
                    for _name in _hostnames_to_try:
                        try:
                            _ip2 = _sock.gethostbyname(_name)
                            if _ip2 and _ip2 != mgmt_ip:
                                _per_node_ip = _ip2
                                break
                        except Exception:
                            continue
                except Exception:
                    _per_node_ip = None
                out["active_ncc_ip"] = _per_node_ip  # may be None
                out["source"] = "dns_match" if _per_node_ip else "dns_match_no_per_node_ip"
                return out

        # 3. Cached.
        cached = (cached_active_ncc or "").strip()
        if cached and cached in hosts:
            out["active_ncc_host"] = cached
            out["active_ncc_ip"] = out["dns_map"].get(cached)
            out["source"] = "cached"
            return out

        # 4. Fallback.
        out["active_ncc_host"] = hosts[0]
        out["active_ncc_ip"] = out["dns_map"].get(hosts[0])
        out["source"] = "fallback"
    except Exception as _e:
        logging.debug("[ncc-resolve] failed: %s", _e)
    return out


def _probe_active_ncc_via_kvm(kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list,
                              ncc_mgmt_ip: str = "", timeout_s: int = 6) -> dict:
    """Discover the ACTIVE NCC VM by asking the KVM host directly.

    Why this exists: ``_resolve_active_ncc_host`` only works when lab DNS
    maps exactly one NCC hostname to ``ncc_mgmt_ip`` (the cluster VIP).
    In GI mode (and for freshly-installed clusters) that mapping is
    frequently stale or missing, so both NCCs DNS-resolve identically,
    or to no IP at all, and the resolver falls back to ``ncc_vms[0]``
    -- which is wrong 50% of the time. The iTerm path then lands the
    operator on the STANDBY NCC and the session either hangs or shows
    the wrong prompt.

    This helper SSHes to the KVM host and uses three cheap signals
    (no virsh console attach) to identify the active NCC:

      1. ``arp -an | grep <ncc_mgmt_ip>`` -- the NCC whose MAC owns the
         VIP is the active one. This is the most reliable signal when
         the cluster is healthy in DNOS mode; unreliable in GI because
         neither NCC has claimed the VIP yet.
      2. ``virsh domifaddr <vm>`` for each NCC -- gives the VMs' per-
         node management IPs. Whichever matches ``ncc_mgmt_ip`` is
         active. Also unreliable in GI mode (IPs come from DHCP inside
         the guest and are not visible to the host).
      3. ``virsh dominfo <vm>`` / ``virsh list --all`` -- confirms at
         least one NCC is running. If exactly one NCC is running
         (the common "one VM crashed" case), that one is active.

    Returns the same shape as ``_resolve_active_ncc_host`` so callers
    can swap it in or chain the two (DNS first, then kvm probe). Never
    raises; returns ``{"source": "kvm_unreachable"}`` on failure so the
    caller can decide whether to trust a stale DNS fallback.
    """
    import paramiko
    import time
    out = {
        "active_ncc_host": "",
        "active_ncc_ip": None,
        "dns_map": {},
        "source": "",
    }
    vms = [v for v in (ncc_vms or []) if isinstance(v, str) and v.strip()]
    if not kvm_host or not vms:
        return out

    mgmt_ip = (ncc_mgmt_ip or "").strip().split("/")[0]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            kvm_host, username=kvm_user or "dn",
            password=kvm_pass or "drive1234!",
            timeout=timeout_s, allow_agent=False, look_for_keys=False,
        )
    except Exception as exc:
        out["source"] = f"kvm_unreachable:{type(exc).__name__}"
        return out

    def _run(cmd: str) -> str:
        try:
            _, stdout, _ = ssh.exec_command(cmd, timeout=timeout_s)
            return stdout.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    try:
        virsh_list = _run("sudo virsh list --all 2>/dev/null || virsh list --all 2>/dev/null")
        running_vms = []
        for line in virsh_list.split("\n"):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("-"):
                continue
            parts = line_stripped.split()
            if len(parts) < 3:
                continue
            for vm in vms:
                if vm in line_stripped and "running" in line_stripped.lower():
                    if vm not in running_vms:
                        running_vms.append(vm)

        ipv4_re = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
        domif_ips = {}
        for vm in running_vms:
            dif = _run(
                f"sudo virsh domifaddr {vm} --source agent 2>/dev/null "
                f"|| sudo virsh domifaddr {vm} 2>/dev/null "
                f"|| virsh domifaddr {vm} 2>/dev/null"
            )
            for m in ipv4_re.findall(dif):
                if not m.startswith(("127.", "169.254.")):
                    domif_ips.setdefault(vm, []).append(m)

        for vm, ips in domif_ips.items():
            out["dns_map"][vm] = ips[0] if ips else None

        if mgmt_ip:
            vip_vm = [v for v, ips in domif_ips.items() if mgmt_ip in ips]
            if len(vip_vm) == 1:
                out["active_ncc_host"] = vip_vm[0]
                out["active_ncc_ip"] = mgmt_ip
                out["source"] = "kvm_domifaddr_match"
                return out

            arp = _run(f"arp -an 2>/dev/null | grep -w {mgmt_ip} || ip neigh | grep -w {mgmt_ip}")
            arp_mac_match = re.search(
                r"([0-9a-f]{2}(?::[0-9a-f]{2}){5})", arp, re.IGNORECASE
            )
            if arp_mac_match:
                mac_lower = arp_mac_match.group(1).lower()
                for vm in running_vms:
                    vm_xml = _run(
                        f"sudo virsh dumpxml {vm} 2>/dev/null | grep -i 'mac address' "
                        f"|| virsh dumpxml {vm} 2>/dev/null | grep -i 'mac address'"
                    )
                    if mac_lower in vm_xml.lower():
                        out["active_ncc_host"] = vm
                        out["active_ncc_ip"] = mgmt_ip
                        out["source"] = "kvm_arp_mac_match"
                        return out

        if len(running_vms) == 1:
            out["active_ncc_host"] = running_vms[0]
            out["source"] = "kvm_only_running"
            return out

        if running_vms:
            out["active_ncc_host"] = running_vms[0]
            out["source"] = "kvm_first_running"
            return out

        out["source"] = "kvm_no_running_vm"
    finally:
        try:
            ssh.close()
        except Exception:
            pass

    return out


def _connect_virsh_console_sync(kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list, active_ncc: str = None):
    """Blocking: SSH to KVM, run virsh console to active NCC, return (ssh_client, channel).
    Call from thread when method=virsh_console.
    """
    ssh, channel, buf = _open_virsh_ncc_shell_channel(
        kvm_host, kvm_user, kvm_pass, ncc_vms, active_ncc
    )
    channel.settimeout(0)
    return ssh, channel, buf


_CLUSTER_SEED_KEYS = (
    "ncc_type", "kvm_host", "kvm_host_ip", "kvm_host_credentials",
    "ncc_vms", "ncc_console_credentials", "dncli_credentials",
)


def _seed_cluster_metadata_from_mappings(scaler_id: str, ops_dict: dict = None, write_back: bool = True) -> dict:
    """Ensure operational.json carries cluster/KVM metadata for cluster devices.

    Background: Several ops-write paths (``_persist_live_status_to_ops``,
    ``_safe_set_mgmt_ip``, ghost-IP reaper, etc.) load the JSON, mutate a
    handful of fields, and write it back. If the record was already missing
    ``ncc_type`` / ``kvm_host`` / ``ncc_vms`` (e.g. bootstrap race, a prior
    writer replaced the dict, a manual edit) those fields remain absent on
    every subsequent read. That makes ``/api/ssh/probe``, the context
    builder, and the frontend iTerm launch path forget the device is a
    cluster -- which is exactly the PE-4 regression that landed the user
    at a DNOS SSH attempt against the dead VIP.

    The authoritative source for cluster shape is
    ``console_mappings.json::cluster_ncc_access[<scaler_id>]``. This helper
    reads that map and merges any missing fields into the device's
    operational.json so every downstream reader sees a consistent record.

    Semantics:
      * Never overwrites a populated ops field; existing values always win.
      * Also seeds ``ncc_mgmt_ip`` (from ``mgmt_vip``), ``is_cluster`` flag,
        and a best-effort ``active_ncc_vm`` (first VM) when absent.
      * No-op for non-cluster devices or when mappings are unavailable.
      * ``write_back=False`` returns the merged dict without touching disk
        (used by callers that already own the write).

    Args:
        scaler_id: canonical device id (the db/configs subdirectory name).
        ops_dict: optional in-memory ops dict to merge into; when absent
            the function reads/writes operational.json directly.
        write_back: when True and a change occurred, atomically writes the
            merged record back to operational.json.

    Returns:
        The (possibly-mutated) ops dict. Callers that passed ``ops_dict``
        get back the SAME object, now with seeded fields.
    """
    if not scaler_id:
        return ops_dict or {}

    mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
    if not mappings_path.exists():
        return ops_dict or {}

    try:
        mappings = json.loads(mappings_path.read_text())
    except Exception:
        return ops_dict or {}

    cluster_info = (mappings.get("cluster_ncc_access") or {}).get(scaler_id)
    if not cluster_info or cluster_info.get("ncc_type") != "kvm":
        return ops_dict or {}

    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    owns_dict = ops_dict is None
    if owns_dict:
        if ops_path.exists():
            try:
                ops_dict = _read_ops_safe(ops_path)
            except Exception:
                ops_dict = {}
        else:
            ops_dict = {}
    if not isinstance(ops_dict, dict):
        return ops_dict or {}

    changed = False
    for key in _CLUSTER_SEED_KEYS:
        if ops_dict.get(key) in (None, "", [], {}):
            value = cluster_info.get(key)
            if value not in (None, "", [], {}):
                ops_dict[key] = value
                changed = True

    if not ops_dict.get("ncc_mgmt_ip"):
        vip = (cluster_info.get("mgmt_vip") or "").strip()
        if vip:
            ops_dict["ncc_mgmt_ip"] = vip
            changed = True

    if ops_dict.get("ncc_type") == "kvm" and ops_dict.get("is_cluster") is not True:
        ops_dict["is_cluster"] = True
        changed = True

    vms = ops_dict.get("ncc_vms") or []
    if vms and not ops_dict.get("active_ncc_vm"):
        ops_dict["active_ncc_vm"] = vms[0]
        changed = True

    if changed and write_back and owns_dict:
        try:
            ops_path.parent.mkdir(parents=True, exist_ok=True)
            from routes._ops_writer import update_ops as _uops_seed

            def _mut_seed(d, _src=ops_dict):
                d.update(_src)

            _uops_seed(ops_path, _mut_seed, create_if_missing=True)
            logging.info("[cluster-seed] re-seeded cluster metadata for %s from console_mappings", scaler_id)
        except Exception as _exc:
            logging.warning("[cluster-seed] failed to persist seed for %s: %s", scaler_id, _exc)

    return ops_dict


def _parse_mgmt_ip_from_show_interfaces(text: str) -> str:
    """Extract management IPv4 from 'show interfaces management' output.
    Handles both key-value ('ipv4-address 10.x.x.x/20') and DNOS table format
    ('| mgmt0 | enabled | up | 100.64.11.118/20 (d) |').
    Prefers mgmt0 row; falls back to any mgmt-ncc-* row with an IP.
    """
    import re

    mgmt0_ip = ""
    ncc_mgmt_ip = ""
    for line in text.split("\n"):
        m = re.search(r"\|\s*(mgmt[^\|]*?)\s*\|.*?\|\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/\d+)?", line)
        if m:
            iface_name = m.group(1).strip().lower()
            ip = m.group(2).strip()
            if iface_name == "mgmt0" and not mgmt0_ip:
                mgmt0_ip = ip
            elif iface_name.startswith("mgmt-ncc") and not ncc_mgmt_ip:
                ncc_mgmt_ip = ip
    if mgmt0_ip:
        return mgmt0_ip
    if ncc_mgmt_ip:
        return ncc_mgmt_ip

    m = re.search(
        r"(?:ipv4-address|ip-address|ip\s+address)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/\d+)?",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    for pat in (
        r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*/\s*\d+",
        r"\b(100\.(?:6[4-9]|[7-9]\d|\d{3})\.\d{1,3}\.\d{1,3})\b",
    ):
        m2 = re.search(pat, text)
        if m2:
            return m2.group(1).strip()
    return ""


def _detect_cli_mode_from_buffer(text: str) -> str:
    if "GI(" in text:
        return "GI"
    if "DNOS(" in text:
        return "DNOS"
    return ""


def _discover_ncc_mgmt_ip_sync(
    kvm_host: str, kvm_user: str, kvm_pass: str, ncc_vms: list, active_ncc: str = None
) -> dict:
    """Blocking: virsh console to NCC, run show interfaces management, parse IP, verify SSH dnroot."""
    import paramiko
    import time

    result = {
        "ncc_mgmt_ip": "",
        "device_mode": "",
        "ssh_reachable": False,
        "ssh_auth_ok": False,
        "error": "",
    }
    ssh = None
    channel = None

    def _drain(ch, wait=4):
        buf = b""
        deadline = time.time() + wait
        while time.time() < deadline:
            if ch.recv_ready():
                buf += ch.recv(65535)
                deadline = time.time() + 1
            time.sleep(0.15)
        return buf.decode("utf-8", errors="replace")

    try:
        ssh, channel, initial = _open_virsh_ncc_shell_channel(
            kvm_host, kvm_user, kvm_pass, ncc_vms, active_ncc
        )
        channel.settimeout(8)
        combined = (
            initial.decode("utf-8", errors="replace")
            if isinstance(initial, (bytes, bytearray))
            else str(initial)
        )

        device_mode = _detect_cli_mode_from_buffer(combined)
        result["device_mode"] = device_mode

        channel.send("show interfaces management | no-more\n")
        time.sleep(2)
        combined += _drain(channel, wait=5)

        mgmt_ip = _parse_mgmt_ip_from_show_interfaces(combined)
        if not mgmt_ip:
            channel.send("show interfaces management\n")
            time.sleep(2)
            combined += _drain(channel, wait=5)
            mgmt_ip = _parse_mgmt_ip_from_show_interfaces(combined)

        if not mgmt_ip and "$" in combined[-500:]:
            channel.send("dncli\n")
            time.sleep(2)
            combined += _drain(channel, wait=4)
            channel.send("show interfaces management | no-more\n")
            time.sleep(2)
            combined += _drain(channel, wait=6)
            mgmt_ip = _parse_mgmt_ip_from_show_interfaces(combined)

        result["ncc_mgmt_ip"] = mgmt_ip

        # Exit virsh: Ctrl+] then quit
        try:
            channel.send("\x1d")
            time.sleep(0.4)
            channel.send("quit\n")
            time.sleep(0.5)
            _drain(channel, wait=2)
        except Exception:
            pass
        try:
            channel.close()
        except Exception:
            pass
        try:
            ssh.close()
        except Exception:
            pass
        ssh = None
        channel = None

        if not mgmt_ip:
            result["error"] = "Could not parse management IP from CLI output"
            return result

        sock = __import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM)
        sock.settimeout(3.0)
        try:
            sock.connect((mgmt_ip, 22))
            result["ssh_reachable"] = True
        except Exception:
            result["ssh_reachable"] = False
        finally:
            try:
                sock.close()
            except Exception:
                pass

        if result["ssh_reachable"]:
            vssh = paramiko.SSHClient()
            vssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                vssh.connect(
                    mgmt_ip,
                    username="dnroot",
                    password="dnroot",
                    timeout=8,
                    banner_timeout=8,
                    allow_agent=False,
                    look_for_keys=False,
                )
                result["ssh_auth_ok"] = True
                vssh.close()
            except Exception:
                result["ssh_auth_ok"] = False
                try:
                    vssh.close()
                except Exception:
                    pass

    except Exception as e:
        result["error"] = str(e)
        logging.warning(f"[discover_ncc_mgmt] {e}")
    finally:
        if channel:
            try:
                channel.close()
            except Exception:
                pass
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass

    return result

def _build_job_name(body: dict, device_id: str, config_text: str) -> str:
    """Build a descriptive job name from push params."""
    name = body.get("job_name", "").strip()
    if name:
        return name
    lines = len(config_text.strip().split("\n"))
    mode_label = "Commit check" if body.get("dry_run") else (body.get("mode") or "merge").capitalize()
    return f"{lines} lines {mode_label} on {device_id}"

_PUSH_HISTORY_PATH = Path.home() / ".scaler_push_history.json"
_ACTIVE_BUILDS_PATH = Path.home() / ".scaler_active_builds.json"
_ACTIVE_UPGRADES_PATH = Path.home() / ".scaler_active_upgrades.json"
_MAX_HISTORY_JOBS = 50
_MAX_TERMINAL_LINES_IN_HISTORY = 200


def _load_push_history() -> list:
    """Load persisted push jobs from disk."""
    if not _PUSH_HISTORY_PATH.exists():
        return []
    try:
        with open(_PUSH_HISTORY_PATH) as f:
            data = json.load(f)
        return data.get("jobs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception:
        return []


def _save_push_history(jobs: list):
    """Persist completed push jobs to disk. Cap at 50, truncate terminal to 200 lines."""
    to_save = []
    for j in jobs[: _MAX_HISTORY_JOBS]:
        jcopy = dict(j)
        lines = jcopy.get("terminal_lines", [])
        if len(lines) > _MAX_TERMINAL_LINES_IN_HISTORY:
            jcopy["terminal_lines"] = lines[-_MAX_TERMINAL_LINES_IN_HISTORY:]
        to_save.append(jcopy)
    try:
        _PUSH_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_PUSH_HISTORY_PATH, "w") as f:
            json.dump({"jobs": to_save}, f, indent=2)
    except Exception:
        pass


def _invalidate_device_context_cache(device_id: str = "", mgmt_ip: str = "") -> int:
    """Drop cached ``_get_device_context`` results for a device after a
    write operation (config push / upgrade / delete-hierarchy).

    The cache keys are formatted ``devctx:{scaler_device_id_or_device_id}:{mgmt_ip}:{app_user}``
    so we invalidate every key that mentions either identifier. Passing
    an empty string skips that clause; callers should supply at least
    one. Safe to call when the coalescer has not been touched (returns
    0).
    """
    try:
        from routes._live_coalescer import coalescer
    except Exception:
        return 0

    did_token = f":{device_id}:" if device_id else ""
    ip_token = f":{mgmt_ip}:" if mgmt_ip else ""

    def _match(key: str) -> bool:
        if not key.startswith("devctx:"):
            return False
        if did_token and did_token in key:
            return True
        if ip_token and ip_token in key:
            return True
        return False

    try:
        return coalescer.invalidate_matching(_match)
    except Exception:
        return 0


def _persist_job_if_done(job_id: str):
    """If job is done, add to history and persist. Evicts stale done jobs from memory."""
    with _push_jobs_lock:
        job = _push_jobs.get(job_id, {})
        if not job.get("done"):
            return
        jobs = _load_push_history()
        jobs.insert(0, _sanitize_job(job))
        jobs = jobs[:_MAX_HISTORY_JOBS]
        _save_push_history(jobs)
        _evict_stale_jobs_locked()
    if job.get("job_type") == "build_monitor":
        _remove_active_build(job_id)


def _evict_stale_jobs_locked():
    """Remove done jobs older than 30 minutes from memory. Must hold _push_jobs_lock."""
    import time
    cutoff = time.time() - 1800
    stale = [jid for jid, j in _push_jobs.items()
             if j.get("done") and j.get("started_at", "") < _iso_from_ts(cutoff)]
    for jid in stale:
        _push_jobs.pop(jid, None)


def _iso_from_ts(ts):
    """Convert unix timestamp to ISO string for comparison."""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


_INTERNAL_JOB_KEYS = {"_channel", "_client", "_pusher", "_live_output", "_cancel_requested", "_cancel_check", "_sched_token"}


def _json_safe_job_value(value):
    """Return a JSON-serializable copy of a job value.

    Job rows are accumulated from live workers, old history files, and
    recovery snapshots. Some old rows used ``id`` instead of ``job_id`` and
    live rows can briefly carry helper objects. The operations API should
    never fail a browser refresh because one legacy job has an odd shape.
    """
    if isinstance(value, dict):
        return {
            str(k): _json_safe_job_value(v)
            for k, v in value.items()
            if k not in _INTERNAL_JOB_KEYS
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_job_value(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


def _sanitize_job(job: dict) -> dict:
    """Strip internal fields and normalize legacy job rows for API responses."""
    if not isinstance(job, dict):
        return {}
    safe = {
        k: _json_safe_job_value(v)
        for k, v in job.items()
        if k not in _INTERNAL_JOB_KEYS
    }
    legacy_id = safe.get("job_id") or safe.get("id")
    if legacy_id:
        safe["job_id"] = str(legacy_id)
    safe.setdefault("terminal_lines", [])
    if not isinstance(safe["terminal_lines"], list):
        safe["terminal_lines"] = [str(safe["terminal_lines"])]
    else:
        safe["terminal_lines"] = [str(line) for line in safe["terminal_lines"]]
    return safe


def _save_active_build(job_id: str, job_data: dict):
    """Persist an active build-monitor job to disk so it survives server restarts."""
    try:
        builds = {}
        if _ACTIVE_BUILDS_PATH.exists():
            with open(_ACTIVE_BUILDS_PATH) as f:
                builds = json.load(f)
        safe = {k: v for k, v in job_data.items() if k not in _INTERNAL_JOB_KEYS}
        builds[job_id] = safe
        with open(_ACTIVE_BUILDS_PATH, "w") as f:
            json.dump(builds, f, indent=2)
    except Exception:
        pass


def _remove_active_build(job_id: str):
    """Remove a completed/failed build from the active builds file."""
    try:
        if not _ACTIVE_BUILDS_PATH.exists():
            return
        with open(_ACTIVE_BUILDS_PATH) as f:
            builds = json.load(f)
        builds.pop(job_id, None)
        with open(_ACTIVE_BUILDS_PATH, "w") as f:
            json.dump(builds, f, indent=2)
    except Exception:
        pass


def _save_active_upgrade(job_id: str, job_data: dict):
    """Persist a running upgrade job to disk so it can be recovered on restart."""
    try:
        upgrades = {}
        if _ACTIVE_UPGRADES_PATH.exists():
            with open(_ACTIVE_UPGRADES_PATH) as f:
                upgrades = json.load(f)
        safe = {k: v for k, v in job_data.items() if k not in _INTERNAL_JOB_KEYS}
        upgrades[job_id] = safe
        with open(_ACTIVE_UPGRADES_PATH, "w") as f:
            json.dump(upgrades, f, indent=2)
    except Exception:
        pass


def _remove_active_upgrade(job_id: str):
    """Remove a completed/failed upgrade from the active upgrades file."""
    try:
        if not _ACTIVE_UPGRADES_PATH.exists():
            return
        with open(_ACTIVE_UPGRADES_PATH) as f:
            upgrades = json.load(f)
        upgrades.pop(job_id, None)
        with open(_ACTIVE_UPGRADES_PATH, "w") as f:
            json.dump(upgrades, f, indent=2)
    except Exception:
        pass


INVENTORY_FILE = Path(__file__).resolve().parent.parent / "device_inventory.json"
DEVICE_INVENTORY_JSON = Path(__file__).resolve().parent.parent / "device_inventory.json"


def _find_cached_config_by_ip(ssh_host: str) -> tuple:
    """Search SCALER db/configs for a device matching this SSH IP. Returns (device_id, config_text)."""
    configs_dir = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_dir.exists():
        return None, None
    for dev_dir in configs_dir.iterdir():
        if not dev_dir.is_dir():
            continue
        ops_file = dev_dir / "operational.json"
        if ops_file.exists():
            try:
                ops = json.loads(ops_file.read_text())
                if ops.get("mgmt_ip", "").strip() == ssh_host:
                    config_file = dev_dir / "running.txt"
                    config = config_file.read_text() if config_file.exists() else None
                    return dev_dir.name, config
            except Exception:
                continue
    return None, None


def _build_device_identity(
    device_id: str,
    ssh_host: str,
    mgmt_ip: str,
    scaler_device_id: str,
    hostname: str,
    serial: str,
    config_hostname: str,
    try_ids: list,
    inv_dev: dict | None,
) -> dict:
    """Build unified device identity from all known qualifiers.
    Two devices with same mgmt_ip are considered the same (even if names differ).
    """
    identity = {
        "canvas_label": device_id or "",
        "config_hostname": config_hostname or "",
        "serial": serial or "",
        "mgmt_ip": mgmt_ip or "",
        "ssh_host": (ssh_host or mgmt_ip or "").strip(),
        "scaler_ids": list(dict.fromkeys(i for i in try_ids if i)),
        "inventory_keys": [],
    }
    if inv_dev and DEVICE_INVENTORY_JSON.exists():
        try:
            inv_data = json.loads(DEVICE_INVENTORY_JSON.read_text())
            devices = inv_data.get("devices", {})
            inv_ip = (inv_dev.get("mgmt_ip") or inv_dev.get("ip") or "").strip()
            inv_host = (inv_dev.get("hostname") or "").lower()
            inv_ser = (inv_dev.get("serial") or "").lower()
            for key, dev in devices.items():
                d_ip = (dev.get("mgmt_ip") or dev.get("ip") or "").strip()
                dh = (dev.get("hostname") or "").lower()
                ds = (dev.get("serial") or "").lower()
                if inv_ip and d_ip == inv_ip:
                    identity["inventory_keys"].append(key)
                elif inv_host and dh == inv_host:
                    identity["inventory_keys"].append(key)
                elif inv_ser and ds == inv_ser:
                    identity["inventory_keys"].append(key)
        except Exception:
            pass
    identity["hostname_mismatch"] = bool(
        config_hostname and device_id and config_hostname.lower() != device_id.lower()
    )
    return identity


def _identity_norm(value: object) -> str:
    """Normalize identity tokens for cache-owner comparisons."""
    return re.sub(r"[_\-\s.]", "", str(value or "").strip().lower())


def _identity_is_generated(value: object) -> bool:
    """Return true for weak canvas labels such as NCP-1 / S1."""
    norm = _identity_norm(value)
    return bool(re.match(r"^(ncp|ncp\d+|s|s\d+)$", norm))


def _identity_guard_matches_entry(entry: dict | None, guard: dict | None) -> bool:
    """Check whether a SCALER ops-index entry may provide identity-bound cache.

    Onboarding may start from a plain active-NCC IP that already exists in the
    global ops index under a different config directory. IP equality proves the
    transport target, not cache ownership. Require a stable identity match
    (serial or non-generated hostname/scaler id) before consuming stack/LLDP/git
    from that cached owner.
    """
    if not guard:
        return True
    if not entry:
        return False

    serials = {
        _identity_norm(guard.get("registry_serial_number")),
        _identity_norm(guard.get("verified_serial")),
        _identity_norm(guard.get("serial_number")),
    }
    serials.discard("")
    entry_serial = _identity_norm(entry.get("serial"))
    if entry_serial and entry_serial in serials:
        return True

    names = set()
    for key in (
        "requested_device_id",
        "verified_hostname",
        "registry_hostname",
        "hostname",
        "registered_device_id",
    ):
        val = guard.get(key)
        if val and not _identity_is_generated(val):
            names.add(_identity_norm(val))
    names.discard("")

    entry_names = {
        _identity_norm(entry.get("scaler_id")),
        _identity_norm(entry.get("hostname")),
    }
    entry_names.discard("")
    if names and entry_names and (names & entry_names):
        return True

    return False


_SYSTEM_TYPE_SENTINELS = {"", "N/A", "NULL", "NONE", "UNKNOWN"}


def _clean_system_type(raw) -> str:
    """Normalize a raw system_type value. Returns '' for sentinels like 'N/A'.

    Also strips the DNAAS-style inventory noise ``"SA-40C8CD, Family: NCR"``
    down to the first comma-delimited token so the head of a dirty string is
    still usable downstream (frontend sanitizer applies the final validation
    against the known system-type list).
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    if s.upper() in _SYSTEM_TYPE_SENTINELS:
        return ""
    if "," in s:
        s = s.split(",", 1)[0].strip()
    return s


_SCALER_DEVICES_JSON_PATH = Path(SCALER_ROOT) / "db" / "devices.json"


def _load_scaler_devices_json() -> dict:
    """Load ``SCALER/db/devices.json`` (curated cache). Returns {} on error."""
    try:
        if _SCALER_DEVICES_JSON_PATH.exists():
            return json.loads(_SCALER_DEVICES_JSON_PATH.read_text())
    except Exception:
        pass
    return {}


def _find_scaler_db_device(device_id: str, mgmt_ip: str = "",
                           hostname: str = "", try_ids: list | None = None) -> dict | None:
    """Look up a device entry in ``SCALER/db/devices.json`` by id / hostname / ip.

    The scaler CLI treats ``devices.json`` as the curated source of truth for
    per-device platform + ``system_type``. It survives GI transitions (unlike
    ``operational.json`` which the monitor overwrites with ``N/A`` when DNOS
    goes away), so it's the best long-term fallback for the upgrade wizard.
    """
    data = _load_scaler_devices_json()
    devices = data.get("devices") or []
    if not devices:
        return None
    did = (device_id or "").strip().lower()
    host = (hostname or "").strip().lower()
    ip = (mgmt_ip or "").strip()
    extra = [i.lower() for i in (try_ids or []) if i]
    for d in devices:
        d_id = (d.get("id") or "").lower()
        d_host = (d.get("hostname") or "").lower()
        d_ip = (d.get("ip") or "").strip()
        aliases = [str(a).lower() for a in (d.get("aliases") or [])]
        if did and (d_id == did or d_host == did or did in aliases):
            return d
        if host and (d_host == host or d_id == host):
            return d
        if ip and d_ip == ip:
            return d
        for eid in extra:
            if eid and (eid == d_id or eid == d_host or eid in aliases):
                return d
    return None


# Matches the "# \u2022 Type: SA-36CD-S" line emitted by the SCALER
# config-extractor DEVICE SUMMARY block. Also accepts ASCII "*" bullets so
# older / sanitized backups still match.
_CFG_BACKUP_TYPE_RE = re.compile(
    r"^#\s*[\u2022*\-]\s*Type\s*:\s*([A-Za-z0-9][A-Za-z0-9\-]*)",
    re.MULTILINE,
)
# Matches the raw "System Type: <val>" line from `show system` output that
# `full_output.txt` captures while the device was still in DNOS mode.
_CFG_BACKUP_SYSTYPE_RE = re.compile(
    r"System\s+Type\s*:\s*([A-Za-z0-9][A-Za-z0-9\-]*)",
    re.IGNORECASE,
)


def _scan_scaler_config_backups_for_system_type(try_ids: list) -> str:
    """Recover the last-known DNOS-mode ``system_type`` from SCALER config backups.

    When a device boots into GI mode the monitor's ``operational.json`` loses
    the system type (set to ``N/A``) because DNOS sshd is unreachable. But the
    SCALER config extractor writes DEVICE SUMMARY headers into backup files
    like ``pre_upgrade_backup_*.txt`` / ``pre_delete_backup_*.txt`` every time
    the device was seen in DNOS mode. Scan those first (because they are
    guaranteed DNOS-mode snapshots), then fall back to ``running.txt`` /
    ``full_output.txt`` which may be stale GI-mode writes with ``N/A``.
    """
    configs_root = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_root.exists():
        return ""
    # Order matters: pre_*_backup_* files are written BEFORE a destructive
    # op (upgrade/delete) while the device was still in DNOS mode, so their
    # DEVICE SUMMARY headers are the most reliable. running.txt /
    # full_output.txt may have been rewritten by the monitor after the device
    # dropped to GI (with "N/A") -- try them last and rely on
    # ``_clean_system_type`` to discard "N/A" captures.
    candidate_globs = (
        "pre_upgrade_backup_*.txt",
        "pre_delete_backup_*.txt",
        "running.txt",
        "full_output.txt",
    )
    for try_id in try_ids:
        if not try_id:
            continue
        dev_dir = configs_root / try_id
        if not dev_dir.is_dir():
            continue
        for pattern in candidate_globs:
            for fp in sorted(dev_dir.glob(pattern), reverse=True):
                try:
                    # Only read the first 64KB -- DEVICE SUMMARY header is at the top.
                    text = fp.read_text(errors="ignore")[:65536]
                except Exception:
                    continue
                for m in _CFG_BACKUP_TYPE_RE.finditer(text):
                    cand = _clean_system_type(m.group(1))
                    if cand:
                        return cand
                for m in _CFG_BACKUP_SYSTYPE_RE.finditer(text):
                    cand = _clean_system_type(m.group(1))
                    if cand:
                        return cand
    return ""


# -----------------------------------------------------------------------------
# Per-user system_type overrides -- multi-user-correct layer on top of the
# global scaler curated cache (``db/devices.json``).
#
# Why a separate layer? ``db/devices.json`` is shared across every user and
# every topology on the host: the scaler CLI writes to it on every deploy and
# the first-match-wins lookup keys on ``(device_id, hostname, mgmt_ip)``. When
# operator A picks "PE-4 is CL-86" in the Upgrade wizard and we persist the
# choice directly into db/devices.json, operator B's topology (which may have
# its OWN "PE-4" pointing at different hardware) reads the same value and the
# wizard deploys the wrong profile. That violates
# ``.cursor/rules/multiuser-by-default.mdc``.
#
# The override layer keeps the manual pick in the operator's own per-user
# workspace, scoped by ``(domain_id, topology_id)`` as well so one user can
# run two topologies in parallel with different expectations for the same
# hostname. The resolver consults it BEFORE the curated cache; a subsequent
# live DNOS probe still rewrites the curated cache (layer 2) but never stomps
# the user's override, so re-opening the wizard after a live probe confirms
# the hardware truth without losing the operator's original correction.
# -----------------------------------------------------------------------------

_USER_DEVICE_OVERRIDES_FILENAME = "device_overrides.json"


def _user_device_overrides_path(app_user: str):
    """Return the per-user ``device_overrides.json`` path, or ``None``.

    ``None`` is returned for unauthenticated callers (empty / legacy
    ``"default"`` app_user) -- we refuse to write overrides into a shared
    path because that would be indistinguishable from the global bug this
    whole layer is supposed to fix.
    """
    if not app_user or app_user == "default":
        return None
    try:
        from api.auth.user_store import user_store
        return user_store.user_data_path(app_user, _USER_DEVICE_OVERRIDES_FILENAME)
    except Exception:
        return None


def _load_user_device_overrides(app_user: str) -> dict:
    """Load the per-user overrides file. Returns ``{}`` on any error."""
    p = _user_device_overrides_path(app_user)
    if not p or not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def _topo_scope_key(domain_id: str, topology_id: str) -> str:
    """Normalize the per-topology bucket key. Empty pieces collapse to ``_``."""
    d = (domain_id or "").strip() or "_"
    t = (topology_id or "").strip() or "_"
    return f"{d}:{t}"


def _device_override_keys(device_id: str, mgmt_ip: str = "", hostname: str = "") -> list:
    """Build lookup keys for an override entry, most-specific first.

    Order: ``hostname`` -> ``mgmt_ip`` -> ``device_id`` (all lowercased,
    de-duplicated). Used for both read and write so matching by any
    available identifier works even when the canvas label drifts from the
    in-config hostname.
    """
    keys = []
    for v in (hostname, mgmt_ip, device_id):
        k = (v or "").strip().lower()
        if k and k not in keys:
            keys.append(k)
    return keys


def _resolve_user_sys_type_override(app_user: str, device_id: str,
                                    mgmt_ip: str = "", hostname: str = "",
                                    domain_id: str = "",
                                    topology_id: str = "") -> tuple:
    """Return ``(system_type, source)`` from the layered per-user store.

    Lookup order (most specific first):
      1. ``per_topology[<domain:topology>][<key>]`` -- the operator's
         correction while working on THIS topology.
      2. ``per_user[<key>]`` -- carry-over so opening the same physical
         device from a different topology still benefits from a prior fix.

    Returns ``("", "")`` when nothing matches. Never reads or writes any
    shared / global path.
    """
    data = _load_user_device_overrides(app_user)
    if not data:
        return "", ""
    keys = _device_override_keys(device_id, mgmt_ip, hostname)
    if not keys:
        return "", ""

    pt_bucket = (data.get("per_topology") or {}).get(
        _topo_scope_key(domain_id, topology_id)) or {}
    for k in keys:
        entry = pt_bucket.get(k)
        if isinstance(entry, dict):
            st = _clean_system_type(entry.get("system_type"))
            if st:
                return st, "user_override_topology"

    pu_bucket = data.get("per_user") or {}
    for k in keys:
        entry = pu_bucket.get(k)
        if isinstance(entry, dict):
            st = _clean_system_type(entry.get("system_type"))
            if st:
                return st, "user_override_user"

    return "", ""


def _save_user_sys_type_override(app_user: str, device_id: str, system_type: str,
                                 mgmt_ip: str = "", hostname: str = "",
                                 domain_id: str = "",
                                 topology_id: str = "") -> bool:
    """Persist a manual sys-type pick under the authenticated user's workspace.

    Writes to BOTH layers when a topology scope is supplied:
      * ``per_topology[<domain:topology>][<key>]`` (takes precedence in the
        wizard the operator is currently using)
      * ``per_user[<key>]`` (cross-topology carry-over for the same user)

    Atomic rewrite via a sibling ``*.tmp`` so a concurrent read never sees a
    half-written JSON blob. Returns ``False`` for unauthenticated callers or
    I/O errors; never raises. Global ``SCALER/db/devices.json`` is left
    untouched -- that file is now live-probe-only.
    """
    cleaned = _clean_system_type(system_type)
    if not cleaned or not app_user or app_user == "default":
        return False
    p = _user_device_overrides_path(app_user)
    if not p:
        return False

    keys = _device_override_keys(device_id, mgmt_ip, hostname)
    if not keys:
        return False

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "system_type": cleaned,
        "device_id": device_id,
        "mgmt_ip": mgmt_ip or "",
        "hostname": hostname or "",
        "updated_at": now,
    }

    try:
        data = _load_user_device_overrides(app_user)
        if not isinstance(data, dict) or not data:
            data = {"version": 1, "per_topology": {}, "per_user": {}}
        data.setdefault("per_topology", {})
        data.setdefault("per_user", {})

        if topology_id or domain_id:
            scope = _topo_scope_key(domain_id, topology_id)
            bucket = data["per_topology"].setdefault(scope, {})
            for k in keys:
                bucket[k] = dict(record)
        pu = data["per_user"]
        for k in keys:
            pu[k] = dict(record)

        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n")
        try:
            import os as _os
            _os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(p)
        return True
    except Exception:
        return False


def _persist_system_type_to_scaler_db(device_id: str, system_type: str,
                                      mgmt_ip: str = "", hostname: str = "",
                                      try_ids: list | None = None,
                                      source: str = "topology_auto") -> bool:
    """Remember a freshly discovered ``system_type`` in ``SCALER/db/devices.json``.

    Idempotent: returns False when the file / device is missing or the value
    is already current. The scaler CLI owns this file too, so we merge in
    place (preserving all other fields) instead of rewriting it. This lets us
    auto-heal entries like ``rr_sa_2`` that the curated list never received a
    ``system_type`` for.

    As of 2026-04-24 this function is called ONLY from live-probe paths
    (``operational_json`` source or a config-backup scan). Manual wizard
    picks now flow through ``_save_user_sys_type_override`` instead so
    user A's correction never leaks into user B's topology. See the
    header comment above ``_user_device_overrides_path`` for the full
    multi-user rationale.

    Operator-pinned guard (added 2026-04-24 for PE-4 CL-86 drift):
        When the existing entry is tagged ``system_type_source ==
        "operator_pinned"`` AND it holds a cluster class (``CL-*``),
        refuse to overwrite it with a non-cluster (``SA-*``) value from
        an auto source. This defends against the classic cluster
        mis-detection where a stale DNAAS inventory snapshot (keyed by
        hostname while the device briefly had an NCP-1 chassis) bleeds
        into the plan builder via the operational.json fallback chain.
        A live DNOS probe returning another CL-* code IS allowed through
        -- hardware is the authority for the *specific* cluster SKU.
        Callers from trusted paths can pass ``source`` to bypass the
        guard (e.g. ``source="dnos_live_probe"``).
    """
    cleaned = _clean_system_type(system_type)
    if not cleaned:
        return False
    try:
        path = _SCALER_DEVICES_JSON_PATH
        if not path.exists():
            return False
        data = json.loads(path.read_text())
        devices = data.get("devices") or []
        if not isinstance(devices, list):
            return False
        entry = _find_scaler_db_device(device_id, mgmt_ip, hostname, try_ids)
        if entry is None:
            return False
        cur_val = _clean_system_type(entry.get("system_type"))
        if cur_val == cleaned:
            return False
        cur_src = (entry.get("system_type_source") or "").lower()
        if cur_src == "operator_pinned" \
                and cur_val.upper().startswith("CL-") \
                and not cleaned.upper().startswith("CL-") \
                and source != "dnos_live_probe":
            # Stale NCP-1 snapshot trying to overwrite a pinned cluster value.
            # Caller is almost certainly operational.json / config-backup /
            # DNAAS inventory while the device is in GI mode. Keep the pin.
            return False
        entry["system_type"] = cleaned
        # Tag provenance so future code can distinguish curated vs auto-discovered
        # values without breaking the scaler CLI (which just ignores unknown keys).
        entry["system_type_source"] = source or "topology_auto"
        path.write_text(json.dumps(data, indent=2) + "\n")
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# Active-NCC recovery helpers
# -----------------------------------------------------------------------------
#
# For cluster devices (CL-*) in GI mode the live port-22 scan that
# ``_resolve_active_ncc_host`` runs is unreliable: BOTH NCC VMs expose baseos
# sshd on their per-node IPs and the "first to answer" wins, which is a
# coin flip. The same robustness we added for ``system_type`` applies here:
# when DNOS isn't live, trust a *pre-upgrade snapshot* ahead of any live probe.
#
# Resolution order (fast to slow, trusted to weak):
#   1. ``operational.json.active_ncc_source == "kvm_virsh_probe"`` -- an
#      actual virsh console probe verified the active NCC by reading its
#      GI CLI prompt. Authoritative in any state.
#   2. ``operational.json.deploy_command`` / ``deploy_ncc_id`` -- scaler
#      stamps this at the moment the user initiates an upgrade/delete with
#      ``request system deploy ... ncc-id N``. Survives the GI transition.
#   3. ``SCALER/db/devices.json`` -- curated cache that topology-auto
#      persists whenever a probe, snapshot, or backup scan wins.
#   4. ``pre_upgrade_backup_*.txt`` / ``pre_delete_backup_*.txt`` -- older
#      upgrades also emitted the deploy_command inside the backup file.
#   5. DNS / port-22 scan in ``_resolve_active_ncc_host`` (existing path).
#      Kept as the last resort for freshly-added clusters that never had
#      a deploy initiated through the topology app.
# -----------------------------------------------------------------------------

_NCC_ID_IN_DEPLOY_CMD_RE = re.compile(r"\bncc[-_]id\s+(\d+)\b", re.IGNORECASE)
_NCC_ID_IN_VM_NAME_RE = re.compile(r"ncc[-_]?(\d+)\b", re.IGNORECASE)

# Sources for which we trust the cached ``active_ncc_vm`` in ops over the
# live port-22 scan. Any prefix match counts.
#   - ``kvm_*``                   -- legacy family set by
#                                    ``_probe_active_ncc_via_kvm``
#                                    (kvm_first_running, kvm_domifaddr_match,
#                                    kvm_arp_mac_match, kvm_only_running).
#   - ``virsh_console_verified``  -- SSH probe endpoint attached to the VM
#                                    console successfully; strongest live
#                                    signal available in GI mode.
#   - ``pre_upgrade_snapshot``    -- derived from ops.deploy_command /
#                                    deploy_ncc_id that scaler stamped when
#                                    the deploy was initiated.
#   - ``pre_upgrade_backup``      -- recovered from a config-backup scan.
#   - ``scaler_db_cache``         -- curated / auto-persisted devices.json.
#   - ``topology_virsh_probe``    -- ad-hoc virsh probe initiated from the
#                                    upgrade wizard "Detect" link.
#   - ``upgrade_start_snapshot``  -- explicit pre-upgrade snapshot we write
#                                    the moment the operator begins an
#                                    upgrade (see ``pre_upgrade_active_ncc_vm``).
#                                    This is the HIGHEST priority non-live
#                                    source -- intentionally more
#                                    authoritative than a fresh probe
#                                    that runs mid-upgrade, because the
#                                    cluster state is in flux during that
#                                    window.
_TRUSTED_ACTIVE_NCC_SOURCES = (
    "kvm_",
    "virsh_console_verified",
    "pre_upgrade_snapshot",
    "pre_upgrade_backup",
    "scaler_db_cache",
    "topology_virsh_probe",
    "upgrade_start_snapshot",
    # `post_reboot_virsh_probe` is the value `routes/upgrade.py`'s
    # `_probe_libvirt_active_ncc_post_reboot` stamps after a
    # `request system delete` reboot, once the live virsh probe has
    # re-identified the active NCC VM (the cluster usually fails over
    # during the delete reboot). It is trusted at the same level as
    # `topology_virsh_probe` because it comes from the same probe
    # surface (live libvirt + dncli reachability gate).
    "post_reboot_virsh_probe",
)


def _extract_ncc_id(value) -> int | None:
    """Best-effort extraction of a numeric NCC id (0 / 1) from:
    - a deploy_command string (``... ncc-id 1``),
    - a VM name (``kvm108-cl408d-ncc1``),
    - a plain integer or numeric string.
    Returns None for anything else so callers can chain without exceptions.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value in (0, 1) else None
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        n = int(s)
        return n if n in (0, 1) else None
    m = _NCC_ID_IN_DEPLOY_CMD_RE.search(s) or _NCC_ID_IN_VM_NAME_RE.search(s)
    if m:
        n = int(m.group(1))
        return n if n in (0, 1) else None
    return None


def _vm_for_ncc_id(ncc_vms: list, ncc_id: int) -> str:
    """Return the VM name in ``ncc_vms`` whose embedded ncc number equals ``ncc_id``."""
    if ncc_id is None or not ncc_vms:
        return ""
    for vm in ncc_vms:
        m = _NCC_ID_IN_VM_NAME_RE.search(str(vm))
        if m and int(m.group(1)) == ncc_id:
            return str(vm)
    return ""


def _infer_active_ncc_from_ops(ops: dict) -> tuple[str, str]:
    """Return ``(active_ncc_vm, source)`` derived from pre-upgrade snapshot
    fields inside ``operational.json``.

    Priority inside this helper:
      1. ``pre_upgrade_active_ncc_vm`` -- explicit snapshot that
         ``snapshot_active_ncc_for_upgrade()`` writes the moment the
         operator begins an upgrade through the topology wizard. This
         is the authoritative answer while an upgrade is in progress
         (cluster state is in flux; live probes can flip).
      2. ``deploy_command`` (``... ncc-id N``) -- scaler stamps this at
         ``connect_for_upgrade`` time. Survives the GI-mode rewrite.
      3. ``deploy_ncc_id`` -- same snapshot, numeric form.

    Returns ``("", "")`` when no snapshot is available so callers fall
    through to the scaler DB / backup scan.
    """
    if not isinstance(ops, dict):
        return "", ""
    vms = ops.get("ncc_vms") or []
    if not vms:
        return "", ""
    # 1. Explicit upgrade-start snapshot (highest precedence).
    preup_vm = (ops.get("pre_upgrade_active_ncc_vm") or "").strip()
    if preup_vm and preup_vm in vms:
        # Only trust when the upgrade hasn't been explicitly marked
        # complete; ``pre_upgrade_cleared_at`` is set by the upgrade
        # completion hook to retire the snapshot.
        if not ops.get("pre_upgrade_cleared_at"):
            return preup_vm, "upgrade_start_snapshot"
    # 2 / 3. Scaler deploy command / deploy_ncc_id.
    n = _extract_ncc_id(ops.get("deploy_command"))
    if n is None:
        n = _extract_ncc_id(ops.get("deploy_ncc_id"))
    vm = _vm_for_ncc_id(vms, n)
    return (vm, "pre_upgrade_snapshot") if vm else ("", "")


def _scan_scaler_config_backups_for_active_ncc(try_ids: list, ncc_vms: list) -> tuple[str, str]:
    """Recover the pre-upgrade active NCC VM from SCALER config backups.

    Scans ``pre_upgrade_backup_*.txt`` / ``pre_delete_backup_*.txt`` /
    ``running.txt`` / ``full_output.txt`` for:
      - a ``# \u2022 Active NCC: kvm...-nccN`` line (emitter-side addition
        so future backups have ground truth), or
      - an embedded ``ncc-id N`` deploy command (older backups contain
        this because SCALER writes the deploy command into the
        placeholder ``running.txt`` for GI-mode devices, and newer
        backups contain it in the DEVICE SUMMARY header).
    Returns ``(vm, source)`` or ``("", "")`` when nothing usable is found.
    """
    configs_root = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_root.exists() or not ncc_vms:
        return "", ""
    _active_ncc_line_re = re.compile(
        r"^#\s*[\u2022*\-]\s*Active\s+NCC\s*:\s*(\S+)",
        re.MULTILINE | re.IGNORECASE,
    )
    candidate_globs = (
        "pre_upgrade_backup_*.txt",
        "pre_delete_backup_*.txt",
        "running.txt",
        "full_output.txt",
    )
    for try_id in try_ids:
        if not try_id:
            continue
        dev_dir = configs_root / try_id
        if not dev_dir.is_dir():
            continue
        for pattern in candidate_globs:
            for fp in sorted(dev_dir.glob(pattern), reverse=True):
                try:
                    text = fp.read_text(errors="ignore")[:65536]
                except Exception:
                    continue
                m = _active_ncc_line_re.search(text)
                if m:
                    cand = m.group(1).strip()
                    if cand in ncc_vms:
                        return cand, "pre_upgrade_backup"
                    # Fall through: may be a partial match, try ncc-id scan.
                m = _NCC_ID_IN_DEPLOY_CMD_RE.search(text)
                if m:
                    vm = _vm_for_ncc_id(ncc_vms, int(m.group(1)))
                    if vm:
                        return vm, "pre_upgrade_backup"
    return "", ""


def snapshot_active_ncc_for_upgrade(device_id: str, scaler_device_id: str = "",
                                    hostname: str = "", app_user: str = "default",
                                    explicit_active_ncc_vm: str = "") -> dict:
    """Freeze the current active-NCC selection into ``operational.json`` as
    the authoritative "pre-upgrade snapshot".

    Call this the instant the operator begins an upgrade/deploy/delete
    through the topology wizard. From that moment until the upgrade
    completes (or ``clear_active_ncc_upgrade_snapshot`` is invoked) the
    snapshot wins over any live probe, because the cluster state can
    flip unpredictably during the upgrade window.

    Resolution order when ``explicit_active_ncc_vm`` is NOT supplied:
      1. ``ops.active_ncc_vm`` (whatever the latest trusted probe stamped).
      2. A fresh best-effort resolver pass (pre-upgrade snapshot /
         scaler DB / backup scan).

    Persists the result to:
      - ``operational.json.pre_upgrade_active_ncc_vm``
      - ``operational.json.pre_upgrade_active_ncc_source``
      - ``operational.json.pre_upgrade_snapshot_at``
      - ``SCALER/db/devices.json`` via ``_persist_active_ncc_to_scaler_db``
        (tagged with source ``upgrade_start_snapshot``) so the next upgrade
        has a durable record even if operational.json is wiped.

    Returns ``{"active_ncc_vm": "...", "source": "...", "snapshot_at": "..."}``
    or an empty dict on failure.
    """
    from datetime import datetime as _dt
    configs_root = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_root.exists():
        return {}
    candidates = [c for c in (scaler_device_id, device_id, hostname) if c]
    ops_path = None
    for cand in candidates:
        p = configs_root / cand / "operational.json"
        if p.exists():
            ops_path = p
            break
    if ops_path is None:
        return {}
    try:
        ops = _read_ops_safe(ops_path)
    except Exception:
        return {}

    vm = (explicit_active_ncc_vm or "").strip()
    src = "wizard_explicit" if vm else ""
    if not vm:
        cand_vm = (ops.get("active_ncc_vm") or "").strip()
        cand_src = (ops.get("active_ncc_source") or "").strip()
        if cand_vm and cand_vm in (ops.get("ncc_vms") or []):
            vm = cand_vm
            src = cand_src or "ops_active_ncc"
    if not vm:
        try:
            resolved_vm, resolved_src = _resolve_active_ncc_best_effort(
                ops,
                device_id=device_id,
                scaler_device_id=scaler_device_id,
                hostname=hostname,
                mgmt_ip=(ops.get("mgmt_ip") or ""),
            )
        except Exception:
            resolved_vm, resolved_src = "", ""
        if resolved_vm:
            vm = resolved_vm
            src = resolved_src or "pre_upgrade_snapshot"
    if not vm:
        return {}

    snapshot_at = _dt.utcnow().isoformat() + "Z"
    ops["pre_upgrade_active_ncc_vm"] = vm
    ops["pre_upgrade_active_ncc_source"] = src
    ops["pre_upgrade_snapshot_at"] = snapshot_at
    ops.pop("pre_upgrade_cleared_at", None)
    # Also refresh the live ops pointers so any reader that picks up
    # operational.json between snapshot and upgrade-start sees the same
    # answer (cannot flip during the window).
    ops["active_ncc_vm"] = vm
    ops["active_ncc_source"] = "upgrade_start_snapshot"
    try:
        from ._ops_writer import update_ops as _update_ops_snap

        def _mutate_snap(d: dict, snapshot=ops) -> None:
            d.clear()
            d.update(snapshot)

        _ok_s, _ = _update_ops_snap(ops_path, _mutate_snap, create_if_missing=False)
        if not _ok_s:
            return {}
    except Exception:
        return {}
    try:
        _persist_active_ncc_to_scaler_db(
            device_id=device_id,
            active_ncc_vm=vm,
            source="upgrade_start_snapshot",
            mgmt_ip=(ops.get("mgmt_ip") or ""),
            hostname=hostname,
            try_ids=candidates,
        )
    except Exception:
        pass
    return {
        "active_ncc_vm": vm,
        "source": src,
        "snapshot_at": snapshot_at,
    }


def clear_active_ncc_upgrade_snapshot(device_id: str, scaler_device_id: str = "",
                                      hostname: str = "") -> bool:
    """Retire the pre-upgrade snapshot once an upgrade has finished.

    Called from the upgrade finalizer so the wizard resumes using live
    probes (or scaler-DB cache) for the next session. Idempotent.
    """
    from datetime import datetime as _dt
    configs_root = Path(SCALER_ROOT) / "db" / "configs"
    if not configs_root.exists():
        return False
    candidates = [c for c in (scaler_device_id, device_id, hostname) if c]
    ops_path = None
    for cand in candidates:
        p = configs_root / cand / "operational.json"
        if p.exists():
            ops_path = p
            break
    if ops_path is None:
        return False
    try:
        ops = _read_ops_safe(ops_path)
    except Exception:
        return False
    if not ops.get("pre_upgrade_active_ncc_vm") and ops.get("pre_upgrade_cleared_at"):
        return False
    ops["pre_upgrade_cleared_at"] = _dt.utcnow().isoformat() + "Z"
    try:
        from ._ops_writer import update_ops as _update_ops_clear

        def _mutate_clear(d: dict, snapshot=ops) -> None:
            d.clear()
            d.update(snapshot)

        _ok_c, _ = _update_ops_clear(ops_path, _mutate_clear, create_if_missing=False)
        return bool(_ok_c)
    except Exception:
        return False


def _persist_active_ncc_to_scaler_db(device_id: str, active_ncc_vm: str,
                                     source: str = "topology_auto",
                                     mgmt_ip: str = "", hostname: str = "",
                                     try_ids: list | None = None) -> bool:
    """Remember a discovered ``active_ncc_vm`` in ``SCALER/db/devices.json``.

    Idempotent. Tags ``active_ncc_source`` with the discovery provenance
    so later runs can tell whether the cached value came from a real
    virsh probe, a pre-upgrade snapshot, or a backup scan.
    """
    vm = (active_ncc_vm or "").strip()
    if not vm:
        return False
    try:
        path = _SCALER_DEVICES_JSON_PATH
        if not path.exists():
            return False
        data = json.loads(path.read_text())
        devices = data.get("devices") or []
        if not isinstance(devices, list):
            return False
        entry = _find_scaler_db_device(device_id, mgmt_ip, hostname, try_ids)
        if entry is None:
            return False
        if (entry.get("active_ncc_vm") == vm
                and entry.get("active_ncc_source") == source):
            return False
        entry["active_ncc_vm"] = vm
        entry["active_ncc_source"] = source
        from datetime import datetime as _dt
        entry["active_ncc_updated_at"] = _dt.utcnow().isoformat() + "Z"
        path.write_text(json.dumps(data, indent=2) + "\n")
        return True
    except Exception:
        return False


def _resolve_active_ncc_best_effort(
    ops: dict,
    device_id: str,
    scaler_device_id: str,
    hostname: str,
    mgmt_ip: str,
) -> tuple[str, str]:
    """Pick the most trustworthy ``(active_ncc_vm, source)`` from the
    resilient non-live sources.

    Caller should short-circuit when ``ops.active_ncc_source`` already
    starts with ``kvm_`` (fresh virsh probe wins). For anything else,
    we prefer a pre-upgrade snapshot over the scaler DB cache, over a
    config-backup scan. Never touches the network.
    """
    if not isinstance(ops, dict):
        return "", ""
    ncc_vms = ops.get("ncc_vms") or []
    if not ncc_vms:
        return "", ""
    try_ids = [
        i for i in (
            (scaler_device_id or "").strip(),
            (device_id or "").strip(),
            (hostname or "").strip(),
        ) if i
    ]
    vm, src = _infer_active_ncc_from_ops(ops)
    if vm:
        return vm, src
    try:
        scaler_dev = _find_scaler_db_device(device_id, mgmt_ip, hostname, try_ids)
    except Exception:
        scaler_dev = None
    if scaler_dev:
        cand = (scaler_dev.get("active_ncc_vm") or "").strip()
        if cand and cand in ncc_vms:
            src = (scaler_dev.get("active_ncc_source") or "scaler_db_cache") or "scaler_db_cache"
            if not any(src.startswith(p) for p in _TRUSTED_ACTIVE_NCC_SOURCES):
                src = "scaler_db_cache"
            return cand, src
    return _scan_scaler_config_backups_for_active_ncc(try_ids, ncc_vms)


def _find_inventory_device(device_id: str, ssh_host: str = "") -> dict | None:
    """Find device in device_inventory.json by label, hostname, IP, or serial.
    Returns None when not found (callers use `if inv_dev:` which is falsy for None).
    """
    if not DEVICE_INVENTORY_JSON.exists():
        return None
    try:
        inv_data = json.loads(DEVICE_INVENTORY_JSON.read_text())
        devices = inv_data.get("devices", {})
    except Exception:
        return None

    did_lower = device_id.lower()
    for key, dev in devices.items():
        k = key.lower()
        dev_ip = (dev.get("mgmt_ip") or dev.get("ip") or "").strip()
        if ssh_host and dev_ip == ssh_host:
            return dev
        if k == did_lower:
            return dev
    for key, dev in devices.items():
        k = key.lower()
        dev_hostname = (dev.get("hostname") or "").lower()
        dev_serial = (dev.get("serial") or dev.get("deviceSerial") or "").lower()
        if did_lower and (did_lower in k or k in did_lower or
                          did_lower == dev_hostname or did_lower == dev_serial):
            return dev
    return None


def _get_device_context(device_id: str, live: bool = False, ssh_host: str = "",
                        app_user: str = "default",
                        domain_id: str = "",
                        topology_id: str = "",
                        bypass_cache: bool = False,
                        identity_guard: dict | None = None) -> dict:
    """Build unified device context for wizard suggestions.

    Resolution order:
    1. If ssh_host provided, use it to find cached config and inventory by IP
    2. Try _resolve_device(device_id) via discovery API
    3. Fuzzy match in device_inventory.json and SCALER db/configs

    ``app_user``, ``domain_id``, and ``topology_id`` scope the per-user
    system_type overrides (see ``_resolve_user_sys_type_override``). They're
    optional -- unauthenticated / unscoped callers fall straight through to
    the global resolution chain, preserving the existing behaviour for
    background jobs and legacy callers.
    """
    from datetime import datetime
    ctx = {
        "device_id": device_id,
        "interfaces": {
            "physical": [],
            "bundle": [],
            "subinterface": [],
            "pwhe": [],
            "free_physical": [],
        },
        "lldp": [],
        "protocols": _empty_protocol_ops(),
        "config_summary": {},
        "wan_interfaces": [],
        "igp": {"protocol": "", "area": "", "interfaces": []},
        "services": {"fxc_count": 0, "vrf_count": 0, "next_evi": 1000},
        "next_bundle_number": 1,
        "system_type": "",
        "cached": not live,
        "timestamp": datetime.now().isoformat(),
        "resolved_via": "",
        "loopbacks": [],
        "vrfs": [],
        "bridge_domains": [],
        "flowspec_policies": [],
        "routing_policies": {},
        "bgp_peers": [],
        "multihoming": {},
        "platform_limits": {},
        "scale_suggestions": [],
        "policy_suggestions": [],
        "lo0_isis_net": "",
        "detected_l2ac_parent": None,
        "detected_bgp_neighbors": [],
        "existing_route_targets": [],
        "next_free": {"vrf_number": 1, "rt": 1},
        "stack": [],
        "stack_fetched_at": "",
        "git_commit": None,
        "git_commit_fetched_at": "",
        "active_ncc_ip": None,
        "device_state": None,
        "cache_owner_conflicts": [],
    }

    try:
        mgmt_ip, scaler_device_id, via = _resolve_mgmt_ip(device_id, ssh_host)
        ctx["resolved_via"] = via
        ctx["resolved_ip"] = mgmt_ip
        ctx["mgmt_ip"] = mgmt_ip
        ctx["ip"] = mgmt_ip
    except Exception:
        mgmt_ip = ""
        scaler_device_id = device_id
        ctx["resolved_via"] = "failed"

    safe_identity_id = ""
    if identity_guard and ssh_host and re.match(r"^\d+\.\d+\.\d+\.\d+$", ssh_host.strip()):
        try:
            idx = _build_scaler_ops_index()
            resolved_entry = idx.get(scaler_device_id.lower()) if scaler_device_id else None
            ip_entry = idx.get(mgmt_ip) if mgmt_ip else None
            entry = resolved_entry or ip_entry
            if entry and not _identity_guard_matches_entry(entry, identity_guard):
                ctx["cache_owner_conflicts"].append({
                    "owner": entry.get("scaler_id") or "",
                    "hostname": entry.get("hostname") or "",
                    "serial": entry.get("serial") or "",
                    "ip": entry.get("ip") or "",
                    "reason": "direct_ip_owner_did_not_match_onboarding_identity",
                })
                safe_identity_id = (
                    identity_guard.get("registry_hostname")
                    or identity_guard.get("verified_hostname")
                    or identity_guard.get("requested_device_id")
                    or device_id
                )
                scaler_device_id = safe_identity_id
                ctx["resolved_via"] = f"onboarding_ip_direct_untrusted_cache:{mgmt_ip}"
        except Exception:
            pass

    hostname = safe_identity_id or device_id
    serial = ""
    # Always attempt serial lookup -- the serial is a stable identifier
    # across upgrades / ghost-IP reaps and does NOT depend on mgmt_ip
    # resolution succeeding. The frontend's SN-based iTerm launch depends
    # on this being populated even for reaped devices.
    try:
        idx = _build_scaler_ops_index()
        entry = None
        if mgmt_ip:
            entry = idx.get(mgmt_ip)
            if identity_guard and entry and not _identity_guard_matches_entry(entry, identity_guard):
                entry = None
        if not entry:
            for try_id in (
                (scaler_device_id or "").lower(),
                (device_id or "").lower(),
            ):
                if try_id and try_id in idx:
                    entry = idx[try_id]
                    break
        if entry:
            hostname = entry.get("hostname", device_id) or device_id
            serial = entry.get("serial", "") or ""
    except Exception:
        pass

    # Last-resort: read the scaler operational.json directly for the
    # canvas label. Covers the case where `_build_scaler_ops_index`
    # lost the entry (rare) but the JSON file is still on disk.
    if not serial:
        try:
            from pathlib import Path as _P
            ops_path = _P("/home/dn/SCALER/db/configs") / (scaler_device_id or device_id) / "operational.json"
            if ops_path.exists():
                ops_data = _read_ops_safe(ops_path)
                sn_fallback = (ops_data.get("serial_number") or ops_data.get("serial") or "").strip()
                if sn_fallback and sn_fallback != "N/A":
                    serial = sn_fallback
        except Exception:
            pass
    config = _get_cached_config(scaler_device_id)
    if not config and scaler_device_id != device_id:
        config = _get_cached_config(device_id)
    if not config and hostname != device_id:
        config = _get_cached_config(hostname)

    live_ops = {"lldp": [], "stack": [], "git_commit": None, "protocols": _empty_protocol_ops()}
    if live and mgmt_ip:
        # Wave 2.2: coalesce concurrent live fetches for the same
        # (device, user). Without this, N browser tabs for the same
        # canvas trigger N parallel SSH sessions; with this, they all
        # share a single fetch within a 90-second TTL.
        from routes._live_coalescer import coalescer as _live_coalescer

        coalesce_key = f"devctx:{scaler_device_id or device_id}:{mgmt_ip}:{app_user}"
        if bypass_cache:
            try:
                _live_coalescer.invalidate(coalesce_key)
                logging.info(
                    "[STACK-TIMING] %s coalescer invalidate (bypass_cache) key=%s",
                    scaler_device_id or device_id, coalesce_key,
                )
            except Exception:
                pass

        def _do_live_fetch():
            from concurrent.futures import ThreadPoolExecutor
            user, password = _get_credentials(
                app_user=app_user,
                device_id=device_id or scaler_device_id,
                hostname=hostname or scaler_device_id,
            )
            new_config = None
            new_live_ops = {"lldp": [], "stack": [], "git_commit": None, "protocols": _empty_protocol_ops()}
            # =====================================================
            # Cluster GI/RECOVERY short-circuit.
            # =====================================================
            # For a KVM cluster in GI/RECOVERY/BASEOS_SHELL the
            # ``mgmt_ip`` we hold IS the cluster VIP (e.g.
            # 100.64.4.98), and that VIP is unclaimed when no NCC
            # is hosting DNOS. Letting the parallel SSH path try
            # paramiko.connect(VIP) costs 15s per attempt and 30s
            # for the banner read -- the dialog hangs ~45-60s
            # before the inevitable failure, and even then there's
            # no DNOS stack to read because DNOS isn't running.
            #
            # Honour ``ops.last_working_method`` and the cached
            # ``device_state``: if either says cluster + non-DNOS,
            # skip direct SSH entirely and go straight to the
            # virsh-console fallback (which talks to the KVM host
            # and runs ``virsh console`` against the active NCC --
            # the only path that works in GI). For DNOS clusters
            # we keep the existing parallel SSH path.
            try:
                _pre_ops = {}
                if scaler_device_id:
                    _pre_path = (
                        Path(SCALER_ROOT) / "db" / "configs"
                        / scaler_device_id / "operational.json"
                    )
                    if _pre_path.exists():
                        _pre_ops = _read_ops_safe(_pre_path)
                _is_cluster_pre = (
                    _pre_ops.get("ncc_type") == "kvm"
                    or _pre_ops.get("is_cluster") is True
                )
                _state_pre = (_pre_ops.get("device_state") or "").upper()
                _last_method_pre = (
                    _pre_ops.get("last_working_method") or ""
                ).lower()
                _virsh_only = (
                    _is_cluster_pre and (
                        _state_pre in ("GI", "BASEOS_SHELL", "RECOVERY")
                        or "virsh" in _last_method_pre
                    )
                )
            except Exception:
                _virsh_only = False
            if _virsh_only and scaler_device_id:
                # Freshness short-circuit: the virsh-console probe is
                # expensive (~10-20 s). When the cached stack was
                # refreshed in the last 5 min by ANY trusted writer
                # (scaler monitor, our preprobe, the global poller) we
                # already hold the latest reality -- there's no DNOS
                # config-change pace that would invalidate it on a GI
                # device. Surface the cached values in `live_ops` so
                # the downstream merge still treats them as "live"
                # (ctx.cached=False) and skip the SSH cost. The
                # operator's manual Refresh button stays honest because
                # the dialog passes `forceRefresh=true` which causes
                # ScalerAPI to call `live=True&bypassCache=true`,
                # invalidating the live coalescer key, but the on-disk
                # snapshot can still be reused if it's within the
                # 5-minute window.
                _CACHE_FRESH_S = 300
                _cached_fresh = False
                try:
                    from datetime import datetime as _dt_f, timezone as _tz_f
                    _ts_raw = (
                        _pre_ops.get("stack_fetched_at")
                        or _pre_ops.get("active_ncc_monitored_at")
                        or _pre_ops.get("last_updated")
                        or ""
                    )
                    if _ts_raw:
                        _ts = _dt_f.fromisoformat(
                            str(_ts_raw).replace("Z", "+00:00")
                        )
                        if _ts.tzinfo is None:
                            _ts = _ts.replace(tzinfo=_tz_f.utc)
                        _age_s = (_dt_f.now(_tz_f.utc) - _ts).total_seconds()
                        _cached_fresh = (
                            _age_s < _CACHE_FRESH_S
                            and bool(_pre_ops.get("stack_components"))
                        )
                except Exception:
                    _cached_fresh = False
                if _cached_fresh:
                    new_live_ops = {
                        "lldp": list(_pre_ops.get("lldp_neighbors") or []),
                        "stack": [
                            {
                                "name": c.get("name", c.get("component", "")),
                                "hw_model": c.get("hw_model", "-"),
                                "revert": c.get("revert", "-"),
                                "current": c.get("current", "-"),
                                "target": c.get("target", "-"),
                            }
                            for c in (_pre_ops.get("stack_components") or [])
                        ],
                        "git_commit": _pre_ops.get("git_commit"),
                        "device_state": _pre_ops.get("device_state"),
                        "active_ncc_node": _pre_ops.get("active_ncc_vm"),
                        "protocols": _pre_ops.get("protocol_states") or _empty_protocol_ops(),
                    }
                    return (new_config, new_live_ops)
                try:
                    new_live_ops = _fetch_ops_via_virsh_fallback(
                        scaler_device_id, user, password,
                    ) or new_live_ops
                except Exception:
                    pass
                return (new_config, new_live_ops)
            with ThreadPoolExecutor(max_workers=2) as pool:
                config_future = pool.submit(
                    _fetch_config_via_ssh, scaler_device_id, mgmt_ip, user, password)
                ops_future = pool.submit(
                    _fetch_all_operational_via_ssh, mgmt_ip, user, password,
                    scaler_device_id, app_user)
                try:
                    new_config = config_future.result(timeout=25)
                except Exception:
                    pass
                try:
                    new_live_ops = ops_future.result(timeout=45)
                except Exception:
                    pass
            return (new_config, new_live_ops)

        try:
            (new_config, new_live_ops), origin = _live_coalescer.get(
                coalesce_key, _do_live_fetch)
            if new_config:
                config = new_config
                ctx["cached"] = False
                if origin == "fresh":
                    ctx["resolved_via"] = f"live_ssh:{mgmt_ip}"
                else:
                    ctx["resolved_via"] = f"live_ssh:{mgmt_ip} ({origin})"
            if new_live_ops:
                live_ops = new_live_ops
        except Exception:
            pass

    config_hostname = ""
    if config:
        try:
            from scaler.wizard.parsers import extract_hierarchy_section
            sys_section = extract_hierarchy_section(config, "system")
            if sys_section:
                nm = re.search(r"^\s+name\s+(\S+)", sys_section, re.MULTILINE)
                if nm:
                    config_hostname = (nm.group(1) or "").strip()
        except Exception:
            pass

    base_try_ids = list(dict.fromkeys(i for i in [scaler_device_id, hostname, device_id] if i))
    try_ids = list(base_try_ids)
    if config_hostname and config_hostname not in try_ids:
        try_ids.insert(0, config_hostname)

    # Self-heal cluster metadata: if any candidate id is listed in
    # console_mappings.json::cluster_ncc_access but its operational.json is
    # missing ncc_type / kvm_host / ncc_vms (e.g. after a hostile writer
    # replaced the dict), re-seed from the mappings file. Non-cluster
    # devices are no-ops. This runs BEFORE any operational.json read below
    # so cluster detection is always consistent with console_mappings.
    for _seed_id in try_ids:
        if not _seed_id:
            continue
        try:
            _seed_cluster_metadata_from_mappings(_seed_id)
        except Exception:
            pass

    if mgmt_ip:
        _build_scaler_ops_index()
        seen_ids = set(i.lower() for i in try_ids)
        for ie in (_scaler_ops_ip_map or {}).get(mgmt_ip, []):
            if identity_guard and not _identity_guard_matches_entry(ie, identity_guard):
                ctx["cache_owner_conflicts"].append({
                    "owner": ie.get("scaler_id") or "",
                    "hostname": ie.get("hostname") or "",
                    "serial": ie.get("serial") or "",
                    "ip": ie.get("ip") or "",
                    "reason": "same_ip_owner_did_not_match_onboarding_identity",
                })
                continue
            if ie["scaler_id"].lower() not in seen_ids:
                try_ids.append(ie["scaler_id"])
                seen_ids.add(ie["scaler_id"].lower())
            hn = ie.get("hostname", "")
            if hn and hn.lower() not in seen_ids:
                try_ids.append(hn)
                seen_ids.add(hn.lower())

    inv_dev = _find_inventory_device(device_id, mgmt_ip)
    if not inv_dev and ssh_host:
        inv_dev = _find_inventory_device(ssh_host, mgmt_ip)
    # Source tracking so the UI / logs can tell whether we fell back to a
    # long-lived cache vs got a fresh DNOS probe. Not part of the external
    # contract -- purely informational for debugging GI-mode gaps.
    ctx["system_type_source"] = ""

    # Resolution order (most -> least authoritative):
    #   0. Per-user + per-user-per-topology override (multi-user fix)
    #      -- ONLY consulted when app_user is a real authenticated user;
    #         "default" / anonymous callers skip straight to layer 1, which
    #         preserves legacy behaviour for background jobs + cron.
    #   1. SCALER operational.json  (freshest DNOS snapshot)
    #   2. SCALER db/devices.json   (curated cache; the scaler CLI writes this
    #                                from actual deploys, so cluster devices
    #                                carry the real ``CL-<N>`` value here)
    #   3. SCALER config backups    (pre-upgrade/pre-delete snapshots taken
    #                                while the device was still in DNOS)
    #   4. device_inventory.json    (DNAAS cache -- LAST resort because it
    #                                stores the NCP hw model like
    #                                ``SA-40C8CD, Family: NCR`` for cluster
    #                                devices, which is wrong for deploys)
    _override_val, _override_src = _resolve_user_sys_type_override(
        app_user=app_user,
        device_id=device_id,
        mgmt_ip=mgmt_ip or "",
        hostname=hostname or "",
        domain_id=domain_id,
        topology_id=topology_id,
    )
    if _override_val:
        ctx["system_type"] = _override_val
        ctx["system_type_source"] = _override_src
        ctx["system_type_override_scope"] = (
            _topo_scope_key(domain_id, topology_id)
            if _override_src == "user_override_topology" else "user"
        )

    for _st_try_id in try_ids:
        if ctx["system_type"]:
            break
        if not _st_try_id:
            continue
        _st_op = Path(SCALER_ROOT) / "db" / "configs" / _st_try_id / "operational.json"
        if _st_op.exists():
            try:
                _st_data = _read_ops_safe(_st_op)
                _st_val = _clean_system_type(
                    _st_data.get("system_type")
                    or _st_data.get("deploy_system_type")
                )
                if _st_val:
                    ctx["system_type"] = _st_val
                    ctx["system_type_source"] = "operational_json"
                    break
            except Exception:
                pass

    if not ctx["system_type"]:
        _scaler_dev = _find_scaler_db_device(
            device_id=device_id,
            mgmt_ip=mgmt_ip or "",
            hostname=hostname or "",
            try_ids=try_ids,
        )
        if _scaler_dev:
            _scaler_val = _clean_system_type(_scaler_dev.get("system_type"))
            if _scaler_val:
                ctx["system_type"] = _scaler_val
                ctx["system_type_source"] = "scaler_db"

    if not ctx["system_type"]:
        _backup_val = _scan_scaler_config_backups_for_system_type(try_ids)
        if _backup_val:
            ctx["system_type"] = _backup_val
            ctx["system_type_source"] = "config_backup"
            _persist_system_type_to_scaler_db(
                device_id=device_id,
                system_type=_backup_val,
                mgmt_ip=mgmt_ip or "",
                hostname=hostname or "",
                try_ids=try_ids,
            )

    if not ctx["system_type"] and inv_dev:
        _inv_val = _clean_system_type(inv_dev.get("system_type"))
        if _inv_val:
            ctx["system_type"] = _inv_val
            ctx["system_type_source"] = "inventory"

    # Auto-heal the curated cache when we land a live DNOS probe: the
    # operational.json write-through by the scaler extractor is the
    # authoritative source, so persist it to db/devices.json too. Guarded by
    # ``live`` so cached page loads don't keep rewriting the file.
    #
    # Tagged as ``dnos_live_probe`` so the persist-layer's operator-pin
    # guard lets a genuine live DNOS reading (e.g. cluster back from GI,
    # reporting CL-86) correct a stale operator pin. Cached reads without
    # ``live=True`` never reach this branch at all, so the pin remains
    # authoritative while the device is in GI.
    if live and ctx["system_type"] and ctx["system_type_source"] == "operational_json":
        _persist_system_type_to_scaler_db(
            device_id=device_id,
            system_type=ctx["system_type"],
            mgmt_ip=mgmt_ip or "",
            hostname=hostname or "",
            try_ids=try_ids,
            source="dnos_live_probe",
        )

    identity = _build_device_identity(
        device_id=device_id,
        ssh_host=ssh_host or "",
        mgmt_ip=mgmt_ip or "",
        scaler_device_id=scaler_device_id or "",
        hostname=hostname or "",
        serial=serial or "",
        config_hostname=config_hostname or "",
        try_ids=try_ids,
        inv_dev=inv_dev,
    )
    ctx["identity"] = identity

    # LLDP: prefer live SSH data (from parallel fetch), then cached operational.json, then inventory
    if live_ops.get("lldp"):
        ctx["lldp"] = list(live_ops["lldp"])
    if _has_protocol_ops(live_ops.get("protocols")):
        ctx["protocols"] = live_ops["protocols"]

    if not ctx["lldp"]:
        for try_id in try_ids:
            if not try_id:
                continue
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
            if ops_path.exists():
                try:
                    ops = _read_ops_safe(ops_path)
                    ctx["lldp"] = [_normalize_lldp_neighbor(n) for n in ops.get("lldp_neighbors", [])]
                    if ops.get("protocol_states") and not _has_protocol_ops(ctx.get("protocols")):
                        ctx["protocols"] = ops.get("protocol_states") or _empty_protocol_ops()
                    if ctx["lldp"]:
                        break
                except Exception:
                    pass

    if not ctx["lldp"] and inv_dev:
        ctx["lldp"] = [_normalize_lldp_neighbor(n) for n in inv_dev.get("lldp_neighbors", [])]

    # Stack/git/device_state: prefer live SSH data (from parallel fetch), then cached operational.json
    if live_ops.get("stack"):
        ctx["stack"] = list(live_ops["stack"])
    if live_ops.get("git_commit"):
        ctx["git_commit"] = live_ops["git_commit"]
    if live_ops.get("device_state"):
        ctx["device_state"] = live_ops["device_state"]
    if live_ops.get("active_ncc_node"):
        ctx["active_ncc_node"] = live_ops["active_ncc_node"]
    if _has_protocol_ops(live_ops.get("protocols")):
        ctx["protocols"] = live_ops["protocols"]

    # =================================================================
    # Cluster active-NCC pre-probe (live path only).
    # =================================================================
    # When the wizard requests a live context for a KVM cluster device
    # whose on-disk ``active_ncc_source`` is empty or untrusted (typical
    # after scaler's raw `connect_for_upgrade` write clobbered our
    # provenance), kick the resolver-side `_cluster_preprobe` so the
    # operational.json gets re-stamped with `active_ncc_source=
    # kvm_virsh_probe`. The downstream block (~line 4866) then surfaces
    # the trusted value into ``ctx`` instead of falling through to the
    # DNS / port-22 resolver which can't see GI-mode clusters.
    if live:
        for _try_id in try_ids:
            if not _try_id:
                continue
            _ops_path = Path(SCALER_ROOT) / "db" / "configs" / _try_id / "operational.json"
            if not _ops_path.exists():
                continue
            try:
                _pp_ops = _read_ops_safe(_ops_path)
            except Exception:
                _pp_ops = {}
            _is_cluster_pp = (
                _pp_ops.get("ncc_type") == "kvm"
                or _pp_ops.get("is_cluster") is True
            )
            if not _is_cluster_pp:
                break
            _src = (_pp_ops.get("active_ncc_source") or "").strip()
            _trusted = bool(_src) and any(
                _src.startswith(p) for p in _TRUSTED_ACTIVE_NCC_SOURCES
            )
            if _trusted:
                break
            try:
                from routes._device_mode_resolver import _cluster_preprobe as _pp_fn
                _pp_fn(_try_id, _pp_ops)
            except Exception as _exc:
                logger.debug(
                    "[ctx] cluster preprobe for %s failed: %s", _try_id, _exc
                )
            break

    for try_id in try_ids:
        if not try_id:
            continue
        # IMPORTANT: do NOT short-circuit here when stack/git_commit
        # are already populated (e.g. by the live SSH / virsh fallback
        # path). The block below also propagates cluster identity
        # (``active_ncc_vm``, ``ncc_type``, ``kvm_host``,
        # ``pre_upgrade_*``, ``is_cluster``) from ops into ctx, and
        # the wizard/iTerm/upgrade-NCC dropdown all depend on those
        # being present. Skipping this block when the live fetch
        # only filled stack+git was the root cause of the wizard
        # showing "(detecting...)" for cluster devices on a forced
        # live refresh -- stack came from virsh, but active_ncc_vm
        # never made it into ctx.
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / try_id / "operational.json"
        if ops_path.exists():
            try:
                ops = _read_ops_safe(ops_path)
                stack_comps = ops.get("stack_components", [])
                if stack_comps and not ctx["stack"]:
                    ctx["stack"] = [
                        {
                            "name": c.get("name", c.get("component", "")),
                            "hw_model": c.get("hw_model", "-"),
                            "revert": c.get("revert", "-"),
                            "current": c.get("current", "-"),
                            "target": c.get("target", "-"),
                        }
                        for c in stack_comps
                    ]
                    if not ctx.get("stack_fetched_at"):
                        _cached_ts = (
                            ops.get("stack_fetched_at")
                            or ops.get("connection_probe_at")
                            or ""
                        )
                        if not _cached_ts:
                            try:
                                import datetime as _dt
                                _mt = ops_path.stat().st_mtime
                                _cached_ts = _dt.datetime.utcfromtimestamp(_mt).strftime(
                                    "%Y-%m-%dT%H:%M:%SZ"
                                )
                            except Exception:
                                _cached_ts = ""
                        if _cached_ts:
                            ctx["stack_fetched_at"] = _cached_ts
                if ctx["git_commit"] is None and ops.get("git_commit"):
                    ctx["git_commit"] = ops["git_commit"]
                    if not ctx.get("git_commit_fetched_at") and ops.get("git_commit_fetched_at"):
                        ctx["git_commit_fetched_at"] = ops["git_commit_fetched_at"]
                if ops.get("protocol_states") and not _has_protocol_ops(ctx.get("protocols")):
                    ctx["protocols"] = ops.get("protocol_states") or _empty_protocol_ops()
                # For CLUSTER devices we leave active_ncc_ip to the
                # cluster-aware block below. Writing ``ops.mgmt_ip``
                # here is unsafe for a cluster because ``ops.mgmt_ip``
                # can temporarily hold the VIP (``100.64.4.98``) --
                # exactly the dead target that rejects dnroot in GI
                # and that the frontend iTerm path must NEVER hit.
                _is_cluster_dev = (
                    ops.get("ncc_type") == "kvm"
                    or ops.get("is_cluster") is True
                )
                if not ctx.get("active_ncc_ip") and ops.get("mgmt_ip") and not _is_cluster_dev:
                    ctx["active_ncc_ip"] = ops["mgmt_ip"]
                if ops.get("ncc_mgmt_ip") and not ctx.get("ncc_mgmt_ip"):
                    ctx["ncc_mgmt_ip"] = ops["ncc_mgmt_ip"]
                if ops.get("ssh_host") and not ctx.get("ssh_host"):
                    ctx["ssh_host"] = ops["ssh_host"]
                if ops.get("device_state") and not ctx.get("device_state"):
                    ctx["device_state"] = ops["device_state"]
                if not ctx.get("active_ncc_node") and ops.get("active_ncc_vm"):
                    ctx["active_ncc_node"] = ops["active_ncc_vm"]
                # Expose cluster / KVM identity so the frontend iTerm flow
                # can detect cluster devices WITHOUT relying on the canvas-
                # cached `sshConfig._isCluster` flag. After a fresh page
                # load that flag is often unset, which previously caused
                # the GI-mode / active-NCC iTerm branch to be skipped and
                # the raw NCC mgmt IP handed to the OS (landing the
                # operator on a recovery bash prompt instead of the real
                # active-NCC shell).
                _ncc_type_val = ops.get("ncc_type")
                if _ncc_type_val and not ctx.get("ncc_type"):
                    ctx["ncc_type"] = _ncc_type_val
                if _ncc_type_val == "kvm" and "is_cluster" not in ctx:
                    ctx["is_cluster"] = True
                if ops.get("active_ncc_vm") and not ctx.get("active_ncc_vm"):
                    ctx["active_ncc_vm"] = ops["active_ncc_vm"]
                # Expose the upgrade-start snapshot so the wizard can:
                #   (a) visibly label the "Deploy NCC" dropdown as
                #       "NCC-N (from upgrade start)" while an upgrade
                #       is in progress,
                #   (b) warn the operator if a live probe now disagrees
                #       (cluster may have failed over mid-upgrade).
                # When ``pre_upgrade_cleared_at`` is set we still
                # surface the historical values so the UI can display
                # "last upgrade used NCC-N" in post-upgrade states.
                if ops.get("pre_upgrade_active_ncc_vm") and not ctx.get("pre_upgrade_active_ncc_vm"):
                    ctx["pre_upgrade_active_ncc_vm"] = ops["pre_upgrade_active_ncc_vm"]
                if ops.get("pre_upgrade_active_ncc_source") and not ctx.get("pre_upgrade_active_ncc_source"):
                    ctx["pre_upgrade_active_ncc_source"] = ops["pre_upgrade_active_ncc_source"]
                if ops.get("pre_upgrade_snapshot_at") and not ctx.get("pre_upgrade_snapshot_at"):
                    ctx["pre_upgrade_snapshot_at"] = ops["pre_upgrade_snapshot_at"]
                if ops.get("pre_upgrade_cleared_at") and not ctx.get("pre_upgrade_cleared_at"):
                    ctx["pre_upgrade_cleared_at"] = ops["pre_upgrade_cleared_at"]
                if ops.get("kvm_host") and not ctx.get("kvm_host"):
                    ctx["kvm_host"] = ops["kvm_host"]
                if ops.get("kvm_host_ip") and not ctx.get("kvm_host_ip"):
                    ctx["kvm_host_ip"] = ops["kvm_host_ip"]
                if ops.get("ncc_vms") and not ctx.get("ncc_vms"):
                    ctx["ncc_vms"] = list(ops.get("ncc_vms") or [])
                if ops.get("ncc_hosts") and not ctx.get("ncc_hosts"):
                    ctx["ncc_hosts"] = list(ops.get("ncc_hosts") or [])
                if ops.get("last_working_method") and not ctx.get("last_working_method"):
                    ctx["last_working_method"] = ops["last_working_method"]
                if ops.get("hostname") and not ctx.get("hostname"):
                    ctx["hostname"] = ops["hostname"]
                if ops.get("recovery_mode_detected") is not None and "recovery_mode_detected" not in ctx:
                    ctx["recovery_mode_detected"] = bool(ops.get("recovery_mode_detected"))
                if ops.get("recovery_type") and not ctx.get("recovery_type"):
                    ctx["recovery_type"] = ops["recovery_type"]
                # For KVM clusters, expose the authoritative active NCC to
                # the frontend iTerm path.
                #
                # Source priority:
                #   1. `active_ncc_source == "kvm_*"` in ops -- the probe
                #      endpoint SSHed to the KVM host and read the live
                #      running-VM / VIP→MAC mapping. This is the only
                #      trustworthy signal in GI / RECOVERY, where the
                #      cluster VIP is unclaimed and both NCC hostnames
                #      DNS-resolve identically (or not at all).
                #   2. DNS-match resolution against the cluster VIP --
                #      works for healthy DNOS clusters but silently wrong
                #      in GI mode.
                #   3. DNS-fallback to ncc_vms[0] -- 50% chance wrong on
                #      a two-NCC cluster. Still better than "" which
                #      causes the frontend to skip the iTerm path.
                #
                # We avoid a second expensive `_probe_active_ncc_via_kvm`
                # call here -- the probe endpoint already wrote the result
                # to ops. Context callers who need a FRESH probe can
                # invoke `/api/ssh/probe` explicitly.
                try:
                    if (
                        ops.get("ncc_type") == "kvm"
                        and (ops.get("ncc_hosts") or ops.get("ncc_vms"))
                    ):
                        _ops_source = (ops.get("active_ncc_source") or "").strip()
                        _ops_active_vm = (ops.get("active_ncc_vm") or "").strip()
                        # Pre-upgrade snapshot recovery: if ops doesn't
                        # already hold a trusted value, try the resilient
                        # non-live sources (deploy_command snapshot, scaler
                        # DB cache, backup scan) BEFORE the DNS/port-22
                        # resolver can pollute the answer. Pin the result
                        # into ops in-memory so the trust check below
                        # treats it like a KVM-probe result. See
                        # ``_TRUSTED_ACTIVE_NCC_SOURCES``.
                        _is_trusted_ops_source = any(
                            _ops_source.startswith(p) for p in _TRUSTED_ACTIVE_NCC_SOURCES
                        )
                        if not (_ops_active_vm and _is_trusted_ops_source):
                            try:
                                _resolved_vm, _resolved_src = _resolve_active_ncc_best_effort(
                                    ops,
                                    device_id=device_id,
                                    scaler_device_id=scaler_device_id,
                                    hostname=hostname,
                                    mgmt_ip=mgmt_ip,
                                )
                            except Exception:
                                _resolved_vm, _resolved_src = "", ""
                            if _resolved_vm:
                                ops["active_ncc_vm"] = _resolved_vm
                                ops["active_ncc_source"] = _resolved_src
                                _ops_active_vm = _resolved_vm
                                _ops_source = _resolved_src
                                # Ctx copies above already ran from the
                                # old ops values (which could be empty);
                                # back-fill them now so the frontend
                                # (which reads ``active_ncc_node`` /
                                # ``active_ncc_vm`` on ctx) sees the
                                # recovered pre-upgrade snapshot.
                                ctx["active_ncc_node"] = _resolved_vm
                                ctx["active_ncc_vm"] = _resolved_vm
                                ctx["active_ncc_source"] = _resolved_src
                                # Remember this for future sessions so
                                # GI-mode wizards don't have to re-scan
                                # the backup directory on every open.
                                try:
                                    _persist_active_ncc_to_scaler_db(
                                        device_id=device_id,
                                        active_ncc_vm=_resolved_vm,
                                        source=_resolved_src,
                                        mgmt_ip=mgmt_ip,
                                        hostname=hostname,
                                        try_ids=[
                                            scaler_device_id, device_id, hostname,
                                        ],
                                    )
                                except Exception:
                                    pass
                        _vms_list = ops.get("ncc_vms") or []
                        _hosts_list = ops.get("ncc_hosts") or _vms_list
                        _ctx_state_recovery = str(
                            ctx.get("device_state") or ops.get("device_state") or ""
                        ).upper() in ("GI", "BASEOS_SHELL", "RECOVERY")
                        # Live monitor path: DeviceMonitor calls
                        # `/api/devices/<id>/context?live=true`, not the SSH
                        # probe endpoint. For GI/BASEOS/RECOVERY clusters we
                        # must actively refresh the active NCC here too;
                        # otherwise the canvas/SSH dialog can keep suggesting a
                        # stale `active_ncc_vm` (usually ncc0) until the user
                        # manually opens the SSH dialog and hits Verify.
                        if live and _ctx_state_recovery and _vms_list:
                            try:
                                _kvm_host = (
                                    ops.get("kvm_host_ip")
                                    or ops.get("kvm_host")
                                    or ""
                                )
                                _kvm_host = str(_kvm_host).split("/")[0].strip()
                                _kvm_cfg = (
                                    ops.get("kvm_host_credentials")
                                    or ops.get("kvm_credentials")
                                    or {}
                                )
                                _kvm_user = (_kvm_cfg.get("username") or "dn") or "dn"
                                _kvm_pass = (_kvm_cfg.get("password") or "drive1234!") or "drive1234!"
                                if _kvm_host:
                                    _mon_res = _probe_active_ncc_via_kvm(
                                        _kvm_host,
                                        _kvm_user,
                                        _kvm_pass,
                                        _vms_list,
                                        ops.get("ncc_mgmt_ip", ""),
                                        timeout_s=5,
                                    )
                                    _mon_vm = (_mon_res.get("active_ncc_host") or "").strip()
                                    _mon_src = (_mon_res.get("source") or "").strip()
                                    if _mon_vm and _mon_src.startswith("kvm_"):
                                        _ops_active_vm = _mon_vm
                                        _ops_source = _mon_src
                                        ops["active_ncc_vm"] = _mon_vm
                                        ops["active_ncc_source"] = _mon_src
                                        ctx["active_ncc_vm"] = _mon_vm
                                        ctx["active_ncc_node"] = _mon_vm
                                        ctx["active_ncc_host"] = _mon_vm
                                        ctx["active_ncc_source"] = _mon_src
                                        if _mon_res.get("active_ncc_ip"):
                                            ctx["active_ncc_ip"] = _mon_res.get("active_ncc_ip")
                                        if _mon_res.get("dns_map"):
                                            ctx["ncc_dns_map"] = dict(_mon_res.get("dns_map") or {})
                                        # Persist the monitored answer so the
                                        # next upgrade/virsh connection and the
                                        # SSH dialog both start from the same
                                        # active NCC.
                                        try:
                                            from ._ops_writer import update_ops as _update_ops_active_ncc

                                            def _mutate_active_ncc(d: dict,
                                                                   vm=_mon_vm,
                                                                   src=_mon_src) -> None:
                                                d["active_ncc_vm"] = vm
                                                d["active_ncc_source"] = src
                                                d["active_ncc_monitored_at"] = time.strftime(
                                                    "%Y-%m-%dT%H:%M:%SZ",
                                                    time.gmtime(),
                                                )

                                            _update_ops_active_ncc(
                                                ops_path,
                                                _mutate_active_ncc,
                                                create_if_missing=False,
                                            )
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                        # Always resolve DNS map so the frontend can pick
                        # per-node IP / hostname for iTerm. The DNS map
                        # gives us each NCC hostname's per-node IPv4 --
                        # this is what must go in active_ncc_ip for GI
                        # mode (NEVER the VIP, which rejects dnroot).
                        _dns_res = _resolve_active_ncc_host(
                            _hosts_list,
                            ops.get("ncc_mgmt_ip", ""),
                            _ops_active_vm,
                        )
                        if _dns_res.get("dns_map") and not ctx.get("ncc_dns_map"):
                            ctx["ncc_dns_map"] = dict(_dns_res["dns_map"])

                        # Decide active_ncc_host: trusted source verified >
                        # DNS match > DNS fallback. "Trusted" now covers:
                        #   - kvm_*                -- live virsh / KVM probe
                        #   - pre_upgrade_snapshot -- deploy_command / deploy_ncc_id
                        #   - pre_upgrade_backup   -- config-backup scan
                        #   - scaler_db_cache      -- curated devices.json
                        #   - topology_virsh_probe -- topology-side probe tag
                        _is_trusted_src = any(
                            _ops_source.startswith(p) for p in _TRUSTED_ACTIVE_NCC_SOURCES
                        )
                        if (
                            _is_trusted_src
                            and _ops_active_vm
                            and _ops_active_vm in (_vms_list or _hosts_list)
                        ):
                            if not ctx.get("active_ncc_host"):
                                ctx["active_ncc_host"] = _ops_active_vm
                                ctx["active_ncc_source"] = _ops_source
                        elif _dns_res.get("active_ncc_host") and not ctx.get("active_ncc_host"):
                            ctx["active_ncc_host"] = _dns_res["active_ncc_host"]
                            ctx["active_ncc_source"] = _dns_res.get("source", "")

                        # Decide active_ncc_ip:
                        #   GI / BASEOS_SHELL / RECOVERY:
                        #     -> DNS-resolved PER-NODE IP of the
                        #        active NCC (e.g. 100.64.11.96 for
                        #        kvm108-cl408d-ncc0). This is the
                        #        interface whose sshd accepts
                        #        dnroot; iTerm is supposed to land
                        #        here. FORCE-overwrite any earlier
                        #        value so a stale VIP cannot leak.
                        #   DNOS / healthy:
                        #     -> VIP (``ncc_mgmt_ip``) if present,
                        #        else DNS per-node.
                        _active_host = (ctx.get("active_ncc_host") or "").strip()
                        _per_node_ip = ""
                        if _active_host and isinstance(_dns_res.get("dns_map"), dict):
                            _cand = (_dns_res["dns_map"].get(_active_host) or "").strip()
                            if re.match(r"^\d+\.\d+\.\d+\.\d+$", _cand):
                                _per_node_ip = _cand
                        if _ctx_state_recovery:
                            if _per_node_ip:
                                ctx["active_ncc_ip"] = _per_node_ip
                            elif _dns_res.get("active_ncc_ip"):
                                ctx["active_ncc_ip"] = _dns_res["active_ncc_ip"]
                            # NEVER fall through to the VIP here.
                        else:
                            # Healthy DNOS / unknown: prefer the active NCC's
                            # PER-NODE IP (e.g. ``100.64.4.122`` for
                            # ``kvm108-cl408d-ncc1``) over the cluster VIP.
                            #
                            # Why per-node first instead of VIP:
                            #   - The per-node sshd accepts the universal
                            #     ``dnroot``/``dnroot`` lab credential pair
                            #     in every environment, while the VIP's
                            #     listener can be configured with a
                            #     cluster-VIP-specific password (observed
                            #     on YOR_CL_PE-4 27-Apr-2026: VIP rejected
                            #     dnroot/dnroot, NCC1 per-node accepted
                            #     it). Sending operators to the VIP is
                            #     therefore not safe as a default.
                            #   - The iTerm path on operators' Macs
                            #     usually has lab routing (VPN) but not
                            #     lab DNS, so an IP target avoids the
                            #     ``Could not resolve hostname`` failure
                            #     mode for hostname-based dispatches.
                            #   - The VIP stays exposed in
                            #     ``ctx["ncc_mgmt_ip"]`` for callers that
                            #     specifically need the VIP (cluster mgmt
                            #     UI, upgrade orchestration, automation).
                            #
                            # Order:
                            #   1. _per_node_ip      (DNS-resolved active NCC)
                            #   2. _dns_res.active_ncc_ip (resolver fallback)
                            #   3. VIP (only when no per-node IP available)
                            if not ctx.get("active_ncc_ip"):
                                if _per_node_ip:
                                    ctx["active_ncc_ip"] = _per_node_ip
                                elif _dns_res.get("active_ncc_ip"):
                                    ctx["active_ncc_ip"] = _dns_res["active_ncc_ip"]
                                else:
                                    _vip = (ops.get("ncc_mgmt_ip") or "").strip().split("/")[0]
                                    if _vip and re.match(r"^\d+\.\d+\.\d+\.\d+$", _vip):
                                        ctx["active_ncc_ip"] = _vip

                        # Informational hint for the frontend. The
                        # frontend is free to honour or ignore this --
                        # the iTerm-first flow does NOT read it, so
                        # operators still get iTerm in GI.
                        if _ctx_state_recovery:
                            ctx["recovery_access_note"] = (
                                "GI/BASEOS mode: VIP rejects dnroot; active_ncc_ip is "
                                "the per-node NCC IP (sshd accepts dnroot), and virsh "
                                "console via KVM host is the fallback."
                            )
                except Exception:
                    pass
                if not ctx.get("dnos_version") and ops.get("dnos_version"):
                    ctx["dnos_version"] = ops["dnos_version"]
            except Exception:
                pass

    if live and mgmt_ip and (
        ctx["stack"] or ctx["git_commit"] or live_ops.get("lldp") or _has_protocol_ops(ctx.get("protocols"))
    ):
        try:
            ops_dir = Path(SCALER_ROOT) / "db" / "configs" / scaler_device_id
            ops_dir.mkdir(parents=True, exist_ok=True)
            ops_path = ops_dir / "operational.json"
            from ._ops_writer import update_ops as _update_ops_ctx

            _live_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            # Mirror the timestamp into the in-flight ctx so the
            # response we return to the caller matches what we
            # actually persisted.
            if ctx["stack"]:
                ctx["stack_fetched_at"] = _live_ts
            if ctx["git_commit"]:
                ctx["git_commit_fetched_at"] = _live_ts

            def _mutate_ctx(ops_data: dict,
                            _ctx=ctx, _live_ops=live_ops,
                            _mgmt_ip=mgmt_ip, _hostname=config_hostname,
                            _identity=identity, _ts=_live_ts) -> None:
                if _ctx["stack"]:
                    ops_data["stack_components"] = _ctx["stack"]
                    ops_data["stack_fetched_at"] = _ts
                    for comp in _ctx["stack"]:
                        cname = (comp.get("name") or "").upper()
                        cver = comp.get("current") or ""
                        if cname == "DNOS" and cver and cver != "-":
                            ops_data["dnos_version"] = cver
                        elif cname == "BASEOS" and cver and cver != "-":
                            ops_data["baseos_version"] = cver
                        elif cname == "GI" and cver and cver != "-":
                            ops_data["gi_version"] = cver
                if _ctx["git_commit"]:
                    ops_data["git_commit"] = _ctx["git_commit"]
                    ops_data["git_commit_fetched_at"] = _ts
                if _live_ops.get("lldp"):
                    ops_data["lldp_neighbors"] = [
                        {"local_interface": n["local"], "neighbor_name": n["neighbor"], "neighbor_interface": n["remote"]}
                        for n in _live_ops["lldp"]
                    ]
                if _has_protocol_ops(_ctx.get("protocols")):
                    ops_data["protocol_states"] = _ctx["protocols"]
                    ops_data["protocol_states_fetched_at"] = _ts
                # Guardrailed write. Honours `_safe_set_mgmt_ip`'s veto
                # for KVM-host impersonation / reaped IPs. On rejection
                # we keep whatever mgmt_ip was already persisted so the
                # record stays consistent.
                _safe_set_mgmt_ip(ops_data, _mgmt_ip, source="build_device_context")
                if _hostname:
                    ops_data["hostname"] = _hostname
                if _ctx.get("device_state"):
                    # Do not blindly persist an incoming DNOS classification
                    # when the DB already says GI/BASEOS_SHELL. The Phase-2
                    # live-SSH probe can land on the KVM host's bash prompt
                    # and misclassify as DNOS; let `connect_for_upgrade` own
                    # the authoritative state transitions (it already has
                    # drift detection) and only accept same-class or
                    # same-direction updates here.
                    _incoming_state = str(_ctx["device_state"]).upper()
                    _prev_state = (ops_data.get("device_state") or "").upper()
                    _gi_class = {"GI", "BASEOS_SHELL", "DEPLOYING", "UPGRADING", "RECOVERY"}
                    _delete_in_flight = bool(
                        ops_data.get("_delete_pending")
                        or ops_data.get("delete_initiated")
                    )
                    _phantom_downgrade = (
                        _incoming_state == "DNOS"
                        and (_prev_state in _gi_class or _delete_in_flight)
                    )
                    if _phantom_downgrade:
                        try:
                            from datetime import datetime as _dt2, timezone as _tz2
                            _pe = ops_data.get("_phantom_dnos_events")
                            if not isinstance(_pe, list):
                                _pe = []
                            _pe.append({
                                "at": _dt2.now(_tz2.utc).isoformat(),
                                "prev_state": _prev_state,
                                "probe_mode": _incoming_state,
                                "source": "build_device_context",
                            })
                            ops_data["_phantom_dnos_events"] = _pe[-10:]
                        except Exception:
                            pass
                    else:
                        ops_data["device_state"] = _ctx["device_state"]
                ops_data["_identity"] = _identity

            _update_ops_ctx(ops_path, _mutate_ctx, create_if_missing=True)
        except Exception:
            pass

    iface_details = (inv_dev or {}).get("interface_details", {})

    if config:
        try:
            from scaler.wizard.interfaces import _get_all_interfaces_from_config, categorize_interfaces_by_type, get_bundle_members
            from scaler.wizard.parsers import get_wan_interfaces, parse_existing_evpn_services

            all_ifaces = _get_all_interfaces_from_config(config)
            cats = categorize_interfaces_by_type(all_ifaces)

            for name in cats.get("physical", []):
                det = iface_details.get(name, {})
                ctx["interfaces"]["physical"].append({
                    "name": name,
                    "speed": (det.get("speed") or "").strip(",") or "",
                    "bundle": det.get("bundle", ""),
                    "oper": "up" if any(s.get("oper") == "up" for s in det.get("sub_interfaces", [{}])) else "",
                })

            max_bundle_num = 0
            for name in cats.get("bundle", []):
                try:
                    members = get_bundle_members(name, config)
                except Exception:
                    members = []
                ctx["interfaces"]["bundle"].append({"name": name, "members": members})
                m = re.search(r"bundle-?(?:ether)?(\d+)", name, re.I)
                if m:
                    max_bundle_num = max(max_bundle_num, int(m.group(1)))
            ctx["next_bundle_number"] = max_bundle_num + 1

            for name in (cats.get("bundle_subif", []) + cats.get("physical_subif", [])):
                ctx["interfaces"]["subinterface"].append({"name": name, "vlan": name.split(".")[-1] if "." in name else ""})

            for name in cats.get("pwhe", []):
                ctx["interfaces"]["pwhe"].append({"name": name})

            used = set()
            for b in ctx["interfaces"]["bundle"]:
                used.update(b.get("members", []))
            for p in ctx["interfaces"]["physical"]:
                if p["name"] not in used and not p.get("bundle"):
                    ctx["interfaces"]["free_physical"].append(p["name"])

            ctx["wan_interfaces"] = get_wan_interfaces(config)

            protocols = config
            if "isis" in protocols.lower():
                ctx["igp"]["protocol"] = "isis"
            elif "ospf" in protocols.lower():
                ctx["igp"]["protocol"] = "ospf"
            ctx["igp"]["interfaces"] = list(ctx["wan_interfaces"])

            ctx["config_summary"] = _build_config_summary(config)

            evpn = parse_existing_evpn_services(config)
            fxc = evpn.get("fxc", [])
            vpls = evpn.get("vpls", [])
            ctx["services"]["fxc_count"] = len(fxc)
            ctx["services"]["vrf_count"] = len(evpn.get("mpls", []))
            max_evi = 999
            for s in fxc + vpls:
                rd = s.get("rd", "")
                if rd and ":" in rd:
                    try:
                        max_evi = max(max_evi, int(rd.split(":")[-1]))
                    except ValueError:
                        pass
            ctx["services"]["next_evi"] = max_evi + 1

            from scaler.wizard.parsers import (
                parse_vrf_instances,
                parse_l2vpn_bridge_domains,
                parse_all_routing_policies,
                parse_existing_multihoming,
            )
            ctx["vrfs"] = parse_vrf_instances(config)
            ctx["bridge_domains"] = parse_l2vpn_bridge_domains(config)
            ctx["routing_policies"] = parse_all_routing_policies(config)
            ctx["multihoming"] = parse_existing_multihoming(config)

            flp = re.findall(r"flowspec-local-policies.*?policy\s+(\S+)", config, re.DOTALL)
            ctx["flowspec_policies"] = list(dict.fromkeys(flp))

            nbr_pattern = re.compile(r"neighbor\s+(\d+\.\d+\.\d+\.\d+)\s*\n\s*remote-as\s+(\d+)")
            seen = set()
            for m in nbr_pattern.finditer(config):
                ip_as = (m.group(1), m.group(2))
                if ip_as not in seen:
                    seen.add(ip_as)
                    ctx["bgp_peers"].append({"ip": m.group(1), "remote_as": int(m.group(2))})

            lo_pattern = re.compile(r"^\s*(lo\d+)\s*$.*?ipv4-address\s+(\S+)", re.MULTILINE | re.DOTALL)
            for m in lo_pattern.finditer(config):
                ctx["loopbacks"].append({"name": m.group(1), "ip": m.group(2)})

            ctx["platform_limits"] = _load_limits(device_id)

            # Phase 2B: Enhanced context fields
            try:
                from scaler.wizard.scale_operations import (
                    _detect_l2ac_parent_from_config_str,
                    _detect_bgp_neighbors,
                    _generate_scale_up_suggestions,
                    parse_services_from_config,
                    _scan_used_route_targets,
                    _scan_used_vrf_numbers,
                )
                ctx["detected_l2ac_parent"] = _detect_l2ac_parent_from_config_str(config)
                ctx["detected_bgp_neighbors"] = _detect_bgp_neighbors(config)
                rt_used = _scan_used_route_targets(config, "65000")
                ctx["existing_route_targets"] = [f"65000:{n}" for n in sorted(rt_used)]
                ctx["next_free"]["rt"] = next((n for n in range(1, 65536) if n not in rt_used), 1)
                vrf_used = _scan_used_vrf_numbers(config, "VRF-")
                ctx["next_free"]["vrf_number"] = next((n for n in range(1, 65536) if n not in vrf_used), 1)
                device_services = {scaler_device_id: parse_services_from_config(config)}
                class _MinimalCtx:
                    configs = {scaler_device_id: config}
                suggestions = _generate_scale_up_suggestions(_MinimalCtx(), device_services)
                ctx["scale_suggestions"] = [{k: v for k, v in s.items() if k != "apply_func" and not callable(v)} for s in suggestions]
                lo0_ip = next((lb["ip"] for lb in ctx["loopbacks"] if lb.get("name") == "lo0"), None)
                if lo0_ip:
                    from scaler.wizard.igp import ip_to_isis_net
                    ctx["lo0_isis_net"] = ip_to_isis_net(lo0_ip, "49.0001")
                rp = ctx.get("routing_policies") or {}
                policy_names = [p.get("name") for p in rp.get("policies", []) if p.get("name")]
                ctx["policy_suggestions"] = policy_names
            except ImportError:
                pass
            except Exception:
                pass

        except ImportError as e:
            ctx["config_summary"] = {"error": str(e)}
        except Exception as e:
            ctx["config_summary"] = {"error": str(e)}

    return ctx


def _compute_wizard_suggestions(device_id: str, completed_wizard: str, created_data: dict, ctx: dict) -> list:
    """Compute next-wizard suggestions from completed wizard and created data."""
    suggestions = []
    interfaces = created_data.get("interfaces") or []
    loopback_ip = created_data.get("loopback_ip") or created_data.get("loopback")
    vrfs = created_data.get("vrfs") or []
    has_interfaces = bool(interfaces)
    has_loopback = bool(loopback_ip)
    has_vrfs = bool(vrfs)

    if completed_wizard == "interfaces":
        if has_interfaces:
            suggestions.append({
                "wizard": "vrf",
                "reason": "Attach new sub-interfaces to VRFs",
                "prefill": {"attachInterfaces": True, "interfaceList": interfaces},
            })
            suggestions.append({
                "wizard": "service",
                "reason": "Create FXC/VPWS with these interfaces",
                "prefill": {"attachInterfaces": True, "interfaceList": interfaces},
            })
        if has_loopback or has_interfaces:
            igp_ifaces = (["lo0"] if has_loopback else []) + list(interfaces)
            suggestions.append({
                "wizard": "igp",
                "reason": "Add loopback + interfaces to IGP",
                "prefill": {"interfaces": igp_ifaces, "router_ip": loopback_ip},
            })
            suggestions.append({
                "wizard": "bgp",
                "reason": "Configure BGP with loopback as update-source",
                "prefill": {"update_source": "lo0", "router_id": loopback_ip},
            })
    elif completed_wizard in ("services", "bridge-domain"):
        if has_interfaces:
            suggestions.append({
                "wizard": "multihoming",
                "reason": "Add multihoming ESI to L2 interfaces",
                "prefill": {"interfaces": interfaces},
            })
        suggestions.append({"wizard": "flowspec", "reason": "Add FlowSpec local policy", "prefill": {}})
    elif completed_wizard == "vrf":
        if has_vrfs:
            suggestions.append({
                "wizard": "bgp",
                "reason": "Add BGP VRF instance for new VRFs",
                "prefill": {"vrfs": vrfs},
            })
        suggestions.append({"wizard": "flowspec-vpn", "reason": "Add FlowSpec VPN policy", "prefill": {"vrfs": vrfs}})
    elif completed_wizard == "igp":
        suggestions.append({"wizard": "bgp", "reason": "Configure BGP peers", "prefill": {"update_source": "lo0"}})
    elif completed_wizard == "bgp":
        suggestions.append({"wizard": "flowspec", "reason": "Enable BGP FlowSpec AFI on neighbors", "prefill": {}})
    elif completed_wizard in ("flowspec", "flowspec-vpn"):
        suggestions.append({"wizard": "routing-policy", "reason": "Create routing policy for BGP attach", "prefill": {}})

    return suggestions

