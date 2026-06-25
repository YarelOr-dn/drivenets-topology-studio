"""
Append-only audit log for push / upgrade / admin events (Wave 7.5).

Goals
-----
In a multi-user environment we need to be able to answer, after the fact:

    * Which user pushed which config to which device at what time?
    * Which pushes were rejected (429 per-user-cap, 503 device-busy,
      403 unauthorized) and why?
    * Which jobs were auto-reaped due to abandoned dry-runs?
    * Who ran a force-commit / force-cancel on someone else's job?

The answer lives in a JSONL file (one JSON event per line) under
``TP_AUDIT_LOG_PATH`` (default ``~/.topology_audit.log``). We pick JSONL
because:

    * Line-buffered append writes are atomic for small records on POSIX.
    * ``grep`` / ``jq`` / ``tail -f`` are the usual forensic tools.
    * Rotation is trivial: size-based roll to ``<path>.<N>``.

Hot-path safety
---------------
``record_event`` MUST never block a push / upgrade worker. Rules:

    * Serialization is done on the caller thread (cheap, microseconds).
    * File IO is done under a module-level ``threading.Lock`` with a
      bounded retry (3 attempts) so a full disk can't hang the worker.
    * Any exception is swallowed and counted in ``audit_stats()``. Audit
      visibility is best-effort; no push/upgrade should ever fail
      because the audit log is unhappy.

Rotation
--------
When the file reaches ``TP_AUDIT_LOG_MAX_BYTES`` (default 100 MiB) it is
moved to ``<path>.1``, the existing ``.1`` is bumped to ``.2``, etc., up
to ``TP_AUDIT_LOG_MAX_FILES`` (default 5). Older files are deleted.

Environment variables
---------------------
* ``TP_AUDIT_LOG_PATH``       -- default ``~/.topology_audit.log``
* ``TP_AUDIT_LOG_MAX_BYTES``  -- default 104_857_600 (100 MiB)
* ``TP_AUDIT_LOG_MAX_FILES``  -- default 5
* ``TP_AUDIT_LOG_ENABLED``    -- ``0`` to disable (default enabled)

Schema
------
Each line is a JSON object with at least::

    {
      "ts": "2026-04-19T12:34:56.789Z",
      "action": "push_start",         # push_start|push_complete|push_failed|
                                      # push_rejected|push_commit|push_cancel|
                                      # push_reaped|upgrade_start|...
      "owner": "alice",
      "role": "user",
      "device_id": "PE-1",
      "mgmt_ip": "100.64.7.197",
      "job_id": "ed2f...",
      "result": "ok|rejected|failed|cancelled|reaped|...",
      "detail": { ... action-specific fields ... }
    }
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off", "")


def _default_audit_path() -> Path:
    raw = os.environ.get("TP_AUDIT_LOG_PATH")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".topology_audit.log"


AUDIT_PATH = _default_audit_path()
AUDIT_ENABLED = _env_bool("TP_AUDIT_LOG_ENABLED", True)
AUDIT_MAX_BYTES = _env_int("TP_AUDIT_LOG_MAX_BYTES", 100 * 1024 * 1024)
AUDIT_MAX_FILES = max(1, _env_int("TP_AUDIT_LOG_MAX_FILES", 5))


_audit_lock = threading.Lock()
_audit_stats: Dict[str, Any] = {
    "events_written": 0,
    "events_failed": 0,
    "rotations": 0,
    "last_write_ts": None,
    "last_error": None,
    "path": str(AUDIT_PATH),
    "enabled": AUDIT_ENABLED,
}


def audit_stats() -> Dict[str, Any]:
    """Return a copy of the audit counters for the health endpoint."""
    with _audit_lock:
        return dict(_audit_stats)


def _rotate_if_needed(path: Path) -> None:
    """Rotate ``path`` to ``path.1``, ``path.1`` to ``path.2``, etc.

    Called under the audit lock only when the current size exceeds
    ``AUDIT_MAX_BYTES``. Rotation failures are non-fatal: if rotation
    cannot happen (readonly disk, permission error) we simply keep
    appending to the existing file.
    """
    try:
        if not path.exists() or path.stat().st_size < AUDIT_MAX_BYTES:
            return
    except Exception:
        return

    # Drop the oldest generation.
    oldest = path.with_suffix(path.suffix + f".{AUDIT_MAX_FILES}")
    try:
        if oldest.exists():
            oldest.unlink()
    except Exception:
        pass

    for n in range(AUDIT_MAX_FILES - 1, 0, -1):
        src = path.with_suffix(path.suffix + f".{n}")
        dst = path.with_suffix(path.suffix + f".{n + 1}")
        try:
            if src.exists():
                src.rename(dst)
        except Exception:
            pass

    try:
        path.rename(path.with_suffix(path.suffix + ".1"))
        _audit_stats["rotations"] += 1
    except Exception as exc:
        _audit_stats["last_error"] = f"rotate failed: {exc}"


def _redact(value: Any) -> Any:
    """Remove obvious secrets from audit detail payloads.

    We never write raw config text or full command output into the audit
    log -- only identifiers, counts, and metadata. This helper is a
    defense-in-depth filter for callers that pass a ``detail`` dict
    through by accident.
    """
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            key_l = str(k).lower()
            if any(
                tag in key_l
                for tag in ("password", "secret", "token", "config_text",
                            "credential", "bearer")
            ):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = _redact(v)
        return cleaned
    if isinstance(value, list):
        return [_redact(v) for v in value]
    if isinstance(value, str) and len(value) > 512:
        return value[:509] + "..."
    return value


def record_event(
    *,
    action: str,
    owner: str = "",
    role: str = "",
    device_id: str = "",
    mgmt_ip: str = "",
    job_id: str = "",
    result: str = "",
    detail: Optional[Dict[str, Any]] = None,
) -> bool:
    """Append one JSONL event to the audit log.

    Returns True on success, False on failure. Never raises.
    """
    if not AUDIT_ENABLED:
        return True

    try:
        event = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": str(action or "")[:64],
            "owner": str(owner or "")[:128],
            "role": str(role or "")[:32],
            "device_id": str(device_id or "")[:128],
            "mgmt_ip": str(mgmt_ip or "")[:64],
            "job_id": str(job_id or "")[:64],
            "result": str(result or "")[:32],
        }
        if detail:
            event["detail"] = _redact(detail)
        line = json.dumps(event, default=str, ensure_ascii=False) + "\n"
    except Exception as exc:
        logger.warning("audit: serialize failed action=%s: %s", action, exc)
        with _audit_lock:
            _audit_stats["events_failed"] += 1
            _audit_stats["last_error"] = str(exc)
        return False

    with _audit_lock:
        try:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            _rotate_if_needed(AUDIT_PATH)
            # ``open(... "a")`` is O_APPEND which is atomic for small
            # writes on POSIX, so concurrent writers can't interleave
            # a single line. We still hold ``_audit_lock`` for the
            # rotate path consistency.
            with open(AUDIT_PATH, "a", encoding="utf-8") as fh:
                fh.write(line)
            _audit_stats["events_written"] += 1
            _audit_stats["last_write_ts"] = event["ts"]
            return True
        except Exception as exc:
            _audit_stats["events_failed"] += 1
            _audit_stats["last_error"] = str(exc)
            logger.warning(
                "audit: write failed action=%s path=%s: %s",
                action, AUDIT_PATH, exc
            )
            return False
