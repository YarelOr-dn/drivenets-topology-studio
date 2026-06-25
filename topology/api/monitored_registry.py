"""Auto-monitor reference-counted device registry (shared SQLite DAL).

Companion design doc: ``topology/docs/AUTO_MONITOR_ON_ATTACH.md``.

The shared registry is the canonical "who is monitoring this device" record.
A second user attaching the same device on a different topology bumps the
reference count instead of spinning up a duplicate poller. Removal stops
monitoring only when the last reference detaches AND the device is not a
``legacy_global`` baseline device (PE-1 / PE-4 / DNAAS-* etc., backfilled
from ``~/SCALER/db/devices.json`` in Phase 3).

Storage layout (matches the existing ``topology/api/device_state.py`` pattern):

  ~/.topology_shared/monitored_registry.db   -- WAL + busy_timeout=5000
  ~/.topology_shared/                          -- mode 0700
  monitored_registry.db                        -- mode 0600

Tables
------

* ``devices(key TEXT PRIMARY KEY, ...)`` -- one row per
  ``key = "<management_ip>|<serial_number>"``. Cluster devices key on the
  CHASSIS mgmt-IP; per-NCC IPs go in ``cluster_ncc_ips_json`` (OQ-3).
* ``references(key, username, scope_type, scope_id, attached_at)`` -- one row
  per (device, user, scope). PK includes ``username`` so user A's detach
  can never delete user B's reference.
* ``monitoring_subsystems(key, subsystem, status, last_run_at, last_error)``
  -- one row per (device, subsystem). Phase 2 populates a small set
  (``scaler_devices_mirror``, ``network_mapper``); future phases extend.
* ``audit_log(id, at, actor, action, key, payload_json)`` -- append-only
  trail. Useful for forensics ("when did user X register PE-9?").

Pure stdlib + sqlite3. No FastAPI imports. The DAL is callable from any
process (bridge, serve, scripts) and is safe under multi-user contention
because every write goes through the module-level ``_WRITE_LOCK`` and
every connection runs ``PRAGMA journal_mode=WAL`` + ``busy_timeout=5000``.

This module NEVER stores credentials. The per-user
``~/.topology_users/<u>/devices.json`` file (managed by
``api/auth/router.py``) is the only place a password lives. The registry
just records ``credentials_id`` (a string the dispatch layer understands).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import settings


REGISTRY_DB_PATH = Path(settings.shared_topologies_dir).expanduser() / "monitored_registry.db"

# All known subsystem identifiers Phase 2 / Phase 3 will populate. Kept as a
# canonical list so `bring_up` / `tear_down` can iterate without a magic
# string scattered through the dispatch layer.
SUBSYSTEM_SCALER_MIRROR = "scaler_devices_mirror"
SUBSYSTEM_NETWORK_MAPPER = "network_mapper"
SUBSYSTEM_SUBIF_DESCRIPTION = "subif_description"
SUBSYSTEM_LINK_TELEMETRY = "link_telemetry"
SUBSYSTEM_ALARMS_HEALTH = "alarms_health"

ALL_SUBSYSTEMS = (
    SUBSYSTEM_SCALER_MIRROR,
    SUBSYSTEM_NETWORK_MAPPER,
    SUBSYSTEM_SUBIF_DESCRIPTION,
    SUBSYSTEM_LINK_TELEMETRY,
    SUBSYSTEM_ALARMS_HEALTH,
)

# Action verbs recorded in audit_log. Keep stable -- the audit log is
# append-only and consumers grep for these tokens.
ACTION_REGISTERED = "registered"
ACTION_REFERENCE_ADDED = "reference_added"
ACTION_REFERENCE_REMOVED = "reference_removed"
ACTION_TEARDOWN = "teardown"
ACTION_LEGACY_BACKFILL = "legacy_backfill"
ACTION_SUBSYSTEM_STATUS = "subsystem_status"

_WRITE_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_key(management_ip: str, serial_number: str) -> str:
    """Compose the canonical registry key.

    Empty serial number is allowed (some devices in BASEOS / RECOVERY mode
    don't expose one yet); the dispatch layer can fill it in on a later
    refresh and re-key. The key is ``"<ip>|<sn>"`` so a future migration
    can split it cheaply.
    """
    ip = (management_ip or "").strip()
    sn = (serial_number or "").strip()
    if not ip:
        raise ValueError("make_key: management_ip is required")
    return f"{ip}|{sn}"


def _is_ip(value: str) -> bool:
    parts = (value or "").strip().split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def _is_generated_canvas_label(value: str) -> bool:
    return bool(re.match(r"^(NCP|NCP-\d+|S|S\d+)$", (value or "").strip(), re.I))


def _should_replace_management_ip(existing_value: str, incoming_value: str) -> bool:
    """Avoid downgrading a canonical IP to a typed serial/NCC hostname."""
    existing = (existing_value or "").strip()
    incoming = (incoming_value or "").strip()
    if not incoming:
        return False
    if not existing:
        return True
    if _is_ip(incoming):
        return True
    if _is_ip(existing):
        return False
    return existing != incoming


def _ensure_shared_dir(path: Path) -> None:
    """Create the parent dir with restrictive perms.

    The same dir holds ``_device_state.db`` already, so don't lower perms
    if the caller already chmodded it tighter. Only attempt to RAISE perms
    toward 0700 when we just created the directory.
    """
    parent = path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except OSError:
            pass


@contextlib.contextmanager
def _open_db():
    _ensure_shared_dir(REGISTRY_DB_PATH)
    is_new = not REGISTRY_DB_PATH.exists()
    # ``isolation_level=None`` matches the pattern used by
    # ``api/device_state.py``: every statement auto-commits, which is
    # what we want for an audit-style DAL where writes need to survive
    # the connection close even on the happy path. Without this flag
    # Python's sqlite3 module wraps DML in an implicit transaction that
    # rolls back at close() unless the caller explicitly commits, and
    # silent rollbacks are exactly the failure mode that
    # ``test_monitored_registry_unit.py`` caught.
    conn = sqlite3.connect(str(REGISTRY_DB_PATH), timeout=5.0,
                           isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass
        if is_new:
            try:
                os.chmod(REGISTRY_DB_PATH, 0o600)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _ensure_schema() -> None:
    with _WRITE_LOCK, _open_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                key TEXT PRIMARY KEY,
                management_ip TEXT NOT NULL,
                serial_number TEXT NOT NULL DEFAULT '',
                hostname TEXT NOT NULL DEFAULT '',
                platform TEXT NOT NULL DEFAULT '',
                is_cluster INTEGER NOT NULL DEFAULT 0,
                cluster_ncc_ips_json TEXT NOT NULL DEFAULT '[]',
                last_seen_ok TEXT,
                legacy_global INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_devices_ip
            ON devices(management_ip)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_devices_hostname
            ON devices(hostname)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS references_tbl (
                key TEXT NOT NULL,
                username TEXT NOT NULL,
                scope_type TEXT NOT NULL DEFAULT 'topology',
                scope_id TEXT NOT NULL DEFAULT '',
                attached_at TEXT NOT NULL,
                PRIMARY KEY (key, username, scope_type, scope_id),
                FOREIGN KEY (key) REFERENCES devices(key) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_refs_user
            ON references_tbl(username)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_subsystems (
                key TEXT NOT NULL,
                subsystem TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                last_run_at TEXT,
                last_error TEXT,
                PRIMARY KEY (key, subsystem),
                FOREIGN KEY (key) REFERENCES devices(key) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                at TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                key TEXT,
                payload_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_at
            ON audit_log(at)
        """)


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

