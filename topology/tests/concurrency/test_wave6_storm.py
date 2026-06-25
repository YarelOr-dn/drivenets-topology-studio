"""Wave 6: 100-user storm smoke test.

Validates that the Wave 6 hardening (global push slot cap, bounded push
executor, SSH pool enlargement, per-user cap, pre-queue rejection, and
observability) actually prevents the pathologies the bare waves 2-5
stack would exhibit at 100 concurrent users:

* Thread explosion: with plain ``Thread(..., daemon=True).start()`` per
  push, 100 users issuing 3 pushes each = 300 OS threads. Wave 6.2 caps
  this at ``TP_PUSH_EXECUTOR_SIZE`` (default 50).

* Silent infinite queueing: with 100 users all pushing to one device,
  the 100th waiter would sit in the scheduler queue for 25+ minutes.
  Wave 6.5 rejects at queue depth >= ``TP_DEVICE_QUEUE_MAX`` with a 503
  + Retry-After.

* Network / CPU saturation: with no cap on simultaneous SSH+commit,
  100 concurrent sessions flood the lab. Wave 6.1 caps this at
  ``TP_GLOBAL_PUSH_SLOTS`` (default 20).

* One user monopolizing the pool: a misbehaving user or client loop
  could submit 100 pushes and starve others. Wave 6.4 caps per-user at
  ``TP_PER_USER_PUSH_MAX`` (default 5).

Scenario A (baseline): 100 users, each pushing to a UNIQUE device.
  Expectations:
  - All 100 admitted (no 429, no 503)
  - At any instant, <= TP_GLOBAL_PUSH_SLOTS in the SSH/commit section
  - p99 end-to-end wait acceptable given the slot cap

Scenario B (per-user cap): 1 user issues ``per_user_max + 3`` pushes.
  Expectations:
  - First ``per_user_max`` admitted, next 3 rejected with PerUserLimitError

Scenario C (device queue cap): 100 users all target the SAME device.
  Expectations:
  - Exactly 1 runs + TP_DEVICE_QUEUE_MAX queued = admitted
  - The rest rejected with DeviceBusyError (503 semantics)

Scenario D (observability): after the storm, ``scheduler.snapshot()``
  and ``pool_stats()`` return coherent counts matching our tracking.
"""
from __future__ import annotations

import os
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# Configure Wave 6 envs BEFORE importing the scheduler so the module-
# level constants pick them up.
os.environ["TP_GLOBAL_PUSH_SLOTS"] = "20"
os.environ["TP_PER_USER_PUSH_MAX"] = "5"
os.environ["TP_DEVICE_QUEUE_MAX"] = "10"
os.environ["TP_PUSH_EXECUTOR_SIZE"] = "50"
os.environ["TP_UPGRADE_EXECUTOR_SIZE"] = "10"
os.environ["TP_SSH_POOL_MAX"] = "200"

sys.path.insert(0, "/home/dn/drivenets-topology-studio/topology")

from routes._device_scheduler import (  # noqa: E402
    DeviceOpScheduler,
    DeviceBusyError,
    PerUserLimitError,
)
from routes._worker_pool import pool_stats, reset_for_tests, submit_push  # noqa: E402
from routes.bridge_helpers import SSHConnectionPool  # noqa: E402


# Realistic but fast: each simulated push takes ~120-180ms so 100 jobs
# run in ~5-10 wall seconds while still exercising contention paths.
PUSH_SIM_S = 0.15


