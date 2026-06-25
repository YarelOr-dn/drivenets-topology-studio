#!/usr/bin/env python3
"""Synthetic tests for scenario_runner. Run with:

    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_scenario_runner

No pytest dependency. Uses monkey-patching for ask_product_bug.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import List

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite import (  # noqa: E402
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryGuards,
    RecoveryState,
)
from e2e_lite.scenario_runner import (  # noqa: E402
    FailureClass,
    ScenarioResult,
    ScenarioSpec,
    ScenarioVerdict,
    SuiteResult,
    UnrecoverableSuiteFailure,
    default_classifier,
    run,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _spec(id: str, fn, on_failure: str = "fix_and_rerun", known_bug: str = None, max_retries=None) -> ScenarioSpec:
    return ScenarioSpec(
        id=id,
        name=id,
        run_fn=fn,
        on_failure=on_failure,
        known_bug=known_bug,
        max_retries=max_retries,
    )


def _fsm(reconnects: int = 3, scenario_retries: int = 2):
    return RecoveryFsmLite(guards=RecoveryGuards(
        max_spirent_reconnects=reconnects,
        max_scenario_retries=scenario_retries,
        spirent_backoff_sec=0,
        ssh_backoff_sec=0,
    ))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_all_pass() -> None:
    def scenario_fn(spec, ctx):
        return ScenarioResult(id=spec.id, verdict=ScenarioVerdict.PASS)

    fsm = _fsm()
    r = run(
        suite_id="test_all_pass",
        scenarios=[_spec("SC01", scenario_fn), _spec("SC02", scenario_fn)],
        fsm=fsm,
    )
    assert r.all_passed, r.to_dict()
    assert r.passed == 2
    assert r.failed == 0


def test_auto_retry_on_automation_fail() -> None:
    """First call fails with SSH-drop message; second call passes."""
    call_count = {"n": 0}

    def scenario_fn(spec, ctx):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Connection reset by peer (SSH drop)")
        return ScenarioResult(id=spec.id, verdict=ScenarioVerdict.PASS)

    fsm = _fsm()
    # Register a no-op PREREQ healer so FSM can walk back to STABLE.
    fsm.register_healer(RecoveryState.PREREQ_FAILED, lambda f, p: RecoveryEvent.PREREQ_FIXED)

    r = run(
        suite_id="test_auto_retry",
        scenarios=[_spec("SC01", scenario_fn)],
        fsm=fsm,
    )
    assert r.all_passed, r.to_dict()
    assert call_count["n"] == 2
    assert len(r.scenarios[0]["attempts"]) == 2


def test_unrecoverable_when_automation_retries_exhausted() -> None:
    def scenario_fn(spec, ctx):
        raise RuntimeError("Spirent session dead")

    fsm = _fsm(scenario_retries=1)
    fsm.register_healer(RecoveryState.PREREQ_FAILED, lambda f, p: RecoveryEvent.PREREQ_FIXED)

    raised = False
    try:
        run(
            suite_id="test_auto_unrec",
            scenarios=[_spec("SC01", scenario_fn)],
            fsm=fsm,
        )
    except UnrecoverableSuiteFailure:
        raised = True
    assert raised


def test_product_bug_known_becomes_xfail() -> None:
    def scenario_fn(spec, ctx):
        raise AssertionError("expected 5 entries, got 3")  # assertion -> PRODUCT_BUG

    fsm = _fsm()
    r = run(
        suite_id="test_known_bug",
        scenarios=[_spec("SC01", scenario_fn, known_bug="SW-123456")],
        fsm=fsm,
    )
    assert r.xfailed == 1
    assert r.failed == 0
    assert r.scenarios[0]["attempts"][-1]["verdict"] == "XFAIL"


def test_product_bug_ask_continue() -> None:
    """AskQuestion returns 'continue' -> scenario marked FAIL and suite proceeds."""
    def scenario_fn(spec, ctx):
        raise AssertionError("DNOS bug SW-xxxxx")

    def pass_fn(spec, ctx):
        return ScenarioResult(id=spec.id, verdict=ScenarioVerdict.PASS)

    asked = {"n": 0}
    def ask(spec, res):
        asked["n"] += 1
        return "continue"

    fsm = _fsm()
    r = run(
        suite_id="test_ask_continue",
        scenarios=[_spec("SC01", scenario_fn, on_failure="ask_user"), _spec("SC02", pass_fn)],
        fsm=fsm,
        ask_product_bug=ask,
    )
    assert asked["n"] == 1
    assert r.failed == 1
    assert r.passed == 1


def test_product_bug_abort_policy() -> None:
    def scenario_fn(spec, ctx):
        raise AssertionError("bug")

    fsm = _fsm()
    raised = False
    try:
        run(
            suite_id="test_abort",
            scenarios=[_spec("SC01", scenario_fn, on_failure="abort")],
            fsm=fsm,
        )
    except UnrecoverableSuiteFailure:
        raised = True
    assert raised


def test_default_classifier_signatures() -> None:
    assert default_classifier(RuntimeError("paramiko ssh banner")) == FailureClass.AUTOMATION
    assert default_classifier(RuntimeError("Spirent lab server 404")) == FailureClass.AUTOMATION
    assert default_classifier(AssertionError("mac count mismatch")) == FailureClass.PRODUCT_BUG
    assert default_classifier(RuntimeError("some weird random message")) == FailureClass.UNKNOWN


def test_active_session_persisted(tmp_path_factory=None) -> None:
    import tempfile
    path = Path(tempfile.mkdtemp()) / "active_test_session.json"

    def pass_fn(spec, ctx):
        return ScenarioResult(id=spec.id, verdict=ScenarioVerdict.PASS)

    fsm = _fsm()
    r = run(
        suite_id="test_persist",
        scenarios=[_spec("SC01", pass_fn)],
        fsm=fsm,
        active_session_path=path,
    )
    import json
    data = json.loads(path.read_text())
    assert data["fsm_state"] == "Stable"
    assert data["suite"] == "test_persist"
    assert "scenario_retries_this_run" in data


def test_multiple_scenarios_keep_going_on_xfail() -> None:
    seen = []
    def bug_fn(spec, ctx):
        seen.append(spec.id)
        raise AssertionError("bug")

    def ok_fn(spec, ctx):
        seen.append(spec.id)
        return ScenarioResult(id=spec.id, verdict=ScenarioVerdict.PASS)

    fsm = _fsm()
    r = run(
        suite_id="test_mixed",
        scenarios=[
            _spec("SC01", bug_fn, known_bug="SW-KNOWN"),
            _spec("SC02", ok_fn),
            _spec("SC03", ok_fn),
        ],
        fsm=fsm,
    )
    assert seen == ["SC01", "SC02", "SC03"]
    assert r.passed == 2
    assert r.xfailed == 1
    assert r.failed == 0


def _run_all() -> int:
    tests = [
        test_all_pass,
        test_auto_retry_on_automation_fail,
        test_unrecoverable_when_automation_retries_exhausted,
        test_product_bug_known_becomes_xfail,
        test_product_bug_ask_continue,
        test_product_bug_abort_policy,
        test_default_classifier_signatures,
        test_active_session_persisted,
        test_multiple_scenarios_keep_going_on_xfail,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception:
            failed += 1
            print(f"[FAIL] {fn.__name__}")
            traceback.print_exc()
    print()
    print(f"Total: {len(tests)}  Passed: {len(tests) - failed}  Failed: {failed}")
    return failed


if __name__ == "__main__":
    sys.exit(_run_all())
