"""Background poller for live-status kinds (branches, Jira, test_suites, spirent).

Runs one asyncio task per enabled kind, started by ``scaler_bridge`` on
FastAPI ``startup`` and cancelled on ``shutdown``. Design goals:

* **De-duplicated** -- if five users have attached the same Jenkins branch,
  we call Jenkins once per cycle, not five times. The first row wins; the
  refreshed payload then updates every identical row across all users.
* **Concurrency-capped** -- each kind fans out at most ``PER_KIND_CONCURRENCY``
  simultaneous live fetches. One user attaching 100 branches can't starve
  the poller for the others.
* **Never-die** -- the inner while loop catches every exception, logs, and
  continues. Cancellation is still honored via ``asyncio.CancelledError``.
* **Respectful** -- never polls private rows (those are user-authored free
  text like notes). Only kinds flagged ``supports_live=True``.
* **Delta-aware** -- publishes a WebSocket event only when the payload
  changed materially (e.g. new build number, new status). Prevents UI
  render storms during quiet periods.
* **Observable** -- ``status()`` returns per-kind last-cycle timestamp,
  fetched count, and most recent error so an admin endpoint can tell at
  a glance whether the poller is healthy.

Shutdown semantics: FastAPI's ``shutdown`` event calls ``stop()``; we set
``_stop`` and cancel each task. The task's ``wait_for`` returns immediately
and the cancel propagates through ``asyncio.gather``.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import knowledge as knowledge_module

logger = logging.getLogger(__name__)


# -- Configuration -----------------------------------------------------------

# Per-kind poll interval in seconds. Keep these generous -- the user can
# always click "Refresh" for an immediate update.
DEFAULT_INTERVALS: Dict[str, int] = {
    "branch":     180,   # 3 min -- Jenkins builds finish every few minutes
    "jira_epic":  300,   # 5 min -- Jira status changes are slower-moving
    "test_suite": 120,   # 2 min -- local filesystem, cheap
    "spirent":    300,   # 5 min -- local filesystem, rarely changes
}

# Max simultaneous live-fetcher HTTP calls per kind per cycle. 4 keeps us
# well below any reasonable Jenkins/Jira rate limit while still draining
# large rosters quickly.
PER_KIND_CONCURRENCY = 4

# How many recent per-kind errors to retain for the /status endpoint.
ERROR_WINDOW = 5


def _enabled_kinds() -> List[str]:
    """Environment-variable opt-out. ``KNOWLEDGE_POLLER_KINDS=none`` disables the poller entirely;
    ``KNOWLEDGE_POLLER_KINDS=branch,jira_epic`` restricts to those."""
    raw = os.environ.get("KNOWLEDGE_POLLER_KINDS", "").strip().lower()
    if raw == "none":
        return []
    if not raw:
        # Use every kind that has a registered live_fetcher.
        return [k for k, v in DEFAULT_INTERVALS.items() if knowledge_module.get_spec(k)]
    wanted = {p.strip() for p in raw.split(",") if p.strip()}
    return [k for k in DEFAULT_INTERVALS if k in wanted and knowledge_module.get_spec(k)]


# -- Delta detection ---------------------------------------------------------

def _delta_signature(kind: str, payload: Optional[Dict[str, Any]]) -> Tuple:
    """Stable tuple that captures "what does the UI actually care about"
    for a given payload. If this tuple changes between polls we publish
    a WebSocket event; otherwise we stay silent to avoid spamming the UI."""
    p = payload or {}
    if kind == "branch":
        b = p.get("last_build") or {}
        return (
            int(b.get("number") or 0),
            str(b.get("result") or ""),
            bool(b.get("building")),
            bool(b.get("sanitizer")),
            bool(b.get("has_images")),
        )
    if kind == "jira_epic":
        return (
            str(p.get("status") or ""),
            str(p.get("assignee") or ""),
            str(p.get("priority") or ""),
            str(p.get("summary") or ""),
            str(p.get("last_error") or ""),
        )
    if kind == "test_suite":
        runs = p.get("last_runs") or []
        if not isinstance(runs, list) or not runs:
            return ("",)
        r0 = runs[0] or {}
        return (str(r0.get("run_id") or ""), str(r0.get("verdict") or ""))
    if kind == "spirent":
        return (
            int(p.get("stream_count") or 0),
            int(p.get("device_count") or 0),
            str(p.get("last_run_at") or ""),
        )
    return tuple(sorted((p or {}).items(), key=lambda kv: kv[0]))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# -- Main loop ---------------------------------------------------------------

class KnowledgePoller:
    """Orchestrates one polling task per enabled kind."""

    def __init__(self) -> None:
        self._tasks: List[asyncio.Task] = []
        self._stop = asyncio.Event()
        # Per-kind diagnostic state surfaced via status().
        self._stats: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------ lifecycle

    async def start(self) -> None:
        if self._tasks:
            return
        self._stop.clear()
        kinds = _enabled_kinds()
        for kind in kinds:
            self._stats[kind] = {
                "interval_s": DEFAULT_INTERVALS.get(kind, 300),
                "started_at": _now_iso(),
                "last_cycle_at": None,
                "last_cycle_ms": None,
                "rows_seen": 0,
                "rows_refreshed": 0,
                "events_emitted": 0,
                "recent_errors": [],
            }
            self._tasks.append(asyncio.create_task(
                self._supervise(kind), name=f"knowledge-poller:{kind}",
            ))
        if self._tasks:
            logger.info(
                "[knowledge_poller] started %d pollers: %s",
                len(self._tasks), ", ".join(k for k in kinds),
            )

    async def stop(self) -> None:
        self._stop.set()
        for t in self._tasks:
            if not t.done():
                t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    # ------------------------------------------------------------ diagnostics

    def status(self) -> Dict[str, Any]:
        """Snapshot for the /knowledge/poller/status endpoint."""
        alive = {t.get_name(): (not t.done()) for t in self._tasks}
        return {
            "running": any(alive.values()),
            "task_count": len(self._tasks),
            "enabled_kinds": list(self._stats.keys()),
            "tasks_alive": alive,
            "stats": dict(self._stats),
        }

    # ------------------------------------------------------------ internals

    async def _supervise(self, kind: str) -> None:
        """Outer never-die loop. ``_run_kind`` is expected to handle all
        cycle-level errors, but if it somehow raises we log + restart
        after a small backoff. Only ``CancelledError`` breaks out."""
        backoff = 5
        while not self._stop.is_set():
            try:
                await self._run_kind(kind)
                return  # _run_kind exits cleanly only on stop
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 -- keep polling alive
                self._record_error(kind, f"supervisor restart: {exc}")
                logger.warning(
                    "[knowledge_poller] %s supervisor restarting in %ds after: %s",
                    kind, backoff, exc,
                )
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, 60)

    async def _run_kind(self, kind: str) -> None:
        interval = DEFAULT_INTERVALS.get(kind, 300)
        # Jitter the first run so multiple kinds starting together don't
        # all hit Jenkins/Jira at t=0. The jitter is capped at a quarter
        # of the interval so the user still sees their first refresh soon
        # after server boot.
        jitter = random.uniform(2.0, min(20.0, interval / 4))
        logger.info(
            "[knowledge_poller] %s: interval=%ds, first cycle in %.1fs",
            kind, interval, jitter,
        )
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=jitter)
            return  # stop() raced us before the first cycle
        except asyncio.TimeoutError:
            pass

        while not self._stop.is_set():
            start = asyncio.get_running_loop().time()
            try:
                await self._cycle_kind(kind)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                self._record_error(kind, str(exc))
                logger.warning("[knowledge_poller] %s cycle failed: %s", kind, exc)
            elapsed_ms = int((asyncio.get_running_loop().time() - start) * 1000)
            self._stats[kind]["last_cycle_at"] = _now_iso()
            self._stats[kind]["last_cycle_ms"] = elapsed_ms
            # Sleep until next cycle OR stop.
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    async def _cycle_kind(self, kind: str) -> None:
        spec = knowledge_module.get_spec(kind)
        if not spec or not spec.supports_live:
            return
        # Lazy imports to avoid circular imports at module load time.
        from ..auth.user_store import user_store
        from ..event_bus import event_bus

        rows = await asyncio.to_thread(
            user_store.list_all_public_knowledge_rows, kind,
        )
        if not rows:
            return

        # De-duplicate by natural key -- the *first* matching row drives
        # the fetch, and its refreshed payload is fanned out to all
        # duplicates across users.
        by_key: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            by_key.setdefault(r["key"], []).append(r)

        self._stats[kind]["rows_seen"] = len(rows)
        refreshed = 0
        events = 0

        sem = asyncio.Semaphore(PER_KIND_CONCURRENCY)

        async def _process_group(key: str, duplicates: List[Dict[str, Any]]) -> None:
            nonlocal refreshed, events
            if self._stop.is_set():
                return
            driver = duplicates[0]
            async with sem:
                try:
                    new_payload = await asyncio.to_thread(
                        spec.live_fetcher, driver["owner"], driver["payload"],
                    )
                except Exception as exc:  # noqa: BLE001 -- fetch is best-effort
                    self._record_error(kind, f"{key}: {exc}")
                    return
            if not new_payload:
                return
            before = _delta_signature(kind, driver["payload"])
            after = _delta_signature(kind, new_payload)
            changed = before != after

            # Fan write into EVERY duplicate's owning DB so cross-user
            # viewers see fresh values.
            for dup in duplicates:
                try:
                    await asyncio.to_thread(
                        user_store.update_public_knowledge_payload,
                        dup["owner"], dup["domain_id"], kind, key, new_payload,
                    )
                    refreshed += 1
                except Exception as exc:  # noqa: BLE001
                    self._record_error(
                        kind, f"{key}@{dup['owner']}: db-write {exc}",
                    )
                    continue
                if changed:
                    try:
                        viewers = await asyncio.to_thread(
                            user_store.domain_viewers,
                            dup["owner"], dup["domain_id"],
                        )
                    except Exception:
                        viewers = [dup["owner"]]
                    event_bus.publish_to_users_sync(viewers, {
                        "type": "domain.knowledge.updated",
                        "domain_id": dup["domain_id"],
                        "kind": kind,
                        "key": key,
                        "visibility": "public",
                        "payload": new_payload,
                        "source": "poller",
                    })
                    events += 1

        await asyncio.gather(
            *(_process_group(k, dups) for k, dups in by_key.items()),
            return_exceptions=True,
        )

        self._stats[kind]["rows_refreshed"] = refreshed
        self._stats[kind]["events_emitted"] = events

    def _record_error(self, kind: str, message: str) -> None:
        bucket = self._stats.setdefault(kind, {}).setdefault("recent_errors", [])
        bucket.append({"at": _now_iso(), "error": message[:300]})
        if len(bucket) > ERROR_WINDOW:
            del bucket[: len(bucket) - ERROR_WINDOW]


poller = KnowledgePoller()
