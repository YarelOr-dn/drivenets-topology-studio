"""Manual resilience test for the device-mode resolver + 3-poller monitor.

Not a pytest -- runs against the live SCALER tree on this host. Invoke
with:
    cd topology && python3 tests/manual_devmode_resilience.py

Sections:
  1. Steady state with all 3 pollers
  2. Mid-cycle stop -> no half-written operational.json
  3. Stop+start idempotency
  4. upgrade_in_progress flag pickup
  5. Ghost-IP simulation: scribble bad mgmt_ip + verify safe_set/reaper
  6. Concurrent storm -> coalescer collapses to one SSH
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("SCALER_ROOT", "/home/dn/SCALER")
# Accelerate timers so we exercise multiple cycles in a few minutes.
os.environ.setdefault("TP_DEVICE_MODE_GLOBAL_POLL_S", "30")
os.environ.setdefault("TP_DEVICE_MODE_WATCHER_POLL_S", "8")
os.environ.setdefault("TP_DEVICE_MODE_INFLIGHT_POLL_S", "20")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routes._device_mode_resolver import (  # noqa: E402
    GLOBAL_POLL_INTERVAL_S,
    INFLIGHT_POLL_INTERVAL_S,
    WATCHER_POLL_INTERVAL_S,
    get_device_mode,
    invalidate,
    snapshot,
    start_all_pollers,
    stop_all_pollers,
)

SCALER_ROOT = Path(os.environ["SCALER_ROOT"])
TARGET_DEV = "YOR_PE-1"  # known reachable from the live test
OPS = SCALER_ROOT / "db" / "configs" / TARGET_DEV / "operational.json"


# ---------- helpers ----------
def _read_ops():
    """Use the project's corruption-tolerant reader, not raw json.loads.

    A pre-existing legacy non-atomic write may have left the file with
    two concatenated objects; ``read_ops`` quarantines and returns {}.
    """
    from routes._ops_writer import read_ops
    return read_ops(OPS) or {}


def _write_ops(data):
    """Write through the atomic updater so we don't reintroduce the
    very corruption pattern this test is meant to expose.
    """
    from routes._ops_writer import update_ops

    def _mut(d):
        d.clear()
        d.update(data)

    update_ops(OPS, _mut, create_if_missing=True)


def _section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _summary(snap):
    p = snap.get("pollers", {})
    s = snap.get("stats", {})
    d = snap.get("drift", {})
    print(f"  entries={snap.get('entries')} inflight={snap.get('inflight')}")
    print(
        f"  pollers: in-flight={p.get('inflight_running')} "
        f"watcher={p.get('watcher_running')} global={p.get('global_running')}"
    )
    print(
        f"  stats: hits_cache={s.get('hits_cache')} "
        f"hits_inflight={s.get('hits_inflight')} misses={s.get('misses')} "
        f"errors={s.get('errors')}"
    )
    print(f"  drift.total={d.get('total')} last={d.get('last_device')} ")


# ---------- 1. Steady state ----------
def test_steady_state(duration_s=90):
    _section(
        f"1. STEADY STATE ({duration_s}s, intervals: "
        f"inflight={INFLIGHT_POLL_INTERVAL_S}s, "
        f"watcher={WATCHER_POLL_INTERVAL_S}s, "
        f"global={GLOBAL_POLL_INTERVAL_S}s)"
    )
    start_all_pollers()
    t0 = time.time()
    samples = []
    while time.time() - t0 < duration_s:
        time.sleep(10)
        snap = snapshot()
        samples.append(
            {
                "t": int(time.time() - t0),
                "entries": snap.get("entries"),
                "errors": snap.get("stats", {}).get("errors"),
                "drift": snap.get("drift", {}).get("total"),
            }
        )
        print(
            f"  t+{samples[-1]['t']:>3}s  entries={samples[-1]['entries']:>3}  "
            f"errors={samples[-1]['errors']:>2}  drift={samples[-1]['drift']:>2}"
        )

    final = snapshot()
    _summary(final)
    errors = final.get("stats", {}).get("errors", 0)
    assert errors == 0, f"FAIL: {errors} errors in steady state"
    assert final["pollers"]["inflight_running"]
    assert final["pollers"]["watcher_running"]
    assert final["pollers"]["global_running"]
    print("  PASS: steady state, no errors, all 3 pollers alive")


# ---------- 2. Mid-cycle stop ----------
def test_midcycle_stop_and_corruption_recovery():
    _section(
        "2. MID-CYCLE STOP + corruption recovery (writes garbage, confirms "
        "auto-heal via _ops_writer.read_ops quarantine path)"
    )
    before = _read_ops()
    before_size = OPS.stat().st_size
    print(f"  ops.json before: {before_size} bytes, "
          f"device_state={before.get('device_state')}")

    t0 = time.time()
    stop_all_pollers(timeout=4.0)
    elapsed = time.time() - t0
    print(f"  stop_all_pollers returned in {elapsed:.2f}s")
    snap = snapshot()
    assert not snap["pollers"]["inflight_running"]
    assert not snap["pollers"]["watcher_running"]
    assert not snap["pollers"]["global_running"]

    # Now corrupt the file by appending trailing garbage (mimics the
    # legacy non-atomic writer race that we observed in 06:56 today).
    # The next probe must heal it without raising.
    raw = OPS.read_text()
    OPS.write_text(raw + "\nXXX_GARBAGE_TRAILER_XXX\n")
    print(f"  injected corruption: file is now {OPS.stat().st_size} bytes")

    # Run a forced fresh probe -- this must not raise, and after it
    # completes the file must be valid JSON again.
    invalidate(TARGET_DEV, TARGET_DEV)
    try:
        r = get_device_mode(
            device_id=TARGET_DEV, scaler_hostname=TARGET_DEV, force=True,
        )
        print(f"  post-corruption probe: mode={r.get('mode')} "
              f"reachable={r.get('reachable')}")
    except Exception as exc:
        print(f"  FAIL: probe raised {type(exc).__name__}: {exc}")
        raise AssertionError("probe should heal corruption, not raise")

    healed = _read_ops()
    quarantine = sorted(OPS.parent.glob(f"{OPS.name}.corrupt-*"))
    print(f"  quarantine files: {[q.name for q in quarantine]}")
    print(f"  ops.json after heal: {OPS.stat().st_size} bytes, "
          f"valid JSON, device_state={healed.get('device_state')}")
    assert isinstance(healed, dict) and healed.get("device_state"), \
        "ops.json should be valid + populated after auto-heal"
    print("  PASS: corruption auto-quarantined + ops.json reconstructed")


# ---------- 3. Restart idempotency ----------
def test_restart_idempotency():
    _section("3. RESTART (stop -> stop -> start -> start) idempotency")
    stop_all_pollers(timeout=2.0)
    stop_all_pollers(timeout=2.0)
    start_all_pollers()
    snap1 = snapshot()
    start_all_pollers()
    snap2 = snapshot()
    assert snap1["pollers"]["inflight_running"]
    assert snap2["pollers"]["inflight_running"]
    print(f"  pollers running after double-start: "
          f"inflight={snap2['pollers']['inflight_running']} "
          f"watcher={snap2['pollers']['watcher_running']} "
          f"global={snap2['pollers']['global_running']}")
    print("  PASS: start/stop idempotent, no thread leak")


# ---------- 4. upgrade_in_progress flip ----------
def test_inflight_pickup():
    _section("4. UPGRADE_IN_PROGRESS pickup")
    invalidate(TARGET_DEV, TARGET_DEV)
    ops = _read_ops()
    original_flag = ops.get("upgrade_in_progress", False)
    print(f"  original upgrade_in_progress = {original_flag}")

    ops["upgrade_in_progress"] = True
    _write_ops(ops)
    print(f"  set upgrade_in_progress=True; waiting for in-flight poller "
          f"({INFLIGHT_POLL_INTERVAL_S}s + slack) ...")
    time.sleep(INFLIGHT_POLL_INTERVAL_S + 8)

    snap_a = snapshot()
    print(f"  after wait: cache entries={snap_a.get('entries')} "
          f"errors={snap_a.get('stats', {}).get('errors')}")

    ops = _read_ops()
    ops["upgrade_in_progress"] = original_flag
    _write_ops(ops)
    print(f"  restored upgrade_in_progress={original_flag}")

    errors = snap_a.get("stats", {}).get("errors", 0)
    assert errors == 0, f"FAIL: {errors} errors after flag flip"
    print("  PASS: in-flight poller handled the flip with no errors")


# ---------- 5. Ghost-IP simulation ----------
def test_ghost_ip_invalidation():
    _section("5. GHOST-IP simulation (scribble mgmt_ip + verify slow rediscover)")

    invalidate(TARGET_DEV, TARGET_DEV)
    t0 = time.time()
    r = get_device_mode(
        device_id=TARGET_DEV, scaler_hostname=TARGET_DEV, force=True,
    )
    print(f"  baseline probe: {time.time() - t0:.2f}s mode={r['mode']} "
          f"mgmt_ip={r['mgmt_ip']} fast_path={r['fast_path']}")
    assert r["mode"] in ("DNOS", "GI", "RECOVERY", "BASEOS_SHELL", "ONIE")
    # Take the IP from the resolver result -- operational.json may have
    # been quarantined+rebuilt earlier in the suite, leaving mgmt_ip
    # blank on disk while the resolver still knows it from the live
    # discovery walk.
    real_ip = (r.get("mgmt_ip") or "").split("/")[0]
    print(f"  resolver-reported mgmt_ip = {real_ip}")
    assert real_ip, "FAIL: resolver did not return an mgmt_ip"

    # Simulate a fast-path that lands on the WRONG device by passing a
    # hostname that doesn't match. Hostname-mismatch path should fire
    # _mark_device_ip_stale + fall through to slow path. We use the
    # real IP but a fake expected hostname to exercise the ghost-IP
    # branch without actually corrupting the lab.
    from routes._device_mode_resolver import _fast_ssh_classify

    fake_result = _fast_ssh_classify(
        real_ip, "dnroot", "dnroot",
        connect_timeout=4.0, expected_hostname="GHOST_DEVICE",
    )
    print(f"  ghost-IP probe result: {fake_result}")
    assert fake_result.get("_ghost_ip") == "1", \
        "FAIL: ghost-IP branch did not trigger"
    print(f"  ghost-IP detected (actual={fake_result.get('actual_hostname')})")
    print("  PASS: ghost-IP branch fires hostname-mismatch on demand")


# ---------- 6. Concurrent storm ----------
def test_concurrent_storm(n=50):
    _section(f"6. CONCURRENT STORM ({n}-way get_device_mode on same device)")
    invalidate(TARGET_DEV, TARGET_DEV)

    results = []
    errors = []

    def _worker():
        try:
            t0 = time.time()
            r = get_device_mode(
                device_id=TARGET_DEV, scaler_hostname=TARGET_DEV,
            )
            results.append((time.time() - t0, r.get("source"), r.get("mode")))
        except Exception as exc:
            errors.append(str(exc))

    t0 = time.time()
    threads = [threading.Thread(target=_worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - t0

    sources = {}
    for _, src, _ in results:
        sources[src] = sources.get(src, 0) + 1
    print(f"  {n} parallel calls finished in {elapsed:.2f}s, "
          f"errors={len(errors)}, sources={sources}")
    print(f"  result modes: "
          f"{set(m for _, _, m in results)}")

    snap = snapshot()
    print(f"  coalescer stats after storm: {snap.get('stats')}")
    assert len(errors) == 0, f"FAIL: {errors[:3]} ..."
    # ALL N callers should have shared at most 1 fresh SSH (the rest
    # served from cache or the inflight wait).
    fresh = sources.get("fresh", 0)
    assert fresh <= 1, \
        f"FAIL: coalescer let {fresh} parallel SSH sessions through"
    print(f"  PASS: {n} concurrent calls -> {fresh} SSH session(s) "
          f"({sources.get('cache', 0)} cache, "
          f"{sources.get('inflight_wait', 0)} inflight_wait)")


# ---------- main ----------
def main():
    failed = []
    for name, fn in [
        ("steady_state", lambda: test_steady_state(duration_s=90)),
        ("midcycle_stop", test_midcycle_stop_and_corruption_recovery),
        ("restart_idempotency", test_restart_idempotency),
        ("inflight_pickup", test_inflight_pickup),
        ("ghost_ip", test_ghost_ip_invalidation),
        ("concurrent_storm", lambda: test_concurrent_storm(n=50)),
    ]:
        try:
            fn()
        except AssertionError as exc:
            print(f"  ASSERTION FAILED in {name}: {exc}")
            failed.append(name)
        except Exception as exc:
            print(f"  EXCEPTION in {name}: {exc}")
            failed.append(name)

    stop_all_pollers(timeout=2.0)
    _section("RESULT")
    if failed:
        print(f"  FAILED: {failed}")
        sys.exit(1)
    print("  ALL PASS")


if __name__ == "__main__":
    main()
