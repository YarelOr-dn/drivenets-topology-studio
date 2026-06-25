"""
Live device-context coalescer (Wave 2.2).

Purpose
-------
Deduplicate simultaneous ``live=True`` calls to ``_get_device_context``.
When N users have the same device on their canvas and their browsers
all hit ``GET /api/devices/<id>/context?live=true`` within the same
90-second window, a naive backend would open N SSH sessions to the
device. This module collapses that to 1 SSH round-trip:

* First caller becomes the *leader*: runs the fetch.
* Subsequent callers (within TTL and before leader finishes) are
  *followers*: they park on the same :class:`concurrent.futures.Future`
  and get the leader's result once it resolves.
* Subsequent callers (within TTL but after leader finishes) read the
  completed result from the cache.
* Callers after TTL expiry trigger a fresh leader fetch.

Keys
----
``(device_id, app_user)`` -- per-user isolation so audit logs on the
device reflect the actual initiator (credentials may differ per user).
Cross-user sharing is a future optimization but semantically wrong if
DNOS shows per-user views.

Failure handling
----------------
If the leader raises, the exception is propagated to all followers and
no cache entry is written. The in-flight slot is freed so the next call
triggers a fresh fetch.

Cache bound
-----------
Soft cap of 256 entries. When exceeded, the oldest completed entry is
evicted (simple FIFO, not true LRU -- good enough for a lab tool).
"""
from __future__ import annotations

import concurrent.futures
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple


class _Cached:
    __slots__ = ("value", "completed_at")

    def __init__(self, value: Any):
        self.value = value
        self.completed_at = time.time()


class LiveCoalescer:
    """Per-key single-flight + TTL cache for expensive live fetches."""

    def __init__(self, ttl_seconds: float = 90.0,
                 max_wait_seconds: float = 90.0,
                 max_entries: int = 256):
        self.ttl = ttl_seconds
        self.max_wait = max_wait_seconds
        self.max_entries = max_entries
        self._cache: "OrderedDict[str, _Cached]" = OrderedDict()
        self._inflight: Dict[str, concurrent.futures.Future] = {}
        self._lock = threading.Lock()
        self._stats = {
            "hits_cache": 0,
            "hits_inflight": 0,
            "misses": 0,
            "errors": 0,
            "evictions": 0,
        }

    def _evict_if_needed(self) -> None:
        """Assumes caller holds ``self._lock``."""
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1

    def get(
        self,
        key: str,
        fetch: Callable[[], Any],
        *,
        ttl_seconds: Optional[float] = None,
    ) -> Tuple[Any, str]:
        """Return ``(value, origin)`` where ``origin`` is one of
        ``"cache"`` / ``"coalesced"`` / ``"fresh"`` / ``"stale_fallback"``.

        ``fetch`` is invoked at most once per TTL window per key.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl
        now = time.time()

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None and (now - cached.completed_at) < ttl:
                self._stats["hits_cache"] += 1
                # Refresh FIFO position so this key isn't the first
                # evicted.
                self._cache.move_to_end(key)
                return cached.value, "cache"

            fut = self._inflight.get(key)
            if fut is not None:
                self._stats["hits_inflight"] += 1
                is_leader = False
            else:
                fut = concurrent.futures.Future()
                self._inflight[key] = fut
                self._stats["misses"] += 1
                is_leader = True

        if is_leader:
            try:
                value = fetch()
            except BaseException as exc:
                with self._lock:
                    self._inflight.pop(key, None)
                    self._stats["errors"] += 1
                fut.set_exception(exc)
                raise
            with self._lock:
                self._cache[key] = _Cached(value)
                self._cache.move_to_end(key)
                self._inflight.pop(key, None)
                self._evict_if_needed()
            fut.set_result(value)
            return value, "fresh"

        # Follower: wait for the leader's result.
        try:
            value = fut.result(timeout=self.max_wait)
            return value, "coalesced"
        except concurrent.futures.TimeoutError:
            # Leader is stuck. Surface the stale cached value if any,
            # else re-raise.
            with self._lock:
                cached = self._cache.get(key)
            if cached is not None:
                return cached.value, "stale_fallback"
            raise

    def invalidate(self, key: str) -> None:
        """Drop the cached value for ``key`` so the next ``get`` fetches
        fresh. Useful after a write operation that changes device state
        (config push, upgrade).
        """
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        """Drop all cached keys starting with ``prefix``. Returns count."""
        with self._lock:
            to_drop = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in to_drop:
                self._cache.pop(k, None)
        return len(to_drop)

    def invalidate_matching(self, predicate: Callable[[str], bool]) -> int:
        """Drop all cached keys for which ``predicate(key)`` returns True.

        Useful when the key format embeds multiple fields and the caller
        only knows a subset (e.g. mgmt_ip without scaler_device_id).
        """
        with self._lock:
            to_drop = [k for k in self._cache.keys() if predicate(k)]
            for k in to_drop:
                self._cache.pop(k, None)
        return len(to_drop)

    def snapshot(self) -> Dict[str, Any]:
        """Observability snapshot for the /api/health/concurrency endpoint."""
        with self._lock:
            return {
                "ttl_seconds": self.ttl,
                "entries": len(self._cache),
                "inflight": len(self._inflight),
                "inflight_keys": list(self._inflight.keys()),
                "stats": dict(self._stats),
            }


# Module-level singleton. 90-second TTL is a compromise between "fresh
# enough that users don't see stale LLDP/BGP state" and "rare enough
# that we don't hammer a 10-device topology with 10 concurrent SSH
# sessions per canvas refresh".
coalescer = LiveCoalescer(ttl_seconds=90.0, max_wait_seconds=90.0)


__all__ = ["LiveCoalescer", "coalescer"]
