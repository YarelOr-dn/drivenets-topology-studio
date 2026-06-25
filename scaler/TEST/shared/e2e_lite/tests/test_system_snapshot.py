#!/usr/bin/env python3
"""Synthetic tests for system_snapshot.py expected-changes DSL.

Run with:
    cd scaler/TEST/shared
    python3 -m e2e_lite.tests.test_system_snapshot
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import List, Tuple

_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from e2e_lite.system_snapshot import (  # noqa: E402
    DiffEntry,
    ExpectedChangeError,
    SnapshotDiff,
    SystemSnapshot,
    SystemSnapshotter,
    diff_snapshots,
    parse_rule,
)


def _make_snap(device: str, label: str, metrics: dict) -> SystemSnapshot:
    return SystemSnapshot(
        device=device, label=label, timestamp="t", metrics=dict(metrics),
    )


# ---------------------------------------------------------------------------
# DSL parser
# ---------------------------------------------------------------------------

def test_parse_rule_forbidden() -> None:
    r = parse_rule("FORBIDDEN")
    ok, _ = r(1, 1)
    assert ok
    ok, _ = r(1, 2)
    assert not ok


def test_parse_rule_allowed() -> None:
    r = parse_rule("ALLOWED")
    ok, _ = r(1, 100)
    assert ok


def test_parse_rule_unchanged() -> None:
    r = parse_rule("UNCHANGED")
    assert r("hi", "hi")[0]
    assert not r("hi", "bye")[0]


def test_parse_rule_increase_by_default_is_1() -> None:
    r = parse_rule("INCREASE_BY")
    ok, _ = r(5, 6)
    assert ok
    ok, _ = r(5, 7)
    assert not ok


def test_parse_rule_increase_by_n() -> None:
    r = parse_rule("INCREASE_BY(3)")
    ok, _ = r(10, 13)
    assert ok
    ok, _ = r(10, 15)
    assert not ok


def test_parse_rule_increase_by_at_most() -> None:
    r = parse_rule("INCREASE_BY_AT_MOST(2)")
    assert r(10, 10)[0]
    assert r(10, 12)[0]
    assert not r(10, 13)[0]
    assert not r(10, 9)[0]


def test_parse_rule_increase_by_at_least() -> None:
    r = parse_rule("INCREASE_BY_AT_LEAST(2)")
    assert r(10, 12)[0]
    assert r(10, 100)[0]
    assert not r(10, 11)[0]


def test_parse_rule_exactly() -> None:
    r = parse_rule("EXACTLY(42)")
    assert r(99, 42)[0]
    assert not r(99, 43)[0]
    r2 = parse_rule("EXACTLY(running)")
    assert r2("stopped", "running")[0]


def test_parse_rule_invalid_raises() -> None:
    try:
        parse_rule("BOGUS_OP(1)")
    except ExpectedChangeError:
        return
    raise AssertionError("expected ExpectedChangeError")


# ---------------------------------------------------------------------------
# Diff logic
# ---------------------------------------------------------------------------

def test_diff_all_declared_rules_pass() -> None:
    before = _make_snap("PE-4", "before", {
        "process_restart:routing:bgpd": 0,
        "new_core_dumps": 0,
        "interface_flap:bundle-100.219": 7,
    })
    after = _make_snap("PE-4", "after", {
        "process_restart:routing:bgpd": 1,
        "new_core_dumps": 0,
        "interface_flap:bundle-100.219": 7,
    })
    diff = diff_snapshots(before, after, expected={
        "process_restart:routing:bgpd": "INCREASE_BY(1)",
        "new_core_dumps": "FORBIDDEN",
        "interface_flap:bundle-100.219": "UNCHANGED",
    })
    assert diff.ok, diff.summary()


def test_diff_flags_unexpected_change() -> None:
    before = _make_snap("PE-4", "before", {
        "process_restart:routing:bgpd": 0,
        "alarm:link_down": 0,
    })
    after = _make_snap("PE-4", "after", {
        "process_restart:routing:bgpd": 1,
        "alarm:link_down": 1,   # a new alarm appeared but no rule declared
    })
    diff = diff_snapshots(before, after, expected={
        "process_restart:routing:bgpd": "INCREASE_BY(1)",
    })
    assert not diff.ok
    assert any(u.key == "alarm:link_down" for u in diff.unexpected_changes), \
        diff.summary()


def test_diff_forbidden_rule_detects_unexpected_new_core() -> None:
    before = _make_snap("PE-4", "before", {"new_core_dumps": 0})
    after = _make_snap("PE-4", "after", {"new_core_dumps": 1})
    diff = diff_snapshots(before, after, expected={
        "new_core_dumps": "FORBIDDEN",
    })
    assert not diff.ok
    e = [e for e in diff.entries if e.key == "new_core_dumps"][0]
    assert not e.ok


def test_diff_ignore_keys_suppresses_unexpected() -> None:
    before = _make_snap("PE-4", "before", {"cpu_pct:bgpd": 20.0})
    after = _make_snap("PE-4", "after", {"cpu_pct:bgpd": 40.0})
    sampler = SystemSnapshotter(device="PE-4", run_show=lambda *_a, **_k: "")
    diff = sampler.diff(before, after, expected={}, ignore_keys=["cpu_pct:"])
    assert diff.ok, diff.summary()


def test_diff_missing_after_value_treated_as_0_for_integer_rules() -> None:
    before = _make_snap("PE-4", "before", {"process_restart:bgpd": 5})
    after = _make_snap("PE-4", "after", {})  # key absent -> 0
    # INCREASE_BY(0) would pass only if delta == 0, but here delta = -5.
    diff = diff_snapshots(before, after, expected={
        "process_restart:bgpd": "INCREASE_BY(0)",
    })
    assert not diff.ok


def test_diff_allows_noop_when_metric_vanishes_from_zero() -> None:
    # A metric that was 0 and disappears should NOT count as an unexpected change.
    before = _make_snap("PE-4", "before", {"counter:x": 0})
    after = _make_snap("PE-4", "after", {})
    diff = diff_snapshots(before, after, expected={})
    assert diff.ok, diff.summary()


# ---------------------------------------------------------------------------
# Sampler (with fake run_show)
# ---------------------------------------------------------------------------

def test_sampler_captures_process_restarts_and_alarms() -> None:
    outputs = {
        "show system process routing:bgpd | no-more":
            "Process routing:bgpd is running. PID: 1234. Restarts: 2",
        "show system containers | no-more":
            "name                     state    restarts\n"
            "ncc/0/routing_engine     running  3\n"
            "ncc/1/routing_engine     running  0\n",
        "show system alarms | no-more":
            "Alarm Name       Severity   Timestamp\n"
            "-----\n"
            "Link Down ge100-0/0/1 critical 2026-04-19T10:00:00\n",
        "show system core-dumps | no-more":
            "bgpd.core.12345 2026-04-01 00:00:00\n",
        "show system | include core":
            "",
        "show interfaces bundle-100.219 | no-more":
            "Interface bundle-100.219\n  Link transitions: 7\n",
    }

    def fake_run_show(device: str, cmd: str) -> str:
        return outputs.get(cmd, "")

    sampler = SystemSnapshotter(
        device="PE-4",
        run_show=fake_run_show,
        processes=["routing:bgpd"],
        containers=["ncc/0/routing_engine"],
        interfaces=["bundle-100.219"],
    )
    snap = sampler.capture("before")

    assert snap.metrics["process_state:routing:bgpd"] == "running"
    assert snap.metrics["process_restart:routing:bgpd"] == 2
    assert snap.metrics["container_restart:ncc/0/routing_engine"] == 3
    assert snap.metrics["core_dumps"] == 1
    assert snap.metrics["interface_flap:bundle-100.219"] == 7
    # Alarm row was captured
    assert any(k.startswith("alarm:") for k in snap.metrics)


def test_full_flow_with_expected_ha_switchover() -> None:
    """SC08 ncc_switchover mimic: bgpd restarts once, container restarts once,
    a link flap happens on 100.219, core dumps must stay 0."""
    before_metrics = {
        "process_state:routing:bgpd": "running",
        "process_restart:routing:bgpd": 1,
        "container_restart:ncc/0/routing_engine": 0,
        "interface_flap:bundle-100.219": 2,
        "core_dumps": 0,
    }
    after_metrics = {
        "process_state:routing:bgpd": "running",
        "process_restart:routing:bgpd": 2,  # +1
        "container_restart:ncc/0/routing_engine": 1,  # +1
        "interface_flap:bundle-100.219": 3,  # +1 (we allowed it)
        "core_dumps": 0,
    }
    before = _make_snap("PE-4", "before_sc08", before_metrics)
    after = _make_snap("PE-4", "after_sc08", after_metrics)
    diff = diff_snapshots(before, after, expected={
        "process_state:routing:bgpd": "UNCHANGED",
        "process_restart:routing:bgpd": "INCREASE_BY(1)",
        "container_restart:ncc/0/routing_engine": "INCREASE_BY(1)",
        "interface_flap:bundle-100.219": "ALLOWED",
        "core_dumps": "FORBIDDEN",
    })
    assert diff.ok, diff.summary()


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
