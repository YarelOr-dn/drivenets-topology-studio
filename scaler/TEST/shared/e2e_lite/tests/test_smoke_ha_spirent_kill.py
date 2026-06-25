#!/usr/bin/env python3
"""
Phase 1 SMOKE TEST -- synthetic equivalent of:
    /TEST run TEST_evpn_elan_ha_SW248907 on PE-4 and kill Spirent mid-scenario.

Because this runs headless (no device, no Spirent), it stubs the
`spirent_tool.py` subprocess with a FakeSpirent that:

    * scenario SC07:   always healthy
    * scenario SC08:   first call crashes (dead session), heal, second call succeeds
    * scenario SC09:   always healthy

The test asserts:
    1. The scenario runner never silently skips SC08 after the crash.
    2. The watchdog emits RecoveryEvent to the FSM and heals.
    3. The FSM ends in STABLE (not UNRECOVERABLE).
    4. The suite reports all three scenarios PASSED.
    5. `active_test_session.json` reflects fsm_state, scenario_retries, etc.
    6. `/tmp/spirent_watchdog.json` was written.

This is the synthetic half of the Phase 1 smoke. The live-device half lives
in `smoke_ha_spirent_kill.py` (sibling module) and is run manually on PE-4.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# -- path shim -------------------------------------------------------------
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # scaler/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Packages that need to be importable as "TEST.shared.e2e_lite.*"
from TEST.shared.e2e_lite import (  # noqa: E402
    FailureClass,
    RecoveryFsmLite,
    RecoveryGuards,
    ScenarioSpec,
    ScenarioVerdict,
    SpirentUnrecoverableError,
    SpirentWatchdog,
    UnrecoverableSuiteFailure,
    default_classifier,
    run_suite,
)
from TEST.shared.e2e_lite import scenario_runner as sr  # noqa: E402
from TEST.shared.e2e_lite import spirent_watchdog as wd_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Fake spirent_tool.py -- just enough to exercise the watchdog.
# ---------------------------------------------------------------------------

class FakeSpirent:
    """Scriptable stand-in for `subprocess.run([python, spirent_tool, ...])`."""

    def __init__(self) -> None:
        self.calls: list = []
        self.scenario: str = "SC07"   # changed by the test harness
        self.crashes_left: int = 0
        self.total_invocations: int = 0

    def set_scenario(self, name: str, crashes: int = 0) -> None:
        self.scenario = name
        self.crashes_left = crashes

    def __call__(self, cmd, **kwargs):
        self.total_invocations += 1
        args = list(cmd)
        # Extract the spirent_tool args after the "--" style invocation:
        # [python, /path/to/spirent_tool.py, sub, arg, ...]
        sub = args[2] if len(args) >= 3 else ""
        self.calls.append({"sub": sub, "scenario": self.scenario, "args": args[2:]})

        # Status probe -- always returns a reasonable dict unless we're in
        # "all dead" mode.
        if sub == "status":
            active = (self.scenario != "DEAD") and (self.crashes_left <= 0)
            payload = {
                "session": {
                    "name": "smoke",
                    "active": active,
                    "port_reserved": active,
                },
            }
            rc = 0 if active else 1
            return subprocess.CompletedProcess(
                args, rc, json.dumps(payload), "" if rc == 0 else "No active session",
            )

        # Mutating commands -- crash if crashes_left > 0.
        if self.crashes_left > 0:
            self.crashes_left -= 1
            return subprocess.CompletedProcess(
                args, 1, "", "ERROR: No active session on Lab Server (404 BLL Handle)",
            )
        return subprocess.CompletedProcess(
            args, 0, f"OK: {sub} -- scenario={self.scenario}", "",
        )


# ---------------------------------------------------------------------------
# Scenario run functions -- mimic SC07/SC08/SC09 of TEST_evpn_elan_ha_SW248907
# ---------------------------------------------------------------------------

def _do_spirent(watchdog: SpirentWatchdog, sub: str) -> None:
    """Wrapper for the scenario body; uses the watchdog like mac_trigger does."""
    res = watchdog.guarded_run([sub, "--name", "smoke"], timeout=5, retries=3)
    if not res.ok:
        raise RuntimeError(f"spirent_tool {sub} failed: {res.combined[:200]}")


def make_scenarios(watchdog: SpirentWatchdog, fake: FakeSpirent):
    def sc07(spec, ctx):
        fake.set_scenario("SC07", crashes=0)
        _do_spirent(watchdog, "create-stream")
        return ScenarioVerdict.PASS

    def sc08(spec, ctx):
        # This one fails on first call, heals, and succeeds on retry.
        # But from the scenario_runner's POV the scenario body itself runs
        # once and succeeds (watchdog handles the inner retry silently).
        fake.set_scenario("SC08", crashes=1)
        _do_spirent(watchdog, "create-stream")
        return ScenarioVerdict.PASS

    def sc09(spec, ctx):
        fake.set_scenario("SC09", crashes=0)
        _do_spirent(watchdog, "create-stream")
        return ScenarioVerdict.PASS

    return [
        ScenarioSpec(id="SC07", name="SC07_mac_recovery", run_fn=sc07),
        ScenarioSpec(id="SC08", name="SC08_ncc_switchover", run_fn=sc08),
        ScenarioSpec(id="SC09", name="SC09_mac_move_during_gr", run_fn=sc09),
    ]


# ---------------------------------------------------------------------------
# Test case
# ---------------------------------------------------------------------------

class TestPhase1Smoke(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ha_smoke_"))
        self.session_path = self.tmpdir / "active_test_session.json"
        self.results_path = self.tmpdir / "suite_result.json"
        self.watchdog_state_path = self.tmpdir / "spirent_watchdog.json"

        # Redirect watchdog state path so we don't stomp /tmp on shared CI.
        self.real_state_path = wd_mod.WATCHDOG_STATE_PATH
        wd_mod.WATCHDOG_STATE_PATH = self.watchdog_state_path

        self.fake = FakeSpirent()

    def tearDown(self):
        wd_mod.WATCHDOG_STATE_PATH = self.real_state_path
        for p in (self.session_path, self.results_path, self.watchdog_state_path):
            if p.exists():
                p.unlink()
        try:
            self.tmpdir.rmdir()
        except OSError:
            pass

    def test_mid_run_spirent_crash_heals_and_all_scenarios_pass(self):
        # Stub subprocess.run in both the watchdog and FSM healer modules.
        with patch.object(wd_mod.subprocess, "run", side_effect=self.fake), \
             patch("TEST.shared.e2e_lite.recovery_fsm_lite.subprocess.run", side_effect=self.fake):

            guards = RecoveryGuards(
                max_ssh_retries=3,
                max_spirent_reconnects=3,
                max_scenario_retries=2,
                max_heavy_ops_per_session=1,
                hard_timeout_sec=300,
            )
            fsm = RecoveryFsmLite(guards=guards)
            watchdog = SpirentWatchdog(
                fsm=fsm,
                tool_path=Path("/fake/spirent_tool.py"),
                probe_ttl_s=0.01,   # always re-probe so the fake script is exercised
            )
            scenarios = make_scenarios(watchdog, self.fake)

            result = run_suite(
                suite_id="TEST_evpn_elan_ha_SW248907",
                scenarios=scenarios,
                fsm=fsm,
                active_session_path=self.session_path,
                results_path=self.results_path,
                classifier=default_classifier,
                on_product_bug="abort",  # no user prompt in headless mode
            )

        # ---- Suite-level assertions ----
        self.assertEqual(result.total, 3, "all 3 scenarios recorded")
        self.assertEqual(result.passed, 3, f"all 3 should PASS (got {result.passed}); scenarios={result.scenarios}")
        self.assertEqual(result.failed, 0)
        self.assertEqual(result.errored, 0)
        self.assertFalse(result.unrecoverable, "FSM should not be unrecoverable")
        self.assertEqual(result.final_fsm_state, "Stable")

        # ---- Watchdog telemetry ----
        self.assertTrue(self.watchdog_state_path.exists(),
                        "watchdog state file must be written")
        wd_state = json.loads(self.watchdog_state_path.read_text())
        self.assertIn(wd_state["state"], ("healthy", "dead"),
                      f"watchdog state={wd_state['state']}")
        self.assertGreaterEqual(wd_state["total_heals"], 1,
                                "at least one heal should have been recorded")

        # ---- Active session.json ----
        self.assertTrue(self.session_path.exists(),
                        "active_test_session.json must be written")
        sess = json.loads(self.session_path.read_text())
        self.assertEqual(sess["suite"], "TEST_evpn_elan_ha_SW248907")
        self.assertEqual(sess["fsm_state"], "Stable")
        self.assertFalse(sess["active"], "suite finished -> active=False")
        self.assertIn("fsm_snapshot", sess)
        self.assertIn("scenario_retries_this_run", sess)

        # ---- Per-scenario results ----
        by_id = {s["id"]: s for s in result.scenarios}
        for sid in ("SC07", "SC08", "SC09"):
            self.assertIn(sid, by_id, f"scenario {sid} missing from result")
            last = by_id[sid]["attempts"][-1]
            self.assertEqual(last["verdict"], ScenarioVerdict.PASS.value)

        # SC08 is where the Spirent session crashed. The watchdog handles the
        # retry inside _do_spirent, so the scenario_runner sees it as one
        # attempt that PASSED. The FSM should have recorded a Spirent
        # recovery transition in its history.
        fsm_events = [t.event for t in fsm.context.transitions]
        self.assertIn("spirent_session_dead", fsm_events,
                      "FSM history must include the Spirent dead event")
        self.assertIn("health_ok", fsm_events,
                      "FSM history must include a heal transition")

        # ---- Fake spirent sanity ----
        # probe + create-stream per scenario. SC08 does an extra retry.
        subs = [c["sub"] for c in self.fake.calls]
        self.assertIn("create-stream", subs)
        sc08_calls = [c for c in self.fake.calls if c["scenario"] == "SC08"]
        self.assertGreaterEqual(
            len([c for c in sc08_calls if c["sub"] == "create-stream"]),
            2,
            "SC08 should have at least one retry after the crash",
        )

    def test_unhealable_spirent_causes_clean_abort(self):
        """When the session is permanently dead, suite aborts with
        UnrecoverableSuiteFailure (NOT a silent skip)."""
        self.fake.set_scenario("DEAD", crashes=100)

        def always_dead(spec, ctx):
            _do_spirent(
                SpirentWatchdog(fsm=ctx.fsm, tool_path=Path("/fake/spirent_tool.py"),
                                probe_ttl_s=0.01),
                "create-stream",
            )
            return ScenarioVerdict.PASS

        with patch.object(wd_mod.subprocess, "run", side_effect=self.fake), \
             patch("TEST.shared.e2e_lite.recovery_fsm_lite.subprocess.run", side_effect=self.fake):

            fsm = RecoveryFsmLite(guards=RecoveryGuards(
                max_spirent_reconnects=1,
                max_heavy_ops_per_session=0,
                max_scenario_retries=1,
                hard_timeout_sec=300,
            ))
            scenarios = [
                ScenarioSpec(id="DEAD1", name="dead_session_scenario", run_fn=always_dead),
            ]
            with self.assertRaises(UnrecoverableSuiteFailure):
                run_suite(
                    suite_id="TEST_dead_smoke",
                    scenarios=scenarios,
                    fsm=fsm,
                    active_session_path=self.session_path,
                    results_path=self.results_path,
                    on_product_bug="abort",
                )

        # The suite must have marked itself as unrecoverable in
        # active_test_session.json -- never silently skip.
        sess = json.loads(self.session_path.read_text())
        self.assertFalse(sess["active"], "suite marked inactive on abort")
        self.assertIn(sess["fsm_state"], ("Unrecoverable", "SpirentHealReconnect",
                                          "SpirentHealLabServer", "SpirentDown"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
