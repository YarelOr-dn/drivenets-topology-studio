#!/usr/bin/env python3
"""Synthetic tests for core_dump_registry.py (Phase 3.2).

Run with:
    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_core_dump_registry
"""
from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.core_dump_registry import (  # noqa: E402
    CORE_DUMP_REGISTRY_STATE_PATH,
    CoreDumpEvent,
    CoreDumpRegistryError,
    CoreDumpRegistrySummary,
    CoreDumpSessionRegistry,
    default_core_dump_commands,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

class _Fleet:
    """Mutable map device -> current dump listing used by _run_show."""

    def __init__(self, initial: Optional[Dict[str, List[str]]] = None) -> None:
        self.state: Dict[str, List[str]] = dict(initial or {})
        self.lock = threading.RLock()

    def set(self, device: str, lines: List[str]) -> None:
        with self.lock:
            self.state[device] = list(lines)

    def append(self, device: str, line: str) -> None:
        with self.lock:
            self.state.setdefault(device, []).append(line)

    def run_show(self, device: str, cmd: str) -> str:
        with self.lock:
            lines = list(self.state.get(device, []))
        if cmd == "show system core-dumps | no-more":
            return "\n".join(lines) if lines else ""
        if cmd == "show system | include core":
            return ""
        return ""


def _tmp_state_path(tmp_name: str) -> Path:
    here = Path(__file__).resolve().parent
    p = here / f"_tmp_cdr_{tmp_name}.json"
    if p.exists():
        p.unlink()
    return p


# ---------------------------------------------------------------------------
# Baseline and sampling
# ---------------------------------------------------------------------------

def test_requires_devices() -> None:
    raised = False
    try:
        CoreDumpSessionRegistry(devices=[])
    except CoreDumpRegistryError:
        raised = True
    assert raised


def test_baseline_captures_existing_dumps() -> None:
    fleet = _Fleet({"PE-4": ["bgpd.core.111 2026-04-01"]})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("baseline"),
    )
    reg.capture_baseline()
    snap = reg.snapshot("PE-4")
    assert snap["baseline"] == ["bgpd.core.111 2026-04-01"]
    assert snap["observed"] == snap["baseline"]
    assert snap["new_count"] == 0


def test_start_captures_baseline_implicitly() -> None:
    fleet = _Fleet({"PE-4": ["bgpd.core.111 2026-04-01"]})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        poll_interval_sec=60,  # won't fire during the test
        state_path=_tmp_state_path("start_implicit"),
    )
    try:
        reg.start()
        assert reg.snapshot("PE-4")["baseline"] == [
            "bgpd.core.111 2026-04-01"
        ]
    finally:
        reg.stop()


def test_new_dump_detected_on_poll_once() -> None:
    fleet = _Fleet({"PE-4": ["bgpd.core.111"]})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("poll_once"),
    )
    reg.capture_baseline()
    fleet.append("PE-4", "bgpd.core.222 2026-04-19")
    new = reg.poll_once()
    assert new == 1
    events = reg.new_events("PE-4")
    assert len(events) == 1
    assert events[0].dump_line == "bgpd.core.222 2026-04-19"
    assert events[0].device == "PE-4"
    assert events[0].poll_index >= 1


def test_baseline_dumps_do_not_count_as_new() -> None:
    fleet = _Fleet({"PE-4": ["bgpd.core.a", "bgpd.core.b"]})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("baseline_suppress"),
    )
    reg.capture_baseline()
    reg.poll_once()
    reg.poll_once()
    assert reg.new_cores_total() == 0


def test_sampling_uses_default_commands() -> None:
    cmds = default_core_dump_commands()
    assert "show system core-dumps | no-more" in cmds


def test_sampling_dedupes_within_single_poll() -> None:
    calls: List[str] = []

    def run_show(device: str, cmd: str) -> str:
        calls.append(cmd)
        return "bgpd.core.dup 2026-04-19\nbgpd.core.dup 2026-04-19"

    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", run_show)],
        state_path=_tmp_state_path("dedupe"),
    )
    reg.capture_baseline()
    snap = reg.snapshot("PE-4")
    assert snap["baseline"] == ["bgpd.core.dup 2026-04-19"]


def test_marker_override() -> None:
    def run_show(device: str, cmd: str) -> str:
        return (
            "random stdout line\n"
            "custom_dump: /var/crash/1.xz\n"
        )

    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", run_show)],
        markers=("custom_dump",),
        state_path=_tmp_state_path("markers"),
    )
    reg.capture_baseline()
    snap = reg.snapshot("PE-4")
    assert snap["baseline"] == ["custom_dump: /var/crash/1.xz"]


def test_error_during_sample_is_recorded() -> None:
    class _Boom:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, device: str, cmd: str) -> str:
            self.calls += 1
            if self.calls > 2:  # let baseline succeed, poll fails
                raise RuntimeError("SSH dead")
            return ""

    run_show = _Boom()
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", run_show)],
        state_path=_tmp_state_path("sample_error"),
    )
    reg.capture_baseline()

    def failing_sample(device: str, _: Any) -> List[str]:
        raise RuntimeError("sample totally failed")

    reg._sample_one = failing_sample  # type: ignore[method-assign]
    reg.poll_once()
    snap = reg.snapshot("PE-4")
    assert "sample totally failed" in snap["last_poll_error"]
    assert snap["poll_count"] == 1


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------

