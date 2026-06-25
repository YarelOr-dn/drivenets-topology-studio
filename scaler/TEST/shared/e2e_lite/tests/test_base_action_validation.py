#!/usr/bin/env python3
"""Synthetic tests for base_action.py + base_validation.py.

Run with:
    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_base_action_validation

No external deps.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import List, Tuple

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.base_action import (  # noqa: E402
    BaseAction,
    CallableAction,
    RecoverableError,
    default_is_recoverable,
)
from e2e_lite.base_validation import (  # noqa: E402
    BaseValidation,
    CallableValidation,
    ShowCommandContains,
    ValidationStatus,
    WaitForCondition,
)
from e2e_lite.recovery_fsm_lite import (  # noqa: E402
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryState,
)


# ---------------------------------------------------------------------------
# BaseValidation tests
# ---------------------------------------------------------------------------

def test_callable_validation_pass() -> None:
    v = CallableValidation(fn=lambda: True, name="ok")
    res = v.execute()
    assert res.status == ValidationStatus.PASSED
    assert v.last_result is res


def test_callable_validation_fail() -> None:
    v = CallableValidation(fn=lambda: False, name="no")
    res = v.execute()
    assert res.status == ValidationStatus.FAILED


def test_negative_validation_passes_when_predicate_false() -> None:
    v = CallableValidation(fn=lambda: False, name="neg", negative_validation=True)
    res = v.execute()
    assert res.status == ValidationStatus.PASSED


def test_negative_validation_passes_when_predicate_raises() -> None:
    def boom():
        raise RuntimeError("boom")
    v = CallableValidation(fn=boom, name="neg_raise", negative_validation=True)
    res = v.execute()
    assert res.status == ValidationStatus.PASSED


def test_validation_error_reraised_when_fail_on_error() -> None:
    def boom():
        raise ValueError("explode")
    v = CallableValidation(fn=boom, name="err", fail_on_error=True)
    try:
        v.execute()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_validation_error_swallowed_when_not_fail_on_error() -> None:
    def boom():
        raise ValueError("explode")
    v = CallableValidation(fn=boom, name="err", fail_on_error=False)
    res = v.execute()
    assert res.status == ValidationStatus.ERRORED


def test_show_command_contains_uses_session() -> None:
    class FakeSession:
        def __init__(self): self.seen = []
        def send_command(self, c, timeout=None):
            self.seen.append(c)
            return "interface ge100-0/0/1 is UP"
    s = FakeSession()
    v = ShowCommandContains("show interfaces", "UP", session=s)
    res = v.execute()
    assert res.status == ValidationStatus.PASSED
    assert s.seen == ["show interfaces"]


def test_wait_for_condition_polls_then_passes() -> None:
    counter = {"n": 0}
    def ready():
        counter["n"] += 1
        return counter["n"] >= 3
    v = WaitForCondition(predicate=ready, timeout=2, poll_interval=0.05, name="wait")
    res = v.execute()
    assert res.status == ValidationStatus.PASSED
    assert counter["n"] >= 3


def test_wait_for_condition_times_out() -> None:
    v = WaitForCondition(predicate=lambda: False, timeout=0.2,
                         poll_interval=0.05, name="wait_fail")
    res = v.execute()
    assert res.status == ValidationStatus.FAILED


# ---------------------------------------------------------------------------
# BaseAction tests
# ---------------------------------------------------------------------------

def test_callable_action_runs_validations_in_order() -> None:
    order: List[str] = []

    class V(BaseValidation):
        def __init__(self, label: str):
            super().__init__(name=label)
            self._label = label
        def collect_data(self) -> None:
            order.append(f"{self._label}_collect")
        def _validate(self) -> bool:
            order.append(f"{self._label}_validate")
            return True

    pre = V("pre")
    post = V("post")
    action = CallableAction(
        fn=lambda: order.append("action") or "result",
        name="demo",
    )
    action.add_pre_validation(pre).add_post_validation(post)

    out = action.execute()
    assert out == "result"
    # collect_data runs on post-validations BEFORE the action.
    # pre-validations run BEFORE the action. Action runs. Post-validations run.
    assert order == [
        "post_collect",
        "pre_validate",
        "action",
        "post_validate",
    ], order


def test_action_fails_fast_on_failed_pre_validation() -> None:
    class Fail(BaseValidation):
        def _validate(self) -> bool:
            return False

    executed = {"flag": False}
    action = CallableAction(fn=lambda: executed.__setitem__("flag", True), name="x")
    action.add_pre_validation(Fail(name="bad"))
    try:
        action.execute()
    except AssertionError:
        assert executed["flag"] is False  # action never ran
        return
    raise AssertionError("expected AssertionError from failed pre-validation")


def test_action_recoverable_error_emits_fsm_event() -> None:
    """Action.execute emits SPIRENT_SESSION_DEAD -> FSM moves to SPIRENT_DOWN.

    The Action's job is to report the failure; the scenario_runner (not the
    Action) is responsible for driving the heal.
    """
    fsm = RecoveryFsmLite()
    # Prime FSM to STABLE (otherwise it starts in INIT).
    fsm.on_event(RecoveryEvent.HEALTH_OK)
    assert fsm.state == RecoveryState.STABLE

    def fn():
        raise RecoverableError("Spirent session dead")

    action = CallableAction(fn=fn, name="crash")
    action.bind_fsm(fsm)
    try:
        action.execute()
    except RecoverableError:
        pass
    else:
        raise AssertionError("expected RecoverableError")

    # FSM must have recorded the Spirent-dead event.
    events = [t.event for t in fsm.context.transitions]
    assert "spirent_session_dead" in events, events
    assert fsm.state == RecoveryState.SPIRENT_DOWN, fsm.state


def test_action_classifies_ssh_error_as_ssh_fail() -> None:
    fsm = RecoveryFsmLite()
    fsm.on_event(RecoveryEvent.HEALTH_OK)

    def fn():
        raise RuntimeError("paramiko SSH banner error")

    action = CallableAction(fn=fn, name="ssh_boom")
    action.bind_fsm(fsm)
    try:
        action.execute()
    except RuntimeError:
        pass
    events = [t.event for t in fsm.context.transitions]
    assert "ssh_fail" in events, events
    assert fsm.state == RecoveryState.DUT_SSH_DOWN, fsm.state


def test_default_is_recoverable_matrix() -> None:
    assert default_is_recoverable(RecoverableError("x"))
    assert default_is_recoverable(RuntimeError("paramiko ssh broken"))
    assert default_is_recoverable(RuntimeError("Lab Server 404"))
    assert default_is_recoverable(RuntimeError("session dead"))
    assert not default_is_recoverable(ValueError("unrelated"))
    assert not default_is_recoverable(AssertionError("bug"))


def test_postpone_validations_allows_manual_run() -> None:
    count = {"pre": 0, "post": 0}

    class V(BaseValidation):
        def __init__(self, key):
            super().__init__(name=key)
            self._key = key
        def _validate(self) -> bool:
            count[self._key] += 1
            return True

    action = CallableAction(fn=lambda: "ok", name="manual")
    action.add_pre_validation(V("pre")).add_post_validation(V("post"))
    action.postpone_pre_validations().postpone_post_validations()
    out = action.execute()
    assert out == "ok"
    assert count == {"pre": 0, "post": 0}  # nothing auto-ran

    action.run_validations(pre_validations=True, post_validations=True)
    assert count == {"pre": 1, "post": 1}


def test_action_output_injected_into_validations() -> None:
    class EchoAction(BaseAction):
        def __init__(self, stream_name):
            super().__init__(name="echo")
            self.stream_name = stream_name
        def _execute_action(self):
            return {"stream": self.stream_name}
        def get_action_outputs(self):
            return {"stream_name": self.stream_name}

    seen: List[str] = []

    class CheckStream(BaseValidation):
        def _validate(self) -> bool:
            seen.append(self.params.get("stream_name", "<none>"))
            return bool(self.params.get("stream_name"))

    a = EchoAction("mac_stream_1")
    a.add_post_validation(CheckStream(name="has_stream"))
    a.execute()
    assert seen == ["mac_stream_1"]


def test_action_record_captures_timings_and_errors() -> None:
    def boom():
        raise RecoverableError("SSH broken")

    action = CallableAction(fn=boom, name="bad")
    try:
        action.execute()
    except RecoverableError:
        pass
    rec = action.last_record
    assert rec is not None
    assert rec.recoverable
    assert "SSH broken" in rec.error
    assert rec.duration_sec >= 0


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _discover_tests() -> List[Tuple[str, callable]]:
    g = globals()
    return sorted(
        (name, fn) for name, fn in g.items()
        if name.startswith("test_") and callable(fn)
    )


def run_all() -> int:
    tests = _discover_tests()
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception:
            print(f"[FAIL] {name}")
            traceback.print_exc()
            failed += 1
    print(f"\nTotal: {len(tests)}  Passed: {passed}  Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
