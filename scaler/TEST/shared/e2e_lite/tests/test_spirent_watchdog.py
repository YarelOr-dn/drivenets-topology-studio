#!/usr/bin/env python3
"""Synthetic tests for spirent_watchdog. Run with:

    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_spirent_watchdog

subprocess.run is monkey-patched so no real Spirent is contacted.
"""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite import (  # noqa: E402
    RecoveryEvent,
    RecoveryFsmLite,
    RecoveryGuards,
    RecoveryState,
    SpirentUnrecoverableError,
    SpirentWatchdog,
    WATCHDOG_STATE_PATH,
)
from e2e_lite import recovery_fsm_lite as fsm_module  # noqa: E402
from e2e_lite import spirent_watchdog as sw_module  # noqa: E402


# ---------------------------------------------------------------------------
# Fake subprocess harness
# ---------------------------------------------------------------------------

@dataclass
class _FakeCompleted:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class _SubprocessStub:
    """Records calls and returns scripted responses."""

    def __init__(self) -> None:
        self.calls: List[List[str]] = []
        # List of responses to return; consumed in order.
        self.responses: List[_FakeCompleted] = []

    def run(self, cmd, **kwargs):  # noqa: ARG002
        self.calls.append(list(cmd))
        if not self.responses:
            return _FakeCompleted(returncode=0, stdout="{}", stderr="")
        return self.responses.pop(0)


def _install_stub() -> _SubprocessStub:
    stub = _SubprocessStub()
    sw_module.subprocess.run = stub.run  # type: ignore[assignment]
    fsm_module.subprocess.run = stub.run  # type: ignore[assignment]
    return stub


# Reset subprocess references between tests so a test doesn't pollute others.
_ORIG_SW_RUN = sw_module.subprocess.run
_ORIG_FSM_RUN = fsm_module.subprocess.run


def _restore_stub() -> None:
    sw_module.subprocess.run = _ORIG_SW_RUN  # type: ignore[assignment]
    fsm_module.subprocess.run = _ORIG_FSM_RUN  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _fake_tool_path(tmp_dir: Path) -> Path:
    p = tmp_dir / "spirent_tool.py"
    p.write_text("# fake\n")
    return p


def _fsm() -> RecoveryFsmLite:
    return RecoveryFsmLite(guards=RecoveryGuards(
        max_spirent_reconnects=2,
        max_heavy_ops_per_session=1,
        spirent_backoff_sec=0,
    ))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_probe_healthy() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            stub.responses = [_FakeCompleted(returncode=0, stdout=json.dumps({
                "session": {"active": True, "port_reserved": True}
            }))]
            wd = SpirentWatchdog(fsm=_fsm(), tool_path=tool, probe_ttl_s=0.1)
            h = wd.probe(force=True)
            assert h.healthy, h
            assert h.active
            assert h.port_reserved
        finally:
            _restore_stub()


def test_probe_dead() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            stub.responses = [_FakeCompleted(returncode=1, stdout="", stderr="No active session")]
            wd = SpirentWatchdog(fsm=_fsm(), tool_path=tool, probe_ttl_s=0.1)
            h = wd.probe(force=True)
            assert not h.healthy
        finally:
            _restore_stub()


def test_guarded_run_ok_first_try() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            # precheck probe -> healthy, then actual create-stream -> ok
            stub.responses = [
                _FakeCompleted(0, json.dumps({"session": {"active": True, "port_reserved": True}})),
                _FakeCompleted(0, "stream created"),
            ]
            wd = SpirentWatchdog(fsm=_fsm(), tool_path=tool, max_retries=1)
            result = wd.guarded_run(["create-stream", "--name", "test"])
            assert result.ok
            assert result.attempts == 1
        finally:
            _restore_stub()


def test_guarded_run_recovers_after_dead_session() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            # Sequence:
            #  1. precheck probe -> healthy (so we try)
            #  2. create-stream fails with "No active session"
            #  3. FSM healer: default_spirent_reconnect_healer -> connect -> success
            #  4. FSM healer: default_spirent_reconnect_healer -> reserve -> success
            #  5. force probe after heal -> healthy
            #  6. retry create-stream -> ok
            stub.responses = [
                _FakeCompleted(0, json.dumps({"session": {"active": True, "port_reserved": True}})),
                _FakeCompleted(1, "", "No active session (stale handles)"),
                _FakeCompleted(0, "connected"),
                _FakeCompleted(0, "reserved"),
                _FakeCompleted(0, json.dumps({"session": {"active": True, "port_reserved": True}})),
                _FakeCompleted(0, "stream created"),
            ]
            wd = SpirentWatchdog(fsm=_fsm(), tool_path=tool, max_retries=3)
            result = wd.guarded_run(["create-stream", "--name", "test"])
            assert result.ok, (result.rc, result.combined)
            assert result.attempts >= 2
            assert result.healed
            # FSM should be STABLE
            assert wd.fsm.state == RecoveryState.STABLE
        finally:
            _restore_stub()


def test_guarded_run_unrecoverable_when_reconnect_fails() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            # 1. probe -> healthy
            # 2. create-stream -> dead
            # 3..: FSM healing chain, every attempt fails with non-zero rc
            stub.responses = [
                _FakeCompleted(0, json.dumps({"session": {"active": True, "port_reserved": True}}))
            ] + [_FakeCompleted(1, "", "No active session")] * 20
            wd = SpirentWatchdog(
                fsm=_fsm(),
                tool_path=tool,
                max_retries=2,
            )
            raised = False
            try:
                wd.guarded_run(["create-stream", "--name", "x"], raise_on_error=True)
            except SpirentUnrecoverableError:
                raised = True
            assert raised
        finally:
            _restore_stub()


def test_watchdog_state_persists() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            stub.responses = [_FakeCompleted(0, json.dumps({"session": {"active": True, "port_reserved": True}}))]
            wd = SpirentWatchdog(fsm=_fsm(), tool_path=tool)
            wd.probe(force=True)
            data = json.loads(WATCHDOG_STATE_PATH.read_text())
            assert data["state"] in ("healthy", "idle")
            assert "fsm_state" in data
            assert data["port_reserved"] is True
        finally:
            _restore_stub()


def test_read_watchdog_state() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tool = _fake_tool_path(Path(td))
        stub = _install_stub()
        try:
            stub.responses = [_FakeCompleted(0, json.dumps({"session": {"active": True, "port_reserved": True}}))]
            wd = SpirentWatchdog(fsm=_fsm(), tool_path=tool)
            wd.probe(force=True)
            state = sw_module.read_watchdog_state()
            assert state is not None
            assert "fsm_state" in state
        finally:
            _restore_stub()


def _run_all() -> int:
    tests = [
        test_probe_healthy,
        test_probe_dead,
        test_guarded_run_ok_first_try,
        test_guarded_run_recovers_after_dead_session,
        test_guarded_run_unrecoverable_when_reconnect_fails,
        test_watchdog_state_persists,
        test_read_watchdog_state,
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
