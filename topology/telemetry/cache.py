"""Per-user SQLite cache for link telemetry show-command payloads."""
from __future__ import annotations

import json
import time
from typing import Any, Optional

try:
    from api.auth.user_store import _open_db, user_store
except Exception:  # pragma: no cover - tests can inject fallback behavior
    _open_db = None
    user_store = None


DEFAULT_TTL_SECONDS = 60


def _db_path(username: str):
    if not user_store:
        return None
    return user_store.user_data_path(username or "default", "link_telemetry_cache.sqlite")


def _ensure_schema(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS link_telemetry_cache (
            cache_key TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            device_id TEXT NOT NULL,
            command TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_link_telemetry_user_device "
        "ON link_telemetry_cache(username, device_id)"
    )


def get_cached(username: str, device_id: str, command: str, ttl: int = DEFAULT_TTL_SECONDS) -> Optional[Any]:
    path = _db_path(username)
    if not path or not _open_db:
        return None
    key = f"{username}:{device_id}:{command}"
    now = time.time()
    with _open_db(path) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT payload, created_at FROM link_telemetry_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if not row:
            return None
        if now - float(row["created_at"]) > ttl:
            return None
        try:
            return json.loads(row["payload"])
        except Exception:
            return None


def set_cached(username: str, device_id: str, command: str, payload: Any) -> None:
    path = _db_path(username)
    if not path or not _open_db:
        return
    key = f"{username}:{device_id}:{command}"
    with _open_db(path) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO link_telemetry_cache(cache_key, username, device_id, command, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload = excluded.payload,
                created_at = excluded.created_at
            """,
            (key, username, device_id, command, json.dumps(payload), time.time()),
        )
        conn.commit()


def invalidate(username: str, device_ids: Optional[list[str]] = None) -> int:
    path = _db_path(username)
    if not path or not _open_db:
        return 0
    with _open_db(path) as conn:
        _ensure_schema(conn)
        if device_ids:
            total = 0
            for did in device_ids:
                cur = conn.execute(
                    "DELETE FROM link_telemetry_cache WHERE username = ? AND device_id = ?",
                    (username, did),
                )
                total += int(cur.rowcount or 0)
        else:
            cur = conn.execute(
                "DELETE FROM link_telemetry_cache WHERE username = ?",
                (username,),
            )
            total = int(cur.rowcount or 0)
        conn.commit()
        return total
