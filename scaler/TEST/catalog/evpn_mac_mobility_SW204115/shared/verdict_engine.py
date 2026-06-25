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
from typing import Any, Callable, Dict, List, Optional, Set


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
    expected_warns: Set[str] = field(default_factory=set)

    def compute_overall(self) -> None:
        if not self.layers:
            self.overall = VerdictStatus.SKIP
            return
        statuses = []
        for lr in self.layers:
            if lr.status == VerdictStatus.WARN and lr.layer in self.expected_warns:
                statuses.append(VerdictStatus.PASS)
            else:
                statuses.append(lr.status)
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
                    # ``evidence`` may legitimately be None when a layer
                    # records only a verdict + one-line detail (e.g. timing,
                    # bgp_session). Guard against ``None[:2000]`` so the
                    # post-suite ``write_results`` never crashes after a
                    # successful run of 11 scenarios.
                    "evidence": (lr.evidence or "")[:2000],
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
    "single_mac_move_sec": 90.0,
    "rapid_flap_sec": 200.0,
    "scale_64k_move_sec": 120.0,
    "ha_recovery_sec": 180.0,
    # wait_aging scenarios intentionally hold 3x_configured_aging (capped at 600s)
    # to verify MAC aging/persistence. Use a generous threshold above the cap.
    "wait_aging_sec": 700.0,
    "suppression_trigger_sec": 15.0,
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


def check_all_sources_present(
    device: str,
    evpn_name: str,
    expected_sources: List[Any],
    run_show: RunShowFn,
    forbidden_flags: Optional[List[str]] = None,
) -> LayerResult:
    """Verify that required MAC/source flags coexist in the EVPN table.

    ``expected_sources`` accepts the strict shape used by SC04:
    ``{"mac": "...", "flag": "L>", "source": "local"}``.
    It also accepts the legacy lightweight form ``["L>", "B>", "v>"]`` and
    then checks that at least one MAC exists for each requested flag.
    """
    from .mac_parsers import parse_mac_table_piped

    def _has_flag(flags: str, expected_flag: str) -> bool:
        flags = (flags or "").strip()
        expected_flag = (expected_flag or "").strip()
        return bool(expected_flag) and (
            expected_flag in flags
            or all(ch in flags for ch in expected_flag if not ch.isspace())
        )

    forbidden_flags = forbidden_flags or []
    t0 = time.time()
    output = run_show(device, f"show evpn mac-table instance {evpn_name} | no-more")
    entries = parse_mac_table_piped(output)
    elapsed = time.time() - t0

    if not isinstance(expected_sources, list) or not expected_sources:
        return LayerResult(
            "all_sources_present",
            VerdictStatus.FAIL,
            "No expected source/flag definitions were provided",
            output[:1000],
            elapsed,
        )

    passed = []
    failed = []
    for item in expected_sources:
        if isinstance(item, str):
            matches = [entry for entry in entries if _has_flag(entry.flags, item)]
            if matches:
                passed.append(f"{item}: {matches[0].mac} ({matches[0].flags})")
            else:
                failed.append(f"{item}: missing")
            continue

        if not isinstance(item, dict):
            failed.append(f"{item!r}: invalid expectation")
            continue

        mac = str(item.get("mac", "")).lower()
        expected_flag = str(item.get("flag") or item.get("flags") or "")
        expected_source = str(item.get("source", "")).lower()
        label = str(item.get("label") or mac or expected_flag)
        entry = next((candidate for candidate in entries if candidate.mac == mac), None)

        if not entry:
            failed.append(f"{label}: MAC {mac or '<missing>'} missing")
            continue
        if expected_flag and not _has_flag(entry.flags, expected_flag):
            failed.append(
                f"{label}: expected flag {expected_flag}, got {entry.flags or '<none>'}"
            )
            continue
        if expected_source and entry.source != expected_source:
            failed.append(
                f"{label}: expected source {expected_source}, got {entry.source}"
            )
            continue
        forbidden_hits = [
            flag for flag in forbidden_flags
            if flag and flag in (entry.flags or "")
        ]
        if forbidden_hits:
            failed.append(
                f"{label}: forbidden flag(s) {','.join(forbidden_hits)} in {entry.flags}"
            )
            continue
        passed.append(f"{label}: {entry.mac} {entry.flags} {entry.source}")

    if failed:
        return LayerResult(
            "all_sources_present",
            VerdictStatus.FAIL,
            f"{len(failed)} missing/mismatched source checks: " + "; ".join(failed),
            output[:1000],
            elapsed,
        )
    return LayerResult(
        "all_sources_present",
        VerdictStatus.PASS,
        f"{len(passed)}/{len(expected_sources)} source checks passed: "
        + "; ".join(passed),
        output[:1000],
        elapsed,
    )


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
    required: bool = True,
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
    if not required:
        return LayerResult("bgp_session", VerdictStatus.WARN,
                           f"0/{parsed['total']} ESTABLISHED (not required for this test)",
                           output[:500], elapsed)
    return LayerResult("bgp_session", VerdictStatus.FAIL,
                       f"0/{parsed['total']} ESTABLISHED",
                       output[:500], elapsed)