class _Tracker:
    """Live invariant tracker + event log."""

    def __init__(self, global_slot_cap: int) -> None:
        self.global_slot_cap = global_slot_cap
        self.lock = threading.Lock()
        # per-device count of active critical sections (must be <= 1)
        self.active_per_device: Dict[str, int] = {}
        # number of slots currently held
        self.slots_held = 0
        # count of each (user, outcome)
        self.outcomes: Dict[str, int] = {"ok": 0, "rate_limited": 0,
                                         "queue_full": 0, "error": 0}
        self.violations: List[str] = []
        self.wait_samples: List[float] = []
        self.end_to_end_samples: List[float] = []
        # track per-user active counts to cross-check PerUserLimitError
        self.active_per_user: Dict[str, int] = {}
        self.peak_per_user: Dict[str, int] = {}

    def enter_slot(self) -> None:
        with self.lock:
            self.slots_held += 1
            if self.slots_held > self.global_slot_cap:
                self.violations.append(
                    f"global_slot: {self.slots_held} > cap {self.global_slot_cap}"
                )

    def exit_slot(self) -> None:
        with self.lock:
            self.slots_held -= 1

    def enter_device(self, mgmt_ip: str) -> None:
        with self.lock:
            self.active_per_device[mgmt_ip] = \
                self.active_per_device.get(mgmt_ip, 0) + 1
            if self.active_per_device[mgmt_ip] > 1:
                self.violations.append(
                    f"device_mutex: {mgmt_ip} has "
                    f"{self.active_per_device[mgmt_ip]} concurrent holders"
                )

    def exit_device(self, mgmt_ip: str) -> None:
        with self.lock:
            self.active_per_device[mgmt_ip] -= 1
            if self.active_per_device[mgmt_ip] == 0:
                self.active_per_device.pop(mgmt_ip, None)

    def enter_user(self, owner: str) -> None:
        with self.lock:
            self.active_per_user[owner] = self.active_per_user.get(owner, 0) + 1
            cur = self.active_per_user[owner]
            if cur > self.peak_per_user.get(owner, 0):
                self.peak_per_user[owner] = cur

    def exit_user(self, owner: str) -> None:
        with self.lock:
            self.active_per_user[owner] -= 1
            if self.active_per_user[owner] == 0:
                self.active_per_user.pop(owner, None)

    def record(self, outcome: str, wait_s: float = 0.0,
               end_to_end_s: float = 0.0) -> None:
        with self.lock:
            self.outcomes[outcome] = self.outcomes.get(outcome, 0) + 1
            if end_to_end_s > 0:
                self.end_to_end_samples.append(end_to_end_s)
            if wait_s > 0:
                self.wait_samples.append(wait_s)


def _simulated_push_job(
    owner: str,
    mgmt_ip: str,
    scheduler: DeviceOpScheduler,
    tracker: _Tracker,
) -> str:
    """Mirrors the real routes/operations.py push flow minus SSH."""
    t0 = time.time()
    try:
        scheduler.check_device_queue_capacity(mgmt_ip)
    except DeviceBusyError:
        tracker.record("queue_full")
        return "queue_full"
    try:
        scheduler.reserve_user_push(owner)
    except PerUserLimitError:
        tracker.record("rate_limited")
        return "rate_limited"
    tracker.enter_user(owner)
    push_slot = None
    dev_token = None
    try:
        push_slot = scheduler.acquire_global_push_slot(
            op="push", owner=owner, job_id=f"{owner}:{mgmt_ip}:{t0}",
        )
        tracker.enter_slot()
        try:
            dev_token = scheduler.acquire(
                mgmt_ip, "push", owner, f"{owner}:{mgmt_ip}:{t0}",
            )
            tracker.enter_device(mgmt_ip)
            try:
                time.sleep(PUSH_SIM_S)  # simulate SSH + commit
            finally:
                tracker.exit_device(mgmt_ip)
                scheduler.release(dev_token)
                dev_token = None
        finally:
            tracker.exit_slot()
            scheduler.release_global_push_slot(push_slot)
            push_slot = None
        wait_s = (push_slot.get("wait_s", 0.0) if push_slot else 0.0) + \
                 (dev_token.wait_s if dev_token else 0.0)
        tracker.record("ok", wait_s=wait_s, end_to_end_s=time.time() - t0)
        return "ok"
    except Exception as exc:
        tracker.record("error")
        return f"error: {exc}"
    finally:
        scheduler.release_user_push(owner)
        tracker.exit_user(owner)
        # Safety nets
        if dev_token is not None:
            scheduler.release(dev_token)
        if push_slot is not None:
            scheduler.release_global_push_slot(push_slot)


def _run_scenario_a(scheduler: DeviceOpScheduler) -> Tuple[_Tracker, float]:
    """100 users, each pushing to a UNIQUE device.

    Validates the global slot cap + executor boundedness without
    triggering the per-user or device-queue rejection paths.
    """
    tracker = _Tracker(global_slot_cap=20)
    users = [f"user{i:03d}" for i in range(100)]
    devices = [f"10.1.{i // 256}.{i % 256}" for i in range(100)]
    pairs = list(zip(users, devices))

    start = time.time()
    with ThreadPoolExecutor(max_workers=100, thread_name_prefix="storm-a") as ex:
        futures = [
            ex.submit(_simulated_push_job, u, d, scheduler, tracker)
            for (u, d) in pairs
        ]
        for f in as_completed(futures):
            f.result()
    elapsed = time.time() - start
    return tracker, elapsed


