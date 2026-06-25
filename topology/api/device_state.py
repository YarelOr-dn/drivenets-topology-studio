"""Shared, per-device state store: watchers, events, and per-user prefs.

Architecture model
------------------

The scaler device DB (``scaler/db/configs/<device>/operational.json``) is the
*physical* source of truth for a device (mgmt_ip, cluster info, upgrade
history). It is shared across ALL users -- a ghost-IP reap by one user is
visible to everyone.

This module adds the *logical* layer on top: who is watching which device,
what maintenance events have fired, and per-user private preferences. The
goal is that every new mechanism (ghost-IP reaper, future features) can
plug in cleanly while respecting the "shared device, per-user view"
invariant the user called out on 2026-04-20.

Tables
~~~~~~

``~/.topology_shared/_device_state.db``:

- ``device_watchers(device_id, username, topology_id, last_seen_at)``
  A user "watches" a device while that device is on their canvas. Rows
  expire after ``WATCHER_IDLE_TTL_SECONDS`` of no heartbeat so stale
  browser tabs don't keep receiving events forever.

- ``device_events(id, device_id, event_type, actor_user, at, payload_json)``
  Audit log of every maintenance action that affects the shared device
  record. Used for polling fallback and forensics ("why did my session
  die?" -> "user X reaped this IP as ghost 30 seconds ago"). Ring-buffer
  style: ``prune_old_events()`` trims to ``EVENT_RETENTION_DAYS``.

- ``user_device_prefs(username, device_id, prefs_json, updated_at)``
  Per-user private state. Today holds last-working method, custom notes,
  and ghost-clear ack history. Future code should use this table instead
  of polluting the shared operational.json with user-specific fields.

All path construction is centralized here -- no other module touches the
device-state DB path. Mirrors the pattern set by ``user_store.UserStore``.
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .config import settings


DEVICE_STATE_DB_PATH = Path(settings.shared_topologies_dir).expanduser() / "_device_state.db"
WATCHER_IDLE_TTL_SECONDS = 5 * 60      # 5 min since last heartbeat -> stale
EVENT_RETENTION_DAYS = 30
EVENT_LIST_DEFAULT_LIMIT = 200
EVENT_LIST_MAX_LIMIT = 2000

# Event types we support (free-form strings in DB; these are the canonical set).
EVENT_GHOST_IP_REAPED = "ghost_ip_reaped"
EVENT_MGMT_IP_UPDATED = "mgmt_ip_updated"
EVENT_CLUSTER_STATE_CHANGED = "cluster_state_changed"
EVENT_MAINTENANCE_NOTE = "maintenance_note"
EVENT_WATCHER_ADDED = "watcher_added"
EVENT_WATCHER_REMOVED = "watcher_removed"

_WRITE_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        # datetime.fromisoformat handles the "+00:00" offset that _now_iso emits.
        return datetime.fromisoformat(s)
    except Exception:
        return None


@contextlib.contextmanager
def _open_db():
    DEVICE_STATE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DEVICE_STATE_DB_PATH), isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


class DeviceStateStore:
    """Shared watchers + events + per-user prefs on top of a sqlite DB."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self):
        with _WRITE_LOCK, _open_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_watchers (
                    device_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    topology_id TEXT,
                    canvas_ip TEXT,
                    last_seen_at TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    PRIMARY KEY (device_id, username)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_watchers_username
                ON device_watchers(username)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_watchers_last_seen
                ON device_watchers(last_seen_at)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor_user TEXT NOT NULL,
                    at TEXT NOT NULL,
                    payload_json TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_device_at
                ON device_events(device_id, at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_at
                ON device_events(at)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_device_prefs (
                    username TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    prefs_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (username, device_id)
                )
            """)

    # ----------------------------------------------------------------- watchers

    def register_watcher(
        self,
        device_id: str,
        username: str,
        topology_id: Optional[str] = None,
        canvas_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upsert a (device_id, username) watcher entry.

        Called when the user opens a topology that contains this device,
        and again periodically as a heartbeat.
        """
        device_id = (device_id or "").strip()
        username = (username or "").strip()
        if not device_id or not username:
            raise ValueError("device_id and username are required")
        now = _now_iso()
        is_new = False
        with _WRITE_LOCK, _open_db() as conn:
            existing = conn.execute(
                "SELECT registered_at FROM device_watchers WHERE device_id=? AND username=?",
                (device_id, username),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE device_watchers SET last_seen_at=?, topology_id=COALESCE(?, topology_id), "
                    "canvas_ip=COALESCE(?, canvas_ip) WHERE device_id=? AND username=?",
                    (now, topology_id, canvas_ip, device_id, username),
                )
            else:
                is_new = True
                conn.execute(
                    "INSERT INTO device_watchers (device_id, username, topology_id, canvas_ip, last_seen_at, registered_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (device_id, username, topology_id, canvas_ip, now, now),
                )
        return {
            "device_id": device_id,
            "username": username,
            "topology_id": topology_id,
            "canvas_ip": canvas_ip,
            "last_seen_at": now,
            "newly_registered": is_new,
        }

    def unregister_watcher(self, device_id: str, username: str) -> bool:
        device_id = (device_id or "").strip()
        username = (username or "").strip()
        if not device_id or not username:
            return False
        with _WRITE_LOCK, _open_db() as conn:
            cur = conn.execute(
                "DELETE FROM device_watchers WHERE device_id=? AND username=?",
                (device_id, username),
            )
            return cur.rowcount > 0

    def heartbeat(self, username: str, device_ids: Iterable[str]) -> Dict[str, Any]:
        """Bulk-update last_seen_at for all devices in the user's canvas.

        Also prunes rows (for the same user) that were NOT in the list --
        this lets the frontend communicate the full watcher set in one
        call instead of tracking removals client-side.
        """
        username = (username or "").strip()
        if not username:
            raise ValueError("username required")
        device_ids = [d.strip() for d in device_ids if d and d.strip()]
        now = _now_iso()
        added, kept, pruned = [], [], []
        with _WRITE_LOCK, _open_db() as conn:
            current = {
                row["device_id"]
                for row in conn.execute(
                    "SELECT device_id FROM device_watchers WHERE username=?",
                    (username,),
                ).fetchall()
            }
            for dev in device_ids:
                if dev in current:
                    conn.execute(
                        "UPDATE device_watchers SET last_seen_at=? WHERE device_id=? AND username=?",
                        (now, dev, username),
                    )
                    kept.append(dev)
                else:
                    conn.execute(
                        "INSERT INTO device_watchers "
                        "(device_id, username, topology_id, canvas_ip, last_seen_at, registered_at) "
                        "VALUES (?, ?, NULL, NULL, ?, ?)",
                        (dev, username, now, now),
                    )
                    added.append(dev)
            stale = current.difference(device_ids)
            if stale:
                conn.executemany(
                    "DELETE FROM device_watchers WHERE device_id=? AND username=?",
                    [(d, username) for d in stale],
                )
                pruned.extend(stale)
        return {
            "username": username,
            "heartbeat_at": now,
            "added": added,
            "kept": kept,
            "pruned": list(pruned),
            "active_count": len(kept) + len(added),
        }

    def is_watcher(self, device_id: str, username: str) -> bool:
        device_id = (device_id or "").strip()
        username = (username or "").strip()
        if not device_id or not username:
            return False
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=WATCHER_IDLE_TTL_SECONDS)).isoformat()
        with _open_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM device_watchers "
                "WHERE device_id=? AND username=? AND last_seen_at >= ?",
                (device_id, username, cutoff),
            ).fetchone()
        return row is not None

    def list_active_watched_devices(self) -> List[str]:
        """Return distinct device_ids that have at least one currently-active
        watcher across ALL users.

        Used by the device-mode resolver's per-watcher polling loop to
        decide which devices need a tight-cadence refresh while users
        are looking at them. Idle (no-watcher) devices fall back to the
        slower 5-minute global poll.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=WATCHER_IDLE_TTL_SECONDS)).isoformat()
        with _open_db() as conn:
            rows = conn.execute(
                "SELECT DISTINCT device_id FROM device_watchers "
                "WHERE last_seen_at >= ? ORDER BY device_id",
                (cutoff,),
            ).fetchall()
        return [r["device_id"] for r in rows if r["device_id"]]

    def list_watchers_for_device(self, device_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        device_id = (device_id or "").strip()
        if not device_id:
            return []
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=WATCHER_IDLE_TTL_SECONDS)).isoformat()
        with _open_db() as conn:
            if active_only:
                rows = conn.execute(
                    "SELECT device_id, username, topology_id, canvas_ip, last_seen_at, registered_at "
                    "FROM device_watchers WHERE device_id=? AND last_seen_at >= ? "
                    "ORDER BY last_seen_at DESC",
                    (device_id, cutoff),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT device_id, username, topology_id, canvas_ip, last_seen_at, registered_at "
                    "FROM device_watchers WHERE device_id=? ORDER BY last_seen_at DESC",
                    (device_id,),
                ).fetchall()
        return [dict(r) for r in rows]

    def list_watched_devices(self, username: str, active_only: bool = True) -> List[Dict[str, Any]]:
        username = (username or "").strip()
        if not username:
            return []
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=WATCHER_IDLE_TTL_SECONDS)).isoformat()
        with _open_db() as conn:
            if active_only:
                rows = conn.execute(
                    "SELECT device_id, topology_id, canvas_ip, last_seen_at, registered_at "
                    "FROM device_watchers WHERE username=? AND last_seen_at >= ? "
                    "ORDER BY last_seen_at DESC",
                    (username, cutoff),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT device_id, topology_id, canvas_ip, last_seen_at, registered_at "
                    "FROM device_watchers WHERE username=? ORDER BY last_seen_at DESC",
                    (username,),
                ).fetchall()
        return [dict(r) for r in rows]

    def prune_stale_watchers(self) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=WATCHER_IDLE_TTL_SECONDS)).isoformat()
        with _WRITE_LOCK, _open_db() as conn:
            cur = conn.execute(
                "DELETE FROM device_watchers WHERE last_seen_at < ?",
                (cutoff,),
            )
            return cur.rowcount

    # ------------------------------------------------------------------- events

    def record_event(
        self,
        device_id: str,
        event_type: str,
        actor_user: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append an event to the shared device audit log. Returns the row."""
        device_id = (device_id or "").strip()
        event_type = (event_type or "").strip()
        actor_user = (actor_user or "default").strip() or "default"
        if not device_id or not event_type:
            raise ValueError("device_id and event_type are required")
        now = _now_iso()
        payload_json = json.dumps(payload or {}, default=str)
        with _WRITE_LOCK, _open_db() as conn:
            cur = conn.execute(
                "INSERT INTO device_events (device_id, event_type, actor_user, at, payload_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (device_id, event_type, actor_user, now, payload_json),
            )
            row_id = cur.lastrowid
        return {
            "id": row_id,
            "device_id": device_id,
            "event_type": event_type,
            "actor_user": actor_user,
            "at": now,
            "payload": payload or {},
        }

    def list_events(
        self,
        device_id: Optional[str] = None,
        since_iso: Optional[str] = None,
        since_id: Optional[int] = None,
        limit: int = EVENT_LIST_DEFAULT_LIMIT,
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit or EVENT_LIST_DEFAULT_LIMIT), EVENT_LIST_MAX_LIMIT))
        where, params = [], []
        if device_id:
            where.append("device_id = ?")
            params.append(device_id.strip())
        if since_id is not None:
            where.append("id > ?")
            params.append(int(since_id))
        if since_iso:
            where.append("at >= ?")
            params.append(since_iso)
        sql = "SELECT id, device_id, event_type, actor_user, at, payload_json FROM device_events"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
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
                "device_id": r["device_id"],
                "event_type": r["event_type"],
                "actor_user": r["actor_user"],
                "at": r["at"],
                "payload": payload,
            })
        return out

    def prune_old_events(self) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=EVENT_RETENTION_DAYS)).isoformat()
        with _WRITE_LOCK, _open_db() as conn:
            cur = conn.execute("DELETE FROM device_events WHERE at < ?", (cutoff,))
            return cur.rowcount

    # ---------------------------------------------------------- per-user prefs

    def get_user_pref(self, username: str, device_id: str) -> Dict[str, Any]:
        username = (username or "").strip()
        device_id = (device_id or "").strip()
        if not username or not device_id:
            return {}
        with _open_db() as conn:
            row = conn.execute(
                "SELECT prefs_json FROM user_device_prefs WHERE username=? AND device_id=?",
                (username, device_id),
            ).fetchone()
        if not row:
            return {}
        try:
            return json.loads(row["prefs_json"] or "{}")
        except Exception:
            return {}

    def set_user_pref(self, username: str, device_id: str, prefs: Dict[str, Any]) -> Dict[str, Any]:
        username = (username or "").strip()
        device_id = (device_id or "").strip()
        if not username or not device_id:
            raise ValueError("username and device_id are required")
        prefs = dict(prefs or {})
        now = _now_iso()
        payload_json = json.dumps(prefs, default=str)
        with _WRITE_LOCK, _open_db() as conn:
            conn.execute(
                "INSERT INTO user_device_prefs (username, device_id, prefs_json, updated_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(username, device_id) DO UPDATE SET "
                "prefs_json = excluded.prefs_json, updated_at = excluded.updated_at",
                (username, device_id, payload_json, now),
            )
        return {"username": username, "device_id": device_id, "prefs": prefs, "updated_at": now}

    def merge_user_pref(self, username: str, device_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        """Shallow-merge ``patch`` into the existing per-user pref dict."""
        cur = self.get_user_pref(username, device_id)
        cur.update(patch or {})
        return self.set_user_pref(username, device_id, cur)

    # --------------------------------------------------------- summary helpers

    def device_summary(self, device_id: str) -> Dict[str, Any]:
        """One-shot view for the bridge: watchers + last N events + activity window."""
        device_id = (device_id or "").strip()
        if not device_id:
            return {"device_id": "", "watchers": [], "recent_events": []}
        return {
            "device_id": device_id,
            "watchers": self.list_watchers_for_device(device_id, active_only=True),
            "recent_events": self.list_events(device_id=device_id, limit=50),
        }


device_state = DeviceStateStore()
