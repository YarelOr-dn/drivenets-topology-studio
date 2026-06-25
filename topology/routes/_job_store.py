"""Abstract store for push/upgrade job state.

Historically the scaler bridge has tracked in-flight push and upgrade
jobs in a module-level ``_push_jobs: dict`` (``routes/_state.py``)
guarded by ``_push_jobs_lock: threading.Lock``. That works well for a
single uvicorn worker but doesn't survive worker restarts or scale
beyond one process.

Wave 5.2 introduces a :class:`JobStore` abstraction so job storage can
be swapped without rewriting hundreds of call sites:

* :class:`InMemoryJobStore` -- default, wraps the existing
  ``_push_jobs`` dict + lock. Exactly the same behaviour as today.
* :class:`FileSnapshotJobStore` (stub) -- periodically dumps the job
  dict to disk so an unclean shutdown still surfaces recent history.
* future ``RedisJobStore`` -- would keep jobs in Redis hashes so any
  worker can read the state.

Existing handlers that still use ``_push_jobs[job_id]["status"] = ...``
work unchanged: the in-memory store is a thin layer over the same
dict + lock pair. New code is encouraged to go through the facade so
future backend swaps don't require new rewrites.
"""

from __future__ import annotations

import copy
import logging
import os
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional


logger = logging.getLogger(__name__)