def upsert_device(
    *,
    management_ip: str,
    serial_number: str,
    hostname: str,
    platform: str = "",
    is_cluster: bool = False,
    cluster_ncc_ips: Optional[List[str]] = None,
    actor: str,
    legacy_global: bool = False,
) -> Dict[str, Any]:
    """Insert or merge-update the device row.

    The key is recomputed from ``management_ip`` + ``serial_number``. If a
    row already exists for this key, fields that the caller supplied
    (non-empty) overwrite the stored row; empty / None values are
    preserved from the existing row so a second registration that didn't
    know the platform doesn't blank it.

    Sets ``last_seen_ok`` to "now" because every upsert in MVP is the
    response to a successful verify call. Phase 4 may split this into a
    separate ``mark_seen_ok`` helper for the discovery path.

    Returns the persisted row as a dict, including a
    ``newly_inserted`` boolean.
    """
    key = make_key(management_ip, serial_number)
    now = _now_iso()
    payload_ips = json.dumps(list(cluster_ncc_ips or []))
    cleaned = {
        "management_ip": (management_ip or "").strip(),
        "serial_number": (serial_number or "").strip(),
        "hostname": (hostname or "").strip(),
        "platform": (platform or "").strip(),
        "is_cluster": 1 if is_cluster else 0,
        "cluster_ncc_ips_json": payload_ips,
        "legacy_global": 1 if legacy_global else 0,
    }

    with _WRITE_LOCK, _open_db() as conn:
        member_reuse = False
        existing = None
        if is_cluster and cleaned["management_ip"]:
            rows = conn.execute(
                "SELECT * FROM devices WHERE is_cluster=1 AND cluster_ncc_ips_json LIKE ?",
                (f"%{cleaned['management_ip']}%",),
            ).fetchall()
            for candidate in rows:
                try:
                    members = json.loads(candidate["cluster_ncc_ips_json"] or "[]")
                except Exception:
                    members = []
                if cleaned["management_ip"] not in [str(m).strip() for m in members]:
                    continue
                existing_serial = (candidate["serial_number"] or "").strip()
                incoming_serial = cleaned["serial_number"]
                if existing_serial and incoming_serial and existing_serial != incoming_serial:
                    continue
                key = candidate["key"]
                existing = candidate
                member_reuse = True
                break

        if existing is None:
            existing = conn.execute(
                "SELECT * FROM devices WHERE key=?", (key,),
            ).fetchone()
        if existing is None and cleaned["serial_number"]:
            existing = conn.execute(
                """SELECT * FROM devices
                   WHERE serial_number=?
                      OR management_ip=?
                      OR key=?
                   ORDER BY updated_at DESC
                   LIMIT 1""",
                (
                    cleaned["serial_number"],
                    cleaned["serial_number"],
                    f"{cleaned['serial_number']}|",
                ),
            ).fetchone()
        if existing is None and cleaned["hostname"] and not _is_generated_canvas_label(cleaned["hostname"]):
            existing = conn.execute(
                """SELECT * FROM devices
                   WHERE lower(hostname)=lower(?)
                   ORDER BY updated_at DESC
                   LIMIT 1""",
                (cleaned["hostname"],),
            ).fetchone()
        if existing:
            # Field-level merge: only overwrite when the new value is
            # non-empty. legacy_global is "sticky-true" -- once set it
            # stays set even if a later upsert omits it.
            row = dict(existing)
            updated = dict(row)
            for col in ("management_ip", "serial_number", "hostname", "platform"):
                if member_reuse and col == "management_ip":
                    continue
                if col == "management_ip" and not _should_replace_management_ip(row.get(col, ""), cleaned[col]):
                    continue
                if cleaned[col]:
                    updated[col] = cleaned[col]
            updated["is_cluster"] = cleaned["is_cluster"] or row["is_cluster"]
            if cluster_ncc_ips is not None:
                if member_reuse:
                    try:
                        current_members = json.loads(row.get("cluster_ncc_ips_json") or "[]")
                    except Exception:
                        current_members = []
                    merged_members = list(dict.fromkeys(
                        [str(m).strip() for m in current_members if str(m).strip()]
                        + [str(m).strip() for m in (cluster_ncc_ips or []) if str(m).strip()]
                    ))
                    updated["cluster_ncc_ips_json"] = json.dumps(merged_members)
                else:
                    updated["cluster_ncc_ips_json"] = cleaned["cluster_ncc_ips_json"]
            if cleaned["legacy_global"]:
                updated["legacy_global"] = 1
            updated["last_seen_ok"] = now
            updated["updated_at"] = now
            conn.execute(
                """UPDATE devices SET
                    management_ip=?, serial_number=?, hostname=?, platform=?,
                    is_cluster=?, cluster_ncc_ips_json=?, legacy_global=?,
                    last_seen_ok=?, updated_at=?
                   WHERE key=?""",
                (
                    updated["management_ip"], updated["serial_number"],
                    updated["hostname"], updated["platform"],
                    updated["is_cluster"], updated["cluster_ncc_ips_json"],
                    updated["legacy_global"], updated["last_seen_ok"],
                    updated["updated_at"], key,
                ),
            )
            newly = False
            row_dict = updated
        else:
            conn.execute(
                """INSERT INTO devices
                   (key, management_ip, serial_number, hostname, platform,
                    is_cluster, cluster_ncc_ips_json, last_seen_ok,
                    legacy_global, created_at, updated_at, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    key, cleaned["management_ip"], cleaned["serial_number"],
                    cleaned["hostname"], cleaned["platform"],
                    cleaned["is_cluster"], cleaned["cluster_ncc_ips_json"],
                    now, cleaned["legacy_global"], now, now, actor,
                ),
            )
            newly = True
            row_dict = {
                "key": key,
                **cleaned,
                "last_seen_ok": now,
                "created_at": now,
                "updated_at": now,
                "created_by": actor,
            }
        _record_audit_inline(
            conn,
            actor=actor,
            action=ACTION_REGISTERED if newly else "updated",
            key=key,
            payload={"hostname": cleaned["hostname"], "ip": cleaned["management_ip"]},
        )

    out = dict(row_dict)
    out["newly_inserted"] = newly
    out["cluster_ncc_ips"] = json.loads(out.get("cluster_ncc_ips_json") or "[]")
    out["is_cluster"] = bool(out.get("is_cluster"))
    out["legacy_global"] = bool(out.get("legacy_global"))
    return out


def find_by_key(key: str) -> Optional[Dict[str, Any]]:
    if not key:
        return None
    with _open_db() as conn:
        row = conn.execute(
            "SELECT * FROM devices WHERE key=?", (key,),
        ).fetchone()
    return _row_to_device(row) if row else None


def find_by_ip(management_ip: str) -> Optional[Dict[str, Any]]:
    """Look up a device by primary chassis mgmt-IP.

    Cluster devices may also have a ``cluster_ncc_ips_json`` member that
    matches the lookup IP -- we match those too so a user attaching a
    per-NCC IP still resolves to the chassis row. Returns the FIRST
    match (registry currently keys on chassis IP, so duplicates only
    arise from a buggy backfill).
    """
    ip = (management_ip or "").strip()
    if not ip:
        return None
    with _open_db() as conn:
        row = conn.execute(
            "SELECT * FROM devices WHERE management_ip=?", (ip,),
        ).fetchone()
        if row:
            return _row_to_device(row)
        # Fallback: scan cluster rows for per-NCC IP membership.
        rows = conn.execute(
            "SELECT * FROM devices WHERE is_cluster=1 AND cluster_ncc_ips_json LIKE ?",
            (f"%{ip}%",),
        ).fetchall()
    for r in rows:
        try:
            members = json.loads(r["cluster_ncc_ips_json"] or "[]")
        except Exception:
            members = []
        if ip in [str(m).strip() for m in members]:
            return _row_to_device(r)
    return None


def list_devices(*, only_user: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return every device row, optionally filtered to ones the user has
    a reference for.

    The ``only_user`` filter is a JOIN against ``references_tbl``; it is
    used by the ``GET /api/devices/monitored`` endpoint to scope the
    listing per-caller. When ``only_user`` is None the call returns the
    whole shared registry (for admin tooling / backfill auditing).
    """
    with _open_db() as conn:
        if only_user:
            rows = conn.execute(
                """SELECT d.* FROM devices d
                   JOIN references_tbl r ON r.key = d.key
                   WHERE r.username = ?
                   GROUP BY d.key
                   ORDER BY d.hostname, d.management_ip""",
                ((only_user or "").strip(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM devices ORDER BY hostname, management_ip"
            ).fetchall()
    return [_row_to_device(r) for r in rows]


def _row_to_device(row: sqlite3.Row) -> Dict[str, Any]:
    if row is None:
        return {}
    d = dict(row)
    try:
        d["cluster_ncc_ips"] = json.loads(d.get("cluster_ncc_ips_json") or "[]")
    except Exception:
        d["cluster_ncc_ips"] = []
    d["is_cluster"] = bool(d.get("is_cluster"))
    d["legacy_global"] = bool(d.get("legacy_global"))
    return d


def mark_seen_ok(key: str) -> None:
    """Stamp ``last_seen_ok`` without changing other fields.

    Phase 3+ pollers call this after every successful refresh so the
    smooth-ZTP path can decide if the cached state is fresh enough to
    skip a verify probe on first paint.
    """
    if not key:
        return
    now = _now_iso()
    with _WRITE_LOCK, _open_db() as conn:
        conn.execute(
            "UPDATE devices SET last_seen_ok=?, updated_at=? WHERE key=?",
            (now, now, key),
        )


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------

def add_reference(
    *,
    key: str,
    username: str,
    scope_type: str = "topology",
    scope_id: str = "",
) -> Dict[str, Any]:
    """Idempotent attach. Returns the canonical reference state.

    The PK is ``(key, username, scope_type, scope_id)``. Re-attaching the
    same scope is a no-op (no duplicate row, attached_at preserved). Use
    ``scope_type='canvas'`` + ``scope_id=''`` for the simple "this user
    has the device on a canvas somewhere" case; Phase 3 will use
    ``scope_type='topology'`` + ``scope_id=<topology_id>`` to support
    topology-file-delete cleanup (OQ-5).
    """
    key = (key or "").strip()
    username = (username or "").strip()
    if not key or not username:
        raise ValueError("add_reference requires key and username")
    scope_type = (scope_type or "topology").strip() or "topology"
    scope_id = (scope_id or "").strip()
    now = _now_iso()
    is_new = False
    with _WRITE_LOCK, _open_db() as conn:
        # Verify the device exists before allowing a reference.
        exists = conn.execute(
            "SELECT 1 FROM devices WHERE key=?", (key,),
        ).fetchone()
        if not exists:
            raise ValueError(f"add_reference: unknown device key {key!r}")
        prior = conn.execute(
            "SELECT 1 FROM references_tbl WHERE key=? AND username=? "
            "AND scope_type=? AND scope_id=?",
            (key, username, scope_type, scope_id),
        ).fetchone()
        if not prior:
            conn.execute(
                "INSERT INTO references_tbl "
                "(key, username, scope_type, scope_id, attached_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (key, username, scope_type, scope_id, now),
            )
            is_new = True
        _record_audit_inline(
            conn,
            actor=username,
            action=ACTION_REFERENCE_ADDED if is_new else "reference_idempotent",
            key=key,
            payload={"scope_type": scope_type, "scope_id": scope_id},
        )
    return {
        "key": key,
        "username": username,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "newly_attached": is_new,
        "attached_at": now,
    }


def remove_reference(
    *,
    key: str,
    username: str,
    scope_type: str = "topology",
    scope_id: str = "",
) -> Dict[str, Any]:
    """Remove the caller's reference and report whether any remain.

    Response shape::

        {
          "key": ...,
          "removed": bool,           # true if a row actually went away
          "user_references_remaining": int,    # for THIS username only
          "references_count_total": int,       # across all users
          "is_last_reference": bool, # true when references_count_total == 0
          "would_stop_monitoring": bool,
            # is_last_reference AND not legacy_global. The frontend uses
            # this to decide whether to surface the "Stop monitoring this
            # device?" modal -- legacy global devices are never torn down
            # even when references hit zero.
        }
    """
    key = (key or "").strip()
    username = (username or "").strip()
    if not key or not username:
        raise ValueError("remove_reference requires key and username")
    scope_type = (scope_type or "topology").strip() or "topology"
    scope_id = (scope_id or "").strip()
    with _WRITE_LOCK, _open_db() as conn:
        cur = conn.execute(
            "DELETE FROM references_tbl WHERE key=? AND username=? "
            "AND scope_type=? AND scope_id=?",
            (key, username, scope_type, scope_id),
        )
        removed = cur.rowcount > 0
        user_remaining = int(conn.execute(
            "SELECT COUNT(*) AS n FROM references_tbl WHERE key=? AND username=?",
            (key, username),
        ).fetchone()["n"])
        total = int(conn.execute(
            "SELECT COUNT(*) AS n FROM references_tbl WHERE key=?",
            (key,),
        ).fetchone()["n"])
        legacy_row = conn.execute(
            "SELECT legacy_global FROM devices WHERE key=?", (key,),
        ).fetchone()
        legacy = bool(legacy_row["legacy_global"]) if legacy_row else False
        if removed:
            _record_audit_inline(
                conn,
                actor=username,
                action=ACTION_REFERENCE_REMOVED,
                key=key,
                payload={
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "user_remaining": user_remaining,
                    "total_remaining": total,
                },
            )
    return {
        "key": key,
        "removed": removed,
        "user_references_remaining": user_remaining,
        "references_count_total": total,
        "is_last_reference": total == 0,
        "would_stop_monitoring": (total == 0) and not legacy,
    }


def list_references(
    *,
    key: Optional[str] = None,
    username: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filtered listing of references. Used by the GET endpoint and by
    the modal-confirmation flow."""
    where: List[str] = []
    params: List[Any] = []
    if key:
        where.append("key=?")
        params.append(key.strip())
    if username:
        where.append("username=?")
        params.append(username.strip())
    sql = "SELECT key, username, scope_type, scope_id, attached_at FROM references_tbl"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY attached_at DESC"
    with _open_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def reference_summary(key: str) -> Dict[str, Any]:
    """Counts + per-user list (REDACTED for the public endpoint).

    The caller (route handler) decides whether to expose the per-user
    list or only the total count, per the multi-user safety contract:
    user A must NEVER see who else is watching the device unless they
    are an admin.
    """
    if not key:
        return {"key": "", "total": 0, "users": []}
    with _open_db() as conn:
        rows = conn.execute(
            "SELECT username, scope_type, scope_id, attached_at "
            "FROM references_tbl WHERE key=? ORDER BY attached_at",
            (key,),
        ).fetchall()
    return {
        "key": key,
        "total": len(rows),
        "users": [dict(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# Monitoring subsystems
# ---------------------------------------------------------------------------

def update_subsystem_status(
    *,
    key: str,
    subsystem: str,
    status: str,
    last_error: Optional[str] = None,
) -> None:
    """Upsert the subsystem health row for a device.

    ``status`` is free-form but the conventional values are:
        ``pending`` (registration recorded; first run not yet observed)
        ``ok``     (last run succeeded)
        ``degraded`` (last run partial / soft-failed)
        ``failed`` (last run hard-failed; ``last_error`` populated)
    """
    key = (key or "").strip()
    subsystem = (subsystem or "").strip()
    status = (status or "pending").strip() or "pending"
    if not key or not subsystem:
        raise ValueError("update_subsystem_status requires key and subsystem")
    now = _now_iso()
    with _WRITE_LOCK, _open_db() as conn:
        conn.execute(
            """INSERT INTO monitoring_subsystems
               (key, subsystem, status, last_run_at, last_error)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(key, subsystem) DO UPDATE SET
                 status=excluded.status,
                 last_run_at=excluded.last_run_at,
                 last_error=excluded.last_error""",
            (key, subsystem, status, now, last_error),
        )
        _record_audit_inline(
            conn,
            actor="system",
            action=ACTION_SUBSYSTEM_STATUS,
            key=key,
            payload={"subsystem": subsystem, "status": status, "error": last_error},
        )


def list_subsystem_status(key: str) -> List[Dict[str, Any]]:
    if not key:
        return []
    with _open_db() as conn:
        rows = conn.execute(
            "SELECT subsystem, status, last_run_at, last_error "
            "FROM monitoring_subsystems WHERE key=? ORDER BY subsystem",
            (key,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def record_audit(
    *,
    actor: str,
    action: str,
    key: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Public wrapper for code outside this module that needs to write
    an audit row WITHOUT a connection in scope (e.g. the dispatch layer
    after a Network Mapper call). Internal call-sites that already have
    an open connection use ``_record_audit_inline``.
    """
    with _WRITE_LOCK, _open_db() as conn:
        _record_audit_inline(conn, actor=actor, action=action, key=key, payload=payload)


def _record_audit_inline(
    conn: sqlite3.Connection,
    *,
    actor: str,
    action: str,
    key: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    actor = (actor or "system").strip() or "system"
    action = (action or "").strip()
    if not action:
        return
    payload_json = json.dumps(payload or {}, default=str)
    conn.execute(
        "INSERT INTO audit_log (at, actor, action, key, payload_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (_now_iso(), actor, action, key, payload_json),
    )


def list_audit(
    *,
    key: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    where: List[str] = []
    params: List[Any] = []
    if key:
        where.append("key=?")
        params.append(key.strip())
    if actor:
        where.append("actor=?")
        params.append(actor.strip())
    sql = "SELECT id, at, actor, action, key, payload_json FROM audit_log"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(max(1, min(int(limit or 200), 2000)))
    with _open_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        try:
            payload = json.loads(r["payload_json"] or "{}")
        except Exception:
            payload = {}
        out.append({
            "id": r["id"],
            "at": r["at"],
            "actor": r["actor"],
            "action": r["action"],
            "key": r["key"],
            "payload": payload,
        })
    return out


# Initialize the schema on import. Safe to call repeatedly; the CREATE
# TABLE statements are guarded by IF NOT EXISTS so the cost is one
# bookkeeping query when the DB already exists.
_ensure_schema()
