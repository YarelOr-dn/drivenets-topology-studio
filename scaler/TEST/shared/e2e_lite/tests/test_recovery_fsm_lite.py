#!/usr/bin/env python3
"""Synthetic tests for recovery_fsm_lite. Run with:

    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_recovery_fsm_lite

Does NOT require pytest (kept dependency-free so /TEST can run in lab envs).
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# Make "from e2e_lite import ..." work when called standalone.
_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.recovery_fsm_lite import (  # noqa: E402
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryGuards,
    RecoveryState,
    UnrecoverableError,
)


def test_happy_path_stable() -> None:
    fsm = RecoveryFsmLite()
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    assert fsm.state == RecoveryState.STABLE


def test_spirent_reconnect_happy() -> None:
    called: List[str] = []

    def heal(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        called.append("reconnect")
        return RecoveryEvent.SPIRENT_CONNECT_OK

    fsm = RecoveryFsmLite()
    fsm.register_healer(RecoveryState.SPIRENT_HEAL_RECONNECT, heal)
    fsm.on_event(RecoveryEvent.SPIRENT_SESSION_DEAD)
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    assert fsm.state == RecoveryState.STABLE
    assert called == ["reconnect"]


def test_spirent_escalation_after_retries() -> None:
    calls: List[str] = []

    def fail(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        calls.append("reconnect_fail")
        fsm.record_spirent_reconnect()
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL

    def heal_labserver(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        calls.append("labserver_ok")
        return RecoveryEvent.SPIRENT_LAB_SERVER_OK

    guards = RecoveryGuards(max_spirent_reconnects=3, spirent_backoff_sec=0)
    fsm = RecoveryFsmLite(guards=guards)
    fsm.register_healer(RecoveryState.SPIRENT_HEAL_RECONNECT, fail)
    fsm.register_healer(RecoveryState.SPIRENT_HEAL_LAB_SERVER, heal_labserver)
    fsm.on_event(RecoveryEvent.SPIRENT_SESSION_DEAD)
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    assert fsm.state == RecoveryState.STABLE
    assert calls == ["reconnect_fail"] * 3 + ["labserver_ok"]


def test_budget_exhausted_unrecoverable() -> None:
    calls: List[str] = []

    def always_fail(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        calls.append(fsm.state.value)
        fsm.record_spirent_reconnect()
        return RecoveryEvent.SPIRENT_RECONNECT_FAIL

    guards = RecoveryGuards(
        max_spirent_reconnects=2,
        max_heavy_ops_per_session=1,
        spirent_backoff_sec=0,
    )
    fsm = RecoveryFsmLite(guards=guards)
    fsm.register_healer(RecoveryState.SPIRENT_HEAL_RECONNECT, always_fail)
    fsm.register_healer(RecoveryState.SPIRENT_HEAL_LAB_SERVER, always_fail)

    raised = False
    try:
        fsm.on_event(RecoveryEvent.SPIRENT_SESSION_DEAD)
        fsm.on_event(RecoveryEvent.HEALTH_OK)
    except UnrecoverableError as e:
        assert e.state == RecoveryState.UNRECOVERABLE
        raised = True
    assert raised


def test_ssh_max_retries() -> None:
    calls: List[str] = []

    def fail_ssh(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        calls.append("ssh_fail")
        fsm.record_ssh_retry()
        return RecoveryEvent.SSH_FAIL

    guards = RecoveryGuards(max_ssh_retries=3, ssh_backoff_sec=0)
    fsm = RecoveryFsmLite(guards=guards)
    fsm.register_healer(RecoveryState.DUT_SSH_HEALING, fail_ssh)

    raised = False
    try:
        fsm.on_event(RecoveryEvent.SSH_FAIL)
        fsm.on_event(RecoveryEvent.HEALTH_OK)
    except UnrecoverableError:
        raised = True
    assert raised
    assert len(calls) == 3


def test_cli_unresponsive_branch() -> None:
    def cli_hang(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        fsm.record_ssh_retry()
        return RecoveryEvent.SSH_UP_CLI_HANG

    guards = RecoveryGuards(max_ssh_retries=5, ssh_backoff_sec=0)
    fsm = RecoveryFsmLite(guards=guards)
    fsm.register_healer(RecoveryState.DUT_SSH_HEALING, cli_hang)
    fsm.on_event(RecoveryEvent.SSH_FAIL)
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    assert fsm.state == RecoveryState.DUT_CLI_UNRESPONSIVE


def test_prereq_ladder() -> None:
    def fix(fsm: RecoveryFsmLite, payload: dict) -> RecoveryEvent:
        return RecoveryEvent.PREREQ_FIXED

    fsm = RecoveryFsmLite()
    fsm.register_healer(RecoveryState.PREREQ_FAILED, fix)
    fsm.on_event(RecoveryEvent.PREREQ_FAIL)
    assert fsm.state == RecoveryState.STABLE


def test_listener_fires() -> None:
    transitions: List[Tuple[str, str, str]] = []
    fsm = RecoveryFsmLite()
    fsm.on_transition(lambda t: transitions.append((t.from_state, t.event, t.to_state)))
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    assert transitions == [("Init", "health_ok", "Stable")]


def test_scenario_retry_counter() -> None:
    fsm = RecoveryFsmLite()
    fsm.record_scenario_retry("SC01")
    fsm.record_scenario_retry("SC01")
    fsm.record_scenario_retry("SC02")
    assert fsm.scenario_retry_count("SC01") == 2
    assert fsm.scenario_retry_count("SC02") == 1


def test_persisted_snapshot() -> None:
    import json
    from e2e_lite.recovery_fsm_lite import FSM_STATE_PATH

    fsm = RecoveryFsmLite()
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    data = json.loads(FSM_STATE_PATH.read_text())
    assert data["state"] == "Stable"
    assert "context" in data
    assert "guards" in data


def _run_all() -> int:
    tests = [
        test_happy_path_stable,
        test_spirent_reconnect_happy,
        test_spirent_escalation_after_retries,
        test_budget_exhausted_unrecoverable,
        test_ssh_max_retries,
        test_cli_unresponsive_branch,
        test_prereq_ladder,
        test_listener_fires,
        test_scenario_retry_counter,
        test_persisted_snapshot,
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
