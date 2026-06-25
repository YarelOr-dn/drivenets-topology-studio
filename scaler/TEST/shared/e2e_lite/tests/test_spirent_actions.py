#!/usr/bin/env python3
"""Synthetic tests for spirent_actions.py.

No real Spirent Lab Server required: tests substitute a fake
``SpirentWatchdog.guarded_run`` (and/or ``_run_direct`` monkeypatch) and
verify pre/post validations, argv construction, and recoverable-error
propagation end to end.

Run with:
    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_spirent_actions
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite import spirent_actions as sa  # noqa: E402
from e2e_lite.base_action import RecoverableError  # noqa: E402
from e2e_lite.spirent_watchdog import SpirentCmdResult  # noqa: E402


# ---------------------------------------------------------------------------
# Fake watchdog (captures argv, returns scripted results)
# ---------------------------------------------------------------------------

class FakeWatchdog:
    """Stand-in for SpirentWatchdog that records calls and returns canned results."""

    def __init__(self, responder: Callable[[List[str]], SpirentCmdResult]) -> None:
        self.responder = responder
        self.calls: List[List[str]] = []

    def guarded_run(self, argv, timeout: int = 120) -> SpirentCmdResult:
        self.calls.append(list(argv))
        return self.responder(list(argv))


def _ok(stdout: str = "", stderr: str = "") -> SpirentCmdResult:
    return SpirentCmdResult(
        rc=0, stdout=stdout, stderr=stderr,
        attempts=1, healed=False,
    )


def _fail(stdout: str = "", stderr: str = "", rc: int = 1) -> SpirentCmdResult:
    return SpirentCmdResult(
        rc=rc, stdout=stdout, stderr=stderr,
        attempts=1, healed=False,
    )


def _status_payload(
    *,
    reserved: bool = True,
    streams: List[str] | None = None,
    devices: List[str] | None = None,
    traffic_state: str = "STOPPED",
) -> str:
    streams = streams or []
    devices = devices or []
    return json.dumps({
        "port": {"reserved": reserved, "chassis_ip": "10.0.0.1", "slot": 1, "port": 1},
        "streams": [{"name": n} for n in streams],
        "devices": [{"name": d} for d in devices],
        "traffic": {"state": traffic_state},
    })


def _stats_payload(tx_pps: int = 0, tx_bps: int = 0) -> str:
    return json.dumps({
        "port": {"tx_pps": tx_pps, "tx_bps": tx_bps},
    })


def _bgp_payload(states: List[str]) -> str:
    return json.dumps({"peers": [{"state": s} for s in states]})


def _build_responder(
    *,
    status_streams: List[str] | None = None,
    status_devices: List[str] | None = None,
    traffic_state: str = "STOPPED",
    create_stream_new_name: str | None = None,
    tx_pps_after_start: int = 100,
    bgp_states_after_connect: List[str] | None = None,
    scenario: str = "",
):
    """Build a responder that simulates a fresh session and tracks state changes."""
    streams = list(status_streams or [])
    devices = list(status_devices or [])
    traffic = [traffic_state]
    bgp_after = list(bgp_states_after_connect or ["ESTABLISHED"])
    state: Dict[str, Any] = {"started": False, "bgp_configured": False}

    def responder(argv: List[str]) -> SpirentCmdResult:
        cmd = argv[0] if argv else ""
        if cmd == "status":
            return _ok(_status_payload(
                reserved=True,
                streams=streams,
                devices=devices,
                traffic_state=traffic[0],
            ))
        if cmd == "stats":
            if state["started"]:
                return _ok(_stats_payload(tx_pps=tx_pps_after_start, tx_bps=1_000_000))
            return _ok(_stats_payload(tx_pps=0, tx_bps=0))
        if cmd == "bgp-status":
            if state["bgp_configured"]:
                return _ok(_bgp_payload(bgp_after))
            return _ok(_bgp_payload(["IDLE"]))
        if cmd == "create-stream":
            name = None
            for i, a in enumerate(argv):
                if a == "--name" and i + 1 < len(argv):
                    name = argv[i + 1]
                    break
            if name:
                streams.append(name)
            return _ok(stdout=f"Stream {name} created\n")
        if cmd == "create-device":
            name = None
            for i, a in enumerate(argv):
                if a == "--name" and i + 1 < len(argv):
                    name = argv[i + 1]
                    break
            if name:
                devices.append(name)
            return _ok(stdout=f"Device {name} created\n")
        if cmd == "start":
            state["started"] = True
            traffic[0] = "RUNNING"
            return _ok()
        if cmd == "stop":
            state["started"] = False
            traffic[0] = "STOPPED"
            return _ok()
        if cmd == "bgp-peer":
            state["bgp_configured"] = True
            return _ok()
        if cmd == "ecmp":
            state["bgp_configured"] = True
            return _ok()
        return _ok()

    return responder


# ---------------------------------------------------------------------------
# CreateStreamAction
# ---------------------------------------------------------------------------

def test_create_stream_argv_minimal() -> None:
    action = sa.CreateStreamAction(
        stream_name="s1",
        vlan=100,
        src_mac="00:11:22:33:44:55",
        dst_mac="00:AA:BB:CC:DD:EE",
        rate_mbps=5,
    )
    argv = action._build_argv()
    assert argv[0] == "create-stream"
    assert "--name" in argv and argv[argv.index("--name") + 1] == "s1"
    assert "--vlan" in argv and argv[argv.index("--vlan") + 1] == "100"
    assert "--rate-mbps" in argv and argv[argv.index("--rate-mbps") + 1] == "5"


def test_create_stream_requires_name() -> None:
    try:
        sa.CreateStreamAction(stream_name="")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_create_stream_end_to_end_pre_post_validations_pass() -> None:
    wd = FakeWatchdog(_build_responder(status_streams=[]))
    action = sa.CreateStreamAction(
        stream_name="s1", vlan=100, rate_mbps=1,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    out = action.execute()
    assert out["returncode"] == 0
    # Expect: status (pre), create-stream (exec), status (post)
    cmds = [c[0] for c in wd.calls]
    assert cmds.count("status") >= 2
    assert "create-stream" in cmds
    rec = action.last_record
    assert rec is not None
    assert all(v["status"] == "passed" for v in rec.pre_validations)
    assert all(v["status"] == "passed" for v in rec.post_validations)


def test_create_stream_post_validation_fails_when_stream_absent() -> None:
    # Responder never actually adds the stream to status
    def responder(argv: List[str]) -> SpirentCmdResult:
        if argv[0] == "status":
            return _ok(_status_payload(reserved=True, streams=[]))
        if argv[0] == "create-stream":
            return _ok(stdout="pretended to create but didn't persist\n")
        return _ok()

    wd = FakeWatchdog(responder)
    action = sa.CreateStreamAction(
        stream_name="ghost", vlan=10,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    try:
        action.execute()
    except AssertionError:
        pass  # base_action raises AssertionError on validation failure
    except Exception:
        pass
    rec = action.last_record
    assert rec is not None
    post_statuses = [v["status"] for v in rec.post_validations]
    assert "failed" in post_statuses


# ---------------------------------------------------------------------------
# StartTrafficAction
# ---------------------------------------------------------------------------

def test_start_traffic_pre_requires_stream_when_named() -> None:
    wd = FakeWatchdog(_build_responder(status_streams=["foo"]))
    action = sa.StartTrafficAction(
        stream_name="foo", min_tx_pps=1, wait_tx_sec=3,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    out = action.execute()
    assert out["returncode"] == 0
    cmds = [c[0] for c in wd.calls]
    assert "start" in cmds
    assert "stats" in cmds
    rec = action.last_record
    assert rec is not None
    # TX rate post-validation should have passed because responder sets
    # tx_pps=100 after "start"
    assert any(
        v["name"] == "tx_rate_above_zero" and v["status"] == "passed"
        for v in rec.post_validations
    )


def test_start_traffic_post_validation_fails_when_tx_zero() -> None:
    def responder(argv: List[str]) -> SpirentCmdResult:
        if argv[0] == "status":
            return _ok(_status_payload(reserved=True, streams=["foo"]))
        if argv[0] == "start":
            return _ok()
        if argv[0] == "stats":
            return _ok(_stats_payload(tx_pps=0, tx_bps=0))
        return _ok()

    wd = FakeWatchdog(responder)
    action = sa.StartTrafficAction(
        stream_name="foo", min_tx_pps=1, wait_tx_sec=1,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    try:
        action.execute()
    except Exception:
        pass
    rec = action.last_record
    assert rec is not None
    assert any(
        v["name"] == "tx_rate_above_zero" and v["status"] == "failed"
        for v in rec.post_validations
    )


# ---------------------------------------------------------------------------
# StopTrafficAction
# ---------------------------------------------------------------------------

def test_stop_traffic_pre_fails_when_not_running() -> None:
    def responder(argv: List[str]) -> SpirentCmdResult:
        if argv[0] == "status":
            return _ok(_status_payload(reserved=True, traffic_state="STOPPED"))
        return _ok()

    wd = FakeWatchdog(responder)
    action = sa.StopTrafficAction(watchdog=wd, spirent_tool="/fake/spirent_tool.py")
    try:
        action.execute()
    except Exception:
        pass
    rec = action.last_record
    assert rec is not None
    assert any(v["status"] == "failed" for v in rec.pre_validations)
    # "stop" should NOT have been called because pre-validation gated it
    cmds = [c[0] for c in wd.calls]
    assert "stop" not in cmds


# ---------------------------------------------------------------------------
# BgpPeerAction
# ---------------------------------------------------------------------------

def test_bgp_peer_argv_and_establishment() -> None:
    wd = FakeWatchdog(_build_responder(
        status_devices=["dev1"],
        bgp_states_after_connect=["ESTABLISHED"],
    ))
    action = sa.BgpPeerAction(
        device_name="dev1", as_num=65001, dut_as=65002,
        neighbor="10.0.0.1", hold_timer=180,
        negotiate_afi="l2vpn-evpn",
        wait_established_sec=5,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    out = action.execute()
    assert out["returncode"] == 0
    argv_call = next(c for c in wd.calls if c and c[0] == "bgp-peer")
    assert "--as" in argv_call and argv_call[argv_call.index("--as") + 1] == "65001"
    assert "--dut-as" in argv_call
    assert "--negotiate-afi" in argv_call
    rec = action.last_record
    assert rec is not None
    assert any(
        v["name"].startswith("bgp_established") and v["status"] == "passed"
        for v in rec.post_validations
    )


def test_bgp_peer_pre_fails_when_device_missing() -> None:
    wd = FakeWatchdog(_build_responder(status_devices=[]))  # no devices!
    action = sa.BgpPeerAction(
        device_name="missing", as_num=1, dut_as=2,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    try:
        action.execute()
    except Exception:
        pass
    rec = action.last_record
    assert rec is not None
    assert any(
        v["name"].startswith("device_exists") and v["status"] == "failed"
        for v in rec.pre_validations
    )


# ---------------------------------------------------------------------------
# EcmpBlockAction
# ---------------------------------------------------------------------------

def test_ecmp_block_argv_and_min_established_default() -> None:
    wd = FakeWatchdog(_build_responder(
        bgp_states_after_connect=["ESTABLISHED"] * 4,
    ))
    action = sa.EcmpBlockAction(
        count=4, vlan=200, base_ip="10.1.0.1", as_num=100, dut_as=200,
        wait_established_sec=3,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    out = action.execute()
    assert out["returncode"] == 0
    argv_call = next(c for c in wd.calls if c and c[0] == "ecmp")
    assert "--count" in argv_call and argv_call[argv_call.index("--count") + 1] == "4"
    assert action.min_established == 4


def test_ecmp_block_rejects_zero_count() -> None:
    try:
        sa.EcmpBlockAction(count=0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# ---------------------------------------------------------------------------
# CreateMacBlockAction
# ---------------------------------------------------------------------------

def test_create_mac_block_argv_qinq() -> None:
    wd = FakeWatchdog(_build_responder(status_devices=[]))
    action = sa.CreateMacBlockAction(
        device_name="evpn_ac_v219", vlan=219, count=10,
        outer_vlan=100,  # triggers qinq branch
        base_mac="00:DE:AD:00:01:01",
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    argv = action._build_argv()
    assert "--vlan" in argv and argv[argv.index("--vlan") + 1] == "100"
    assert "--inner-vlan" in argv and argv[argv.index("--inner-vlan") + 1] == "219"
    assert "--device-count" in argv and argv[argv.index("--device-count") + 1] == "10"
    assert "--mac-step" in argv
    assert "--no-qinq" not in argv   # outer_vlan set -> qinq ON


def test_create_mac_block_argv_no_qinq() -> None:
    action = sa.CreateMacBlockAction(
        device_name="simple", vlan=500, count=1, no_qinq=True,
    )
    argv = action._build_argv()
    assert "--no-qinq" in argv
    assert argv[argv.index("--vlan") + 1] == "500"


def test_create_mac_block_end_to_end() -> None:
    wd = FakeWatchdog(_build_responder(status_devices=[]))
    action = sa.CreateMacBlockAction(
        device_name="evpn_ac_v42", vlan=42, count=5,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    out = action.execute()
    assert out["returncode"] == 0
    rec = action.last_record
    assert rec is not None
    assert all(v["status"] == "passed" for v in rec.post_validations), rec.post_validations


# ---------------------------------------------------------------------------
# RecoverableError classification
# ---------------------------------------------------------------------------

def test_recoverable_failure_is_classified_and_raised() -> None:
    def responder(argv: List[str]) -> SpirentCmdResult:
        if argv[0] == "status":
            return _ok(_status_payload(reserved=True))
        if argv[0] == "create-stream":
            return _fail(
                stdout="",
                stderr="Error: Session_NOT_FOUND or connection refused (Lab Server)",
            )
        return _ok()

    wd = FakeWatchdog(responder)
    action = sa.CreateStreamAction(
        stream_name="s", vlan=1,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    try:
        action.execute()
    except RecoverableError:
        pass
    else:
        raise AssertionError("expected RecoverableError")
    rec = action.last_record
    assert rec is not None
    assert rec.recoverable is True


def test_non_recoverable_failure_raises_runtime_error() -> None:
    def responder(argv: List[str]) -> SpirentCmdResult:
        if argv[0] == "status":
            return _ok(_status_payload(reserved=True))
        if argv[0] == "create-stream":
            return _fail(stderr="Error: invalid argument --foobar")
        return _ok()

    wd = FakeWatchdog(responder)
    action = sa.CreateStreamAction(
        stream_name="s", vlan=1,
        watchdog=wd, spirent_tool="/fake/spirent_tool.py",
    )
    try:
        action.execute()
    except RuntimeError as exc:
        assert "create-stream" in str(exc)
    except RecoverableError:
        raise AssertionError(
            "must NOT be classified as recoverable for plain CLI arg errors"
        )
    else:
        raise AssertionError("expected RuntimeError")


# ---------------------------------------------------------------------------
# default_spirent_tool_path + spirent_status_json smoke
# ---------------------------------------------------------------------------

def test_default_spirent_tool_path_returns_string() -> None:
    p = sa.default_spirent_tool_path()
    assert isinstance(p, str) and p.endswith("spirent_tool.py")


def test_spirent_status_json_with_watchdog() -> None:
    wd = FakeWatchdog(_build_responder(
        status_streams=["a", "b"], status_devices=["d1"],
    ))
    status = sa.spirent_status_json(watchdog=wd)
    assert status["port"]["reserved"] is True
    assert {s["name"] for s in status["streams"]} == {"a", "b"}


def test_spirent_status_json_error_path() -> None:
    def bad(_argv: List[str]) -> SpirentCmdResult:
        return _fail(stderr="boom")
    wd = FakeWatchdog(bad)
    status = sa.spirent_status_json(watchdog=wd)
    assert "_error" in status


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _discover() -> List[tuple]:
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
