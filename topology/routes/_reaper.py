"""
Stale-dry-run reaper (Wave 7.1).

Problem solved
--------------
A successful dry-run push leaves a job "awaiting_decision": the SSH channel
is held open on the device, the per-device lock is still ours, a global
push slot is consumed, and the per-user push counter is incremented. The
user is expected to follow up with ``push_commit`` or ``push_cancel`` to
release everything. If the user walks away, crashes their browser, loses
network, or simply forgets:

    * The device stays locked forever -- nobody else can push to it.
    * A global push slot is leaked -- every abandoned dry-run shrinks the
      pool that Wave 6.1 relies on to cap parallel pushes.
    * The user's counter stays at ``N``; once they hit
      ``TP_PER_USER_PUSH_MAX`` stuck reservations, they can never push
      again until the bridge restarts.
    * The device's SSH session and channel are held open, keeping the
      paramiko transport alive in the pool.

One user can jam a whole cluster by abandoning five dry-runs.

Design
------
A daemon thread scans ``_push_jobs`` every ``TP_REAPER_INTERVAL_S``
(default 60 s). Any job whose ``awaiting_decision`` is True AND whose
``awaiting_since`` timestamp is older than ``TP_DRYRUN_TTL_S`` (default
600 s) is treated as abandoned. The reaper:

    1.  Atomically flips ``awaiting_decision`` back to False and marks
        the job ``status="reaped"`` / ``cancelled=True`` so the next
        commit/cancel HTTP call is a no-op rather than a double-release.
    2.  Pops ``_sched_token`` / ``_push_slot_handle`` /
        ``_user_push_reserved`` / ``_channel`` / ``_client`` /
        ``_pusher`` / ``_live_output`` under the lock.
    3.  Sends the DNOS ``abort`` command to the held channel (best
        effort) so the device sees a clean rollback, not a half-parsed
        paste stream.
    4.  Closes the channel + client and releases the scheduler token,
        the global push slot, and the per-user counter OUTSIDE the job
        lock -- these calls may block on paramiko teardown or the
        scheduler's own registry lock.
    5.  Emits an audit event (Wave 7.5).

Because step 1 flips ``awaiting_decision`` to False, a racing
``push_commit`` / ``push_cancel`` that arrives a millisecond later sees
``awaiting_decision == False`` and returns HTTP 410 cleanly -- the user
just discovers their session was garbage-collected.

Tunables (env vars, read at module import)
------------------------------------------
* ``TP_DRYRUN_TTL_S``      -- abandonment threshold (default 600 seconds)
* ``TP_REAPER_INTERVAL_S`` -- poll period        (default 60 seconds)
* ``TP_REAPER_ENABLED``    -- ``0`` to disable   (default enabled)

Observability
-------------
``reaper_stats()`` returns running totals (scans, reaped, last_scan_ts)
for the health endpoint.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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


DRYRUN_TTL_S = _env_int("TP_DRYRUN_TTL_S", 600)
REAPER_INTERVAL_S = _env_int("TP_REAPER_INTERVAL_S", 60)
REAPER_ENABLED = _env_bool("TP_REAPER_ENABLED", True)


_reaper_stats: Dict[str, Any] = {
    "scans": 0,
    "reaped_total": 0,
    "reaped_by_reason": {},
    "last_scan_ts": None,
    "last_reap_ts": None,
    "last_error": None,
    "ttl_s": DRYRUN_TTL_S,
    "interval_s": REAPER_INTERVAL_S,
    "enabled": REAPER_ENABLED,
}
_reaper_stats_lock = threading.Lock()
_reaper_thread: Optional[threading.Thread] = None
_reaper_stop = threading.Event()


def reaper_stats() -> Dict[str, Any]:
    """Return a copy of the reaper counters for /api/health/concurrency."""
    with _reaper_stats_lock:
        out = dict(_reaper_stats)
        out["reaped_by_reason"] = dict(out["reaped_by_reason"])
    return out


def _bump(reason: str) -> None:
    with _reaper_stats_lock:
        _reaper_stats["reaped_total"] += 1
        _reaper_stats["reaped_by_reason"][reason] = (
            _reaper_stats["reaped_by_reason"].get(reason, 0) + 1
        )
        _reaper_stats["last_reap_ts"] = datetime.utcnow().isoformat() + "Z"


def _find_candidates(now: float) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Return (job_id, reason, extracted_resources) for each stale dry-run.

    Wave 7.12 refactor: the hot path takes the push-jobs lock TWICE --
    first to snapshot job_ids + the few fields we need to age-filter,
    then per-candidate to atomically flip the row state and pop the
    held resources. The lock is therefore held for O(N) _READS_ (fast
    dict scan) and O(stale) _WRITES_ (single-row flips), never for
    SSH teardown. This keeps push/commit/cancel latency flat even if
    the job table is large (up to the Wave 7.4 per-user quota).
    """
    from routes._state import _push_jobs, _push_jobs_lock

    stale: List[Tuple[str, str, Dict[str, Any]]] = []
    ttl = DRYRUN_TTL_S
    if ttl <= 0:
        return stale

    # --- Pass 1: cheap snapshot under the lock ----------------------
    # Extract only (job_id, awaiting_since) for each awaiting row. We
    # DO NOT mutate here, so commit/cancel/SSE handlers that need the
    # lock get in and out quickly.
    candidates: List[Tuple[str, float]] = []
    with _push_jobs_lock:
        for job_id, job in _push_jobs.items():
            if not isinstance(job, dict):
                continue
            if not job.get("awaiting_decision"):
                continue
            awaiting_since = job.get("awaiting_since_ts")
            if not awaiting_since:
                awaiting_since = job.get("started_at_ts")
            if not awaiting_since:
                started_iso = job.get("started_at") or ""
                try:
                    s = started_iso.rstrip("Z")
                    awaiting_since = datetime.fromisoformat(s).timestamp()
                except Exception:
                    continue  # no usable timestamp -> never reap
            try:
                ts = float(awaiting_since)
            except (TypeError, ValueError):
                continue
            candidates.append((job_id, ts))

    # --- Pass 2: per-stale-row flip under the lock ------------------
    # Done outside the hot iteration so we don't block pushers while
    # we build `stale`. A row that was "awaiting" during the snapshot
    # may have been committed/cancelled by the user in the gap; the
    # re-check inside the lock handles that safely.
    for job_id, awaiting_since in candidates:
        age = now - awaiting_since
        if age < ttl:
            continue
        with _push_jobs_lock:
            job = _push_jobs.get(job_id)
            if not isinstance(job, dict):
                continue
            if not job.get("awaiting_decision"):
                continue  # user beat us to commit/cancel -> leave alone
            reason = "ttl_expired"
            resources = {
                "sched_token": job.pop("_sched_token", None),
                "push_slot_handle": job.pop("_push_slot_handle", None),
                "user_push_reserved": bool(
                    job.pop("_user_push_reserved", False)
                ),
                "owner": job.get("owner", ""),
                "device_id": job.get("device_id", ""),
                "mgmt_ip": job.get("mgmt_ip", ""),
                "channel": job.pop("_channel", None),
                "client": job.pop("_client", None),
                "pusher": job.pop("_pusher", None),
                "live_output": job.pop("_live_output", None),
                "age_s": age,
            }
            job["awaiting_decision"] = False
            job["status"] = "reaped"
            job["done"] = True
            job["success"] = False
            job["cancelled"] = True
            job["reaped"] = True
            job["message"] = (
                f"Dry-run abandoned: session exceeded {ttl}s TTL "
                f"(idle {int(age)}s) and was auto-released."
            )
            job["completed_at"] = datetime.utcnow().isoformat() + "Z"
        stale.append((job_id, reason, resources))

    return stale


