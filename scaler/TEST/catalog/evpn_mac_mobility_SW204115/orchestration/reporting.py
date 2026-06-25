"""Reporting and post-run diagnostics.

Extracted from ``mac_mobility_orchestrator.py``:
  * ``_generate_repro_steps`` -- human-readable REPRO_STEPS.md for QA
  * ``write_results``         -- persists verdict.json / SUMMARY.md / timelines
  * ``_live_failure_detector`` -- auto-diagnoses a failed scenario on the DUT
                                  and proposes retry classification

The only shared mutable state these helpers need is the module-level
dispatch tables (``ACTION_TRIGGER_MAP``, ``_PW_TRIGGERS``, ``_EVPN_FALLBACK``),
which live in :mod:`orchestration.constants`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from shared.mac_parsers import (
    parse_bgp_l2vpn_evpn_summary,
    parse_evpn_mac_entries,
    strip_ansi,
)
from shared.mac_trigger import TrafficMethod, ensure_spirent_ready
from shared.verdict_engine import (
    ScenarioVerdict,
    TestVerdict,
    VerdictStatus,
    format_detailed_report,
)

from .constants import (
    ACTION_TRIGGER_MAP,
    _EVPN_FALLBACK,
    _PW_TRIGGERS,
)
from .session_io import now_iso


# ---------------------------------------------------------------------------
# Human-readable repro step generator (QA manual reproduction)
# ---------------------------------------------------------------------------

def _generate_repro_steps(
    device: str,
    verdict: "TestVerdict",
    recipe: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate REPRO_STEPS.md for QA engineers to reproduce test results manually.

    For each scenario, lists: prerequisites, exact CLI commands in order,
    trigger action, and verification commands with expected output patterns.
    """
    lines = [
        "# Manual Reproduction Steps",
        "",
        f"**Device:** {device}",
        f"**Generated:** {now_iso()}",
        "",
        "---",
    ]

    scenarios = recipe.get("scenarios", []) if recipe else []
    scenario_map = {s.get("id", ""): s for s in scenarios}

    for sv in verdict.scenarios:
        sc_recipe = scenario_map.get(sv.scenario_id, {})
        sc_name = sc_recipe.get("name", sv.scenario_id)
        lines.extend([
            "",
            f"## {sv.scenario_id}: {sc_name}",
            "",
            f"**Result:** {sv.overall.value}",
            "",
        ])

        phases = sc_recipe.get("phases", {})

        prereqs = recipe.get("prerequisites", []) if recipe else []
        if prereqs:
            lines.append("### Step 1: Verify Prerequisites")
            lines.append("")
            for p in prereqs:
                lines.append(f"- Check: `{p.get('check', '')}` -- Fix via: `{p.get('fix_via', 'N/A')}`")
            lines.append("")

        snapshot = phases.get("snapshot") or phases.get("before_snapshot")
        if snapshot and isinstance(snapshot, dict):
            cmds = snapshot.get("show_commands", [])
            if cmds:
                lines.append("### Step 2: Capture Baseline (Before Trigger)")
                lines.append("")
                lines.append("Run these commands and save output for comparison:")
                lines.append("")
                for cmd in cmds:
                    lines.append("```")
                    lines.append(f"{device}# {cmd}")
                    lines.append("```")
                    lines.append("")

        trigger = phases.get("trigger", {})
        if trigger:
            lines.append("### Step 3: Trigger")
            lines.append("")
            action = trigger.get("action", "")
            ha_cmd = trigger.get("ha_command", "")
            method = trigger.get("method", "")
            if ha_cmd:
                lines.append("Run HA command on device:")
                lines.append("")
                lines.append("```")
                lines.append(f"{device}# {ha_cmd}")
                lines.append("```")
            elif action:
                lines.append(f"**Action:** `{action}` (method: `{method}`)")
                if "move_mac" in action:
                    lines.append("")
                    lines.append("Move the test MAC address by sending traffic from a different source port.")
                    lines.append("If using Spirent: re-bind the MAC stream to the second port and start transmission.")
                elif "flap" in action:
                    lines.append("")
                    lines.append("Flap the AC interface (shut/no-shut) to trigger MAC re-learning.")
            lines.append("")

        poll = phases.get("poll_recovery")
        if poll:
            timeout = poll.get("timeout_sec", 120)
            lines.append(f"### Step 4: Wait for Recovery (up to {timeout}s)")
            lines.append("")
            lines.append(f"Poll MAC table every {poll.get('poll_interval_sec', 10)}s until count recovers:")
            lines.append("")
            poll_cmds = poll.get("show_commands", [])
            for cmd in poll_cmds:
                lines.append("```")
                lines.append(f"{device}# {cmd}")
                lines.append("```")
            lines.append("")

        verify = phases.get("verify", {})
        verify_cmds = verify.get("show_commands", [])
        expect = verify.get("expect", {})
        if verify_cmds or expect:
            lines.append("### Step 5: Verify")
            lines.append("")
            if verify_cmds:
                lines.append("Run these verification commands:")
                lines.append("")
                for cmd in verify_cmds:
                    lines.append("```")
                    lines.append(f"{device}# {cmd}")
                    lines.append("```")
                    lines.append("")

            lines.append("**What to check in the output:**")
            lines.append("")
            if expect.get("seq_increment"):
                lines.append("- [ ] Sequence number INCREASED compared to baseline")
            if expect.get("new_ac_attachment"):
                lines.append("- [ ] MAC is now on the new AC interface (different from baseline)")
            if expect.get("check_mac_flags"):
                forbidden = expect.get("forbidden_flags", [])
                expected = expect.get("expected_flags", [])
                if expected:
                    lines.append(f"- [ ] Flags PRESENT: {', '.join(expected)}")
                if forbidden:
                    lines.append(f"- [ ] Flags ABSENT: {', '.join(forbidden)}")
            if expect.get("source_contains"):
                lines.append(f"- [ ] Source is one of: {expect['source_contains']}")
            if expect.get("rt2_advertised"):
                lines.append("- [ ] BGP Type-2 route exists for this MAC (`show bgp l2vpn evpn route-type 2 | include <MAC>` plus peer advertised/received routes)")
            if expect.get("check_forwarding"):
                lines.append(f"- [ ] Forwarding state: {expect.get('expected_fwd_state', 'forwarding')}")
            if expect.get("check_ghost_macs"):
                lines.append("- [ ] No ghost MAC entries for this MAC")
            if expect.get("check_mobility_counter"):
                lines.append("- [ ] MAC mobility counter incremented")
            if expect.get("sanction_applied"):
                lines.append("- [ ] Suppression/sanction is ACTIVE (Frozen/Duplicate/Suppressed)")
            if expect.get("check_suppress_list"):
                lines.append("- [ ] MAC appears in suppression list")
            if expect.get("check_loop_prevention"):
                lines.append(f"- [ ] Loop prevention state: {expect.get('expected_lp_state', 'suppressed')}")
            if "local_loop_count_increments" in expect:
                if expect.get("local_loop_count_increments"):
                    lines.append("- [ ] Local loop count incremented on AC interface (> 0 moves)")
                else:
                    rationale = expect.get("rationale", "SH->SH move is ignored per v26.1 spec (Confluence 6311379530)")
                    lines.append(f"- [ ] Local loop count stays at 0 ({rationale})")
            if expect.get("sequence_consistent"):
                lines.append("- [ ] Sequence number in summary matches sequence in detail output")
            if expect.get("no_stuck_blackhole"):
                lines.append("- [ ] No blackholed MACs in forwarding table")
            if expect.get("sticky_honored"):
                lines.append("- [ ] Sticky MAC stays on original AC, remote move rejected")
            if expect.get("check_rt2_recovery"):
                lines.append("- [ ] BGP RT-2 prefix count recovered to baseline")
            if expect.get("check_ha_traffic"):
                lines.append("- [ ] Traffic loss during HA < 1%")
            lines.append("")

        failed_layers = [
            lr for lr in sv.layers
            if lr.status in (VerdictStatus.FAIL, VerdictStatus.WARN)
        ]
        if failed_layers:
            lines.append("### Findings (automated test)")
            lines.append("")
            lines.append("| Layer | Status | Detail |")
            lines.append("|-------|--------|--------|")
            for lr in failed_layers:
                detail_short = lr.detail[:120].replace("|", "/") if lr.detail else ""
                lines.append(f"| {lr.layer} | {lr.status.value} | {detail_short} |")
            lines.append("")

    lines.extend(["---", "", "_Generated by /TEST MAC Mobility Orchestrator_"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Result persistence
# ---------------------------------------------------------------------------

def write_results(
    run_dir: Path,
    device: str,
    test_id: str,
    mode: str,
    verdict: Optional[TestVerdict] = None,
    body: Optional[Dict[str, Any]] = None,
    recipe: Optional[Dict[str, Any]] = None,
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)

    if verdict:
        verdict_dict = verdict.to_dict()
        (run_dir / "verdict.json").write_text(json.dumps(verdict_dict, indent=2))

        report = format_detailed_report(verdict)
        summary_lines = [
            f"# {test_id}",
            "",
            f"**Device:** {device}",
            f"**Mode:** {mode}",
            f"**Time:** {now_iso()}",
            f"**Overall:** {verdict.overall.value}",
            f"**Elapsed:** {verdict.total_elapsed_sec:.1f}s",
            "",
            report,
        ]

        if verdict.observability_summary:
            obs = verdict.observability_summary
            summary_lines.extend([
                "",
                "## Observability Summary",
                "",
                f"- **Commands executed:** {obs.get('total_commands_executed', 0)}",
                f"- **Anomalies detected:** {obs.get('total_anomalies_detected', 0)}",
                f"- **Scenarios:** {obs.get('scenario_count', 0)}",
            ])
            phase_cmds = obs.get("commands_per_phase", {})
            if phase_cmds:
                summary_lines.append("- **Commands per phase:**")
                for pname, cnt in phase_cmds.items():
                    summary_lines.append(f"  - {pname}: {cnt}")

        (run_dir / "SUMMARY.md").write_text("\n".join(summary_lines))

        repro_md = _generate_repro_steps(device, verdict, recipe)
        (run_dir / "REPRO_STEPS.md").write_text(repro_md)

        for sv in verdict.scenarios:
            obs_log = sv.observability_log
            if obs_log and isinstance(obs_log, dict):
                sc_dir = run_dir / sv.scenario_id
                sc_dir.mkdir(parents=True, exist_ok=True)
                (sc_dir / "observability.json").write_text(json.dumps(obs_log, indent=2))

                timeline_lines = []
                for evt in obs_log.get("timeline", []):
                    etype = evt.get("event_type", "").upper().ljust(12)
                    timeline_lines.append(f"{evt.get('timestamp', '')}  {etype}  {evt.get('message', '')}")
                if timeline_lines:
                    (sc_dir / "timeline.log").write_text("\n".join(timeline_lines))

                diffs = obs_log.get("diffs", [])
                if diffs:
                    (sc_dir / "diffs.json").write_text(json.dumps(diffs, indent=2))

    elif body:
        def _default(o):
            if hasattr(o, "__dict__"):
                return {k: v for k, v in o.__dict__.items() if not k.startswith("_")}
            return str(o)

        (run_dir / "SUMMARY.md").write_text(
            f"# {test_id}\n\n**Device:** {device}\n**Mode:** {mode}\n"
            f"**Time:** {now_iso()}\n\n```json\n{json.dumps(body, indent=2, default=_default)[:20000]}\n```"
        )

    return run_dir


# ---------------------------------------------------------------------------
# Live failure detector -- post-fail auto-diagnosis
# ---------------------------------------------------------------------------

def _live_failure_detector(
    device: str,
    scenario: Dict[str, Any],
    sv: ScenarioVerdict,
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    ac1_vlan: int,
    ac2_vlan: int,
    method: TrafficMethod,
) -> Dict[str, Any]:
    """Auto-diagnose a failed scenario immediately after verdict.

    Runs 5 diagnostic checks, classifies root cause, and determines if the
    failure is fixable. Returns a diagnosis dict consumed by execute_test()
    to decide whether to retry the scenario or continue.

    Classifications:
      orchestrator_bug  -- wrong params, invalid config, timing issue
      infra_issue       -- Spirent dead, DNAAS broken, BGP peer down
      dut_bug           -- unexpected DUT state (ghost MACs, trace errors)
      unknown           -- can't determine cause
    """
    sc_id = scenario.get("id", "?")
    trigger_action = (scenario.get("phases", {}).get("trigger") or {}).get("action", "")
    mapped_trigger = ACTION_TRIGGER_MAP.get(trigger_action, trigger_action)
    _is_pw_diag = mapped_trigger in _PW_TRIGGERS
    if _is_pw_diag and params.get("pw_evpn_name"):
        evpn_name = params["pw_evpn_name"]
    else:
        evpn_name = params.get("evpn_name", _EVPN_FALLBACK)
    test_mac = params.get("test_mac", "00:DE:AD:00:01:01")
    diag: Dict[str, Any] = {
        "scenario_id": sc_id,
        "classification": "unknown",
        "checks": [],
        "fixable": False,
        "fix_applied": False,
        "fix_description": "",
        "should_retry": False,
    }

    print(f"    [DETECTOR] Running live failure analysis for {sc_id}...", flush=True)

    # -- Check 1: MAC table state on DUT --
    try:
        mac_out = run_show(device, f"show evpn mac-table instance {evpn_name} | no-more")
        mac_entries = parse_evpn_mac_entries(mac_out)
        test_mac_found = any(e["mac"] == test_mac.lower() for e in mac_entries)
        total_macs = len(mac_entries)
        diag["checks"].append({
            "check": "mac_table",
            "total_macs": total_macs,
            "test_mac_present": test_mac_found,
            "detail": f"{total_macs} MACs in {evpn_name}, test MAC {'found' if test_mac_found else 'NOT found'}",
        })
        print(f"    [DETECTOR] MAC table: {total_macs} MACs, test MAC={test_mac_found}", flush=True)
    except Exception as exc:
        diag["checks"].append({"check": "mac_table", "error": str(exc)})

    # -- Check 2: Spirent session health --
    spirent_ok = False
    if method == TrafficMethod.SPIRENT:
        try:
            from shared.mac_trigger import _run_spirent
            status_raw = _run_spirent(["status", "--json"], timeout=15)
            try:
                status = json.loads(status_raw)
                sess = status.get("session", {})
                spirent_ok = bool(sess.get("port_reserved") and sess.get("active"))
                devices = sess.get("devices", [])
                diag["checks"].append({
                    "check": "spirent_health",
                    "session_active": sess.get("active"),
                    "port_reserved": sess.get("port_reserved"),
                    "device_count": len(devices),
                    "detail": f"Spirent {'OK' if spirent_ok else 'UNHEALTHY'}, {len(devices)} devices",
                })
            except (json.JSONDecodeError, ValueError):
                diag["checks"].append({
                    "check": "spirent_health",
                    "error": f"Cannot parse status: {status_raw[:200]}",
                })
            print(f"    [DETECTOR] Spirent: {'OK' if spirent_ok else 'UNHEALTHY'}", flush=True)
        except Exception as exc:
            diag["checks"].append({"check": "spirent_health", "error": str(exc)})

    # -- Check 3: VLAN parameter audit --
    vlan_map_raw = params.get("_ac_outer_vlan_map", "{}")
    try:
        vlan_map = {int(k): int(v) for k, v in json.loads(vlan_map_raw).items()}
    except Exception:
        vlan_map = {}
    ac1_outer = vlan_map.get(ac1_vlan)
    ac2_outer = vlan_map.get(ac2_vlan)
    vlan_issues = []
    if ac1_vlan > 255 and ac1_outer is None:
        vlan_issues.append(f"AC1 inner VLAN {ac1_vlan} has no outer VLAN mapping (Q-in-Q required)")
    if ac2_vlan > 255 and ac2_outer is None:
        vlan_issues.append(f"AC2 inner VLAN {ac2_vlan} has no outer VLAN mapping (Q-in-Q required)")
    diag["checks"].append({
        "check": "vlan_params",
        "ac1_vlan": ac1_vlan, "ac1_outer": ac1_outer,
        "ac2_vlan": ac2_vlan, "ac2_outer": ac2_outer,
        "issues": vlan_issues,
        "detail": f"AC1={ac1_vlan}(outer={ac1_outer}), AC2={ac2_vlan}(outer={ac2_outer})",
    })
    if vlan_issues:
        print(f"    [DETECTOR] VLAN issues: {'; '.join(vlan_issues)}", flush=True)
    else:
        print(f"    [DETECTOR] VLANs OK: {ac1_vlan}/{ac2_vlan} outer={ac1_outer}/{ac2_outer}", flush=True)

    # -- Check 4: BGP L2VPN EVPN peer state --
    try:
        bgp_out = run_show(device, "show bgp l2vpn evpn summary | no-more")
        bgp_info = parse_bgp_l2vpn_evpn_summary(bgp_out)
        estab = bgp_info.get("established", 0)
        total = bgp_info.get("total", 0)
        diag["checks"].append({
            "check": "bgp_evpn",
            "established": estab, "total": total,
            "detail": f"{estab}/{total} EVPN peers ESTABLISHED",
        })
        print(f"    [DETECTOR] BGP EVPN: {estab}/{total} ESTABLISHED", flush=True)
    except Exception as exc:
        diag["checks"].append({"check": "bgp_evpn", "error": str(exc)})

    # -- Check 5: DUT trace errors near failure time --
    try:
        trace_out = run_show(device, "show file traces routing_engine/bgpd_traces | tail 50 | no-more")
        error_lines = [
            ln for ln in strip_ansi(trace_out).splitlines()
            if any(kw in ln.lower() for kw in ("error", "crash", "core dump", "notification sent"))
        ]
        diag["checks"].append({
            "check": "dut_traces",
            "error_count": len(error_lines),
            "errors": error_lines[:5],
            "detail": f"{len(error_lines)} error lines in recent bgpd traces",
        })
        if error_lines:
            print(f"    [DETECTOR] DUT traces: {len(error_lines)} errors found", flush=True)
        else:
            print("    [DETECTOR] DUT traces: clean", flush=True)
    except Exception as exc:
        diag["checks"].append({"check": "dut_traces", "error": str(exc)})

    # -- Classify root cause --
    mac_check = next((c for c in diag["checks"] if c["check"] == "mac_table"), {})
    vlan_check = next((c for c in diag["checks"] if c["check"] == "vlan_params"), {})
    trace_check = next((c for c in diag["checks"] if c["check"] == "dut_traces"), {})

    total_macs = mac_check.get("total_macs", -1)
    vlan_problems = vlan_check.get("issues", [])
    trace_errors = trace_check.get("error_count", 0)

    if vlan_problems:
        diag["classification"] = "orchestrator_bug"
        diag["fix_description"] = f"VLAN mapping issue: {'; '.join(vlan_problems)}"
    elif not spirent_ok and method == TrafficMethod.SPIRENT:
        diag["classification"] = "infra_issue"
        diag["fix_description"] = "Spirent session unhealthy"
        diag["fixable"] = True
    elif total_macs == 0 and spirent_ok:
        diag["classification"] = "infra_issue"
        diag["fix_description"] = (
            "Spirent OK but 0 MACs on DUT -- likely DNAAS path or VLAN tag mismatch. "
            "Traffic is being sent but not reaching the DUT."
        )
    elif trace_errors > 0:
        diag["classification"] = "dut_bug"
        diag["fix_description"] = f"{trace_errors} trace errors found -- possible DUT bug"
    elif total_macs > 0 and not mac_check.get("test_mac_present"):
        diag["classification"] = "orchestrator_bug"
        diag["fix_description"] = (
            f"DUT has {total_macs} MACs but test MAC {test_mac} not found -- "
            "wrong MAC address in test params?"
        )

    if diag["classification"] == "infra_issue" and diag["fixable"]:
        if not spirent_ok:
            print("    [DETECTOR] Attempting Spirent reconnect...", flush=True)
            recovered = ensure_spirent_ready()
            diag["fix_applied"] = recovered
            diag["should_retry"] = recovered
            if recovered:
                print("    [DETECTOR] Spirent recovered -- scenario eligible for retry", flush=True)
            else:
                print("    [DETECTOR] Spirent recovery FAILED", flush=True)

    classification = diag["classification"]
    detail = diag.get("fix_description", "Unknown failure mode")
    print(f"    [DETECTOR] Classification: {classification} -- {detail}", flush=True)
    if diag["should_retry"]:
        print(f"    [DETECTOR] Fix applied, will RETRY scenario {sc_id}", flush=True)

    return diag


__all__ = [
    "_generate_repro_steps",
    "write_results",
    "_live_failure_detector",
]
