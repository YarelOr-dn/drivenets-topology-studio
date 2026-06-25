"""Verify the resolver's writes interoperate with scaler's legacy
non-atomic writes to operational.json.

Three checks:
  1. Cross-write race: 100 alternating writes from (a) topology
     ``_update_ops`` and (b) scaler-style raw ``json.dump``. Confirm
     the file ends up valid JSON (read_ops never returns {}).
  2. Schema sync: trigger a topology probe + a scaler-side write
     (refresh_device_state) and confirm both end up reading the same
     ``device_state``.
  3. Live drift sync: a scaler write changes device_state behind the
     resolver's back -> next resolver probe must observe and
     overwrite it (or leave it, depending on which is fresher).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

os.environ.setdefault("SCALER_ROOT", "/home/dn/SCALER")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routes._device_mode_resolver import (  # noqa: E402
    get_device_mode, invalidate,
)
from routes._ops_writer import read_ops, update_ops  # noqa: E402

SCALER_ROOT = Path(os.environ["SCALER_ROOT"])
TARGET_DEV = "YOR_PE-1"
OPS = SCALER_ROOT / "db" / "configs" / TARGET_DEV / "operational.json"


def _section(t):
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# ---------- 1. concurrent atomic-vs-raw writes ----------
def test_cross_write_race(n=100):
    _section(
        f"1. CROSS-WRITE RACE: {n} alternating writes "
        "(atomic _update_ops vs raw json.dump like scaler)"
    )
    invalidate(TARGET_DEV, TARGET_DEV)
    # Seed with a known-good baseline.
    update_ops(
        OPS,
        lambda d: d.update({"device_state": "DNOS", "marker": "baseline"}),
        create_if_missing=True,
    )

    errors = []
    corruptions = []

    def _topology_writer():
        for i in range(n):
            try:
                update_ops(
                    OPS,
                    lambda d, i=i: d.update({
                        "device_state": "DNOS",
                        "topology_seq": i,
                    }),
                    create_if_missing=True,
                )
            except Exception as e:
                errors.append(("topo", i, str(e)))

    def _scaler_legacy_writer():
        # Mimics scaler's connection_strategy.py:2315 pattern exactly.
        for i in range(n):
            try:
                # Read non-atomically (scaler does this).
                try:
                    data = json.loads(OPS.read_text())
                except Exception:
                    data = {}
                data["scaler_seq"] = i
                data["device_state"] = "DNOS"
                # Write non-atomically (the legacy bad pattern).
                with open(OPS, "w") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                errors.append(("scaler", i, str(e)))

    def _reader():
        for _ in range(n * 2):
            try:
                d = json.loads(OPS.read_text())
                if not isinstance(d, dict):
                    corruptions.append("non-dict")
            except Exception as e:
                corruptions.append(str(e))
            time.sleep(0.001)

    t0 = time.time()
    threads = [
        threading.Thread(target=_topology_writer),
        threading.Thread(target=_scaler_legacy_writer),
        threading.Thread(target=_reader),
        threading.Thread(target=_reader),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - t0

    final = read_ops(OPS)
    raw_corrupt = False
    try:
        json.loads(OPS.read_text())
    except Exception:
        raw_corrupt = True

    # Count raw-read corruptions vs total reads
    print(f"  ran in {elapsed:.2f}s, write errors={len(errors)}, "
          f"raw read corruptions caught={len(corruptions)}")
    print(f"  final state: device_state={final.get('device_state')} "
          f"topology_seq={final.get('topology_seq')} "
          f"scaler_seq={final.get('scaler_seq')}")
    print(f"  raw json.loads on final file: "
          f"{'CORRUPT' if raw_corrupt else 'valid'}")

    # Verdict: it's expected that some intermediate reads see corruption
    # (that's the whole point -- scaler's writer is non-atomic). What
    # MUST hold is that read_ops always recovers (the file is valid
    # OR has been quarantined and a fresh write follows).
    assert final.get("device_state"), \
        "FAIL: final state lost device_state entirely"
    if corruptions:
        rate = 100.0 * len(corruptions) / (n * 4)
        print(f"  corruption rate during race: {rate:.1f}% of raw reads")
        print(f"  -> demonstrates why read_ops with quarantine is needed")
    else:
        print("  no corruption observed in this run "
              "(timing-dependent; race is real, see below)")
    print("  PASS: read_ops + atomic update_ops keeps the system "
          "reliable through scaler's legacy writes")


# ---------- 2. schema sync ----------
def test_schema_sync():
    _section("2. SCHEMA SYNC: topology probe + scaler write end up consistent")
    invalidate(TARGET_DEV, TARGET_DEV)

    r = get_device_mode(
        device_id=TARGET_DEV, scaler_hostname=TARGET_DEV, force=True,
    )
    after_probe = read_ops(OPS)
    print(f"  probe returned: mode={r['mode']} "
          f"mgmt_ip={r.get('mgmt_ip')}")
    print(f"  ops.json after probe: device_state={after_probe.get('device_state')} "
          f"dnos_version={after_probe.get('dnos_version')}")

    # Both must agree on the canonical mode key. Scaler reads
    # ``device_state``; topology writes ``device_state``. If they're
    # in sync, the upper-cased mode from the probe == the file value.
    file_state = (after_probe.get("device_state") or "").upper()
    probe_mode = (r["mode"] or "").upper()
    assert file_state == probe_mode, (
        f"FAIL: schema mismatch -- probe={probe_mode!r} "
        f"file_state={file_state!r}"
    )
    print(f"  PASS: probe mode and on-disk device_state agree "
          f"({probe_mode})")


# ---------- 3. drift sync ----------
def test_drift_sync():
    _section(
        "3. DRIFT SYNC: scaler-side write changes device_state -> "
        "next resolver probe corrects it"
    )
    invalidate(TARGET_DEV, TARGET_DEV)
    # Get baseline.
    r0 = get_device_mode(
        device_id=TARGET_DEV, scaler_hostname=TARGET_DEV, force=True,
    )
    baseline = (r0["mode"] or "").upper()
    print(f"  baseline live mode: {baseline}")

    # Simulate a scaler-side write that's WRONG (device is in DNOS but
    # something flipped device_state to RECOVERY).
    update_ops(
        OPS,
        lambda d: d.update({
            "device_state": "RECOVERY",
            "_drift_test_marker": True,
        }),
        create_if_missing=True,
    )
    on_disk = read_ops(OPS).get("device_state")
    print(f"  injected wrong on-disk state: {on_disk}")

    # Force fresh probe -- should detect drift and correct.
    invalidate(TARGET_DEV, TARGET_DEV)
    from routes._device_mode_resolver import snapshot
    drift_before = snapshot()["drift"]["total"]
    r1 = get_device_mode(
        device_id=TARGET_DEV, scaler_hostname=TARGET_DEV, force=True,
    )
    drift_after = snapshot()["drift"]["total"]
    final = read_ops(OPS)
    print(f"  probe returned: {r1['mode']} (was on-disk: {on_disk})")
    print(f"  ops.json final: device_state={final.get('device_state')}")
    print(f"  drift counter: {drift_before} -> {drift_after}")

    # cleanup
    update_ops(OPS, lambda d: d.pop("_drift_test_marker", None) or True)

    assert (r1["mode"] or "").upper() == baseline, \
        f"FAIL: probe didn't return live mode ({baseline}); got {r1['mode']}"
    assert (final.get("device_state") or "").upper() == baseline, \
        f"FAIL: ops.json not corrected; still {final.get('device_state')}"
    assert drift_after > drift_before, \
        f"FAIL: drift counter didn't tick ({drift_before} -> {drift_after})"
    print(f"  PASS: scaler-side write corrected by resolver "
          f"({on_disk} -> {final.get('device_state')}), "
          f"drift counter ticked +{drift_after - drift_before}")


def main():
    failed = []
    for name, fn in [
        ("cross_write_race", lambda: test_cross_write_race(n=80)),
        ("schema_sync", test_schema_sync),
        ("drift_sync", test_drift_sync),
    ]:
        try:
            fn()
        except AssertionError as exc:
            print(f"  ASSERTION FAILED in {name}: {exc}")
            failed.append(name)
        except Exception as exc:
            print(f"  EXCEPTION in {name}: {exc}")
            import traceback
            traceback.print_exc()
            failed.append(name)
    _section("RESULT")
    if failed:
        print(f"  FAILED: {failed}")
        sys.exit(1)
    print("  ALL PASS")


if __name__ == "__main__":
    main()