def _release_resources(job_id: str, resources: Dict[str, Any]) -> None:
    """Close channel/client, release scheduler token, slot, and user counter."""
    from routes._device_scheduler import scheduler as _device_scheduler

    channel = resources.get("channel")
    client = resources.get("client")
    pusher = resources.get("pusher")

    # Try a clean DNOS abort before tearing down the channel so the
    # device state machine returns to exec mode rather than timing out.
    try:
        if pusher and hasattr(pusher, "abort_held_session"):
            pusher.abort_held_session(channel, client)
        else:
            if channel:
                try:
                    channel.send("abort\n")
                    time.sleep(0.5)
                except Exception:
                    pass
            if channel:
                try:
                    channel.close()
                except Exception:
                    pass
            if client:
                try:
                    client.close()
                except Exception:
                    pass
    except Exception as exc:
        logger.warning(
            "reaper: clean abort failed for job=%s: %s", job_id, exc
        )

    # Scheduler release is a no-op if the token is None (safety-net
    # idempotency, matches Wave 6.1 semantics). Exceptions here are
    # swallowed so one broken scheduler entry can't stop the reaper.
    try:
        _device_scheduler.release(resources.get("sched_token"))
    except Exception as exc:
        logger.warning("reaper: scheduler release failed for job=%s: %s",
                       job_id, exc)
    try:
        _device_scheduler.release_global_push_slot(
            resources.get("push_slot_handle")
        )
    except Exception as exc:
        logger.warning("reaper: slot release failed for job=%s: %s",
                       job_id, exc)
    if resources.get("user_push_reserved"):
        try:
            _device_scheduler.release_user_push(resources.get("owner", ""))
        except Exception as exc:
            logger.warning(
                "reaper: user-push release failed for job=%s owner=%s: %s",
                job_id, resources.get("owner", ""), exc
            )