class JobStore(ABC):
    """Abstract CRUD + atomic update + snapshot interface for jobs."""

    kind: str = "abstract"

    @abstractmethod
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Return a deep-copy of the job dict (or None if missing)."""

    @abstractmethod
    def put(self, job_id: str, job: Dict[str, Any]) -> None:
        """Insert or replace the job under this id."""

    @abstractmethod
    def update(
        self,
        job_id: str,
        mutator: Callable[[Dict[str, Any]], None],
    ) -> bool:
        """Atomically mutate the job dict in place. Returns False if missing."""

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """Remove the job. Returns False if it wasn't present."""

    @abstractmethod
    def ids(self) -> List[str]:
        """Return a snapshot of all job ids."""

    @abstractmethod
    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Return a deep-copy of every job keyed by id."""

    @abstractmethod
    def count(self) -> int:
        """Total number of tracked jobs."""

    @abstractmethod
    def lock(self) -> Iterator[None]:
        """Context manager yielding the underlying lock.

        Concrete implementations decorate their override with
        :func:`contextlib.contextmanager`. Call sites that need
        read-modify-write atomicity across several fields should use
        this via ``with store.lock():``; the in-memory backend returns
        the same ``_push_jobs_lock`` that existing handlers already
        hold, so bare-dict mutations and facade mutations stay in
        lockstep.
        """

    def stats(self) -> Dict[str, Any]:
        """Monitoring snapshot. Overridden per backend."""
        return {"kind": self.kind, "count": self.count()}


class InMemoryJobStore(JobStore):
    """Default backend: wraps an in-process dict + a lock.

    Binding to an existing ``_push_jobs`` dict + lock (rather than
    holding our own) keeps every legacy call site backward-compatible.
    Mutations through the facade and mutations through the bare dict
    are visible to each other.

    The lock SHOULD be a :class:`threading.RLock` if callers want to
    perform compound transactions via ``with store.lock():`` that then
    call other facade methods -- plain :class:`threading.Lock` would
    self-deadlock in that pattern. The facade accepts either type.
    """

    kind = "inmemory"

    def __init__(
        self,
        jobs_dict: Dict[str, Dict[str, Any]],
        lock: Any,  # threading.Lock or threading.RLock
    ) -> None:
        self._jobs = jobs_dict
        self._lock = lock

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        if not job_id:
            return None
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return copy.deepcopy(job)

    def put(self, job_id: str, job: Dict[str, Any]) -> None:
        if not job_id:
            raise ValueError("job_id must be non-empty")
        with self._lock:
            self._jobs[job_id] = job

    def update(
        self,
        job_id: str,
        mutator: Callable[[Dict[str, Any]], None],
    ) -> bool:
        if not job_id:
            return False
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            try:
                mutator(job)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[job_store] mutator raised for %s: %s", job_id, exc,
                )
                raise
        return True

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def ids(self) -> List[str]:
        with self._lock:
            return list(self._jobs.keys())

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: copy.deepcopy(v) for k, v in self._jobs.items()}

    def count(self) -> int:
        with self._lock:
            return len(self._jobs)

    @contextmanager
    def lock(self) -> Iterator[None]:
        with self._lock:
            yield

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._jobs)
            by_status: Dict[str, int] = {}
            by_type: Dict[str, int] = {}
            active = 0
            for job in self._jobs.values():
                status = job.get("status") or "unknown"
                by_status[status] = by_status.get(status, 0) + 1
                jtype = job.get("job_type") or job.get("type") or "unknown"
                by_type[jtype] = by_type.get(jtype, 0) + 1
                if status in (
                    "running", "queued", "queued_global",
                    "in_progress", "pending_commit",
                ):
                    active += 1
        return {
            "kind": self.kind,
            "count": total,
            "active": active,
            "by_status": by_status,
            "by_type": by_type,
        }


class FileSnapshotJobStore(InMemoryJobStore):
    """Experimental: in-memory store that periodically snapshots to disk.

    Primarily a proof of concept for Wave 5 persistence; not wired into
    the app yet. Takes a ``snapshot_path`` (typically under
    ``~/.scaler_active_upgrades.json``-adjacent) and writes a JSON dump
    every ``flush_interval_s`` seconds, or whenever ``flush_now()`` is
    called. Restoration at startup is up to the caller -- this store
    itself does NOT auto-load, because the existing upgrade recovery
    logic already handles that file.
    """

    kind = "file_snapshot"

    def __init__(
        self,
        jobs_dict: Dict[str, Dict[str, Any]],
        lock: Any,  # threading.Lock or threading.RLock
        snapshot_path: str,
        flush_interval_s: float = 10.0,
    ) -> None:
        super().__init__(jobs_dict, lock)
        self._snapshot_path = snapshot_path
        self._flush_interval_s = max(1.0, float(flush_interval_s))
        self._flusher_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._flusher_thread is not None:
            return
        t = threading.Thread(
            target=self._flush_loop,
            name="job-store-flusher",
            daemon=True,
        )
        self._flusher_thread = t
        t.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._flusher_thread is not None:
            self._flusher_thread.join(timeout=5.0)

    def flush_now(self) -> bool:
        import json
        try:
            snap = self.snapshot()
            tmp = f"{self._snapshot_path}.tmp"
            with open(tmp, "w", encoding="utf-8") as fp:
                json.dump(snap, fp, default=str)
            os.replace(tmp, self._snapshot_path)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("[job_store] flush failed: %s", exc)
            return False

    def _flush_loop(self) -> None:
        while not self._stop_event.wait(self._flush_interval_s):
            self.flush_now()

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["snapshot_path"] = self._snapshot_path
        base["flush_interval_s"] = self._flush_interval_s
        return base


def select_job_store(
    jobs_dict: Dict[str, Dict[str, Any]],
    lock: Any,  # threading.Lock or threading.RLock
) -> JobStore:
    """Pick a store implementation from environment config.

    Respects ``TP_JOB_STORE`` (``inmemory`` default, ``file_snapshot``).
    Unknown values fall back to in-memory. The Redis variant is not
    implemented yet -- it would require rewriting the per-job mutation
    semantics above a proper transaction layer.
    """
    kind = (os.environ.get("TP_JOB_STORE") or "inmemory").strip().lower()
    if kind == "file_snapshot":
        path = os.environ.get(
            "TP_JOB_STORE_PATH",
            os.path.expanduser("~/.scaler_job_store.json"),
        )
        interval = float(os.environ.get("TP_JOB_STORE_FLUSH_S", "10"))
        store = FileSnapshotJobStore(jobs_dict, lock, path, interval)
        store.start()
        return store
    if kind not in ("inmemory", "memory", "default"):
        logger.warning(
            "[job_store] unknown TP_JOB_STORE=%r -- using in-memory", kind,
        )
    return InMemoryJobStore(jobs_dict, lock)


__all__ = [
    "JobStore",
    "InMemoryJobStore",
    "FileSnapshotJobStore",
    "select_job_store",
]