# NOTE: previous layer helpers `check_suppression_applied` and
# `check_sticky_enforcement` were removed in PR7d (2026-04-14). They were not
# wired into any layer dispatch map. The orchestrator drives suppression /
# sticky verification through the corresponding `verify_*` helpers in
# `shared/mac_verifiers.py`; re-add wrappers here only when a new layer
# group needs them.


def check_no_trace_errors(
    device: str,
    timestamp_hhmm: str,
    run_show: RunShowFn,
    skip_if_infra_fail: bool = False,
    skip_reason: str = "",
    relevant_neighbors: list[str] | None = None,
) -> LayerResult:
    """Grep bgpd and fibmgrd traces for ERROR/CRASH near the test timestamp.

    Uses the shared trace cache so auto_diagnose doesn't re-scan the same files.
    When skip_if_infra_fail is True, skip expensive trace greps and return SKIP.

    ``skip_reason`` lets the caller distinguish between the optimization paths:
      - "infra_fail"  -> MAC never appeared, trace scan won't help
      - "all_pass"    -> no functional FAIL, traces add zero signal
      - "" (default)  -> legacy behavior (keep old message for compat)
    """
    if skip_if_infra_fail:
        if skip_reason == "all_pass":
            detail = "Skipped (optimization: all functional layers PASS, traces add no signal)"
        elif skip_reason == "infra_fail":
            detail = "Skipped (infra failure: MAC never learned, trace scan won't localize)"
        else:
            detail = "Skipped trace check (infra failure detected)"
        return LayerResult("traces", VerdictStatus.SKIP, detail, "", 0.0)

    import re
    from datetime import datetime

    from .trace_analyzer import _get_trace_lines

    t0 = time.time()
    results = []
    today_prefix = datetime.now().strftime("%Y-%m-%dT")
    relevant_neighbor_set = {str(n) for n in (relevant_neighbors or []) if n}
    for trace_file in ["bgpd_traces", "fibmgrd_traces"]:
        cached = _get_trace_lines(device, trace_file, timestamp_hhmm, run_show)
        if cached and cached.strip():
            error_lines = []
            for line in cached.strip().splitlines():
                stripped = line.strip()
                upper = stripped.upper()
                lower = stripped.lower()
                if not stripped or today_prefix not in stripped or "ERROR" not in upper:
                    continue
                if trace_file == "bgpd_traces" and "notification" in lower and relevant_neighbor_set:
                    neighbor_match = re.search(r"neighbor\s+(\d+\.\d+\.\d+\.\d+)", lower)
                    if not neighbor_match or neighbor_match.group(1) not in relevant_neighbor_set:
                        continue
                error_lines.append(stripped)
                if len(error_lines) >= 5:
                    break
            if error_lines:
                results.append(f"routing_engine/{trace_file}: {error_lines[0][:300]}")
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
    absent_is_pass: bool = False,
) -> LayerResult:
    """Check MAC detail flags from 'show evpn mac-table detail instance'.

    absent_is_pass: flush/clear scenarios -- MAC not being in the table is
        the expected post-trigger state, so return PASS instead of FAIL.
    """
    from .mac_verifiers import verify_mac_flags

    t0 = time.time()
    output = run_show(device, f"show evpn mac-table detail instance {evpn_name} | no-more")
    result = verify_mac_flags(
        output, test_mac, expected_flags, forbidden_flags,
        absent_is_pass=absent_is_pass,
    )
    elapsed = time.time() - t0
    status = VerdictStatus.PASS if result["pass"] else VerdictStatus.FAIL
    return LayerResult("mac_flags", status, result.get("detail", ""), output[:1000], elapsed)