def test_subscriber_called_on_new_dump() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("subscribers"),
    )
    reg.capture_baseline()
    events: List[CoreDumpEvent] = []
    reg.subscribe(events.append)
    fleet.append("PE-4", "bgpd.core.777")
    reg.poll_once()
    assert len(events) == 1
    assert events[0].device == "PE-4"
    assert events[0].dump_line == "bgpd.core.777"


def test_unsubscribe_stops_notifications() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("unsub"),
    )
    reg.capture_baseline()
    calls: List[CoreDumpEvent] = []
    reg.subscribe(calls.append)
    reg.unsubscribe(calls.append)
    fleet.append("PE-4", "bgpd.core.1")
    reg.poll_once()
    assert calls == []


def test_subscriber_exception_does_not_break_poll() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("sub_exc"),
    )
    reg.capture_baseline()

    def bad(_: CoreDumpEvent) -> None:
        raise RuntimeError("subscriber exploded")

    good_calls: List[CoreDumpEvent] = []
    reg.subscribe(bad)
    reg.subscribe(good_calls.append)
    fleet.append("PE-4", "bgpd.core.sub")
    reg.poll_once()
    assert len(good_calls) == 1


def test_subscriber_callable_required() -> None:
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", lambda d, c: "")],
        state_path=None,
    )
    raised = False
    try:
        reg.subscribe("not callable")  # type: ignore[arg-type]
    except CoreDumpRegistryError:
        raised = True
    assert raised


# ---------------------------------------------------------------------------
# Thread lifecycle
# ---------------------------------------------------------------------------

def test_start_stop_thread_cycle() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        poll_interval_sec=1.0,
        state_path=_tmp_state_path("thread_cycle"),
    )
    reg.start()
    assert reg._thread is not None
    assert reg._thread.is_alive()
    reg.stop(timeout_sec=5.0)
    assert reg._thread is None


def test_double_start_is_noop_by_default() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        poll_interval_sec=60,
        state_path=_tmp_state_path("double_start"),
    )
    try:
        reg.start()
        reg.start()  # must not raise by default
    finally:
        reg.stop()


def test_double_start_raises_when_flag_set() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        poll_interval_sec=60,
        raise_if_started_twice=True,
        state_path=_tmp_state_path("double_start_raise"),
    )
    try:
        reg.start()
        raised = False
        try:
            reg.start()
        except CoreDumpRegistryError:
            raised = True
        assert raised
    finally:
        reg.stop()


def test_context_manager_starts_and_stops() -> None:
    fleet = _Fleet({"PE-4": []})
    sp = _tmp_state_path("ctx")
    with CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        poll_interval_sec=60,
        state_path=sp,
    ) as reg:
        assert reg._thread is not None
    assert reg._thread is None


def test_background_thread_detects_dumps_over_time() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        poll_interval_sec=0.1,
        state_path=_tmp_state_path("bg_thread"),
    )
    reg.start()
    try:
        time.sleep(0.1)
        fleet.append("PE-4", "bgpd.core.bg1")
        time.sleep(0.5)
        fleet.append("PE-4", "bgpd.core.bg2")
        time.sleep(0.5)
    finally:
        reg.stop()
    events = reg.new_events("PE-4")
    assert any(e.dump_line == "bgpd.core.bg1" for e in events)
    assert any(e.dump_line == "bgpd.core.bg2" for e in events)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_state_file_is_written() -> None:
    fleet = _Fleet({"PE-4": ["bgpd.core.0"]})
    sp = _tmp_state_path("persist")
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=sp,
    )
    reg.capture_baseline()
    fleet.append("PE-4", "bgpd.core.new")
    reg.poll_once()
    assert sp.exists()
    data = json.loads(sp.read_text())
    assert data["new_cores_total"] == 1
    assert any(d["device"] == "PE-4" for d in data["devices"])
    sp.unlink()


def test_none_state_path_skips_persistence() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=None,
    )
    reg.capture_baseline()
    # No exception means success
    assert True


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_summary_ok_true_when_no_new() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("summary_ok"),
    )
    reg.capture_baseline()
    reg.poll_once()
    summary = reg.summary()
    assert isinstance(summary, CoreDumpRegistrySummary)
    assert summary.ok
    assert summary.new_cores_total == 0


def test_summary_ok_false_when_new() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=_tmp_state_path("summary_fail"),
    )
    reg.capture_baseline()
    fleet.append("PE-4", "bgpd.core.evil")
    reg.poll_once()
    summary = reg.summary()
    assert not summary.ok
    assert summary.new_cores_total == 1


# ---------------------------------------------------------------------------
# Multi-device
# ---------------------------------------------------------------------------

def test_multi_device_tracks_independently() -> None:
    fleet = _Fleet({"PE-4": ["bgpd.core.a"], "PE-1": []})
    reg = CoreDumpSessionRegistry(
        devices=[
            ("PE-4", fleet.run_show),
            ("PE-1", fleet.run_show),
        ],
        state_path=_tmp_state_path("multi"),
    )
    reg.capture_baseline()
    fleet.append("PE-1", "bgpd.core.new")
    reg.poll_once()
    assert reg.new_cores_total() == 1
    pe1_events = reg.new_events("PE-1")
    pe4_events = reg.new_events("PE-4")
    assert len(pe1_events) == 1
    assert len(pe4_events) == 0


def test_snapshot_unknown_device_raises() -> None:
    fleet = _Fleet({"PE-4": []})
    reg = CoreDumpSessionRegistry(
        devices=[("PE-4", fleet.run_show)],
        state_path=None,
    )
    reg.capture_baseline()
    raised = False
    try:
        reg.snapshot("UNKNOWN")
    except CoreDumpRegistryError:
        raised = True
    assert raised


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