def _scan_once() -> int:
    """One reaper pass. Returns count of jobs reaped."""
    with _reaper_stats_lock:
        _reaper_stats["scans"] += 1
        _reaper_stats["last_scan_ts"] = datetime.utcnow().isoformat() + "Z"
    try:
        now = time.time()
        stale = _find_candidates(now)
    except Exception as exc:
        with _reaper_stats_lock:
            _reaper_stats["last_error"] = str(exc)
        logger.exception("reaper: candidate scan failed")
        return 0

    count = 0
    for job_id, reason, resources in stale:
        _release_resources(job_id, resources)
        _bump(reason)
        try:
            from routes._audit_log import record_event
            record_event(
                action="push_reaped",
                owner=resources.get("owner", ""),
                device_id=resources.get("device_id", ""),
                mgmt_ip=resources.get("mgmt_ip", ""),
                job_id=job_id,
                result="reaped",
                detail={"reason": reason, "age_s": resources.get("age_s")},
            )
        except Exception:
            pass  # audit failure must never break the reaper
        logger.warning(
            "reaper: reaped abandoned dry-run job=%s owner=%s device=%s "
            "age=%.0fs",
            job_id,
            resources.get("owner", ""),
            resources.get("device_id", ""),
            resources.get("age_s", 0.0),
        )
        count += 1
    return count


def _reaper_loop() -> None:
    """Daemon thread: periodic scan + reap."""
    logger.info(
        "reaper: starting (interval=%ds ttl=%ds)",
        REAPER_INTERVAL_S, DRYRUN_TTL_S
    )
    # Initial delay so the bridge finishes startup before the first scan.
    _reaper_stop.wait(min(30, REAPER_INTERVAL_S))
    while not _reaper_stop.is_set():
        try:
            _scan_once()
        except Exception as exc:
            with _reaper_stats_lock:
                _reaper_stats["last_error"] = str(exc)
            logger.exception("reaper: scan iteration failed")
        if _reaper_stop.wait(REAPER_INTERVAL_S):
            break
    logger.info("reaper: stopped")


def start_reaper() -> None:
    """Start the reaper daemon if it is enabled and not already running."""
    global _reaper_thread
    if not REAPER_ENABLED:
        logger.info("reaper: disabled via TP_REAPER_ENABLED")
        return
    if _reaper_thread is not None and _reaper_thread.is_alive():
        return
    _reaper_stop.clear()
    t = threading.Thread(
        target=_reaper_loop, name="tp-dryrun-reaper", daemon=True
    )
    t.start()
    _reaper_thread = t


def stop_reaper(timeout: float = 5.0) -> None:
    """Request the reaper to stop (used by graceful shutdown paths)."""
    _reaper_stop.set()
    t = _reaper_thread
    if t is not None:
        t.join(timeout=timeout)


def reap_now() -> int:
    """Force a scan immediately (used by tests and admin endpoints)."""
    return _scan_once()
