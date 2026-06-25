"""
Per-device operation scheduler (Wave 2.1).

Purpose
-------
Prevent config/upgrade collisions on a single DNOS device when multiple
users target it simultaneously. Each management IP gets its own mutex.
Callers wrap the CLI-critical section (`configure` -> `commit` -> reboot)
with ``scheduler.exclusive(mgmt_ip, op, owner, job_id)``; concurrent
callers for the SAME device queue up, callers for DIFFERENT devices run
in parallel.

Read-only operations (show commands, running-config fetch, monitoring)
do NOT acquire the lock -- they're idempotent on DNOS and blocking them
would defeat the purpose of the 5-minute canvas monitor.

Dry-run / held-session flow
---------------------------
``push_config_terminal_check_and_hold`` leaves an SSH channel open while
the user decides whether to Commit or Cancel. The device is still busy
from DNOS's point of view, so we MUST keep the lock held across the
commit/cancel HTTP round-trip. The ``acquire()`` / ``release(token)``
pair lets the initial daemon thread transfer ownership to the later
commit/cancel endpoint without involving a second thread.

Why ``threading.Lock`` (not ``asyncio.Lock`` as the plan originally said)
------------------------------------------------------------------------
The critical sections live in sync daemon threads (``_run_push``,
``_run_device_upgrade``), not coroutines. ``threading.Lock`` is the
native primitive there. Any async endpoint that later needs exclusivity
can still acquire via ``await asyncio.to_thread(scheduler.acquire, ...)``.

What this module does NOT do
----------------------------
* It does not hold locks across process restarts (in-memory by design;
  on restart every device is free again, which is correct because the
  recovery code re-establishes per-job state).
* It does not implement fairness / priority / starvation protection;
  FIFO-ish order is determined by ``threading.Lock``'s underlying
  semantics. Good enough for <= 50 concurrent callers per device, which
  is orders of magnitude more than any realistic lab load.
* It does not serialize across multiple uvicorn workers. Wave 5.1 /
  Wave 5.2 introduce pluggable broker/job-store so a Redis-backed
  scheduler can replace this one without changing callers.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional


# Wave 4.1: global cap on heavy device operations (upgrades, and
# optionally long-running pushes). Prevents 30 parallel upgrades from
# saturating the bridge's paramiko pool, CPU, and network links to the
# lab. Tune via ``TP_UPGRADE_MAX_CONCURRENT`` (default 4). Set to 0 to
# disable the cap entirely (not recommended in production).
def _env_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


_GLOBAL_UPGRADE_SLOTS = _env_int("TP_UPGRADE_MAX_CONCURRENT", 4)

# Wave 6.1: global cap on concurrent config pushes. Unlike upgrades, config
# pushes are short (~10-30s) but a burst of 100 parallel SSH connect+commit
# storms can saturate network egress and CPU. ``TP_GLOBAL_PUSH_SLOTS``
# (default 20) caps total simultaneous push sessions across every device.
# Set to 0 to disable entirely.
_GLOBAL_PUSH_SLOTS = _env_int("TP_GLOBAL_PUSH_SLOTS", 20)

# Wave 6.4: per-user cap on concurrent pushes. Prevents one user from
# submitting 50 simultaneous pushes that monopolize the global pool while
# other users get queued out. ``TP_PER_USER_PUSH_MAX`` (default 5).
# Set to 0 to disable the cap.
_PER_USER_PUSH_MAX = _env_int("TP_PER_USER_PUSH_MAX", 5)

# Wave 6.5: per-device queue depth cap. Beyond this, new waiters are
# rejected with HTTP 503 + Retry-After rather than silently queued (which
# at 100 users on one device means a 25-minute wait). ``TP_DEVICE_QUEUE_MAX``
# (default 10). Set to 0 to disable (unbounded queue).
_DEVICE_QUEUE_MAX = _env_int("TP_DEVICE_QUEUE_MAX", 10)


class DeviceBusyError(RuntimeError):
    """Raised by ``try_acquire`` when the device queue is already too deep.

    The HTTP layer converts this to a 503 + ``Retry-After`` header so the
    client backs off rather than blocking indefinitely.
    """

    __slots__ = ("mgmt_ip", "queue_depth", "retry_after_s")

    def __init__(self, mgmt_ip: str, queue_depth: int, retry_after_s: int = 120):
        super().__init__(
            f"device {mgmt_ip} queue depth {queue_depth} exceeds configured max"
        )
        self.mgmt_ip = mgmt_ip
        self.queue_depth = queue_depth
        self.retry_after_s = retry_after_s


class PerUserLimitError(RuntimeError):
    """Raised when a user already has ``TP_PER_USER_PUSH_MAX`` in-flight pushes.

    The HTTP layer converts this to a 429 + ``Retry-After`` header.
    """

    __slots__ = ("owner", "in_flight", "max_per_user", "retry_after_s")

    def __init__(self, owner: str, in_flight: int, max_per_user: int,
                 retry_after_s: int = 60):
        super().__init__(
            f"user {owner!r} has {in_flight} active pushes (max {max_per_user})"
        )
        self.owner = owner
        self.in_flight = in_flight
        self.max_per_user = max_per_user
        self.retry_after_s = retry_after_s


class _SchedulerToken:
    """Opaque handle returned by ``acquire()``; passed back to ``release()``.

    Instances only hold references, no public API. Comparing tokens is
    identity-based, which is what we want.
    """

    __slots__ = ("token_id", "mgmt_ip", "op", "owner", "job_id",
                 "acquired_at", "wait_s")

    def __init__(self, mgmt_ip: str, op: str, owner: str, job_id: str):
        self.token_id = uuid.uuid4().hex
        self.mgmt_ip = mgmt_ip
        self.op = op
        self.owner = owner
        self.job_id = job_id
        self.acquired_at = 0.0
        self.wait_s = 0.0


class DeviceOpScheduler:
    """Per-mgmt-ip serialization for CLI-mutating operations.

    Thread-safe. Every caller that enters config mode on a device MUST
    go through ``acquire()``/``release()`` or ``exclusive()``; read-only
    show commands SHOULD bypass.
    """

    def __init__(
        self,
        global_upgrade_slots: Optional[int] = None,
        global_push_slots: Optional[int] = None,
        per_user_push_max: Optional[int] = None,
        device_queue_max: Optional[int] = None,
    ) -> None:
        self._locks: Dict[str, threading.Lock] = {}
        self._status: Dict[str, Dict[str, Any]] = {}
        self._waiters: Dict[str, List[Dict[str, Any]]] = {}
        self._tokens: Dict[str, _SchedulerToken] = {}
        self._registry_lock = threading.Lock()
        self._stats = {
            "acquires": 0,
            "wait_time_total_s": 0.0,
            "max_wait_s": 0.0,
        }

        # Wave 4.1: global semaphore that caps heavy operations across
        # ALL devices. Upgrades reserve a slot for their full duration.
        # If slots == 0 we bypass the cap entirely.
        slots = global_upgrade_slots if global_upgrade_slots is not None else _GLOBAL_UPGRADE_SLOTS
        self._global_upgrade_max = int(slots)
        self._global_upgrade_sema: Optional[threading.Semaphore] = (
            threading.Semaphore(self._global_upgrade_max)
            if self._global_upgrade_max > 0 else None
        )
        self._global_upgrade_in_flight: List[Dict[str, Any]] = []
        self._global_upgrade_queued: List[Dict[str, Any]] = []
        self._global_upgrade_stats = {
            "acquires": 0,
            "wait_time_total_s": 0.0,
            "max_wait_s": 0.0,
            "peak_in_flight": 0,
        }

        # Wave 6.1: separate global push pool. Callers nest this OUTSIDE
        # the per-device lock so the cap throttles SSH/commit fan-out
        # without blocking the scheduler queue.
        push_slots = (global_push_slots if global_push_slots is not None
                      else _GLOBAL_PUSH_SLOTS)
        self._global_push_max = int(push_slots)
        self._global_push_sema: Optional[threading.Semaphore] = (
            threading.Semaphore(self._global_push_max)
            if self._global_push_max > 0 else None
        )
        self._global_push_in_flight: List[Dict[str, Any]] = []
        self._global_push_queued: List[Dict[str, Any]] = []
        self._global_push_stats = {
            "acquires": 0,
            "wait_time_total_s": 0.0,
            "max_wait_s": 0.0,
            "peak_in_flight": 0,
        }

        # Wave 6.4: per-user push counter. Keyed by owner; increments on
        # ``reserve_user_push`` (synchronous, non-blocking) and decrements on
        # ``release_user_push``. Bound checked against ``_per_user_push_max``.
        self._per_user_push_max = int(
            per_user_push_max if per_user_push_max is not None
            else _PER_USER_PUSH_MAX
        )
        self._per_user_push_counts: Dict[str, int] = {}
        self._per_user_push_stats = {
            "rejections": 0,
            "peak_by_user": {},  # owner -> max simultaneous
        }

        # Wave 6.5: per-device queue depth cap. ``try_acquire`` checks this
        # BEFORE blocking on the lock; callers past the cap receive
        # ``DeviceBusyError`` so the HTTP layer can return 503 + Retry-After.
        self._device_queue_max = int(
            device_queue_max if device_queue_max is not None
            else _DEVICE_QUEUE_MAX
        )
        self._device_queue_rejections = 0

    def _get_lock(self, mgmt_ip: str) -> threading.Lock:
        with self._registry_lock:
            lock = self._locks.get(mgmt_ip)
            if lock is None:
                lock = threading.Lock()
                self._locks[mgmt_ip] = lock
            return lock

    # ------------------------------------------------------------------
    # Token-based API (used by the dry-run held-session path)
    # ------------------------------------------------------------------
    def acquire(
        self,
        mgmt_ip: str,
        op: str,
        owner: str = "default",
        job_id: str = "",
        on_queued: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        progress_interval_s: float = 5.0,
    ) -> Optional[_SchedulerToken]:
        """Block until exclusive access to ``mgmt_ip`` is granted; return
        a token that MUST be passed to ``release(token)`` when done.

        Returns ``None`` if ``mgmt_ip`` is falsy (caller has nothing to
        serialize against).

        Wave 4.3: ``on_progress`` lets callers surface queue position to
        the end user while they wait. It fires roughly every
        ``progress_interval_s`` seconds with a dict of
        ``{position, total, holder, elapsed_s}``. It stops automatically
        once the lock is acquired or if the caller already reached the
        head of the queue before the first tick.
        """
        if not mgmt_ip:
            return None

        token = _SchedulerToken(mgmt_ip, op, owner, job_id)
        waiter = {
            "op": op,
            "owner": owner,
            "job_id": job_id,
            "queued_at": time.time(),
            "token_id": token.token_id,
        }
        lock = self._get_lock(mgmt_ip)

        with self._registry_lock:
            self._waiters.setdefault(mgmt_ip, []).append(waiter)
            holder = self._status.get(mgmt_ip)
            initial_position = len(self._waiters[mgmt_ip])
            initial_total = initial_position + (1 if holder else 0)
        if on_queued and holder is not None:
            try:
                on_queued(dict(holder))
            except Exception:
                pass

        # Wave 4.3: spawn a progress reporter while we wait. The thread
        # exits quickly once the lock is acquired.
        progress_stop = threading.Event() if on_progress and holder else None
        progress_thread: Optional[threading.Thread] = None
        if progress_stop is not None and progress_interval_s > 0:
            started_at = time.time()

            def _reporter():
                while not progress_stop.is_set():
                    if progress_stop.wait(progress_interval_s):
                        break
                    with self._registry_lock:
                        waiters = self._waiters.get(mgmt_ip, [])
                        try:
                            pos = waiters.index(waiter) + 1
                        except ValueError:
                            # We got the lock; stop reporting.
                            break
                        holder_now = self._status.get(mgmt_ip)
                        total = len(waiters) + (1 if holder_now else 0)
                    try:
                        on_progress({
                            "position": pos,
                            "total": total,
                            "holder": dict(holder_now) if holder_now else None,
                            "elapsed_s": time.time() - started_at,
                        })
                    except Exception:
                        pass

            progress_thread = threading.Thread(
                target=_reporter,
                name=f"scheduler-progress:{mgmt_ip}",
                daemon=True,
            )
            progress_thread.start()

            # Fire one immediate snapshot so the UI doesn't have to wait
            # `progress_interval_s` for the first update.
            try:
                on_progress({
                    "position": initial_position,
                    "total": initial_total,
                    "holder": dict(holder) if holder else None,
                    "elapsed_s": 0.0,
                })
            except Exception:
                pass

        wait_start = time.time()
        try:
            lock.acquire()
        finally:
            if progress_stop is not None:
                progress_stop.set()
        wait_s = time.time() - wait_start
        token.acquired_at = time.time()
        token.wait_s = wait_s

        with self._registry_lock:
            try:
                self._waiters.get(mgmt_ip, []).remove(waiter)
            except ValueError:
                pass
            self._status[mgmt_ip] = {
                "op": op,
                "owner": owner,
                "job_id": job_id,
                "token_id": token.token_id,
                "started_at": token.acquired_at,
                "wait_s": wait_s,
            }
            self._tokens[token.token_id] = token
            self._stats["acquires"] += 1
            self._stats["wait_time_total_s"] += wait_s
            if wait_s > self._stats["max_wait_s"]:
                self._stats["max_wait_s"] = wait_s

        return token

    def release(self, token: Optional[_SchedulerToken]) -> None:
        """Release a lock previously obtained from ``acquire()``.

        Safe to call with ``None`` (no-op). Safe to call twice (second
        call is a no-op).
        """
        if token is None:
            return
        with self._registry_lock:
            stored = self._tokens.pop(token.token_id, None)
            if stored is None:
                return  # already released or foreign token
            current = self._status.get(token.mgmt_ip)
            if current and current.get("token_id") == token.token_id:
                self._status.pop(token.mgmt_ip, None)
            lock = self._locks.get(token.mgmt_ip)
        if lock is not None:
            try:
                lock.release()
            except RuntimeError:
                pass  # already released, should not happen

    # ------------------------------------------------------------------
    # Context-manager API (the common path)
    # ------------------------------------------------------------------
    @contextmanager
    def exclusive(
        self,
        mgmt_ip: str,
        op: str,
        owner: str = "default",
        job_id: str = "",
        on_queued: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_acquired: Optional[Callable[[float], None]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        progress_interval_s: float = 5.0,
    ):
        """Acquire ``mgmt_ip`` for the duration of the ``with`` block.

        Args:
            mgmt_ip: Lock key (management IP). Empty -> no-op.
            op: Short label (``push`` / ``upgrade`` / ``wizard`` / ...).
            owner: Authenticated username that initiated the op.
            job_id: Associated ``_push_jobs`` id.
            on_queued: Called once with the current holder metadata when
                       the caller has to wait.
            on_acquired: Called with wait duration (seconds) on grant.
            on_progress: Wave 4.3 -- called repeatedly with queue
                         position/total while waiting. Stops on grant.
            progress_interval_s: Seconds between progress callbacks.
        """
        token = self.acquire(
            mgmt_ip, op, owner, job_id,
            on_queued=on_queued,
            on_progress=on_progress,
            progress_interval_s=progress_interval_s,
        )
        if on_acquired and token is not None:
            try:
                on_acquired(token.wait_s)
            except Exception:
                pass
        try:
            yield token
        finally:
            self.release(token)

    # ------------------------------------------------------------------
    # Global upgrade slot API (Wave 4.1)
    # ------------------------------------------------------------------
    def acquire_global_upgrade_slot(
        self,
        op: str = "upgrade",
        owner: str = "default",
        job_id: str = "",
        on_queued: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Block until a global upgrade slot is available.

        Returns a handle dict used for release. When the cap is
        disabled (slots == 0), returns a sentinel handle that makes
        release() a no-op.
        """
        sema = self._global_upgrade_sema
        if sema is None:
            return {"disabled": True}
        waiter = {
            "op": op,
            "owner": owner,
            "job_id": job_id,
            "queued_at": time.time(),
        }
        with self._registry_lock:
            # Is a slot immediately available? If so, skip the queued state.
            in_flight = len(self._global_upgrade_in_flight)
            slot_full = in_flight >= self._global_upgrade_max
            if slot_full:
                self._global_upgrade_queued.append(waiter)
                queue_len = len(self._global_upgrade_queued)
            else:
                queue_len = 0
        if slot_full and on_queued:
            try:
                on_queued({"queue_len": queue_len, "in_flight": in_flight,
                           "slots_max": self._global_upgrade_max})
            except Exception:
                pass
        wait_start = time.time()
        sema.acquire()
        wait_s = time.time() - wait_start
        started_at = time.time()
        handle = {
            "op": op,
            "owner": owner,
            "job_id": job_id,
            "started_at": started_at,
            "wait_s": wait_s,
        }
        with self._registry_lock:
            try:
                self._global_upgrade_queued.remove(waiter)
            except ValueError:
                pass
            self._global_upgrade_in_flight.append(handle)
            s = self._global_upgrade_stats
            s["acquires"] += 1
            s["wait_time_total_s"] += wait_s
            if wait_s > s["max_wait_s"]:
                s["max_wait_s"] = wait_s
            if len(self._global_upgrade_in_flight) > s["peak_in_flight"]:
                s["peak_in_flight"] = len(self._global_upgrade_in_flight)
        return handle

    def release_global_upgrade_slot(self, handle: Optional[Dict[str, Any]]) -> None:
        """Release a slot previously obtained from acquire_global_upgrade_slot."""
        if handle is None or handle.get("disabled"):
            return
        with self._registry_lock:
            try:
                self._global_upgrade_in_flight.remove(handle)
            except ValueError:
                pass
        sema = self._global_upgrade_sema
        if sema is not None:
            try:
                sema.release()
            except ValueError:
                pass  # over-release guard

    @contextmanager
    def global_upgrade_slot(
        self,
        op: str = "upgrade",
        owner: str = "default",
        job_id: str = "",
        on_queued: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_acquired: Optional[Callable[[float], None]] = None,
    ):
        handle = self.acquire_global_upgrade_slot(
            op=op, owner=owner, job_id=job_id, on_queued=on_queued,
        )
        if on_acquired and not handle.get("disabled"):
            try:
                on_acquired(handle.get("wait_s", 0.0))
            except Exception:
                pass
        try:
            yield handle
        finally:
            self.release_global_upgrade_slot(handle)

    # ------------------------------------------------------------------
    # Global push slot API (Wave 6.1)
    # ------------------------------------------------------------------
    def acquire_global_push_slot(
        self,
        op: str = "push",
        owner: str = "default",
        job_id: str = "",
        on_queued: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Block until a global push slot is available.

        Mirrors ``acquire_global_upgrade_slot`` but drains a separate pool
        so upgrades and pushes don't compete for the same 4 slots. Callers
        nest this OUTSIDE the per-device lock: grab the push slot first,
        then the device lock, so the slot stays reserved for the duration
        of the SSH session rather than being released at lock handoff.
        """
        sema = self._global_push_sema
        if sema is None:
            return {"disabled": True}
        waiter = {
            "op": op,
            "owner": owner,
            "job_id": job_id,
            "queued_at": time.time(),
        }
        with self._registry_lock:
            in_flight = len(self._global_push_in_flight)
            slot_full = in_flight >= self._global_push_max
            if slot_full:
                self._global_push_queued.append(waiter)
                queue_len = len(self._global_push_queued)
            else:
                queue_len = 0
        if slot_full and on_queued:
            try:
                on_queued({
                    "queue_len": queue_len,
                    "in_flight": in_flight,
                    "slots_max": self._global_push_max,
                    "pool": "push",
                })
            except Exception:
                pass
        wait_start = time.time()
        sema.acquire()
        wait_s = time.time() - wait_start
        started_at = time.time()
        handle = {
            "op": op,
            "owner": owner,
            "job_id": job_id,
            "started_at": started_at,
            "wait_s": wait_s,
        }
        with self._registry_lock:
            try:
                self._global_push_queued.remove(waiter)
            except ValueError:
                pass
            self._global_push_in_flight.append(handle)
            s = self._global_push_stats
            s["acquires"] += 1
            s["wait_time_total_s"] += wait_s
            if wait_s > s["max_wait_s"]:
                s["max_wait_s"] = wait_s
            if len(self._global_push_in_flight) > s["peak_in_flight"]:
                s["peak_in_flight"] = len(self._global_push_in_flight)
        return handle

    def release_global_push_slot(self, handle: Optional[Dict[str, Any]]) -> None:
        """Release a slot previously obtained from acquire_global_push_slot."""
        if handle is None or handle.get("disabled"):
            return
        with self._registry_lock:
            try:
                self._global_push_in_flight.remove(handle)
            except ValueError:
                pass
        sema = self._global_push_sema
        if sema is not None:
            try:
                sema.release()
            except ValueError:
                pass

    @contextmanager
    def global_push_slot(
        self,
        op: str = "push",
        owner: str = "default",
        job_id: str = "",
        on_queued: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_acquired: Optional[Callable[[float], None]] = None,
    ):
        handle = self.acquire_global_push_slot(
            op=op, owner=owner, job_id=job_id, on_queued=on_queued,
        )
        if on_acquired and not handle.get("disabled"):
            try:
                on_acquired(handle.get("wait_s", 0.0))
            except Exception:
                pass
        try:
            yield handle
        finally:
            self.release_global_push_slot(handle)

    # ------------------------------------------------------------------
    # Per-user push reservation (Wave 6.4)
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_owner(owner: Any) -> str:
        """Canonicalize ``owner`` for scheduler bookkeeping.

        Wave 7.2: funnel every owner string through ``routes._state.
        normalize_owner_lax`` so case/whitespace drift in ``request.state.
        user`` across middlewares cannot split a single user's counter
        into two buckets (or worse, leak a commit through under a
        different owner than the reservation).

        Safe to call with ``None``; falls back to ``"default"`` which
        preserves Wave 6 single-user semantics for unauthenticated mode.
        """
        try:
            from routes._state import normalize_owner_lax  # lazy to avoid cycle
            return normalize_owner_lax(owner)
        except Exception:
            # Fallback preserves Wave 6 behaviour exactly if ``_state``
            # is unavailable during bootstrap.
            s = str(owner or "").strip()
            return s if s else "default"

    def reserve_user_push(self, owner: str) -> None:
        """Increment the per-user push counter or raise ``PerUserLimitError``.

        Called by the HTTP layer BEFORE spawning the push worker so we can
        reject with 429 rather than silently queueing a thread that will
        later stall. Safe to call with an empty owner (treated as 'default').

        Counter is decremented via ``release_user_push`` when the job
        terminates (success, failure, or cancel).
        """
        owner = self._normalize_owner(owner)
        cap = self._per_user_push_max
        with self._registry_lock:
            current = self._per_user_push_counts.get(owner, 0)
            if cap > 0 and current >= cap:
                self._per_user_push_stats["rejections"] += 1
                raise PerUserLimitError(owner, current, cap)
            self._per_user_push_counts[owner] = current + 1
            peak = self._per_user_push_stats["peak_by_user"]
            if self._per_user_push_counts[owner] > peak.get(owner, 0):
                peak[owner] = self._per_user_push_counts[owner]

    def release_user_push(self, owner: str) -> None:
        """Decrement the per-user counter. Safe to call on an unknown owner."""
        owner = self._normalize_owner(owner)
        with self._registry_lock:
            current = self._per_user_push_counts.get(owner, 0)
            if current <= 1:
                self._per_user_push_counts.pop(owner, None)
            else:
                self._per_user_push_counts[owner] = current - 1

    def user_push_count(self, owner: str) -> int:
        """Return the current in-flight push count for ``owner``."""
        owner = self._normalize_owner(owner)
        with self._registry_lock:
            return self._per_user_push_counts.get(owner, 0)

    @contextmanager
    def user_push_reservation(self, owner: str):
        """Context-manager form: reserve on entry, release on exit.

        Raises ``PerUserLimitError`` on entry if the cap is hit.
        """
        owner = self._normalize_owner(owner)
        self.reserve_user_push(owner)
        try:
            yield
        finally:
            self.release_user_push(owner)

    # ------------------------------------------------------------------
    # Pre-queue rejection (Wave 6.5)
    # ------------------------------------------------------------------
    def check_device_queue_capacity(self, mgmt_ip: str) -> None:
        """Raise ``DeviceBusyError`` if the ``mgmt_ip`` queue is saturated.

        Non-blocking. Must be called BEFORE ``acquire()``. The HTTP layer
        uses this to fast-fail with 503 + Retry-After when >=
        ``_device_queue_max`` callers are already parked on the device.
        A ``_device_queue_max`` of 0 disables the check entirely.
        """
        if not mgmt_ip or self._device_queue_max <= 0:
            return
        with self._registry_lock:
            depth = len(self._waiters.get(mgmt_ip, []))
            if depth >= self._device_queue_max:
                self._device_queue_rejections += 1
                # Retry after ~= (depth * typical push duration 15s), capped.
                retry_s = max(30, min(300, depth * 15))
                raise DeviceBusyError(mgmt_ip, depth, retry_s)

    # ------------------------------------------------------------------
    # Observability helpers (used by Wave 4.2 /api/health/concurrency)
    # ------------------------------------------------------------------
    def current_holder(self, mgmt_ip: str) -> Optional[Dict[str, Any]]:
        """Return a copy of the current holder's metadata, or None."""
        with self._registry_lock:
            h = self._status.get(mgmt_ip)
            return dict(h) if h else None

    def queue_depth(self, mgmt_ip: str) -> int:
        """Number of waiters parked behind the current holder."""
        with self._registry_lock:
            return len(self._waiters.get(mgmt_ip, []))

    def snapshot(self) -> Dict[str, Any]:
        """Full scheduler state -- used by the health endpoint."""
        with self._registry_lock:
            busy = {ip: dict(s) for ip, s in self._status.items()}
            queued = {ip: [dict(w) for w in ws]
                      for ip, ws in self._waiters.items() if ws}
            stats = dict(self._stats)
            in_flight = [dict(h) for h in self._global_upgrade_in_flight]
            g_queued = [dict(w) for w in self._global_upgrade_queued]
            g_stats = dict(self._global_upgrade_stats)
            p_in_flight = [dict(h) for h in self._global_push_in_flight]
            p_queued = [dict(w) for w in self._global_push_queued]
            p_stats = dict(self._global_push_stats)
            per_user = dict(self._per_user_push_counts)
            per_user_stats = {
                "rejections": self._per_user_push_stats["rejections"],
                "peak_by_user": dict(self._per_user_push_stats["peak_by_user"]),
            }
            device_rejections = self._device_queue_rejections
        return {
            "busy": busy,
            "queued": queued,
            "devices_tracked": len(self._locks),
            "stats": stats,
            "global_upgrades": {
                "slots_max": self._global_upgrade_max,
                "in_flight": in_flight,
                "queued": g_queued,
                "stats": g_stats,
                "enabled": self._global_upgrade_sema is not None,
            },
            "global_pushes": {
                "slots_max": self._global_push_max,
                "in_flight": p_in_flight,
                "queued": p_queued,
                "stats": p_stats,
                "enabled": self._global_push_sema is not None,
            },
            "per_user_pushes": {
                "max_per_user": self._per_user_push_max,
                "in_flight_by_user": per_user,
                "stats": per_user_stats,
                "enabled": self._per_user_push_max > 0,
            },
            "device_queue": {
                "max_depth": self._device_queue_max,
                "rejections": device_rejections,
                "enabled": self._device_queue_max > 0,
            },
        }


# Module-level singleton. All routes share the same scheduler so a push
# from alice on PE-1 blocks an upgrade from bob on the same PE-1.
scheduler = DeviceOpScheduler()


__all__ = [
    "DeviceOpScheduler",
    "scheduler",
    "DeviceBusyError",
    "PerUserLimitError",
]