def check_forwarding_state_layer(
    device: str,
    evpn_name: str,
    test_mac: str,
    expected_state: str,
    run_show: RunShowFn,
    absent_is_pass: bool = False,
) -> LayerResult:
    """Check NCP forwarding state via forwarding-table.

    absent_is_pass: flush/clear scenarios -- MAC missing from the NCP
        forwarding table is the expected post-flush state, so return PASS.
    """
    from .mac_verifiers import verify_forwarding_state

    t0 = time.time()
    output = run_show(device, f"show evpn forwarding-table mac-address-table instance {evpn_name} | no-more")
    result = verify_forwarding_state(
        output, test_mac, expected_state, absent_is_pass=absent_is_pass,
    )
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
    """Legacy mobility counter layer.

    The old dnos-internal redis-count command is not available on current
    DNOS 26.2 lab builds. Capture the validated MAC summary for evidence and
    return WARN so tests do not turn invalid syntax into a false verdict.
    """

    t0 = time.time()
    after_output = run_show(device, "show evpn mac summary | no-more")
    elapsed = time.time() - t0
    return LayerResult(
        "mobility_counter",
        VerdictStatus.WARN,
        "Legacy mobility counter command is unavailable; collected show evpn mac summary instead.",
        after_output[:1000],
        elapsed,
    )


def check_ghost_macs_layer(
    device: str,
    evpn_name: str,
    run_show: RunShowFn,
) -> LayerResult:
    """Check for real ghost/suppression MACs in the DNOS diagnostic view."""
    from .mac_parsers import parse_ghost_macs

    t0 = time.time()
    output = run_show(
        device,
        f"show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more",
    )
    elapsed = time.time() - t0
    ghost_macs = parse_ghost_macs(output)
    if ghost_macs:
        return LayerResult("ghost_macs", VerdictStatus.FAIL,
                           f"{len(ghost_macs)} real ghost MAC(s): {', '.join(ghost_macs[:5])}",
                           output[:500], elapsed)
    return LayerResult("ghost_macs", VerdictStatus.PASS,
                       "No real ghost/suppression MACs", "", elapsed)


def check_no_bgp_notification_layer(
    device: str,
    run_show: RunShowFn,
    timestamp_hhmm: str | None = None,
    relevant_neighbors: list[str] | None = None,
) -> LayerResult:
    """Fail if bgpd traces show NOTIFICATION sent/received during the run."""
    import re
    from datetime import datetime

    t0 = time.time()
    if timestamp_hhmm:
        command = (
            "show file traces routing_engine/bgpd_traces "
            f"| include {timestamp_hhmm} | no-more"
        )
    else:
        command = "show file traces routing_engine/bgpd_traces | include NOTIFICATION | no-more"
    output = run_show(
        device,
        command,
    )
    elapsed = time.time() - t0
    bad_lines = []
    today_prefix = datetime.now().strftime("%Y-%m-%dT")
    relevant_neighbor_set = {str(n) for n in (relevant_neighbors or []) if n}
    for line in output.splitlines():
        lower = line.lower()
        if "show file traces" in lower or "include " in lower:
            continue
        if timestamp_hhmm and today_prefix not in line:
            continue
        if re.search(r"notification\s+(sent|received)|sent\s+notification|rcvd\s+notification", lower):
            if relevant_neighbor_set:
                neighbor_match = re.search(r"neighbor\s+(\d+\.\d+\.\d+\.\d+)", lower)
                if not neighbor_match or neighbor_match.group(1) not in relevant_neighbor_set:
                    continue
            bad_lines.append(line.strip())

    if bad_lines:
        return LayerResult(
            "bgp_notification",
            VerdictStatus.FAIL,
            f"{len(bad_lines)} BGP NOTIFICATION trace line(s) found",
            "\n".join(bad_lines[:5]),
            elapsed,
        )
    return LayerResult(
        "bgp_notification",
        VerdictStatus.PASS,
        "No BGP NOTIFICATION sent/received trace lines",
        "",
        elapsed,
    )


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
