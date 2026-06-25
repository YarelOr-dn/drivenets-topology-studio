"""
Bounded worker pools for push / upgrade / auxiliary daemon jobs (Wave 6.2).

Purpose
-------
Before Wave 6, every config push and every upgrade spawned a fresh
``threading.Thread(..., daemon=True).start()``. At 100 concurrent users,
that's 100+ fresh OS threads, each paying the ~8MB stack cost, plus the
Python interpreter overhead of thread creation and scheduling. Long
bursts could push total thread count past 1000, risking OS thread-limit
errors and non-trivial RAM pressure.

This module replaces the unbounded thread-per-job pattern with two
purpose-built bounded ``ThreadPoolExecutor`` instances:

* ``push_pool`` -- short-lived config pushes (seconds to minutes).
  Default size: ``TP_PUSH_EXECUTOR_SIZE`` (50). Sized above
  ``TP_GLOBAL_PUSH_SLOTS`` (20) so the semaphore (Wave 6.1) remains
  the effective concurrency bottleneck, not the pool itself.
* ``upgrade_pool`` -- long-lived firmware upgrades (minutes to hours).
  Default size: ``TP_UPGRADE_EXECUTOR_SIZE`` (10). Sized above
  ``TP_UPGRADE_MAX_CONCURRENT`` (4) so the semaphore gates concurrency
  while the pool handles monitor/resume side-jobs too.

Callers keep the same fire-and-forget semantics as the old
``Thread(..., daemon=True).start()`` pattern; the pools replace that
with ``push_pool.submit(fn)`` / ``upgrade_pool.submit(fn)``.

Submission to a full pool does NOT block -- the executor's internal
queue accepts the task and a worker picks it up when free. This is
intentional: back-pressure is already enforced upstream by the Wave
6.1/6.4/6.5 admission checks (global slot, per-user cap, device queue
cap), so the executor's unbounded queue just holds already-admitted
jobs until a worker is free.

Context propagation
-------------------
``ContextVars`` set by FastAPI middleware (``current_app_user`` etc.)
do NOT propagate automatically to executor workers. Callers must wrap
their function with ``routes._state.app_user_context(owner)`` before
submission -- exactly like the pre-Wave-6 ``Thread(target=_run_with_user)``
wrappers already did.

Shutdown
--------
Pools use ``daemon`` threads via ``thread_name_prefix`` and are NOT
``.shutdown(wait=True)``-ed at process exit; uvicorn's shutdown signal
simply kills the interpreter and active pushes/upgrades abort like
they did with plain ``daemon=True`` threads. A clean-shutdown hook is
left as a future enhancement (Wave 7).
"""
from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


_PUSH_POOL_SIZE = _env_int("TP_PUSH_EXECUTOR_SIZE", 50)
_UPGRADE_POOL_SIZE = _env_int("TP_UPGRADE_EXECUTOR_SIZE", 10)


# ---------------------------------------------------------------------------
# Module-level singletons. Instantiated lazily so tests can override sizes
# via env before first use.
# ---------------------------------------------------------------------------
_push_pool: Optional[ThreadPoolExecutor] = None
_upgrade_pool: Optional[ThreadPoolExecutor] = None


def _get_push_pool() -> ThreadPoolExecutor:
    global _push_pool
    if _push_pool is None:
        _push_pool = ThreadPoolExecutor(
            max_workers=_PUSH_POOL_SIZE,
            thread_name_prefix="push-worker",
        )
    return _push_pool


def _get_upgrade_pool() -> ThreadPoolExecutor:
    global _upgrade_pool
    if _upgrade_pool is None:
        _upgrade_pool = ThreadPoolExecutor(
            max_workers=_UPGRADE_POOL_SIZE,
            thread_name_prefix="upgrade-worker",
        )
    return _upgrade_pool


def submit_push(fn: Callable[[], None]) -> Future:
    """Submit a push worker function to the bounded push pool.

    The function takes no arguments and returns None -- identical
    semantics to the old ``Thread(target=fn, daemon=True).start()``.
    Returns the Future (callers typically ignore it).
    """
    return _get_push_pool().submit(fn)


def submit_upgrade(fn: Callable[[], None]) -> Future:
    """Submit an upgrade / monitor / resume function to the upgrade pool."""
    return _get_upgrade_pool().submit(fn)


def pool_stats() -> dict:
    """Snapshot of both pools for ``/api/health/concurrency``.

    Workers + queued counts are derived from the executor internals; they
    are best-effort (the interfaces aren't officially public) but stable
    across CPython 3.8+.
    """
    out = {}
    for name, pool in (("push", _push_pool), ("upgrade", _upgrade_pool)):
        if pool is None:
            out[name] = {"initialized": False, "size_max": None}
            continue
        try:
            queued = pool._work_queue.qsize()  # type: ignore[attr-defined]
        except Exception:
            queued = -1
        out[name] = {
            "initialized": True,
            "size_max": pool._max_workers,  # type: ignore[attr-defined]
            "threads_alive": len(pool._threads),  # type: ignore[attr-defined]
            "queue_depth": queued,
        }
    return out


def reset_for_tests() -> None:
    """Shut down current pools so tests can re-read env and re-create.

    Only callable from tests -- production code never needs this.
    """
    global _push_pool, _upgrade_pool
    for p in (_push_pool, _upgrade_pool):
        if p is not None:
            try:
                p.shutdown(wait=False)
            except Exception:
                pass
    _push_pool = None
    _upgrade_pool = None


__all__ = [
    "submit_push",
    "submit_upgrade",
    "pool_stats",
    "reset_for_tests",
]
