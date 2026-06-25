#!/usr/bin/env python3
"""
/debug-dnos trace analysis integration for MAC mobility tests.

When a verdict layer returns FAIL, the orchestrator calls these functions
to automatically grep DNOS traces for root-cause clues. This avoids
manual /debug-dnos invocation for common failure patterns.

Trace pipeline for MAC mobility:
  bgpd_traces     -> RT-2 update/withdraw, MAC mobility ext-community
  fibmgrd_traces  -> MAC FIB install/delete, bridge-domain updates
  wb_agent traces -> NCP MAC table programming, forwarding decisions
  cli traces      -> config commit audit trail

Keywords are from the proven-RETURN list in trace-patterns.md.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from .mac_parsers import (
    FibMacEntry,
    FwdTableEntry,
    LoopPreventionMacEntry,
    MacSuppressEntry,
    parse_fib_evpn_mac,
    parse_forwarding_table_flags,
    parse_ghost_macs,
    parse_loop_prevention_mac_table,
    parse_mac_suppress,
)

RunShowFn = Callable[[str, str], str]

MAC_MOBILITY_TRACE_KEYWORDS = {
    "bgpd_traces": [
        "mac-mobility",
        "MAC",
        "EVPN",
        "RT-2",
        "Type-2",
        "withdraw",
        "announce",
        "seq",
        "duplicate",
        "suppress",
        "frozen",
        "NOTIFICATION",
        "Clearing",
    ],
    "fibmgrd_traces": [
        "MAC",
        "bridge",
        "evpn",
        "FIB",
        "flush",
        "delete",
        "ADD",
    ],
    "rib-manager_traces": [
        "MAC",
        "evpn",
        "FIB",
    ],
}

NCP_TRACE_KEYWORDS = [
    "mac",
    "evpn",
    "bridge",
    "learning",
    "aging",
    "move",
    "flush",
]


@dataclass
class TraceHit:
    trace_file: str
    keyword: str
    lines: List[str] = field(default_factory=list)
    count: int = 0


@dataclass
class TraceAnalysis:
    device: str
    timestamp_hhmm: str
    hits: List[TraceHit] = field(default_factory=list)
    errors_found: List[str] = field(default_factory=list)
    diagnosis: str = ""
    suggested_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "timestamp": self.timestamp_hhmm,
            "errors_found": self.errors_found,
            "diagnosis": self.diagnosis,
            "suggested_action": self.suggested_action,
            "trace_hits": [
                {
                    "file": h.trace_file,
                    "keyword": h.keyword,
                    "count": h.count,
                    "sample_lines": h.lines[:5],
                }
                for h in self.hits
            ],
        }


_trace_cache: Dict[str, str] = {}


def _drop_stale_trace_lines(output: str) -> str:
    """Keep HH:MM trace greps from matching old rotated/stale trace days."""
    if not output:
        return output
    today = datetime.now(timezone.utc).date()
    # Device traces are usually local time and may be one date ahead of UTC
    # near midnight. Older dates are stale rotated lines from the HH:MM grep.
    allowed_dates = {today.isoformat(), (today + timedelta(days=1)).isoformat()}
    dated_seen = False
    kept: List[str] = []
    for line in output.splitlines():
        match = re.search(r"\b(20\d{2}-\d{2}-\d{2})T", line)
        if not match:
            kept.append(line)
            continue
        dated_seen = True
        if match.group(1) in allowed_dates:
            kept.append(line)
    if dated_seen and not kept:
        return ""
    return "\n".join(kept)


def _get_trace_lines(
    device: str,
    trace_file: str,
    timestamp_hhmm: str,
    run_show: RunShowFn,
    ncp_id: str = "0",
) -> str:
    """Fetch trace lines for a file+timestamp, caching to avoid repeated scans."""
    cache_key = f"{device}:{trace_file}:{timestamp_hhmm}"
    if cache_key in _trace_cache:
        return _trace_cache[cache_key]

    if trace_file.startswith("ncp"):
        cmd = (
            f"show file ncp {ncp_id} traces datapath/wb_agent.evpn "
            f"| include {timestamp_hhmm} | no-more"
        )
    else:
        full_path = f"routing_engine/{trace_file}"
        cmd = f"show file traces {full_path} | include {timestamp_hhmm} | no-more"

    try:
        output = run_show(device, cmd)
    except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError) as exc:
        # Trace fetch is best-effort: unreachable device or torn-down SSH
        # session must not abort verdict aggregation.  Anything other than
        # an environmental failure (e.g. AttributeError) is a real bug and
        # is intentionally allowed to propagate.
        output = f"[trace-fetch-failed] {exc.__class__.__name__}: {exc}"
    output = _drop_stale_trace_lines(output)
    _trace_cache[cache_key] = output
    return output


def clear_trace_cache() -> None:
    """Reset the per-scenario trace cache."""
    _trace_cache.clear()


def analyze_failure(
    device: str,
    timestamp_hhmm: str,
    failed_layer: str,
    run_show: RunShowFn,
    ncp_id: str = "0",
) -> TraceAnalysis:
    """
    Run targeted trace greps based on which verdict layer failed.

    Fetches each trace file ONCE (cached), then matches keywords in Python.
    """
    analysis = TraceAnalysis(device=device, timestamp_hhmm=timestamp_hhmm)

    keywords_to_check = _select_keywords(failed_layer)

    for trace_file, keywords in keywords_to_check.items():
        all_lines = _get_trace_lines(device, trace_file, timestamp_hhmm, run_show, ncp_id)
        if not all_lines or not all_lines.strip():
            continue

        cached_lines = [
            ln.strip() for ln in all_lines.strip().splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]

        for kw in keywords:
            matched = [ln for ln in cached_lines if kw in ln][:10]
            if matched:
                hit = TraceHit(
                    trace_file=trace_file,
                    keyword=kw,
                    lines=matched,
                    count=len(matched),
                )
                analysis.hits.append(hit)
                _check_for_errors(hit, analysis)

    _build_diagnosis(analysis, failed_layer)
    return analysis


def quick_error_scan(
    device: str,
    timestamp_hhmm: str,
    run_show: RunShowFn,
) -> TraceAnalysis:
    """Fast scan for ERROR/CRASH/NOTIFICATION across all trace files.

    Uses cached trace output (one fetch per file) instead of per-keyword scans.
    """
    analysis = TraceAnalysis(device=device, timestamp_hhmm=timestamp_hhmm)

    error_keywords = ["ERROR", "CRASH", "NOTIFICATION", "core dump"]
    trace_files = ["bgpd_traces", "fibmgrd_traces", "rib-manager_traces"]

    for tf in trace_files:
        all_lines = _get_trace_lines(device, tf, timestamp_hhmm, run_show)
        if not all_lines or not all_lines.strip():
            continue
        for ek in error_keywords:
            matched = [
                ln.strip() for ln in all_lines.strip().splitlines()
                if ln.strip() and ek.upper() in ln.upper()
            ][:5]
            if matched:
                analysis.errors_found.append(f"{tf}: {ek} -- {matched[0][:200]}")
                analysis.hits.append(TraceHit(tf, ek, matched, len(matched)))

    if analysis.errors_found:
        analysis.diagnosis = (
            f"Found {len(analysis.errors_found)} error(s) near {timestamp_hhmm}. "
            "Run /debug-dnos for full investigation."
        )
        analysis.suggested_action = "/debug-dnos INVESTIGATE with pre-filled timestamp"
    else:
        analysis.diagnosis = f"No ERROR/CRASH/NOTIFICATION near {timestamp_hhmm}."

    return analysis


# NOTE: previous helper `analyze_mac_move_traces` (and its private
# `_build_mac_move_diagnosis` companion) was removed in PR7d (2026-04-14).
# No call site dispatched it; per-MAC trace analysis now happens via
# `analyze_failure` (which already understands the MAC mobility layer keys)
# and the orchestrator's `auto_investigate` path.


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _select_keywords(failed_layer: str) -> Dict[str, List[str]]:
    if failed_layer in ("control_plane", "sequencing", "rt2"):
        return {
            "bgpd_traces": ["MAC", "EVPN", "withdraw", "announce", "seq", "duplicate", "suppress"],
            "rib-manager_traces": ["MAC", "evpn", "FIB"],
        }
    if failed_layer == "suppression":
        return {
            "bgpd_traces": ["suppress", "frozen", "duplicate", "mac-mobility", "NOTIFICATION"],
        }
    if failed_layer == "sticky":
        return {
            "bgpd_traces": ["sticky", "MAC", "seq", "ignore"],
        }
    if failed_layer in ("scale", "timing"):
        return {
            "bgpd_traces": ["MAC", "withdraw", "announce"],
            "fibmgrd_traces": ["MAC", "FIB", "flush"],
            "ncp_traces": ["mac", "learning", "flush"],
        }
    if failed_layer in ("ha", "bgp_session"):
        return {
            "bgpd_traces": ["Clearing", "NOTIFICATION", "Established", "MAC"],
            "fibmgrd_traces": ["FIB", "flush"],
        }
    return MAC_MOBILITY_TRACE_KEYWORDS


def _check_for_errors(hit: TraceHit, analysis: TraceAnalysis) -> None:
    error_markers = ["ERROR", "CRASH", "NOTIFICATION", "core dump", "FATAL"]
    for line in hit.lines:
        for marker in error_markers:
            if marker in line.upper():
                analysis.errors_found.append(f"{hit.trace_file}: {line[:200]}")
                break


def _build_diagnosis(analysis: TraceAnalysis, failed_layer: str) -> None:
    if analysis.errors_found:
        analysis.diagnosis = (
            f"Layer '{failed_layer}' failed. {len(analysis.errors_found)} error(s) "
            f"found in traces near {analysis.timestamp_hhmm}."
        )
        analysis.suggested_action = (
            f"/debug-dnos {analysis.device} -- EVPN MAC mobility {failed_layer} failure. "
            f"Timestamp: {analysis.timestamp_hhmm}. Errors in: "
            + ", ".join(set(e.split(":")[0] for e in analysis.errors_found))
        )
    elif analysis.hits:
        analysis.diagnosis = (
            f"Layer '{failed_layer}' failed. {len(analysis.hits)} trace match(es) "
            f"near {analysis.timestamp_hhmm} but no ERROR lines."
        )
        analysis.suggested_action = "Review trace lines for unexpected state transitions."
    else:
        analysis.diagnosis = (
            f"Layer '{failed_layer}' failed. No trace hits near {analysis.timestamp_hhmm}. "
            "Trace buffer may have rotated or timestamp mismatch."
        )
        analysis.suggested_action = (
            "Reproduce the failure for fresh traces. "
            "Check trace buffer size: show file traces routing_engine/bgpd_traces | trailing 5"
        )


# ---------------------------------------------------------------------------
# E1: Deep evidence collection (suppress, loop-prevention, dnos-internal)
# ---------------------------------------------------------------------------

@dataclass
class DeepEvidence:
    """Extended evidence collected on failure beyond basic trace greps."""
    suppressed_macs: List[MacSuppressEntry] = field(default_factory=list)
    loop_prevention_state: List[LoopPreventionMacEntry] = field(default_factory=list)
    mobility_counter: Dict[str, int] = field(default_factory=dict)
    ghost_macs: List[str] = field(default_factory=list)
    fib_state: List[FibMacEntry] = field(default_factory=list)
    forwarding_flags: List[FwdTableEntry] = field(default_factory=list)
    raw_outputs: Dict[str, str] = field(default_factory=dict)
    debug_traces_collected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suppressed_mac_count": len(self.suppressed_macs),
            "suppressed_macs": [
                {"mac": e.mac, "reason": e.reason, "timer": e.timer_remaining}
                for e in self.suppressed_macs
            ],
            "loop_prevention_entries": [
                {"mac": e.mac, "state": e.state, "move_count": e.move_count,
                 "restore_timer": e.restore_timer}
                for e in self.loop_prevention_state
            ],
            "mobility_counter": self.mobility_counter,
            "ghost_mac_count": len(self.ghost_macs),
            "ghost_macs": self.ghost_macs[:20],
            "fib_entries": [
                {"mac": e.mac, "state": e.fib_state, "interface": e.interface}
                for e in self.fib_state
            ],
            "forwarding_entries": [
                {"mac": e.mac, "state": e.fwd_state, "flags": e.flags, "ncp_id": e.ncp_id}
                for e in self.forwarding_flags
            ],
            "debug_traces_collected": self.debug_traces_collected,
        }


def collect_deep_evidence(
    device: str,
    evpn_name: str,
    test_mac: str,
    run_show: RunShowFn,
    ncp_id: str = "0",
) -> DeepEvidence:
    """Collect deep state evidence from suppress, loop-prevention, and internal commands.

    Runs all evidence-gathering commands and parses results.
    Called by the orchestrator on FAIL/ERROR verdict.
    """
    evidence = DeepEvidence()

    cmds = {
        "suppress": f"show evpn mac-table instance {evpn_name} suppress | no-more",
        "loop_prevention": f"show evpn instance {evpn_name} loop-prevention mac-table | no-more",
        "mac_summary": "show evpn mac summary | no-more",
        "ghost_macs": f"show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more",
        "fib_local": f"show dnos-internal routing fib-manager database evpn local-mac service-instance {evpn_name} | no-more",
        "fwd_table": f"show evpn forwarding-table mac-address-table instance {evpn_name} | no-more",
    }

    for key, cmd in cmds.items():
        try:
            output = run_show(device, cmd)
            evidence.raw_outputs[key] = output
        except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError) as exc:
            evidence.raw_outputs[key] = f"[show-failed] {exc.__class__.__name__}: {exc}"

    evidence.suppressed_macs = parse_mac_suppress(evidence.raw_outputs.get("suppress", ""))
    evidence.loop_prevention_state = parse_loop_prevention_mac_table(
        evidence.raw_outputs.get("loop_prevention", "")
    )
    evidence.ghost_macs = parse_ghost_macs(evidence.raw_outputs.get("ghost_macs", ""))
    evidence.fib_state = parse_fib_evpn_mac(evidence.raw_outputs.get("fib_local", ""))
    evidence.forwarding_flags = parse_forwarding_table_flags(
        evidence.raw_outputs.get("fwd_table", "")
    )

    return evidence


# ---------------------------------------------------------------------------
# E1: Debug trace management (enable/disable on failure)
# ---------------------------------------------------------------------------

_EVPN_DEBUG_CMDS = [
    # DNOS CLI docs do not expose the legacy "debug evpn mac-*" commands,
    # and live runs reject them as Unknown word. Keep trace collection read-only
    # unless a documented debug command is added and validated.
]

_DEBUG_SAFETY_TIMEOUT_SEC = 60


def enable_debug_traces(
    device: str,
    run_show: RunShowFn,
    feature: str = "evpn",
) -> List[str]:
    """Temporarily enable debug flags relevant to MAC mobility failures.

    Returns list of successfully enabled debug flags.
    The caller MUST call disable_debug_traces() after collecting.
    """
    enabled: List[str] = []

    debug_cmds = _EVPN_DEBUG_CMDS if feature == "evpn" else [f"debug {feature}"]

    for cmd in debug_cmds:
        try:
            output = run_show(device, cmd)
            if "error" not in output.lower() and "unknown" not in output.lower():
                enabled.append(cmd)
        except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError):
            # Debug toggle failure is non-fatal: just skip the flag and
            # continue trying the rest.
            continue

    return enabled


def disable_debug_traces(
    device: str,
    run_show: RunShowFn,
    enabled_flags: List[str],
) -> None:
    """Disable all debug flags that were enabled by enable_debug_traces()."""
    for cmd in enabled_flags:
        no_cmd = cmd.replace("debug ", "no debug ", 1)
        try:
            run_show(device, no_cmd)
        except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError):
            # Best-effort cleanup -- if the device is gone we cannot disable
            # the flag, but the next test connect will reset session state.
            continue


def collect_debug_traces_window(
    device: str,
    run_show: RunShowFn,
    enabled_flags: List[str],
    wait_sec: int = 10,
    ncp_id: str = "0",
) -> List[str]:
    """Wait for debug output to accumulate, then collect trace snippets.

    NOTE: this is one of the rare cases where a fixed `time.sleep` is correct:
    we are deliberately allowing the device to write `wait_sec` seconds worth
    of new trace entries after a triggering event (e.g. MAC inject, BGP flap)
    so the snapshot we collect captures the action's effects. There is no
    event to poll for -- we are sampling a continuous stream.
    """
    time.sleep(wait_sec)
    collected: List[str] = []

    for trace_file in ["bgpd_traces", "fibmgrd_traces"]:
        try:
            output = run_show(
                device,
                f"show file traces routing_engine/{trace_file} | tail 50 | no-more",
            )
            if output.strip():
                collected.append(f"--- {trace_file} (tail 50 lines) ---\n{output.strip()}")
        except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError) as exc:
            collected.append(f"--- {trace_file} (FETCH-FAILED) ---\n"
                             f"{exc.__class__.__name__}: {exc}")

    try:
        ncp_output = run_show(
            device,
            f"show file ncp {ncp_id} traces datapath/wb_agent.evpn | trailing 30 | no-more",
        )
        if ncp_output.strip():
            collected.append(f"--- ncp_{ncp_id}/wb_agent.evpn (trailing 30 lines) ---\n{ncp_output.strip()}")
    except (OSError, IOError, ConnectionError, TimeoutError, RuntimeError) as exc:
        collected.append(f"--- ncp_{ncp_id}/wb_agent.evpn (FETCH-FAILED) ---\n"
                         f"{exc.__class__.__name__}: {exc}")

    return collected


# ---------------------------------------------------------------------------
# E2: Auto-investigate (generate /debug-dnos command)
# ---------------------------------------------------------------------------

def auto_investigate(
    device: str,
    failed_layers: List[str],
    deep_evidence: DeepEvidence,
    trace_analysis: Optional[TraceAnalysis],
    test_context: Dict[str, Any],
) -> str:
    """Generate a complete /debug-dnos INVESTIGATE command with all context pre-filled.

    This gives the human operator (or agent) a ready-to-paste command that
    skips the discovery phase and goes straight to targeted investigation.
    """
    parts = [f"/debug-dnos {device} --"]
    parts.append("EVPN MAC mobility test failure.")
    parts.append(f"Test: {test_context.get('test_id', 'unknown')}.")

    if failed_layers:
        parts.append(f"Failed layers: {', '.join(failed_layers)}.")

    timestamp = test_context.get("timestamp", "")
    if timestamp:
        parts.append(f"Timestamp: {timestamp}.")

    suppress_count = len(deep_evidence.suppressed_macs)
    ghost_count = len(deep_evidence.ghost_macs)
    mobility = deep_evidence.mobility_counter.get("total_moves", 0)

    evidence_parts: List[str] = []
    if suppress_count:
        reasons = set(e.reason for e in deep_evidence.suppressed_macs)
        evidence_parts.append(f"Suppressed MACs: {suppress_count} (reasons: {', '.join(reasons)})")
    if ghost_count:
        evidence_parts.append(f"Ghost MACs: {ghost_count}")
    if mobility:
        evidence_parts.append(f"Mobility counter: {mobility}")

    lp_suppressed = [e for e in deep_evidence.loop_prevention_state if e.state != "normal"]
    if lp_suppressed:
        evidence_parts.append(f"Loop-prevention suppressed: {len(lp_suppressed)} MACs")

    fib_errors = [e for e in deep_evidence.fib_state if e.fib_state not in ("programmed", "installed")]
    if fib_errors:
        evidence_parts.append(f"FIB errors: {len(fib_errors)} MACs")

    if evidence_parts:
        parts.append("Evidence: " + "; ".join(evidence_parts) + ".")

    if trace_analysis and trace_analysis.errors_found:
        error_files = set(e.split(":")[0] for e in trace_analysis.errors_found)
        parts.append(f"Errors in: {', '.join(error_files)}.")

    parts.append("Suggested: Phase 3 trace analysis on bgpd + fibmgrd.")

    return " ".join(parts)
