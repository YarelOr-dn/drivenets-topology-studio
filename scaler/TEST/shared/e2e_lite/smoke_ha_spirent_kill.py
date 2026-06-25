#!/usr/bin/env python3
"""
Real-device Phase 1 smoke runner.

Usage:
    python3 -m TEST.shared.e2e_lite.smoke_ha_spirent_kill --device PE-4

What it does:
    1. Builds a tiny suite of 3 scenarios mirroring the TEST_evpn_elan_ha_SW248907
       sequence (mac_recovery -> ncc_switchover -> mac_move_during_gr), but only
       doing harmless `spirent_tool.py status --json` probes in each (no real
       traffic config). The point is to prove the orchestration path works
       end-to-end.
    2. Wires a real SpirentWatchdog + RecoveryFsmLite + scenario_runner.
    3. During scenario 2, it deliberately kills the Spirent session by calling
       `spirent_tool.py detach` (non-destructive; just drops the STC reservation).
    4. Confirms the watchdog reconnects, FSM heals, scenario 2 retries, and
       scenario 3 runs normally.
    5. Writes results JSON + active_test_session.json + /tmp/spirent_watchdog.json.

Run this under a safe test window. It WILL briefly drop your Spirent session.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE.parents[2]) not in sys.path:
    sys.path.insert(0, str(HERE.parents[2]))

from TEST.shared.e2e_lite import (  # noqa: E402
    RecoveryFsmLite,
    RecoveryGuards,
    ScenarioSpec,
    ScenarioVerdict,
    SpirentWatchdog,
    run_suite,
    install_mac_trigger_watchdog,
)


def _find_spirent_tool() -> Path:
    env = os.environ.get("SPIRENT_TOOL_PATH")
    if env and Path(env).exists():
        return Path(env)
    candidates = [
        Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py",
        Path("/home/dn/SCALER/SPIRENT/spirent_tool.py"),
        Path("/home/dn/drivenets-topology-studio/scaler/SPIRENT/spirent_tool.py"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise SystemExit(f"spirent_tool.py not found. Set SPIRENT_TOOL_PATH.")


def make_scenarios(watchdog: SpirentWatchdog, tool: Path, kill_mid_run: bool):
    def probe(spec, ctx) -> ScenarioVerdict:
        ctx.log(f"scenario {spec.id} on device {ctx.payload.get('device')} -- probe")
        res = watchdog.guarded_run(["status", "--json"], timeout=15, retries=2)
        if not res.ok:
            raise RuntimeError(f"watchdog probe failed: {res.combined[:200]}")
        ctx.log(f"scenario {spec.id}: status OK (rc={res.rc})")
        return ScenarioVerdict.PASS

    def probe_after_kill(spec, ctx) -> ScenarioVerdict:
        if kill_mid_run:
            ctx.log(f"scenario {spec.id}: intentionally detaching Spirent session NOW")
            # Subprocess directly (not through watchdog) so we don't heal too early.
            subprocess.run(
                [sys.executable, str(tool), "detach"],
                timeout=30, capture_output=True,
            )
        # Let the watchdog observe the broken state, heal, retry.
        res = watchdog.guarded_run(["status", "--json"], timeout=15, retries=3)
        if not res.ok:
            raise RuntimeError(f"scenario {spec.id} failed after heal: {res.combined[:200]}")
        ctx.log(f"scenario {spec.id}: recovered (attempts={res.attempts}, healed={res.healed})")
        return ScenarioVerdict.PASS

    return [
        ScenarioSpec(id="SC07", name="SC07_mac_recovery", run_fn=probe),
        ScenarioSpec(id="SC08", name="SC08_ncc_switchover", run_fn=probe_after_kill),
        ScenarioSpec(id="SC09", name="SC09_mac_move_during_gr", run_fn=probe),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device", default="PE-4", help="DUT name (logged only)")
    ap.add_argument("--tool", default=None, help="Path to spirent_tool.py")
    ap.add_argument("--no-kill", action="store_true", help="Skip the mid-run detach (dry run)")
    ap.add_argument(
        "--session-path",
        default=str(Path.home() / "SCALER" / "TEST" / "active_test_session.json"),
    )
    ap.add_argument(
        "--results-path",
        default=str(Path.home() / "SCALER" / "TEST" / "phase1_smoke_result.json"),
    )
    args = ap.parse_args()

    tool = Path(args.tool) if args.tool else _find_spirent_tool()
    print(f"[smoke] spirent_tool={tool} device={args.device} kill={not args.no_kill}")

    guards = RecoveryGuards()
    fsm = RecoveryFsmLite(guards=guards)
    watchdog = SpirentWatchdog(fsm=fsm, tool_path=tool)
    install_mac_trigger_watchdog(watchdog)

    scenarios = make_scenarios(watchdog, tool, kill_mid_run=not args.no_kill)

    try:
        result = run_suite(
            suite_id="TEST_evpn_elan_ha_SW248907_phase1_smoke",
            scenarios=scenarios,
            fsm=fsm,
            payload={"device": args.device},
            active_session_path=Path(args.session_path),
            results_path=Path(args.results_path),
            on_product_bug="ask",
        )
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[smoke] suite aborted: {exc}")
        return 2

    ok = result.all_passed and not result.unrecoverable
    print(f"[smoke] DONE: passed={result.passed} failed={result.failed} "
          f"fsm={result.final_fsm_state} ok={ok}")
    print(f"[smoke] results -> {args.results_path}")
    print(f"[smoke] session  -> {args.session_path}")
    from TEST.shared.e2e_lite import read_watchdog_state, WATCHDOG_STATE_PATH
    wd = read_watchdog_state() or {}
    print(f"[smoke] watchdog -> {WATCHDOG_STATE_PATH} state={wd.get('state')} "
          f"heals={wd.get('total_heals')}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