def _run_scenario_b(scheduler: DeviceOpScheduler) -> _Tracker:
    """1 user x (per_user_max + 3) pushes to different devices.

    Expects exactly 3 rate-limited rejections.
    """
    tracker = _Tracker(global_slot_cap=20)
    per_user = scheduler._per_user_push_max
    attempts = per_user + 3
    owner = "heavy_user"
    devices = [f"10.2.0.{i}" for i in range(attempts)]

    with ThreadPoolExecutor(max_workers=attempts,
                            thread_name_prefix="storm-b") as ex:
        futures = [
            ex.submit(_simulated_push_job, owner, d, scheduler, tracker)
            for d in devices
        ]
        for f in as_completed(futures):
            f.result()
    return tracker


def _run_scenario_c(scheduler: DeviceOpScheduler) -> _Tracker:
    """100 users all target the SAME device.

    Expects 1 running + TP_DEVICE_QUEUE_MAX queued admitted; rest rejected.
    """
    tracker = _Tracker(global_slot_cap=20)
    dev_max = scheduler._device_queue_max
    users = [f"flood_user{i:03d}" for i in range(100)]
    mgmt_ip = "10.3.0.1"

    with ThreadPoolExecutor(max_workers=100,
                            thread_name_prefix="storm-c") as ex:
        futures = [
            ex.submit(_simulated_push_job, u, mgmt_ip, scheduler, tracker)
            for u in users
        ]
        for f in as_completed(futures):
            f.result()
    return tracker, dev_max


def _run_scenario_d_executor(scheduler: DeviceOpScheduler) -> Tuple[int, int]:
    """Submit more jobs than the executor size can run simultaneously.

    Verifies the bounded thread pool (Wave 6.2) does NOT spawn 100 fresh
    OS threads; it reuses its configured workers.
    """
    reset_for_tests()
    n = 100
    done = threading.Event()
    counter = {"ran": 0}
    counter_lock = threading.Lock()
    barrier = threading.Event()

    def _worker():
        # Hold briefly so executor has to juggle workers
        time.sleep(0.02)
        with counter_lock:
            counter["ran"] += 1
            if counter["ran"] >= n:
                done.set()

    for _ in range(n):
        submit_push(_worker)
    assert done.wait(timeout=30), "not all pool jobs completed"
    stats = pool_stats()
    max_workers = stats["push"]["size_max"]
    threads_alive = stats["push"]["threads_alive"]
    return max_workers, threads_alive


