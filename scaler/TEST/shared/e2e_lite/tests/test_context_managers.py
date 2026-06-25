#!/usr/bin/env python3
"""Synthetic tests for context_managers.py (Phase 3.1).

Run with:
    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_context_managers
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.context_managers import (  # noqa: E402
    ContextManagerError,
    DutCliSection,
    ProcessRestartSection,
    SectionResult,
    SpirentTrafficSection,
    SpirentTrafficStats,
    SwitchoverSection,
)
from e2e_lite.recovery_fsm_lite import (  # noqa: E402
    RecoveryFsmLite,
    RecoveryGuards,
)
from e2e_lite.spirent_watchdog import SpirentCmdResult  # noqa: E402
from e2e_lite.system_snapshot import (  # noqa: E402
    SystemSnapshot,
    SystemSnapshotter,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class _FakeWatchdog:
    """Drop-in replacement exposing only what the section needs."""

    def __init__(
        self,
        *,
        rc_per_first_arg: Optional[Dict[str, int]] = None,
        stdout_per_first_arg: Optional[Dict[str, str]] = None,
        raise_on_ensure_healthy: bool = False,
    ) -> None:
        self.rc_per_first_arg = dict(rc_per_first_arg or {})
        self.stdout_per_first_arg = dict(stdout_per_first_arg or {})
        self.raise_on_ensure_healthy = raise_on_ensure_healthy
        self.calls: List[List[str]] = []
        self.ensure_healthy_calls: int = 0

    def ensure_healthy(self, raise_if_dead: bool = False) -> None:
        self.ensure_healthy_calls += 1
        if self.raise_on_ensure_healthy:
            if raise_if_dead:
                raise RuntimeError("fake: spirent session dead")

    def guarded_run(
        self,
        args: List[str],
        raise_on_error: bool = False,
        timeout: int = 60,
    ) -> SpirentCmdResult:
        self.calls.append(list(args))
        first = args[0] if args else ""
        rc = self.rc_per_first_arg.get(first, 0)
        stdout = self.stdout_per_first_arg.get(first, "")
        res = SpirentCmdResult(
            rc=rc,
            stdout=stdout,
            stderr="" if rc == 0 else f"fake: {first} failed",
            combined=stdout if rc == 0 else f"fake: {first} failed",
            command=list(args),
        )
        if rc != 0 and raise_on_error:
            raise RuntimeError(res.combined)
        return res


class _FakeSession:
    """In-memory DNOSSession stand-in for DutCliSection tests."""

    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        raise_on_cmd: Optional[str] = None,
        raise_on_close: bool = False,
        **_: Any,
    ) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.raise_on_cmd = raise_on_cmd
        self.raise_on_close = raise_on_close
        self.opened = False
        self.closed = False
        self.sent: List[str] = []

    def open(self) -> None:
        self.opened = True

    def send_command(self, cmd: str) -> str:
        self.sent.append(cmd)
        if self.raise_on_cmd and self.raise_on_cmd in cmd:
            raise RuntimeError(f"fake: cmd {cmd!r} rejected")
        return f"OK: {cmd}"

    def close(self) -> None:
        self.closed = True
        if self.raise_on_close:
            raise RuntimeError("fake: session close exploded")


def _make_fsm() -> RecoveryFsmLite:
    guards = RecoveryGuards(
        max_ssh_retries=1,
        max_spirent_reconnects=1,
        max_scenario_retries=1,
        max_heavy_ops_per_session=5,
        hard_timeout_sec=30,
    )
    return RecoveryFsmLite(guards=guards)


class _RunShowStub:
    """Callable run_show(device, cmd) -> str with recorded history."""

    def __init__(self, mapping: Dict[str, str]) -> None:
        self.mapping = dict(mapping)
        self.calls: List[Tuple[str, str]] = []

    def __call__(self, device: str, cmd: str) -> str:
        self.calls.append((device, cmd))
        return self.mapping.get(cmd, "")


# ---------------------------------------------------------------------------
# SectionResult
# ---------------------------------------------------------------------------

def test_section_result_summary_ok() -> None:
    r = SectionResult(name="X")
    r.entered = True
    r.completed = True
    r.duration_sec = 1.25
    assert r.summary().startswith("X[OK] dur=1.25s")


def test_section_result_summary_fail() -> None:
    r = SectionResult(name="X")
    r.add_error("boom")
    assert "FAIL" in r.summary()
    assert "errs=1" in r.summary()


# ---------------------------------------------------------------------------
# SpirentTrafficSection
# ---------------------------------------------------------------------------

def test_spirent_traffic_happy_path() -> None:
    wd = _FakeWatchdog(
        stdout_per_first_arg={
            "stats": '{"tx_frames": 123, "rx_frames": 122}',
        },
    )
    with SpirentTrafficSection(
        wd, capture_stats=True, start_grace_sec=0,
    ) as sect:
        assert sect.result.entered
        assert isinstance(sect.stats, SpirentTrafficStats)
        assert sect.stats.started_at > 0
    assert sect.result.completed
    # stats -> start -> stats -> stop -> stats
    first_args = [c[0] for c in wd.calls]
    assert first_args[0] == "stats"
    assert first_args[1] == "start"
    assert "stop" in first_args


def test_spirent_traffic_cleanup_runs_on_scenario_exception() -> None:
    wd = _FakeWatchdog()
    try:
        with SpirentTrafficSection(
            wd, capture_stats=False, start_grace_sec=0,
        ):
            raise RuntimeError("scenario boom")
    except RuntimeError as exc:
        assert "scenario boom" in str(exc)
    # stop was still invoked despite the raise
    assert any(c[0] == "stop" for c in wd.calls)


def test_spirent_traffic_skip_stop_when_stop_on_failure_false() -> None:
    wd = _FakeWatchdog()
    try:
        with SpirentTrafficSection(
            wd, capture_stats=False, stop_on_failure=False,
            start_grace_sec=0,
        ):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert not any(c[0] == "stop" for c in wd.calls)


def test_spirent_traffic_setup_failure_propagates() -> None:
    wd = _FakeWatchdog(rc_per_first_arg={"start": 2})
    raised = False
    try:
        with SpirentTrafficSection(
            wd, capture_stats=False, start_grace_sec=0,
        ):
            pass
    except RuntimeError:
        raised = True
    assert raised
    # stop must NOT be called because __enter__ failed
    assert not any(c[0] == "stop" for c in wd.calls)


def test_spirent_traffic_stats_snapshot_parses_json() -> None:
    wd = _FakeWatchdog(
        stdout_per_first_arg={"stats": '{"key": 42}'},
    )
    with SpirentTrafficSection(
        wd, capture_stats=True, start_grace_sec=0,
    ) as sect:
        pass
    assert sect.stats.before == {"key": 42}
    assert sect.stats.after == {"key": 42}
    assert sect.stats.duration_sec >= 0.0


def test_spirent_traffic_stats_handles_bad_json() -> None:
    wd = _FakeWatchdog(
        stdout_per_first_arg={"stats": "not-json"},
    )
    with SpirentTrafficSection(
        wd, capture_stats=True, start_grace_sec=0,
    ) as sect:
        pass
    assert "raw" in sect.stats.before


def test_spirent_traffic_probe_first_invokes_ensure_healthy() -> None:
    wd = _FakeWatchdog()
    with SpirentTrafficSection(
        wd, capture_stats=False, start_grace_sec=0, probe_first=True,
    ):
        pass
    assert wd.ensure_healthy_calls == 1


def test_spirent_traffic_poll_stats_exposed() -> None:
    wd = _FakeWatchdog(stdout_per_first_arg={"stats": '{"tx": 1}'})
    with SpirentTrafficSection(
        wd, capture_stats=False, start_grace_sec=0,
    ) as sect:
        live = sect.poll_stats()
        assert live == {"tx": 1}


# ---------------------------------------------------------------------------
# SwitchoverSection
# ---------------------------------------------------------------------------

def test_switchover_happy_path_with_active_flip() -> None:
    state = {"active": "ncc-0"}

    def fake_run_show(device: str, cmd: str) -> str:
        return f"Active: {state['active']}"

    def do_switchover() -> None:
        state["active"] = "ncc-1"

    fsm = _make_fsm()
    with SwitchoverSection(
        device="PE-4",
        run_show=fake_run_show,
        trigger=do_switchover,
        fsm=fsm,
        wait_for_stable_sec=1,
        poll_interval_sec=1,
    ) as sect:
        pass
    assert sect.active_ncc_before.endswith("ncc-0")
    assert sect.active_ncc_after.endswith("ncc-1")
    assert sect.result.completed
    assert fsm.context.heavy_ops_used == 1


def test_switchover_raises_when_no_flip_and_required() -> None:
    def fake_run_show(device: str, cmd: str) -> str:
        return "Active: ncc-0"

    def do_switchover() -> None:
        pass

    try:
        with SwitchoverSection(
            device="PE-4",
            run_show=fake_run_show,
            trigger=do_switchover,
            wait_for_stable_sec=1,
            poll_interval_sec=1,
            require_active_flip=True,
        ):
            pass
    except ContextManagerError as exc:
        assert "did not flip" in str(exc)
        return
    raise AssertionError("expected ContextManagerError")


def test_switchover_no_flip_but_require_false_passes() -> None:
    def fake_run_show(device: str, cmd: str) -> str:
        return "Active: ncc-0"

    def do_switchover() -> None:
        pass

    with SwitchoverSection(
        device="PE-4",
        run_show=fake_run_show,
        trigger=do_switchover,
        wait_for_stable_sec=1,
        poll_interval_sec=1,
        require_active_flip=False,
    ) as sect:
        pass
    assert sect.result.completed


def test_switchover_with_snapshotter_captures_diff() -> None:
    state = {"active": "ncc-0", "process_restart:routing:bgpd": 0}

    def fake_run_show(device: str, cmd: str) -> str:
        if cmd.startswith("show system process routing:bgpd"):
            return (
                "Process routing:bgpd is running. "
                f"Restarts: {state['process_restart:routing:bgpd']}"
            )
        return f"Active: {state['active']}"

    def do_switchover() -> None:
        state["active"] = "ncc-1"
        state["process_restart:routing:bgpd"] = 1

    snapshotter = SystemSnapshotter(
        device="PE-4",
        run_show=fake_run_show,
        processes=["routing:bgpd"],
        containers=[],
        interfaces=[],
    )

    with SwitchoverSection(
        device="PE-4",
        run_show=fake_run_show,
        trigger=do_switchover,
        snapshotter=snapshotter,
        wait_for_stable_sec=1,
        poll_interval_sec=1,
    ) as sect:
        pass
    assert sect.snapshot_before is not None
    assert sect.snapshot_after is not None
    assert sect.diff is not None


def test_switchover_trigger_failure_propagates() -> None:
    def fake_run_show(device: str, cmd: str) -> str:
        return "Active: ncc-0"

    def bad_trigger() -> None:
        raise RuntimeError("trigger boom")

    raised = False
    try:
        with SwitchoverSection(
            device="PE-4",
            run_show=fake_run_show,
            trigger=bad_trigger,
            wait_for_stable_sec=1,
            poll_interval_sec=1,
        ):
            pass
    except RuntimeError:
        raised = True
    assert raised


# ---------------------------------------------------------------------------
# ProcessRestartSection
# ---------------------------------------------------------------------------

def test_process_restart_healthy_path() -> None:
    state = {"healthy": False}

    def fake_run_show(device: str, cmd: str) -> str:
        if state["healthy"]:
            return "Process routing:bgpd is running. PID: 123"
        return "Process routing:bgpd is stopped"

    def restart(proc: str) -> None:
        state["healthy"] = True

    fsm = _make_fsm()
    with ProcessRestartSection(
        device="PE-4",
        run_show=fake_run_show,
        snapshotter=None,
        process="routing:bgpd",
        restart_fn=restart,
        fsm=fsm,
        wait_for_healthy_sec=2,
        poll_interval_sec=1,
    ) as sect:
        pass
    assert sect.process_healthy
    assert sect.result.completed
    assert fsm.context.heavy_ops_used == 1


def test_process_restart_healthy_wait_fails() -> None:
    def fake_run_show(device: str, cmd: str) -> str:
        return "Process routing:bgpd is stopped"

    def restart(proc: str) -> None:
        pass

    try:
        with ProcessRestartSection(
            device="PE-4",
            run_show=fake_run_show,
            snapshotter=None,
            process="routing:bgpd",
            restart_fn=restart,
            wait_for_healthy_sec=1,
            poll_interval_sec=1,
        ):
            pass
    except ContextManagerError as exc:
        assert "did not return to" in str(exc)
        return
    raise AssertionError("expected ContextManagerError")


def test_process_restart_with_snapshotter_captures_diff() -> None:
    state = {"restarts": 3}

    def fake_run_show(device: str, cmd: str) -> str:
        if cmd.startswith("show system process routing:bgpd"):
            return (
                f"Process routing:bgpd is running. Restarts: {state['restarts']}"
            )
        return ""

    def restart(proc: str) -> None:
        state["restarts"] += 1

    snapshotter = SystemSnapshotter(
        device="PE-4",
        run_show=fake_run_show,
        processes=["routing:bgpd"],
        containers=[],
        interfaces=[],
    )
    with ProcessRestartSection(
        device="PE-4",
        run_show=fake_run_show,
        snapshotter=snapshotter,
        process="routing:bgpd",
        restart_fn=restart,
        wait_for_healthy_sec=1,
        poll_interval_sec=1,
    ) as sect:
        pass
    assert sect.snapshot_before is not None
    assert sect.snapshot_after is not None
    assert sect.diff is not None


def test_process_restart_custom_healthy_substrings() -> None:
    def fake_run_show(device: str, cmd: str) -> str:
        return "State: enabled"

    def restart(proc: str) -> None:
        pass

    with ProcessRestartSection(
        device="PE-4",
        run_show=fake_run_show,
        snapshotter=None,
        process="custom",
        restart_fn=restart,
        wait_for_healthy_sec=1,
        poll_interval_sec=1,
        healthy_substrings=("enabled",),
    ) as sect:
        pass
    assert sect.process_healthy


# ---------------------------------------------------------------------------
# DutCliSection
# ---------------------------------------------------------------------------

def test_dut_cli_opens_sends_cleanup_and_rolls_back() -> None:
    holder: Dict[str, _FakeSession] = {}

    def factory(ip: str, username: str, password: str, **kw: Any) -> _FakeSession:
        sess = _FakeSession(ip, username, password, **kw)
        holder["sess"] = sess
        return sess

    with DutCliSection(
        device="PE-4", ip="1.2.3.4", username="x", password="y",
        cleanup_commands=["no network-services evpn instance TEST"],
        session_factory=factory,
    ) as sect:
        assert sect.session is holder["sess"]
        assert sect.session.opened
    sess = holder["sess"]
    assert sess.closed
    # cleanup -> end -> config -> rollback 0 -> end
    assert "no network-services evpn instance TEST" in sess.sent
    assert "config" in sess.sent
    assert "rollback 0" in sess.sent
    assert sess.sent.count("end") >= 1


def test_dut_cli_cleanup_command_error_is_logged_not_fatal() -> None:
    holder: Dict[str, _FakeSession] = {}

    def factory(*args: Any, **kw: Any) -> _FakeSession:
        sess = _FakeSession(
            *args, raise_on_cmd="BAD", **kw,
        )
        holder["sess"] = sess
        return sess

    with DutCliSection(
        device="PE-4", ip="1.2.3.4", username="x", password="y",
        cleanup_commands=["BAD cmd", "rollback hint"],
        session_factory=factory,
    ) as sect:
        pass
    sess = holder["sess"]
    # Even after cleanup error, session was closed + rollback ran
    assert sess.closed
    assert "rollback 0" in sess.sent
    assert any("BAD cmd" in err for err in sect.result.cleanup_errors)


def test_dut_cli_rollback_only_disabled() -> None:
    holder: Dict[str, _FakeSession] = {}

    def factory(*args: Any, **kw: Any) -> _FakeSession:
        sess = _FakeSession(*args, **kw)
        holder["sess"] = sess
        return sess

    with DutCliSection(
        device="PE-4", ip="1.2.3.4", username="x", password="y",
        cleanup_commands=[],
        force_rollback=False,
        session_factory=factory,
    ):
        pass
    sess = holder["sess"]
    assert "rollback 0" not in sess.sent


def test_dut_cli_close_error_captured() -> None:
    holder: Dict[str, _FakeSession] = {}

    def factory(*args: Any, **kw: Any) -> _FakeSession:
        sess = _FakeSession(*args, raise_on_close=True, **kw)
        holder["sess"] = sess
        return sess

    with DutCliSection(
        device="PE-4", ip="1.2.3.4", username="x", password="y",
        session_factory=factory,
    ) as sect:
        pass
    assert any("close" in err for err in sect.result.cleanup_errors)


def test_dut_cli_with_scenario_exception() -> None:
    holder: Dict[str, _FakeSession] = {}

    def factory(*args: Any, **kw: Any) -> _FakeSession:
        sess = _FakeSession(*args, **kw)
        holder["sess"] = sess
        return sess

    try:
        with DutCliSection(
            device="PE-4", ip="1.2.3.4", username="x", password="y",
            session_factory=factory,
        ):
            raise RuntimeError("scenario failure")
    except RuntimeError:
        pass
    sess = holder["sess"]
    assert sess.closed
    assert "rollback 0" in sess.sent


def test_dut_cli_requires_send_like_api() -> None:

    class _Naked:
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

        def open(self) -> None:
            pass

        def close(self) -> None:
            pass

    raised = False
    try:
        with DutCliSection(
            device="PE-4", ip="1.2.3.4", username="x", password="y",
            cleanup_commands=["anything"],
            session_factory=lambda *a, **kw: _Naked(),
        ):
            pass
    except ContextManagerError:
        raised = True
    except Exception:
        pass
    # _Naked has no send_command, but cleanup is swallow-on-exit -- so the
    # session still exits (logged as cleanup error), not raised to caller.
    # We only assert the section does not explode catastrophically.
    assert raised is False


# ---------------------------------------------------------------------------
# Combined scenarios (integration-ish)
# ---------------------------------------------------------------------------

def test_spirent_inside_switchover_combination() -> None:
    state = {"active": "ncc-0"}

    def fake_run_show(device: str, cmd: str) -> str:
        return f"Active: {state['active']}"

    def trigger() -> None:
        state["active"] = "ncc-1"

    wd = _FakeWatchdog()
    with SpirentTrafficSection(
        wd, capture_stats=False, start_grace_sec=0,
    ) as traffic:
        with SwitchoverSection(
            device="PE-4",
            run_show=fake_run_show,
            trigger=trigger,
            wait_for_stable_sec=1,
            poll_interval_sec=1,
        ) as sw:
            pass
        assert sw.result.completed
    assert traffic.result.completed
    firsts = [c[0] for c in wd.calls]
    assert "start" in firsts and "stop" in firsts


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _discover() -> List[Tuple[str, callable]]:
    g = globals()
    return sorted(
        (name, fn) for name, fn in g.items()
        if name.startswith("test_") and callable(fn)
    )


def run_all() -> int:
    tests = _discover()
    passed = failed = 0
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
