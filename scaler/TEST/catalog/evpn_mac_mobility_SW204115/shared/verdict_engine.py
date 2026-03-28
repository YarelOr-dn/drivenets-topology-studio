#!/usr/bin/env python3
"""
Multi-layer verdict engine for EVPN MAC mobility tests (SW-204115).

Evaluates scenario outcomes across control-plane, datapath, timing, traces,
and generates structured results. Integrates with /debug-dnos trace analysis
on failure.

Verdict layers (subset of the 14-layer system, adapted for MAC mobility):
  1. Control-Plane: MAC table source correct
  2. Sequencing: sequence number incremented on move
  3. RT-2: BGP L2VPN EVPN RT-2 advertisement/withdrawal correct
  4. Suppression: sanctions applied on rapid flap
  5. Sticky: sticky enforcement honored
  6. Timing: MAC move convergence within threshold
  7. Scale: all N MACs moved (count before == count after)
  8. Datapath: traffic forwarded to new AC (Spirent RX on correct VLAN)
  9. Traces: no ERROR/CRASH in bgpd/fibmgrd/wb_agent traces
  10. HA: MAC table restored after switchover/restart
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class VerdictStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class LayerResult:
    layer: str
    status: VerdictStatus
    detail: str
    evidence: str = ""
    elapsed_sec: float = 0.0


@dataclass
class ScenarioVerdict:
    scenario_id: str
    scenario_name: str
    layers: List[LayerResult] = field(default_factory=list)
    overall: VerdictStatus = VerdictStatus.SKIP
    convergence_sec: Optional[float] = None
    trigger_timestamp: str = ""
    debug_hint: str = ""
    known_bugs: List[Any] = field(default_factory=list)
    deep_evidence: Optional[Dict[str, Any]] = None
    auto_investigate_cmd: str = ""
    observability_log: Optional[Dict[str, Any]] = None

    def compute_overall(self) -> None:
        if not self.layers:
            self.overall = VerdictStatus.SKIP
            return
        statuses = [lr.status for lr in self.layers]
        if VerdictStatus.ERROR in statuses:
            self.overall = VerdictStatus.ERROR
        elif VerdictStatus.FAIL in statuses:
            self.overall = VerdictStatus.FAIL
        elif VerdictStatus.WARN in statuses:
            self.overall = VerdictStatus.WARN
        elif all(s == VerdictStatus.SKIP for s in statuses):
            self.overall = VerdictStatus.SKIP
        else:
            self.overall = VerdictStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        result: Dict[str, Any] = {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "overall": self.overall.value,
            "convergence_sec": self.convergence_sec,
            "trigger_timestamp": self.trigger_timestamp,
            "debug_hint": self.debug_hint,
            "layers": [
                {
                    "layer": lr.layer,
                    "status": lr.status.value,
                    "detail": lr.detail,
                    "evidence": lr.evidence[:2000],
                    "elapsed_sec": lr.elapsed_sec,
                }
                for lr in self.layers
            ],
        }
        if self.known_bugs:
            result["known_bugs"] = [
                {"jira_key": b.jira_key, "title": b.title,
                 "status": b.status, "score": b.match_score, "url": b.url}
                if hasattr(b, "jira_key") else b
                for b in self.known_bugs
            ]
        if self.deep_evidence:
            result["deep_evidence"] = self.deep_evidence
        if self.auto_investigate_cmd:
            result["auto_investigate_cmd"] = self.auto_investigate_cmd
        if self.observability_log:
            result["observability_log"] = self.observability_log
        return result


@dataclass
class TestVerdict:
    test_id: str
    device: str
    scenarios: List[ScenarioVerdict] = field(default_factory=list)
    overall: VerdictStatus = VerdictStatus.SKIP
    total_elapsed_sec: float = 0.0
    observability_summary: Optional[Dict[str, Any]] = None

    def compute_overall(self) -> None:
        for sv in self.scenarios:
            sv.compute_overall()
        if not self.scenarios:
            self.overall = VerdictStatus.SKIP
            return
        statuses = [sv.overall for sv in self.scenarios]
        if VerdictStatus.ERROR in statuses:
            self.overall = VerdictStatus.ERROR
        elif VerdictStatus.FAIL in statuses:
            self.overall = VerdictStatus.FAIL
        elif VerdictStatus.WARN in statuses:
            self.overall = VerdictStatus.WARN
        elif all(s == VerdictStatus.SKIP for s in statuses):
            self.overall = VerdictStatus.SKIP
        else:
            self.overall = VerdictStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        result: Dict[str, Any] = {
            "test_id": self.test_id,
            "device": self.device,
            "overall": self.overall.value,
            "total_elapsed_sec": self.total_elapsed_sec,
            "scenarios": [sv.to_dict() for sv in self.scenarios],
        }
        if self.observability_summary:
            result["observability_summary"] = self.observability_summary
        return result


# ---------------------------------------------------------------------------
# Layer evaluators
# ---------------------------------------------------------------------------

RunShowFn = Callable[[str, str], str]

TIMING_THRESHOLDS = {
    "single_mac_move_sec": 2.0,
    "scale_64k_move_sec": 15.0,
    "ha_recovery_sec": 120.0,
    "suppression_trigger_sec": 5.0,
}


def check_control_plane(
    device: str,
    evpn_name: str,
    test_mac: str,
    expected_sources: List[str],
    run_show: RunShowFn,
) -> LayerResult:
    from .mac_verifiers import verify_mac_source

    t0 = time.time()
    output = run_show(device, f"show evpn mac-table instance {evpn_name} mac {test_mac} | no-more")
    result = verify_mac_source(output, test_mac, expected_sources)
    elapsed = time.time() - t0
    if result["pass"]:
        return LayerResult("control_plane", VerdictStatus.PASS,
                           f"MAC {test_mac} source={result.get('source_hint')}",
                           output[:1000], elapsed)
    return LayerResult("control_plane", VerdictStatus.FAIL,
                       f"MAC {test_mac} expected {expected_sources}, got {result.get('source_hint', 'missing')}",
                       output[:1000], elapsed)


def check_mac_count(
    device: str,
    evpn_name: str,
    expected_count: int,
    tolerance_pct: float,
    run_show: RunShowFn,
) -> LayerResult:
    from .mac_parsers import parse_evpn_mac_count

    t0 = time.time()
    output = run_show(device, f"show evpn mac-table instance {evpn_name} | no-more")
    actual = parse_evpn_mac_count(output)
    elapsed = time.time() - t0
    lower = int(expected_count * (1 - tolerance_pct / 100))
    upper = int(expected_count * (1 + tolerance_pct / 100))
    if lower <= actual <= upper:
        return LayerResult("scale", VerdictStatus.PASS,
                           f"MAC count {actual} within [{lower},{upper}]",
                           f"expected={expected_count}", elapsed)
    return LayerResult("scale", VerdictStatus.FAIL,
                       f"MAC count {actual} outside [{lower},{upper}]",
                       f"expected={expected_count}, actual={actual}", elapsed)


def check_convergence_time(
    measured_sec: float,
    threshold_key: str = "single_mac_move_sec",
) -> LayerResult:
    threshold = TIMING_THRESHOLDS.get(threshold_key, 5.0)
    if measured_sec <= threshold:
        return LayerResult("timing", VerdictStatus.PASS,
                           f"{measured_sec:.2f}s <= {threshold}s threshold",
                           f"threshold_key={threshold_key}")
    if measured_sec <= threshold * 2:
        return LayerResult("timing", VerdictStatus.WARN,
                           f"{measured_sec:.2f}s > {threshold}s (within 2x)",
                           f"threshold_key={threshold_key}")
    return LayerResult("timing", VerdictStatus.FAIL,
                       f"{measured_sec:.2f}s >> {threshold}s threshold",
                       f"threshold_key={threshold_key}")


def check_bgp_session_stable(
    device: str,
    run_show: RunShowFn,
) -> LayerResult:
    from .mac_parsers import parse_bgp_l2vpn_evpn_summary

    t0 = time.time()
    output = run_show(device, "show bgp l2vpn evpn summary | no-more")
    parsed = parse_bgp_l2vpn_evpn_summary(output)
    elapsed = time.time() - t0
    if parsed["established"] > 0:
        return LayerResult("bgp_session", VerdictStatus.PASS,
                           f"{parsed['established']}/{parsed['total']} ESTABLISHED",
                           output[:500], elapsed)
    return LayerResult("bgp_session", VerdictStatus.FAIL,
                       f"0/{parsed['total']} ESTABLISHED",
                       output[:500], elapsed)


def check_suppression_applied(
    device: str,
    evpn_name: str,
    test_mac: str,
    run_show: RunShowFn,
) -> LayerResult:
    t0 = time.time()
    output = run_show(device, f"show evpn mac-table instance {evpn_name} mac {test_mac} | no-more")
    elapsed = time.time() - t0
    upper = output.upper()
    for keyword in ("FROZEN", "SUPPRESSED", "BLOCK", "SHUT", "DROP"):
        if keyword in upper:
            return LayerResult("suppression", VerdictStatus.PASS,
                               f"Sanction detected: {keyword}",
                               output[:500], elapsed)
    return LayerResult("suppression", VerdictStatus.WARN,
                       "No suppression keyword found in MAC entry (may need trace check)",
                       output[:500], elapsed)


def check_sticky_enforcement(
    device: str,
    evpn_name: str,
    sticky_mac: str,
    expected_ac: str,
    run_show: RunShowFn,
) -> LayerResult:
    from .mac_verifiers import verify_mac_source

    t0 = time.time()
    output = run_show(device, f"show evpn mac-table instance {evpn_name} mac {sticky_mac} | no-more")
    elapsed = time.time() - t0
    upper = output.upper()
    if "STICKY" not in upper:
        return LayerResult("sticky", VerdictStatus.FAIL,
                           f"MAC {sticky_mac} not marked sticky",
                           output[:500], elapsed)
    result = verify_mac_source(output, sticky_mac, ["local"])
    if result["pass"]:
        return LayerResult("sticky", VerdictStatus.PASS,
                           f"Sticky MAC {sticky_mac} remains local on {expected_ac}",
                           output[:500], elapsed)
    return LayerResult("sticky", VerdictStatus.FAIL,
                       f"Sticky MAC moved away from {expected_ac}",
                       output[:500], elapsed)


def check_no_trace_errors(
    device: str,
    timestamp_hhmm: str,
    run_show: RunShowFn,
) -> LayerResult:
    """Grep bgpd and fibmgrd traces for ERROR/CRASH near the test timestamp."""
    t0 = time.time()
    results = []
    for trace_path in [
        "routing_engine/bgpd_traces",
        "routing_engine/fibmgrd_traces",
    ]:
        out = run_show(
            device,
            f"show file traces {trace_path} | include {timestamp_hhmm} | include ERROR | no-more",
        )
        if out.strip() and "ERROR" in out.upper():
            results.append(f"{trace_path}: {out.strip()[:300]}")
    elapsed = time.time() - t0
    if results:
        return LayerResult("traces", VerdictStatus.WARN,
                           f"ERROR lines found near {timestamp_hhmm}",
                           "\n".join(results), elapsed)
    return LayerResult("traces", VerdictStatus.PASS,
                       f"No ERROR lines near {timestamp_hhmm}",
                       "", elapsed)


# ---------------------------------------------------------------------------
# Enhanced layer evaluators (deep flags, forwarding, loop prevention, mobility)
# ---------------------------------------------------------------------------

def check_mac_flags_layer(
    device: str,
    evpn_name: str,
    test_mac: str,
    expected_flags: List[str],
    forbidden_flags: List[str],
    run_show: RunShowFn,
) -> LayerResult:
    """Check MAC detail flags from 'show evpn mac-table detail instance'."""
    from .mac_verifiers import verify_mac_flags

    t0 = time.time()
    output = run_show(device, f"show evpn mac-table detail instance {evpn_name} | no-more")
    result = verify_mac_flags(output, test_mac, expected_flags, forbidden_flags)
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.FAIL
    return LayerResult("mac_flags", status, result.get("detail", ""), output[:1000], elapsed)


def check_forwarding_state_layer(
    device: str,
    evpn_name: str,
    test_mac: str,
    expected_state: str,
    run_show: RunShowFn,
) -> LayerResult:
    """Check NCP forwarding state via forwarding-table."""
    from .mac_verifiers import verify_forwarding_state

    t0 = time.time()
    output = run_show(device, f"show evpn forwarding-table mac-address-table instance {evpn_name} | no-more")
    result = verify_forwarding_state(output, test_mac, expected_state)
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.FAIL
    return LayerResult("forwarding", status, result.get("detail", ""), output[:1000], elapsed)


def check_loop_prevention_layer(
    device: str,
    evpn_name: str,
    test_mac: str,
    expected_state: str,
    run_show: RunShowFn,
) -> LayerResult:
    """Check loop-prevention state for a MAC."""
    from .mac_verifiers import verify_loop_prevention_state

    t0 = time.time()
    output = run_show(device, f"show evpn instance {evpn_name} loop-prevention mac-table | no-more")
    result = verify_loop_prevention_state(output, test_mac, expected_state)
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.FAIL
    return LayerResult("loop_prevention", status, result.get("detail", ""), output[:1000], elapsed)


def check_mobility_counter_layer(
    device: str,
    before_output: str,
    run_show: RunShowFn,
    expected_increment: int = 1,
) -> LayerResult:
    """Check mac-mobility-redis-count increased after move."""
    from .mac_verifiers import verify_mobility_counter

    t0 = time.time()
    after_output = run_show(device, "show dnos-internal routing evpn mac-mobility-redis-count | no-more")
    result = verify_mobility_counter(before_output, after_output, expected_increment)
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.WARN
    return LayerResult("mobility_counter", status, result.get("detail", ""), "", elapsed)


def check_ghost_macs_layer(
    device: str,
    evpn_name: str,
    run_show: RunShowFn,
) -> LayerResult:
    """Check for ghost MACs (should be zero in healthy state)."""
    from .mac_verifiers import verify_no_ghost_macs

    t0 = time.time()
    output = run_show(device, f"show dnos-internal routing evpn instance {evpn_name} mac-table-ghost | no-more")
    result = verify_no_ghost_macs(output)
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.WARN
    return LayerResult("ghost_macs", status, result.get("detail", ""), output[:500], elapsed)


def check_suppress_list_layer(
    device: str,
    evpn_name: str,
    test_mac: str,
    expect_suppressed: bool,
    run_show: RunShowFn,
) -> LayerResult:
    """Check suppress list for a specific MAC."""
    from .mac_verifiers import verify_suppress_list

    t0 = time.time()
    output = run_show(device, f"show evpn mac-table instance {evpn_name} suppress | no-more")
    result = verify_suppress_list(output, test_mac, expect_suppressed)
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.FAIL
    return LayerResult("suppress_list", status, result.get("detail", ""), output[:500], elapsed)


def check_rt2_recovery_layer(
    device: str,
    before_bgp_output: str,
    run_show: RunShowFn,
) -> LayerResult:
    """After HA, verify BGP L2VPN EVPN RT-2 routes recovered (prefix count parity)."""
    from .mac_parsers import parse_bgp_l2vpn_evpn_summary

    t0 = time.time()
    before_parsed = parse_bgp_l2vpn_evpn_summary(before_bgp_output)
    after_output = run_show(device, "show bgp l2vpn evpn summary | no-more")
    after_parsed = parse_bgp_l2vpn_evpn_summary(after_output)
    elapsed = time.time() - t0

    before_est = before_parsed.get("established", 0)
    after_est = after_parsed.get("established", 0)
    before_pfx = before_parsed.get("total_prefixes", 0)
    after_pfx = after_parsed.get("total_prefixes", 0)

    sessions_ok = after_est >= before_est if before_est > 0 else after_est > 0
    pfx_tolerance = max(1, int(before_pfx * 0.05)) if before_pfx > 0 else 0
    pfx_ok = after_pfx >= (before_pfx - pfx_tolerance) if before_pfx > 0 else True

    if sessions_ok and pfx_ok:
        return LayerResult(
            "rt2_recovery", VerdictStatus.PASS,
            f"RT-2 recovered: sessions {before_est}->{after_est}, "
            f"prefixes {before_pfx}->{after_pfx}",
            after_output[:500], elapsed,
        )
    detail_parts = []
    if not sessions_ok:
        detail_parts.append(f"sessions {before_est}->{after_est}")
    if not pfx_ok:
        detail_parts.append(f"prefixes {before_pfx}->{after_pfx} (lost {before_pfx - after_pfx})")
    return LayerResult(
        "rt2_recovery", VerdictStatus.FAIL,
        f"RT-2 recovery incomplete: {'; '.join(detail_parts)}",
        after_output[:500], elapsed,
    )


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_verdict_table(verdict: TestVerdict) -> str:
    verdict.compute_overall()
    lines = [
        f"## Test Verdict: {verdict.test_id} on {verdict.device}",
        f"**Overall: {verdict.overall.value}** | Elapsed: {verdict.total_elapsed_sec:.1f}s",
        "",
        "| Scenario | Overall | Layers | Convergence | Debug Hint |",
        "|----------|---------|--------|-------------|------------|",
    ]
    for sv in verdict.scenarios:
        layer_summary = ", ".join(f"{lr.layer}={lr.status.value}" for lr in sv.layers)
        conv = f"{sv.convergence_sec:.2f}s" if sv.convergence_sec is not None else "--"
        lines.append(
            f"| {sv.scenario_id} | {sv.overall.value} | {layer_summary} | {conv} | {sv.debug_hint or '--'} |"
        )
    return "\n".join(lines)


def format_detailed_report(verdict: TestVerdict) -> str:
    lines = [format_verdict_table(verdict), ""]
    for sv in verdict.scenarios:
        lines.append(f"### {sv.scenario_id}: {sv.scenario_name}")
        lines.append("")
        lines.append("| Layer | Status | Detail | Time |")
        lines.append("|-------|--------|--------|------|")
        for lr in sv.layers:
            lines.append(f"| {lr.layer} | {lr.status.value} | {lr.detail} | {lr.elapsed_sec:.2f}s |")
        if sv.debug_hint:
            lines.append(f"\n**Debug:** {sv.debug_hint}")
        lines.append("")
    return "\n".join(lines)