def main() -> int:
    print("=" * 70)
    print("Wave 6: 100-user concurrency storm smoke test")
    print("=" * 70)

    # Verify env defaults plumbed correctly
    scheduler = DeviceOpScheduler()
    print(f"  TP_GLOBAL_PUSH_SLOTS    = {scheduler._global_push_max}")
    print(f"  TP_PER_USER_PUSH_MAX    = {scheduler._per_user_push_max}")
    print(f"  TP_DEVICE_QUEUE_MAX     = {scheduler._device_queue_max}")
    print(f"  TP_PUSH_EXECUTOR_SIZE   = (read in pool_stats below)")
    print(f"  TP_SSH_POOL_MAX         = {SSHConnectionPool()._max_connections}")
    print()
    assert scheduler._global_push_max == 20
    assert scheduler._per_user_push_max == 5
    assert scheduler._device_queue_max == 10
    assert SSHConnectionPool()._max_connections == 200

    failures: List[str] = []

    # ---- Scenario A: 100 unique devices ----
    print("[Scenario A] 100 users, 100 unique devices (global-slot stress)")
    t0 = time.time()
    tracker_a, elapsed_a = _run_scenario_a(scheduler)
    print(f"  elapsed: {elapsed_a:.2f}s")
    print(f"  outcomes: {tracker_a.outcomes}")
    if tracker_a.end_to_end_samples:
        p50 = statistics.median(tracker_a.end_to_end_samples)
        p99 = sorted(tracker_a.end_to_end_samples)[
            max(0, int(0.99 * len(tracker_a.end_to_end_samples)) - 1)
        ]
        print(f"  end-to-end p50: {p50*1000:.0f}ms  p99: {p99*1000:.0f}ms")
        # At 20 slots, 100 jobs at 150ms each = ~750ms steady-state
        # throughput; p99 should be under 3s generously.
        if p99 > 3.0:
            failures.append(f"scenario_a: p99 {p99:.2f}s > 3.0s budget")
    if tracker_a.violations:
        failures.append(f"scenario_a: invariant violations: {tracker_a.violations[:3]}")
    if tracker_a.outcomes.get("ok", 0) != 100:
        failures.append(f"scenario_a: expected 100 ok, got {tracker_a.outcomes}")
    print()

    # ---- Scenario B: per-user cap ----
    print("[Scenario B] 1 user, per_user_max + 3 pushes (rate-limit stress)")
    tracker_b = _run_scenario_b(scheduler)
    print(f"  outcomes: {tracker_b.outcomes}")
    rl = tracker_b.outcomes.get("rate_limited", 0)
    ok = tracker_b.outcomes.get("ok", 0)
    if rl != 3:
        failures.append(f"scenario_b: expected 3 rate_limited, got {rl}")
    if ok != scheduler._per_user_push_max:
        failures.append(f"scenario_b: expected {scheduler._per_user_push_max} ok, got {ok}")
    peak = tracker_b.peak_per_user.get("heavy_user", 0)
    print(f"  peak concurrent for heavy_user: {peak} (cap {scheduler._per_user_push_max})")
    if peak > scheduler._per_user_push_max:
        failures.append(f"scenario_b: peak {peak} > cap {scheduler._per_user_push_max}")
    print()

    # ---- Scenario C: device queue cap ----
    print("[Scenario C] 100 users -> 1 device (queue-depth stress)")
    tracker_c, dev_max = _run_scenario_c(scheduler)
    print(f"  outcomes: {tracker_c.outcomes}")
    ok_c = tracker_c.outcomes.get("ok", 0)
    qf = tracker_c.outcomes.get("queue_full", 0)
    # At least the first (dev_max + 1) should succeed (1 running + N queued);
    # the rest should see 503-equivalent.
    # Race: queue fills fast but some requests slot in before check_device_queue_capacity
    # raises. Tolerate +/- 3 around the boundary.
    expected_ok_min = dev_max + 1
    if ok_c < expected_ok_min - 3:
        failures.append(
            f"scenario_c: expected at least ~{expected_ok_min} ok, got {ok_c}"
        )
    if qf < 90 - dev_max - 3:
        failures.append(
            f"scenario_c: expected many queue_full, got only {qf}"
        )
    if tracker_c.violations:
        failures.append(f"scenario_c: invariant violations: {tracker_c.violations[:3]}")
    print()

    # ---- Scenario D: bounded executor ----
    print("[Scenario D] 100 jobs submitted to push executor (thread-cap stress)")
    max_w, alive = _run_scenario_d_executor(scheduler)
    print(f"  executor max_workers: {max_w}  threads alive: {alive}")
    if alive > max_w:
        failures.append(f"scenario_d: threads {alive} > max_workers {max_w}")
    if max_w > 50:
        failures.append(f"scenario_d: max_workers {max_w} > configured 50")
    print()

    # ---- Scenario E: observability coherence ----
    print("[Scenario E] scheduler + pool observability snapshot")
    snap = scheduler.snapshot()
    expected_top_keys = {"busy", "queued", "global_upgrades", "global_pushes",
                         "per_user_pushes", "device_queue", "stats"}
    missing = expected_top_keys - set(snap.keys())
    if missing:
        failures.append(f"scenario_e: snapshot missing keys {missing}")
    gp = snap.get("global_pushes", {})
    if gp.get("slots_max") != 20:
        failures.append(f"scenario_e: global_pushes.slots_max != 20")
    pu = snap.get("per_user_pushes", {})
    if pu.get("max_per_user") != 5:
        failures.append(f"scenario_e: per_user_pushes.max_per_user != 5")
    dq = snap.get("device_queue", {})
    if dq.get("max_depth") != 10:
        failures.append(f"scenario_e: device_queue.max_depth != 10")
    rej = dq.get("rejections", 0)
    print(f"  device_queue rejections recorded: {rej}")
    if rej < 50:  # at least scenario C's rejections should show up
        failures.append(f"scenario_e: rejection counter low ({rej})")
    print(f"  global_pushes.peak_in_flight: {gp.get('stats',{}).get('peak_in_flight')}")
    ps = pool_stats()
    print(f"  pool_stats: {ps}")
    print()

    # ---- Summary ----
    print("=" * 70)
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        print("=" * 70)
        return 1
    print("ALL WAVE 6 INVARIANTS HELD")
    print(f"  scenario A: 100 jobs in {elapsed_a:.2f}s with {scheduler._global_push_max}-slot cap")
    print(f"  scenario B: per-user cap triggered 3x as expected")
    print(f"  scenario C: device queue cap rejected ~{tracker_c.outcomes.get('queue_full')} jobs")
    print(f"  scenario D: bounded executor held {max_w} workers (not 100)")
    print(f"  scenario E: observability exposes all 4 new Wave 6 primitives")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
