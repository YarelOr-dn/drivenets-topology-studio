#!/usr/bin/env python3
"""
Master orchestrator for EVPN MAC Mobility test suite (SW-204115).

Resolves DeviceContext, runs prerequisite_engine, loads recipes,
executes triggers via /SPIRENT, verifies outcomes via mac_verifiers,
produces multi-layer verdicts via verdict_engine, and auto-invokes
trace analysis via /debug-dnos on failures.

Usage:
  python3 mac_mobility_orchestrator.py --device PE-4 --discover
  python3 mac_mobility_orchestrator.py --device PE-4 --list
  python3 mac_mobility_orchestrator.py --device PE-4 --prereq TEST_mac_mob_basic_SW205160
  python3 mac_mobility_orchestrator.py --device PE-4 --prereq TEST_mac_mob_ac_ac_SW205161 --auto-fix
  python3 mac_mobility_orchestrator.py --device PE-4 --run TEST_mac_mob_basic_SW205160 --dry-run
  python3 mac_mobility_orchestrator.py --device PE-4 --run TEST_mac_mob_ac_ac_SW205161 --execute
  python3 mac_mobility_orchestrator.py --device PE-4 --run TEST_mac_mob_ac_ac_SW205161 --execute --ac1-vlan 100 --ac2-vlan 200
  python3 mac_mobility_orchestrator.py --device PE-4 --run TEST_mac_mob_ac_ac_SW205161 --execute --scale 65536
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SUITE_ROOT = Path(__file__).resolve().parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from device_discovery import discover_device_context, format_context_summary
from prerequisite_engine import check_prerequisites, format_prereq_table, get_auto_fix_plan
from shared.mac_parsers import extract_first_mac, parse_evpn_mac_count, parse_evpn_mac_entries, strip_ansi
from shared.mac_trigger import (
    TrafficMethod,
    detect_traffic_methods,
    execute_mac_move_local_to_local,
    execute_mac_move_ac_to_evpn,
    execute_mac_move_evpn_to_ac,
    execute_mac_move_ac_to_pw_via_spirent,
    execute_mac_move_pw_to_pw,
    execute_remote_pe_traffic,
    execute_traffic_via_pw,
    execute_parallel_flap_and_restart,
    execute_rapid_flap,
    execute_scale_mac_move,
    execute_back_and_forth,
    plan_mac_move,
    spirent_create_mac_block,
    spirent_create_l2_stream,
    spirent_start,
    spirent_stop,
    spirent_start_ha_baseline,
    spirent_capture_ha_loss,
    spirent_stop_ha_baseline,
    execute_mac_move_evpn_to_pw,
    execute_mac_move_pw_to_evpn,
)
from shared.mac_trigger import poll_mac_state_after_move
from shared.cross_layer_check import run_cross_layer_check
from shared.mac_verifiers import (
    compare_mac_count,
    verify_mac_present,
    verify_mac_source,
    verify_sequence_incremented,
    verify_suppression_active,
    verify_suppress_list,
    verify_sticky_mac,
    verify_sticky_rejects_remote_move,
    verify_mac_table_recovered,
    verify_mac_flags,
    verify_forwarding_state,
    verify_loop_prevention_state,
    verify_loop_count_incremented,
    verify_mobility_counter,
    verify_no_ghost_macs,
    verify_fib_mac_state,
    poll_mac_recovery,
)
from shared.verdict_engine import (
    TIMING_THRESHOLDS,
    LayerResult,
    ScenarioVerdict,
    TestVerdict,
    VerdictStatus,
    check_bgp_session_stable,
    check_control_plane,
    check_convergence_time,
    check_mac_count,
    check_mac_flags_layer,
    check_forwarding_state_layer,
    check_loop_prevention_layer,
    check_mobility_counter_layer,
    check_ghost_macs_layer,
    check_suppress_list_layer,
    check_no_trace_errors,
    check_suppression_applied,
    check_sticky_enforcement,
    check_rt2_recovery_layer,
    format_detailed_report,
    format_verdict_table,
)
from shared.trace_analyzer import (
    analyze_failure,
    analyze_mac_move_traces,
    auto_investigate,
    collect_deep_evidence,
    collect_debug_traces_window,
    disable_debug_traces,
    enable_debug_traces,
    quick_error_scan,
)
from shared.jira_bug_matcher import (
    BugMatch,
    format_bug_matches,
    search_known_bugs,
)
from shared.observability import ObservabilityCollector
from shared.device_runner import create_device_runner, get_cached_runner, cleanup_all_sessions
from shared.spirent_preflight import run_preflight as spirent_run_preflight
from shared.cross_layer_check import ProactiveXray
from shared.mac_verifiers import verify_spirent_dut_crossref, check_bgp_health_during_poll
from shared.evpn_event_knowledge import enrich_recipe_with_evpn_defaults

# Tier 1 generic engines (feature-agnostic)
try:
    _test_shared = Path(__file__).resolve().parent.parent.parent / "shared"
    if str(_test_shared) not in sys.path:
        sys.path.insert(0, str(_test_shared.parent))
    from TEST.shared.counter_tracker import (
        snapshot_counters, diff_counters,
        load_counter_commands, load_counter_expectations,
    )
    from TEST.shared.event_tracker import audit_events, load_event_expectations
    from TEST.shared.config_baseline import (
        snapshot_config, diff_config, load_baseline_config,
    )
    from TEST.shared.health_guard import (
        snapshot_health, compare_health, load_health_config,
    )
    from TEST.shared.test_isolation import (
        TestIsolationGuard, load_cleanup_commands,
    )
    from TEST.shared.continuous_poller import (
        poll_until_converged, load_poll_config,
    )
    from TEST.shared.regression_detector import run_regression_check
    from TEST.shared.report_generator import (
        FullReport, ScenarioReport, generate_full_report,
    )
    from TEST.shared.post_run_learner import learn_from_run
    from TEST.shared.vtysh_runner import VtyshRunner
    _ENGINES_AVAILABLE = True
except ImportError:
    _ENGINES_AVAILABLE = False

MANIFEST_PATH = SUITE_ROOT / "suite_manifest.json"
RESULTS_DIR = SUITE_ROOT / "results"
ACTIVE_SESSION = Path.home() / "SCALER" / "TEST" / "active_test_session.json"

ACTION_TRIGGER_MAP = {
    "traffic_on_ac1": "learn_on_ac1",
    "move_mac_ac1_to_ac2": "local_to_local",
    "rapid_move_ac1_ac2": "rapid_flap",
    "sequence_moves": "back_and_forth",
    "local_to_local_moves": "local_to_local",
    "attempt_move_to_sticky_ac": "sticky_test",
    "remote_pe_traffic": "spirent_remote_pe",
    "traffic_via_pw": "spirent_pw_traffic",
    "ncp_warm_restart": "ha_cli_command",
    "parallel_flap_and_restart": "spirent_parallel_flap_ha",
    "move_ac_to_pw": "spirent_ac_to_pw",
    "shift_to_remote_evpn": "spirent_ac_to_evpn",
    "move_pw1_to_pw2": "spirent_pw_to_pw",
    "evpn_to_ac_move": "spirent_evpn_to_ac",
    "move_evpn_to_pw": "spirent_evpn_to_pw",
    "move_pw_to_evpn": "spirent_pw_to_evpn",
}


# ---------------------------------------------------------------------------
# Command runner -- resilient fallback chain (MCP -> helper -> SSH -> error)
# ---------------------------------------------------------------------------

_device_runners: Dict[str, Any] = {}


def _default_run_show(device: str, command: str) -> str:
    """Resilient device command runner with automatic SSH fallback.

    Strategy chain:
      1. DNOS_SHOW_HELPER env var (external helper script)
      2. SSH via paramiko (credentials from ~/SCALER/db/devices.json)
      3. Explicit error (never a silent placeholder)
    """
    if device not in _device_runners:
        _device_runners[device] = create_device_runner(device)
    return _device_runners[device](device, command)


# ---------------------------------------------------------------------------
# Recipe / manifest
# ---------------------------------------------------------------------------

def load_manifest() -> Dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


def load_recipe(rel_path: str) -> Dict[str, Any]:
    return json.loads((SUITE_ROOT / rel_path).read_text())


def resolve_runtime_params(
    device: str,
    run_show: Callable[[str, str], str],
    ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if ctx is None:
        ctx = discover_device_context(device, run_show)
    params["active_ncc_id"] = str(ctx.get("active_ncc_id") or "0")
    evpn = ctx.get("evpn_name_primary") or "EVPN_INSTANCE"
    params["evpn_name"] = evpn
    mac_tbl = run_show(device, f"show evpn mac-table instance {evpn} | no-more")
    mac = extract_first_mac(mac_tbl) or "00:DE:AD:00:01:01"
    params["test_mac"] = mac
    ncp_id = str(ctx.get("first_ncp_id") or "0")
    if ncp_id == "0":
        sys_out = run_show(device, "show system | no-more")
        ncp_match = re.search(r"NCP\s+(\d+)", sys_out)
        if ncp_match:
            ncp_id = ncp_match.group(1)
    params["ncp_id"] = ncp_id
    return params


def substitute(cmd: str, params: Dict[str, str]) -> str:
    out = cmd
    for k, v in params.items():
        out = out.replace("{" + k + "}", str(v))
    return out


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def write_active_session(payload: Dict[str, Any]) -> None:
    ACTIVE_SESSION.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_SESSION.write_text(json.dumps(payload, indent=2))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_hhmm() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M")


# ---------------------------------------------------------------------------
# Dry-run (plan only, no execution)
# ---------------------------------------------------------------------------

def run_recipe_dry(
    device: str,
    recipe: Dict[str, Any],
    params: Dict[str, str],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"id": recipe.get("id"), "scenarios": []}
    for sc in recipe.get("scenarios", []):
        entry: Dict[str, Any] = {"id": sc.get("id"), "expanded_commands": [], "trigger_plan": None}
        phases = sc.get("phases") or {}
        for phase_name, phase in phases.items():
            if not isinstance(phase, dict):
                continue
            for cmd in phase.get("show_commands") or []:
                entry["expanded_commands"].append(
                    {"phase": phase_name, "cmd": substitute(cmd, params)}
                )
            ha_cmd = phase.get("ha_command")
            if ha_cmd:
                entry["expanded_commands"].append(
                    {"phase": phase_name, "cmd": substitute(ha_cmd, params), "type": "ha_trigger"}
                )
            action = phase.get("action")
            if action:
                mapped = ACTION_TRIGGER_MAP.get(action, "unknown")
                entry["trigger_plan"] = plan_mac_move(sc.get("id", ""), action, mapped)
        out["scenarios"].append(entry)
    return out


# ---------------------------------------------------------------------------
# Full execution engine
# ---------------------------------------------------------------------------

def execute_scenario(
    device: str,
    scenario: Dict[str, Any],
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    ac1_vlan: int,
    ac2_vlan: int,
    mac_count: int = 1,
    method: TrafficMethod = TrafficMethod.SPIRENT,
    run_dir: Optional[Path] = None,
    recipe: Optional[Dict[str, Any]] = None,
) -> ScenarioVerdict:
    sc_id = scenario.get("id", "unknown")
    sc_name = scenario.get("name", sc_id)
    verdict = ScenarioVerdict(scenario_id=sc_id, scenario_name=sc_name)
    phases = scenario.get("phases") or {}
    test_mac = params.get("test_mac", "00:DE:AD:00:01:01")
    evpn_name = params.get("evpn_name", "EVPN_INSTANCE")

    resilient_show = get_cached_runner(device, agent_callback=run_show)

    obs = ObservabilityCollector(
        test_id=params.get("test_id", "unknown"),
        scenario_id=sc_id,
        device=device,
    )
    if run_dir:
        obs.set_intermediate_dir(run_dir / sc_id)

    recorded_run_show = obs.wrapping_run_show(resilient_show)

    before_output = ""
    before_count = 0
    before_bgp_output = ""

    # -- Snapshot phase --
    obs.begin_phase("snapshot")
    snapshot = phases.get("snapshot") or phases.get("before_snapshot")
    if snapshot and isinstance(snapshot, dict):
        for cmd in snapshot.get("show_commands", []):
            expanded = substitute(cmd, params)
            out = recorded_run_show(device, expanded)
            if "mac-table" in cmd.lower():
                before_output = out
                before_count = parse_evpn_mac_count(out)
                obs.record_parsed("before_mac_count", before_count)
            if "bgp" in cmd.lower() and "evpn" in cmd.lower() and "summary" in cmd.lower():
                before_bgp_output = out
    if not before_bgp_output and phases.get("poll_recovery"):
        before_bgp_output = recorded_run_show(device, "show bgp l2vpn evpn summary | no-more")
    obs.save_snapshot("before", {"mac_count": before_count, "mac_output_len": len(before_output)})
    obs.end_phase()

    # -- ENGINE: Counter snapshot BEFORE trigger --
    counter_before = None
    if _ENGINES_AVAILABLE and recipe:
        try:
            counter_cmds = load_counter_commands(recipe)
            if counter_cmds:
                counter_before = snapshot_counters(device, "before_trigger", counter_cmds, resilient_show)
                obs.record_counter_snapshot(counter_before.to_dict())
        except Exception as exc:
            obs.record_anomaly(f"Counter snapshot before failed: {exc}")

    # -- HA baseline traffic (start before trigger if HA scenario with traffic check) --
    ha_baseline_info: Optional[Dict[str, Any]] = None
    verify_phase = phases.get("verify")
    ha_traffic_expected = (
        verify_phase and isinstance(verify_phase, dict)
        and verify_phase.get("expect", {}).get("check_ha_traffic")
    )
    if ha_traffic_expected and phases.get("poll_recovery") and method == TrafficMethod.SPIRENT:
        obs.begin_phase("ha_traffic_setup")
        ha_baseline_info = spirent_start_ha_baseline(
            ac1_vlan, base_mac=test_mac, rate_mbps=10, mac_count=1,
        )
        obs.record_event("ha_baseline_started", ha_baseline_info.get("detail", ""))
        time.sleep(3)
        obs.end_phase()

    # -- Trigger phase --
    obs.begin_phase("trigger")
    trigger = phases.get("trigger")
    trigger_time = now_hhmm()
    verdict.trigger_timestamp = trigger_time
    t_start = time.time()

    if trigger and isinstance(trigger, dict):
        action = trigger.get("action", "")
        ha_command = trigger.get("ha_command")
        mapped = ACTION_TRIGGER_MAP.get(action, "unknown")

        obs.record_event("trigger", f"Action={action}, mapped={mapped}, method={method.value}",
                         {"action": action, "mapped": mapped, "mac_count": mac_count})

        if mapped == "local_to_local" and method == TrafficMethod.SPIRENT:
            result = execute_mac_move_local_to_local(
                ac1_vlan, ac2_vlan, mac_count, test_mac, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Executed {mapped} ({len(result.get('steps', []))} steps)",
            ))

        elif mapped == "rapid_flap" and method == TrafficMethod.SPIRENT:
            result = execute_rapid_flap(
                ac1_vlan, ac2_vlan, flap_count=10, mac_count=mac_count,
                base_mac=test_mac, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Executed rapid_flap (10 flaps, {mac_count} MACs)",
            ))

        elif mapped == "back_and_forth" and method == TrafficMethod.SPIRENT:
            result = execute_back_and_forth(
                ac1_vlan, ac2_vlan, mac_count=mac_count,
                base_mac=test_mac, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS, "Executed back_and_forth sequence",
            ))

        elif mapped == "learn_on_ac1" and method == TrafficMethod.SPIRENT:
            spirent_create_mac_block(f"learn_v{ac1_vlan}", ac1_vlan, mac_count, test_mac)
            spirent_create_l2_stream(f"learn_s_v{ac1_vlan}", ac1_vlan, test_mac, rate_mbps=1)
            spirent_start()
            time.sleep(5)
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS, f"Learning {mac_count} MACs on AC1 vlan {ac1_vlan}",
            ))

        elif mapped == "spirent_ac_to_evpn" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_bgp_device", "")
            evi_val = int(params.get("evi", "0"))
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            result = execute_mac_move_ac_to_evpn(
                ac1_vlan, bgp_dev, test_mac,
                evi=evi_val, rd=rd_val, rt=rt_val, method=method,
            )
            fallback = any(s.get("action") == "fallback" for s in result.get("steps", []))
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.WARN if fallback else VerdictStatus.PASS,
                f"AC->EVPN move via Spirent ({len(result.get('steps', []))} steps)"
                + (" [RT-2 fallback needed]" if fallback else ""),
            ))

        elif mapped == "spirent_evpn_to_ac" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_bgp_device", "")
            result = execute_mac_move_evpn_to_ac(
                ac1_vlan, bgp_dev, test_mac, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"EVPN->AC move via Spirent ({len(result.get('steps', []))} steps)",
            ))

        elif mapped == "spirent_ac_to_pw" and method == TrafficMethod.SPIRENT:
            pw_vlan = int(params.get("pw_vlan", "0"))
            result = execute_mac_move_ac_to_pw_via_spirent(
                ac1_vlan, pw_vlan, test_mac, mac_count, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if pw_vlan > 0 else VerdictStatus.SKIP,
                f"AC->PW move via Spirent VLAN {pw_vlan}" if pw_vlan > 0
                else "AC->PW: no pw_vlan configured, manual trigger required",
            ))

        elif mapped == "spirent_remote_pe" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_bgp_device", "")
            evi_val = int(params.get("evi", "0"))
            result = execute_remote_pe_traffic(
                bgp_dev, test_mac, evi=evi_val, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if bgp_dev else VerdictStatus.SKIP,
                f"Remote PE traffic via Spirent BGP RT-2 ({test_mac})"
                if bgp_dev else "No spirent_bgp_device configured for remote PE",
            ))

        elif mapped == "spirent_pw_traffic" and method == TrafficMethod.SPIRENT:
            pw_vlan = int(params.get("pw_vlan", "0"))
            result = execute_traffic_via_pw(
                pw_vlan, test_mac, mac_count, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if pw_vlan > 0 else VerdictStatus.SKIP,
                f"PW traffic via Spirent L2 VLAN {pw_vlan}"
                if pw_vlan > 0 else "No pw_vlan for PW traffic",
            ))

        elif mapped == "spirent_parallel_flap_ha" and method == TrafficMethod.SPIRENT:
            ha_cmd = trigger.get("command", "")
            if not ha_cmd:
                ha_cmd = params.get("ha_command",
                    f"request system process restart ncc {params.get('active_ncc_id', '0')} "
                    f"routing-engine routing:bgpd")
            expanded_ha = substitute(ha_cmd, params)
            result = execute_parallel_flap_and_restart(
                ac1_vlan, ac2_vlan, expanded_ha,
                recorded_run_show, device,
                flap_count=10, mac_count=mac_count,
                base_mac=test_mac, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Parallel flap ({10}x) + HA ({expanded_ha}) completed in "
                f"{result.get('total_elapsed_sec', '?')}s",
            ))

        elif mapped == "spirent_pw_to_pw" and method == TrafficMethod.SPIRENT:
            pw1_vlan = int(params.get("pw1_vlan", "0"))
            pw2_vlan = int(params.get("pw2_vlan", "0"))
            result = execute_mac_move_pw_to_pw(
                pw1_vlan, pw2_vlan, test_mac, mac_count, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if (pw1_vlan > 0 and pw2_vlan > 0) else VerdictStatus.SKIP,
                f"PW1->PW2 move via Spirent VLANs {pw1_vlan}->{pw2_vlan}"
                if (pw1_vlan > 0 and pw2_vlan > 0) else "No pw1_vlan/pw2_vlan for PW-to-PW move",
            ))

        elif mapped == "spirent_evpn_to_pw" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_bgp_device", "")
            pw_vlan = int(params.get("pw_vlan", "0"))
            evi_val = int(params.get("evi", "0"))
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            result = execute_mac_move_evpn_to_pw(
                pw_vlan, bgp_dev, test_mac, mac_count,
                evi=evi_val, rd=rd_val, rt=rt_val, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if (pw_vlan > 0 and bgp_dev) else VerdictStatus.SKIP,
                f"EVPN->PW move via RT-2 inject + PW VLAN {pw_vlan}"
                if (pw_vlan > 0 and bgp_dev) else "Missing pw_vlan or bgp_device for EVPN->PW",
            ))

        elif mapped == "spirent_pw_to_evpn" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_bgp_device", "")
            pw_vlan = int(params.get("pw_vlan", "0"))
            evi_val = int(params.get("evi", "0"))
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            result = execute_mac_move_pw_to_evpn(
                pw_vlan, bgp_dev, test_mac, mac_count,
                evi=evi_val, rd=rd_val, rt=rt_val, method=method,
            )
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if (pw_vlan > 0 and bgp_dev) else VerdictStatus.SKIP,
                f"PW->EVPN move via PW VLAN {pw_vlan} + RT-2 inject"
                if (pw_vlan > 0 and bgp_dev) else "Missing pw_vlan or bgp_device for PW->EVPN",
            ))

        elif mapped == "ha_cli_command":
            cli_cmd = trigger.get("command", "")
            if cli_cmd:
                expanded_cli = substitute(cli_cmd, params)
                cli_out = recorded_run_show(device, expanded_cli)
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.PASS, f"HA CLI trigger: {expanded_cli}",
                    evidence=cli_out[:500],
                ))
            else:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    f"No 'command' in trigger for {action}",
                ))

        elif ha_command:
            expanded_ha = substitute(ha_command, params)
            ha_out = recorded_run_show(device, expanded_ha)
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS, f"HA trigger: {expanded_ha}",
                evidence=ha_out[:500],
            ))

        elif mapped == "sticky_test":
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.SKIP,
                f"Sticky MAC enforcement (verify-only, no traffic trigger): {action}",
            ))
        else:
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.SKIP,
                f"Unknown trigger: {action} (mapped={mapped})",
            ))

    t_trigger_done = time.time()
    obs.record_parsed("trigger_duration_sec", round(t_trigger_done - t_start, 3))
    obs.end_phase()

    # -- HA poll recovery or simple propagation wait --
    is_ha_trigger = bool(
        trigger and isinstance(trigger, dict) and (
            trigger.get("ha_command") or trigger.get("ha_type")
            or ACTION_TRIGGER_MAP.get(trigger.get("action", "")) == "ha_cli_command"
        )
    )
    poll_recovery_cfg = phases.get("poll_recovery")
    ha_convergence_sec: Optional[float] = None

    if trigger and poll_recovery_cfg and isinstance(poll_recovery_cfg, dict):
        obs.begin_phase("poll_recovery")
        reconnect_delay = poll_recovery_cfg.get("reconnect_delay_sec", 15)
        min_initial_wait = min(5, reconnect_delay)
        saved_sec = max(0, reconnect_delay - min_initial_wait)
        obs.record_event(
            "reconnect_wait",
            f"Initial wait {min_initial_wait}s (was {reconnect_delay}s fixed sleep); "
            f"SSH session auto-reconnects on poll; {saved_sec}s added to poll timeout",
        )
        time.sleep(min_initial_wait)

        poll_timeout = poll_recovery_cfg.get("timeout_sec", 120) + saved_sec
        poll_interval = poll_recovery_cfg.get("poll_interval_sec", 10)

        poll_result = poll_mac_recovery(
            device, evpn_name, before_count, poll_timeout,
            recorded_run_show, poll_interval=poll_interval,
        )
        ha_convergence_sec = poll_result.get("convergence_sec")
        obs.record_parsed("poll_recovery_result", poll_result)
        obs.record_event(
            "poll_done",
            f"Recovery {'OK' if poll_result['pass'] else 'TIMEOUT'}: "
            f"{poll_result.get('final_count', 0)}/{before_count} in "
            f"{ha_convergence_sec or poll_timeout}s",
        )

        verdict.layers.append(LayerResult(
            "ha_recovery_poll",
            VerdictStatus.PASS if poll_result["pass"] else VerdictStatus.FAIL,
            poll_result.get("detail", ""),
            evidence=json.dumps(poll_result, default=str)[:500],
        ))
        obs.end_phase()

    elif trigger:
        wait_sec = 1 if mac_count <= 100 else 3
        obs.record_event("wait", f"Propagation wait {wait_sec}s (persistent SSH, no reconnect overhead)")
        time.sleep(wait_sec)

    # -- Verify phase --
    obs.begin_phase("verify")
    verify = phases.get("verify")
    after_snapshot = phases.get("after_snapshot")
    after_output = ""

    show_cmds = []
    if after_snapshot and isinstance(after_snapshot, dict):
        show_cmds.extend(after_snapshot.get("show_commands", []))
    if verify and isinstance(verify, dict):
        show_cmds.extend(verify.get("show_commands", []))

    for cmd in show_cmds:
        expanded = substitute(cmd, params)
        out = recorded_run_show(device, expanded)
        if "mac-table" in cmd.lower() and "mac" in cmd.lower():
            after_output = out

    if not after_output and evpn_name:
        after_output = recorded_run_show(
            device,
            f"show evpn mac-table instance {evpn_name} mac {test_mac} | no-more",
        )

    t_verify_done = time.time()
    convergence = t_verify_done - t_start

    after_count = parse_evpn_mac_count(after_output)
    obs.record_parsed("after_mac_count", after_count)
    obs.save_snapshot("after", {"mac_count": after_count, "mac_output_len": len(after_output)})
    obs.compute_diff("mac_count", "show evpn mac-table", "before", "after", before_count, after_count)

    # -- Apply verdict layers based on what the scenario expects --
    expect = {}
    if verify and isinstance(verify, dict):
        expect = verify.get("expect") or {}

    if expect.get("source_contains"):
        layer = check_control_plane(
            device, evpn_name, test_mac, expect["source_contains"], recorded_run_show,
        )
        verdict.layers.append(layer)

    if expect.get("seq_increment"):
        seq_result = verify_sequence_incremented(before_output, after_output, test_mac)
        verdict.layers.append(LayerResult(
            "sequencing",
            VerdictStatus.PASS if seq_result["pass"] else VerdictStatus.FAIL,
            seq_result.get("detail", ""),
        ))

    if expect.get("new_ac_attachment"):
        source_check = verify_mac_source(after_output, test_mac, ["local"])
        verdict.layers.append(LayerResult(
            "control_plane",
            VerdictStatus.PASS if source_check["pass"] else VerdictStatus.FAIL,
            f"AC attachment: {source_check.get('detail', source_check.get('source_hint', 'unknown'))}",
        ))

    if expect.get("sanction_applied"):
        sup = verify_suppression_active(after_output, test_mac)
        verdict.layers.append(LayerResult(
            "suppression",
            VerdictStatus.PASS if sup["pass"] else VerdictStatus.FAIL,
            sup.get("detail", ""),
        ))

    if expect.get("sticky_honored"):
        sticky = verify_sticky_mac(after_output, test_mac)
        verdict.layers.append(LayerResult(
            "sticky",
            VerdictStatus.PASS if sticky["pass"] else VerdictStatus.FAIL,
            sticky.get("detail", ""),
        ))

    if expect.get("mac_count_stable_or_grows"):
        after_full = recorded_run_show(device, f"show evpn mac-table instance {evpn_name} | no-more")
        count_result = compare_mac_count(before_output, after_full)
        ok = count_result["delta"] >= 0
        verdict.layers.append(LayerResult(
            "scale",
            VerdictStatus.PASS if ok else VerdictStatus.FAIL,
            f"Count: {count_result['before']} -> {count_result['after']} (delta={count_result['delta']})",
        ))

    if expect.get("history_consistent"):
        ha_recovery = verify_mac_table_recovered(before_count, after_output)
        verdict.layers.append(LayerResult(
            "ha",
            VerdictStatus.PASS if ha_recovery["pass"] else VerdictStatus.FAIL,
            ha_recovery.get("detail", ""),
        ))

    # -- Enhanced verification layers (deep flags, forwarding, loop prevention) --
    if expect.get("check_mac_flags"):
        expected_f = expect.get("expected_flags", [])
        forbidden_f = expect.get("forbidden_flags", ["F", "D"])
        verdict.layers.append(check_mac_flags_layer(
            device, evpn_name, test_mac, expected_f, forbidden_f, recorded_run_show,
        ))

    if expect.get("check_forwarding"):
        fwd_state = expect.get("expected_fwd_state", "forwarding")
        verdict.layers.append(check_forwarding_state_layer(
            device, evpn_name, test_mac, fwd_state, recorded_run_show,
        ))

    if expect.get("check_loop_prevention"):
        lp_state = expect.get("expected_lp_state", "suppressed")
        verdict.layers.append(check_loop_prevention_layer(
            device, evpn_name, test_mac, lp_state, recorded_run_show,
        ))

    if expect.get("check_suppress_list"):
        verdict.layers.append(check_suppress_list_layer(
            device, evpn_name, test_mac, True, recorded_run_show,
        ))

    if expect.get("check_mobility_counter"):
        mobility_before = recorded_run_show(device, "show dnos-internal routing evpn mac-mobility-redis-count | no-more")
        verdict.layers.append(check_mobility_counter_layer(
            device, mobility_before, recorded_run_show, expected_increment=mac_count,
        ))

    if expect.get("check_ghost_macs"):
        verdict.layers.append(check_ghost_macs_layer(device, evpn_name, recorded_run_show))

    # -- Previously dead expect keys (now wired) --

    if expect.get("rt2_advertised"):
        rt2_out = recorded_run_show(
            device,
            f"show bgp l2vpn evpn route mac-address {test_mac} | no-more",
        )
        rt2_found = bool(test_mac and test_mac.lower() in rt2_out.lower() and "error" not in rt2_out.lower())
        rt2_detail = f"BGP RT-2 for {test_mac}: {'PRESENT' if rt2_found else 'NOT FOUND'}"
        verdict.layers.append(LayerResult(
            "rt2_advertised",
            VerdictStatus.PASS if rt2_found else VerdictStatus.FAIL,
            rt2_detail,
            evidence=rt2_out[:500],
        ))
        obs.record_parsed("rt2_advertised", {"mac": test_mac, "found": rt2_found})

    if expect.get("sequence_consistent"):
        from shared.mac_parsers import parse_mac_detail
        detail_out = recorded_run_show(
            device,
            f"show evpn mac-table detail instance {evpn_name} | no-more",
        )
        detail_entries = parse_mac_detail(detail_out)
        mac_detail = next(
            (d for d in detail_entries if d.mac == (test_mac or "").lower()), None,
        )
        summary_entries = parse_evpn_mac_entries(after_output)
        summary_entry = next(
            (e for e in summary_entries if e["mac"] == (test_mac or "").lower()), None,
        )
        if mac_detail and summary_entry and mac_detail.sequence is not None:
            seq_line_m = re.search(r"seq(?:uence)?[\s:=]+(\d+)", summary_entry.get("line", ""))
            summary_seq = int(seq_line_m.group(1)) if seq_line_m else None
            if summary_seq is not None:
                seq_ok = summary_seq == mac_detail.sequence
                verdict.layers.append(LayerResult(
                    "sequence_consistent",
                    VerdictStatus.PASS if seq_ok else VerdictStatus.FAIL,
                    f"Sequence: summary={summary_seq}, detail={mac_detail.sequence}"
                    + (" MATCH" if seq_ok else " MISMATCH"),
                ))
            else:
                verdict.layers.append(LayerResult(
                    "sequence_consistent", VerdictStatus.WARN,
                    "Sequence not found in summary output",
                ))
        else:
            verdict.layers.append(LayerResult(
                "sequence_consistent", VerdictStatus.WARN,
                f"Cannot compare: detail={'found' if mac_detail else 'missing'}, "
                f"summary={'found' if summary_entry else 'missing'}",
            ))

    if expect.get("local_loop_count_increments"):
        ac_interface = expect.get("loop_interface", "")
        if not ac_interface and evpn_name:
            cfg_out = recorded_run_show(
                device, f"show config network-services evpn instance {evpn_name} | no-more",
            )
            iface_m = re.search(r"interface\s+([\w/.-]+)", cfg_out)
            if iface_m:
                ac_interface = iface_m.group(1)
        if ac_interface:
            before_lp = recorded_run_show(
                device, f"show evpn loop-prevention interface {ac_interface} | no-more",
            )
            after_lp = recorded_run_show(
                device, f"show evpn loop-prevention interface {ac_interface} | no-more",
            )
            lp_result = verify_loop_count_incremented(before_lp, after_lp, ac_interface)
            verdict.layers.append(LayerResult(
                "local_loop_count",
                VerdictStatus.PASS if lp_result["pass"] else VerdictStatus.FAIL,
                lp_result.get("detail", ""),
            ))
        else:
            verdict.layers.append(LayerResult(
                "local_loop_count", VerdictStatus.WARN,
                "AC interface unknown -- cannot check loop count increment",
            ))

    if expect.get("no_stuck_blackhole"):
        from shared.mac_parsers import parse_forwarding_table_flags
        fwd_out = recorded_run_show(
            device,
            f"show evpn forwarding-table mac-address-table instance {evpn_name} | no-more",
        )
        fwd_entries = parse_forwarding_table_flags(fwd_out)
        blackhole_macs = [
            e for e in fwd_entries
            if e.fwd_state and e.fwd_state.lower() in ("blackhole", "drop", "blocked")
        ]
        bh_ok = len(blackhole_macs) == 0
        verdict.layers.append(LayerResult(
            "no_stuck_blackhole",
            VerdictStatus.PASS if bh_ok else VerdictStatus.FAIL,
            f"Forwarding table: {len(blackhole_macs)} blackholed MACs"
            + (f" ({', '.join(e.mac for e in blackhole_macs[:5])})" if blackhole_macs else ""),
            evidence=fwd_out[:500] if blackhole_macs else "",
        ))

    if expect.get("check_rt2_recovery") and is_ha_trigger:
        verdict.layers.append(check_rt2_recovery_layer(
            device, before_bgp_output, recorded_run_show,
        ))

    if expect.get("check_ha_traffic") and is_ha_trigger:
        from shared.mac_verifiers import verify_spirent_no_loss

        if ha_baseline_info and ha_baseline_info.get("started"):
            ha_stats = spirent_capture_ha_loss()
            obs.capture_traffic_stats(
                "ha_recovery",
                ha_stats.get("tx_frames", 0),
                ha_stats.get("rx_frames", 0),
            )
            loss_result = verify_spirent_no_loss(
                ha_stats, threshold_pct=1.0,
            )
            spirent_stop_ha_baseline(ha_baseline_info.get("stream_name"))

            verdict.layers.append(LayerResult(
                "ha_traffic",
                VerdictStatus.PASS if loss_result["pass"] else VerdictStatus.WARN,
                loss_result.get("detail", ""),
                evidence=json.dumps({
                    "tx": ha_stats.get("tx_frames"),
                    "rx": ha_stats.get("rx_frames"),
                    "loss_pct": ha_stats.get("loss_pct"),
                }, default=str)[:500],
            ))
        else:
            traffic_stats = obs.get_traffic_stats()
            if traffic_stats:
                last_stats = traffic_stats[-1] if isinstance(traffic_stats, list) else traffic_stats
                loss_result = verify_spirent_no_loss(last_stats, threshold_pct=1.0)
                verdict.layers.append(LayerResult(
                    "ha_traffic",
                    VerdictStatus.PASS if loss_result["pass"] else VerdictStatus.WARN,
                    loss_result.get("detail", ""),
                ))

    # -- Cross-layer mismatch detection (compares all show commands against each other) --
    if expect.get("cross_layer_check", True) and evpn_name and test_mac:
        mapped_trigger = ACTION_TRIGGER_MAP.get(
            (trigger or {}).get("action", ""), "default"
        ) if trigger else "default"
        enable_xray = expect.get("xray_on_mismatch", False)
        xl_result = run_cross_layer_check(
            device, evpn_name, test_mac, recorded_run_show,
            trigger_type=mapped_trigger,
            enable_xray=enable_xray,
        )
        obs.record_parsed("cross_layer_check", xl_result.to_dict())
        if xl_result.passed:
            verdict.layers.append(LayerResult(
                "cross_layer",
                VerdictStatus.PASS,
                xl_result.summary(),
            ))
        else:
            for mm in xl_result.mismatches:
                verdict.layers.append(LayerResult(
                    f"cross_layer_{mm.rule}",
                    VerdictStatus.FAIL if mm.severity == "FAIL" else VerdictStatus.WARN,
                    mm.detail,
                    evidence=json.dumps(mm.evidence, default=str)[:500] if mm.evidence else "",
                ))
            if xl_result.xray_triggered:
                obs.record_event(
                    "xray_capture",
                    f"XRAY triggered on {xl_result.fail_count} mismatches",
                    {"output_len": len(xl_result.xray_output)},
                )

    # -- Always check: BGP session stable + no trace errors --
    verdict.layers.append(check_bgp_session_stable(device, recorded_run_show))
    verdict.layers.append(check_no_trace_errors(device, trigger_time, recorded_run_show))

    # -- ENGINE: Counter diff + Event audit + BGP health + Spirent crossref --
    if _ENGINES_AVAILABLE and recipe:
        # Counter diff
        if counter_before:
            try:
                counter_cmds = load_counter_commands(recipe)
                counter_after = snapshot_counters(device, "after_verify", counter_cmds, resilient_show)
                obs.record_counter_snapshot(counter_after.to_dict())
                counter_exps = load_counter_expectations(recipe)
                if counter_exps:
                    counter_diff = diff_counters(counter_before, counter_after, counter_exps)
                    obs.record_counter_diff(counter_diff.to_dict())
                    if not counter_diff.passed:
                        for item in counter_diff.items:
                            if not item.passed:
                                verdict.layers.append(LayerResult(
                                    f"counter_{item.label}",
                                    VerdictStatus.FAIL,
                                    item.assessment,
                                ))
            except Exception as exc:
                obs.record_anomaly(f"Counter diff failed: {exc}")

        # Event audit
        try:
            event_exps = load_event_expectations(recipe)
            if event_exps:
                event_result = audit_events(
                    device, sc_id, event_exps, resilient_show,
                    timestamp_hhmm=trigger_time,
                )
                obs.record_event_audit(event_result.to_dict())
                if not event_result.passed:
                    for item in event_result.items:
                        if not item.passed:
                            verdict.layers.append(LayerResult(
                                f"event_{item.event[:30]}",
                                VerdictStatus.FAIL,
                                item.assessment,
                            ))
        except Exception as exc:
            obs.record_anomaly(f"Event audit failed: {exc}")

        # BGP health check
        try:
            bgp_out = resilient_show(device, "show bgp l2vpn evpn summary | no-more")
            bgp_health = check_bgp_health_during_poll(bgp_out)
            obs.record_bgp_health(bgp_health)
        except Exception:
            pass

    obs.end_phase()

    # -- Timing (use HA threshold when applicable) --
    if is_ha_trigger and ha_convergence_sec is not None:
        verdict.convergence_sec = round(ha_convergence_sec, 2)
        verdict.layers.append(check_convergence_time(ha_convergence_sec, "ha_recovery_sec"))
    else:
        verdict.convergence_sec = round(convergence, 2)
        threshold_key = "scale_64k_move_sec" if mac_count > 1000 else "single_mac_move_sec"
        verdict.layers.append(check_convergence_time(convergence, threshold_key))

    # -- Auto-diagnose failures (enhanced: deep evidence + Jira + auto-investigate) --
    verdict.compute_overall()
    if verdict.overall in (VerdictStatus.FAIL, VerdictStatus.ERROR):
        obs.begin_phase("auto_diagnose")
        failed_layers = [lr.layer for lr in verdict.layers if lr.status == VerdictStatus.FAIL]

        analysis = None
        for fl in failed_layers[:2]:
            analysis = analyze_failure(device, trigger_time, fl, recorded_run_show)
            if analysis.diagnosis:
                verdict.debug_hint = analysis.diagnosis
                if analysis.suggested_action:
                    verdict.debug_hint += f" | Action: {analysis.suggested_action}"
                break

        deep = collect_deep_evidence(device, evpn_name, test_mac, recorded_run_show)
        verdict.deep_evidence = deep.to_dict()

        has_critical = (
            deep.ghost_macs
            or any(e.fib_state not in ("programmed", "installed") for e in deep.fib_state)
        )
        if has_critical:
            obs.record_anomaly(f"Critical: ghost_macs={len(deep.ghost_macs)}, fib_errors present")
            enabled = enable_debug_traces(device, recorded_run_show, feature="evpn")
            if enabled:
                traces = collect_debug_traces_window(device, recorded_run_show, enabled, wait_sec=10)
                deep.debug_traces_collected = traces
                disable_debug_traces(device, recorded_run_show, enabled)
                verdict.deep_evidence = deep.to_dict()

        error_keywords = []
        for lr in verdict.layers:
            if lr.status == VerdictStatus.FAIL:
                error_keywords.extend(lr.detail.split()[:3])

        def _jira_callback(jql: str, fields: str, limit: int) -> str:
            """Search local known-bugs catalog instead of Jira API.

            Falls back gracefully -- returns empty results rather than
            failing.  The /TEST framework never writes to Jira.
            """
            known_bugs_path = Path.home() / ".cursor" / "rules" / "known-dnos-bugs.mdc"
            try:
                if known_bugs_path.exists():
                    content = known_bugs_path.read_text()
                    matches = []
                    for kw in error_keywords[:5]:
                        if kw.lower() in content.lower():
                            matches.append(kw)
                    return json.dumps({
                        "source": "local_known_bugs",
                        "matched_keywords": matches,
                        "file": str(known_bugs_path),
                    })
            except Exception:
                pass
            return json.dumps({"source": "local", "results": []})

        bugs = search_known_bugs(failed_layers, "evpn-mac-mobility", error_keywords, _jira_callback)
        verdict.known_bugs = bugs

        test_ctx = {
            "test_id": sc_id,
            "scenario_id": sc_id,
            "timestamp": trigger_time,
            "evpn_name": evpn_name,
            "test_mac": test_mac,
        }
        verdict.auto_investigate_cmd = auto_investigate(
            device, failed_layers, deep, analysis, test_ctx,
        )
        obs.end_phase()

    # -- Attach observability log to verdict --
    obs_log = obs.finalize()
    verdict.observability_log = obs_log

    return verdict


def execute_test(
    device: str,
    recipe: Dict[str, Any],
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    ac1_vlan: int = 100,
    ac2_vlan: int = 200,
    mac_count: int = 1,
    run_dir: Optional[Path] = None,
) -> TestVerdict:
    test_id = recipe.get("id", "unknown")
    params["test_id"] = test_id
    test_verdict = TestVerdict(test_id=test_id, device=device)

    # Enrich recipe with EVPN-specific defaults (Tier 2 knowledge pack)
    recipe = enrich_recipe_with_evpn_defaults(recipe)

    detected = detect_traffic_methods()
    method = detected[0] if detected else TrafficMethod.MANUAL

    preflight = spirent_run_preflight(
        vlans=[ac1_vlan, ac2_vlan], require_spirent=False,
    )
    test_verdict.preflight = preflight  # type: ignore[attr-defined]
    if preflight.get("warnings"):
        for w in preflight["warnings"]:
            print(f"  [PREFLIGHT] {w}")
    if not preflight.get("spirent_available") and method == TrafficMethod.SPIRENT:
        method = TrafficMethod.MANUAL
        print("  [PREFLIGHT] Spirent unavailable, falling back to MANUAL traffic method")

    t0 = time.time()

    # -- ENGINE: Config baseline (golden config before test) --
    config_before = None
    health_before = None
    isolation_guard = None
    if _ENGINES_AVAILABLE:
        resilient = get_cached_runner(device, agent_callback=run_show)
        try:
            baseline_cfg = load_baseline_config(recipe)
            config_before = snapshot_config(
                device, "before_test", resilient,
                sections=baseline_cfg.get("sections"),
                full_config=baseline_cfg.get("full_config", False),
            )
        except Exception as exc:
            print(f"  [ENGINE] Config baseline snapshot failed: {exc}")

        try:
            health_cfg = load_health_config(recipe)
            health_before = snapshot_health(
                device, "before_test", resilient,
                processes=health_cfg.get("processes"),
                check_crashes=health_cfg.get("check_crashes", True),
                check_alarms=health_cfg.get("check_alarms", True),
            )
        except Exception as exc:
            print(f"  [ENGINE] Health snapshot failed: {exc}")

        try:
            cleanup_cmds = load_cleanup_commands(recipe)
            isolation_guard = TestIsolationGuard(device, resilient, cleanup_cmds)
            isolation_guard.__enter__()
        except Exception as exc:
            print(f"  [ENGINE] Isolation guard setup failed: {exc}")

    for scenario in recipe.get("scenarios", []):
        sv = execute_scenario(
            device, scenario, params, run_show,
            ac1_vlan, ac2_vlan, mac_count, method,
            run_dir=run_dir,
            recipe=recipe,
        )
        test_verdict.scenarios.append(sv)

        # Smart flow: early exit on ERROR if stop_on_fail
        if sv.overall == VerdictStatus.ERROR and recipe.get("verdict", {}).get("stop_on_fail"):
            print(f"  [FLOW] Stopping on ERROR in {sv.scenario_id}")
            break

    test_verdict.total_elapsed_sec = round(time.time() - t0, 2)
    test_verdict.compute_overall()

    # -- ENGINE: Post-test health + config baseline diff + regression + cleanup --
    if _ENGINES_AVAILABLE:
        resilient = get_cached_runner(device, agent_callback=run_show)

        if health_before:
            try:
                health_cfg = load_health_config(recipe)
                health_after = snapshot_health(
                    device, "after_test", resilient,
                    processes=health_cfg.get("processes"),
                    check_crashes=health_cfg.get("check_crashes", True),
                    check_alarms=health_cfg.get("check_alarms", True),
                )
                health_result = compare_health(
                    health_before, health_after,
                    cpu_threshold=health_cfg.get("cpu_threshold_pct", 90),
                    mem_threshold=health_cfg.get("memory_threshold_pct", 90),
                )
                test_verdict.health_guard = health_result.to_dict()  # type: ignore[attr-defined]
                if not health_result.passed:
                    print(f"  [HEALTH] {health_result.summary()}")
            except Exception as exc:
                print(f"  [ENGINE] Post-test health check failed: {exc}")

        if config_before:
            try:
                baseline_cfg = load_baseline_config(recipe)
                config_after = snapshot_config(
                    device, "after_test", resilient,
                    sections=baseline_cfg.get("sections"),
                    full_config=baseline_cfg.get("full_config", False),
                )
                config_diff = diff_config(
                    config_before, config_after,
                    ignore_patterns=baseline_cfg.get("ignore_patterns"),
                )
                test_verdict.config_baseline = config_diff.to_dict()  # type: ignore[attr-defined]
                if config_diff.debris_detected:
                    print(f"  [CONFIG] {config_diff.summary()}")
            except Exception as exc:
                print(f"  [ENGINE] Config baseline diff failed: {exc}")

        if run_dir:
            try:
                regression = run_regression_check(
                    RESULTS_DIR, run_dir.name, test_verdict.to_dict(),
                )
                test_verdict.regression = regression.to_dict()  # type: ignore[attr-defined]
                if regression.has_regressions:
                    print(f"  [REGRESSION] {regression.summary()}")
            except Exception as exc:
                print(f"  [ENGINE] Regression check failed: {exc}")

        # Learning
        try:
            timing_data = {}
            for sv in test_verdict.scenarios:
                timing_data[sv.scenario_id] = sv.convergence_sec or 0
            failure_details = []
            for sv in test_verdict.scenarios:
                if sv.overall in (VerdictStatus.FAIL, VerdictStatus.ERROR):
                    for lr in sv.layers:
                        if lr.status == VerdictStatus.FAIL:
                            failure_details.append({
                                "scenario_id": sv.scenario_id,
                                "failed_layer": lr.layer,
                                "error_type": lr.layer,
                                "detail": lr.detail,
                            })
            learning_updates = learn_from_run(
                test_id, device, test_verdict.to_dict(),
                timing_data=timing_data,
                failure_details=failure_details if failure_details else None,
            )
            test_verdict.learning = learning_updates  # type: ignore[attr-defined]
        except Exception as exc:
            print(f"  [ENGINE] Learning update failed: {exc}")

        # Cleanup guarantee
        if isolation_guard:
            try:
                cleanup_result = isolation_guard.cleanup()
                test_verdict.cleanup_result = cleanup_result.to_dict()  # type: ignore[attr-defined]
            except Exception:
                pass

        # Report generation
        if run_dir:
            try:
                report = FullReport(
                    test_id=test_id,
                    test_name=recipe.get("name", test_id),
                    device=device,
                    started_at=now_iso(),
                    overall_verdict=test_verdict.overall.value,
                )
                for sv in test_verdict.scenarios:
                    sr = ScenarioReport(
                        scenario_id=sv.scenario_id,
                        scenario_name=sv.scenario_name,
                        verdict=sv.overall.value if sv.overall else "PENDING",
                        duration_sec=sv.convergence_sec or 0,
                        layer_verdicts={lr.layer: lr.status.value for lr in sv.layers},
                    )
                    report.scenarios.append(sr)
                report.config_baseline = getattr(test_verdict, "config_baseline", None)
                report.regression = getattr(test_verdict, "regression", None)
                report.health_before = health_before.to_dict() if health_before else None
                report.cleanup_result = getattr(test_verdict, "cleanup_result", None)
                report.learning_updates = getattr(test_verdict, "learning", [])
                report.completed_at = now_iso()
                generate_full_report(report, run_dir)
                print(f"  [REPORT] FULL_REPORT.md generated in {run_dir}")
            except Exception as exc:
                print(f"  [ENGINE] Report generation failed: {exc}")

    cleanup_all_sessions()

    total_cmds = 0
    total_anomalies = 0
    phase_counts: Dict[str, int] = {}
    for sv in test_verdict.scenarios:
        obs = sv.observability_log
        if obs and isinstance(obs, dict):
            meta = obs.get("meta", {})
            total_cmds += meta.get("total_commands", 0)
            total_anomalies += meta.get("total_anomalies", 0)
            for p in obs.get("phases", []):
                pname = p.get("phase_name", "unknown")
                phase_counts[pname] = phase_counts.get(pname, 0) + p.get("command_count", 0)
    test_verdict.observability_summary = {
        "total_commands_executed": total_cmds,
        "total_anomalies_detected": total_anomalies,
        "commands_per_phase": phase_counts,
        "scenario_count": len(test_verdict.scenarios),
    }

    return test_verdict


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
            f"**Result:** {sv.verdict.value}",
            "",
        ])

        phases = sc_recipe.get("phases", {})

        # Step 1: Prerequisite commands
        prereqs = recipe.get("prerequisites", []) if recipe else []
        if prereqs:
            lines.append("### Step 1: Verify Prerequisites")
            lines.append("")
            for p in prereqs:
                lines.append(f"- Check: `{p.get('check', '')}` -- Fix via: `{p.get('fix_via', 'N/A')}`")
            lines.append("")

        # Step 2: Before-snapshot (baseline commands)
        snapshot = phases.get("snapshot") or phases.get("before_snapshot")
        if snapshot and isinstance(snapshot, dict):
            cmds = snapshot.get("show_commands", [])
            if cmds:
                lines.append("### Step 2: Capture Baseline (Before Trigger)")
                lines.append("")
                lines.append("Run these commands and save output for comparison:")
                lines.append("")
                for cmd in cmds:
                    lines.append(f"```")
                    lines.append(f"{device}# {cmd}")
                    lines.append(f"```")
                    lines.append("")

        # Step 3: Trigger action
        trigger = phases.get("trigger", {})
        if trigger:
            lines.append("### Step 3: Trigger")
            lines.append("")
            action = trigger.get("action", "")
            ha_cmd = trigger.get("ha_command", "")
            method = trigger.get("method", "")
            if ha_cmd:
                lines.append(f"Run HA command on device:")
                lines.append("")
                lines.append(f"```")
                lines.append(f"{device}# {ha_cmd}")
                lines.append(f"```")
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

        # Step 4: Wait / Poll
        poll = phases.get("poll_recovery")
        if poll:
            timeout = poll.get("timeout_sec", 120)
            lines.append(f"### Step 4: Wait for Recovery (up to {timeout}s)")
            lines.append("")
            lines.append(f"Poll MAC table every {poll.get('poll_interval_sec', 10)}s until count recovers:")
            lines.append("")
            poll_cmds = poll.get("show_commands", [])
            for cmd in poll_cmds:
                lines.append(f"```")
                lines.append(f"{device}# {cmd}")
                lines.append(f"```")
            lines.append("")

        # Step 5: Verify commands
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
                    lines.append(f"```")
                    lines.append(f"{device}# {cmd}")
                    lines.append(f"```")
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
                lines.append("- [ ] BGP Type-2 route exists for this MAC (`show bgp l2vpn evpn route mac-address <MAC>`)")
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
            if expect.get("local_loop_count_increments"):
                lines.append("- [ ] Local loop count incremented on AC interface")
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

        # Actual test output (failures)
        failed_layers = [
            lr for lr in sv.layer_results
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
        (run_dir / "SUMMARY.md").write_text(
            f"# {test_id}\n\n**Device:** {device}\n**Mode:** {mode}\n"
            f"**Time:** {now_iso()}\n\n```json\n{json.dumps(body, indent=2)[:20000]}\n```"
        )

    return run_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="EVPN MAC Mobility suite (SW-204115)")
    parser.add_argument("--device", required=True, help="Device name (Network Mapper name)")
    parser.add_argument("--discover", action="store_true", help="Run device discovery only")
    parser.add_argument("--list", action="store_true", help="List all tests in manifest")
    parser.add_argument("--prereq", metavar="TEST_ID", help="Run prerequisites for a test id")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix failed prerequisites via /SPIRENT")
    parser.add_argument("--run", metavar="TEST_ID", help="Run recipe")
    parser.add_argument("--execute", action="store_true", help="Full execution with triggers + verification")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands only")
    parser.add_argument("--ac1-vlan", type=int, default=100, help="VLAN for AC1 (Spirent traffic)")
    parser.add_argument("--ac2-vlan", type=int, default=200, help="VLAN for AC2 (MAC move target)")
    parser.add_argument("--scale", type=int, default=1, help="Number of MACs (1=single, 65536=scale)")
    args = parser.parse_args()

    device = args.device
    run_show: Callable[[str, str], str] = create_device_runner(device)

    if args.list:
        m = load_manifest()
        for t in m.get("tests", []):
            print(f"{t['id']}\t{t['path']}")
        return

    if args.discover:
        ctx = discover_device_context(device, run_show)
        print(format_context_summary(ctx))
        return

    if args.prereq:
        ctx = discover_device_context(device, run_show)
        result = check_prerequisites(device, ctx, args.prereq, run_show)
        print(format_prereq_table(result))
        if args.auto_fix and result.get("auto_fixable_items"):
            fixes = get_auto_fix_plan(result)
            print(f"\n[INFO] Auto-fix plan ({len(fixes)} items):")
            for f in fixes:
                print(f"  - {f['check_id']}: {f['description']}")
                if f.get("spirent_command"):
                    print(f"    CMD: {f['spirent_command']}")
        return

    if args.run:
        m = load_manifest()
        rel = None
        for t in m.get("tests", []):
            if t["id"] == args.run:
                rel = t["path"]
                break
        if not rel:
            print(f"[ERROR] Unknown test id {args.run}", file=sys.stderr)
            sys.exit(1)

        recipe = load_recipe(rel)
        ctx = discover_device_context(device, run_show)
        pre = check_prerequisites(device, ctx, args.run, run_show)
        params = resolve_runtime_params(device, run_show, ctx)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        run_dir = RESULTS_DIR / f"RUN_{ts}_{device}" / args.run

        write_active_session({
            "active": True,
            "suite": "evpn_mac_mobility_SW204115",
            "test_id": args.run,
            "device": device,
            "ac1_vlan": args.ac1_vlan,
            "ac2_vlan": args.ac2_vlan,
            "scale": args.scale,
            "updated": now_iso(),
        })

        if args.dry_run:
            plan = run_recipe_dry(device, recipe, params)
            body = {"prerequisites": pre, "runtime_params": params, "dry_plan": plan}
            print(json.dumps(body, indent=2))
            write_results(run_dir, device, args.run, "dry-run", body=body)
            write_active_session({"active": False, "completed": now_iso()})
            return

        if args.execute:
            print(f"[INFO] Executing {args.run} on {device} (VLANs {args.ac1_vlan}/{args.ac2_vlan}, scale={args.scale})")
            verdict = execute_test(
                device, recipe, params, run_show,
                ac1_vlan=args.ac1_vlan,
                ac2_vlan=args.ac2_vlan,
                mac_count=args.scale,
                run_dir=run_dir,
            )
            write_results(run_dir, device, args.run, "execute", verdict=verdict, recipe=recipe)
            print(format_detailed_report(verdict))

            if verdict.overall == VerdictStatus.FAIL:
                print("\n[FAIL] Auto-diagnosing failures via trace analysis...")
                timestamp = verdict.scenarios[0].trigger_timestamp if verdict.scenarios else now_hhmm()
                scan = quick_error_scan(device, timestamp, run_show)
                if scan.errors_found:
                    print(f"  Errors: {scan.errors_found}")
                print(f"  Diagnosis: {scan.diagnosis}")
                if scan.suggested_action:
                    print(f"  Next step: {scan.suggested_action}")

                for sv in verdict.scenarios:
                    if sv.deep_evidence:
                        de = sv.deep_evidence
                        print(f"\n  [Deep Evidence] Scenario {sv.scenario_id}:")
                        print(f"    Suppressed MACs: {de.get('suppressed_mac_count', 0)}")
                        print(f"    Ghost MACs: {de.get('ghost_mac_count', 0)}")
                        print(f"    Mobility counter: {de.get('mobility_counter', {})}")
                        if de.get('debug_traces_collected'):
                            print(f"    Debug traces collected: {len(de['debug_traces_collected'])} snippets")
                    if sv.known_bugs:
                        print(f"\n  [Known Bugs] Scenario {sv.scenario_id}:")
                        for b in sv.known_bugs:
                            key = b.get("jira_key", "") if isinstance(b, dict) else getattr(b, "jira_key", "")
                            title = b.get("title", "") if isinstance(b, dict) else getattr(b, "title", "")
                            print(f"    - {key}: {title}")
                    if sv.auto_investigate_cmd:
                        print(f"\n  [Auto-Investigate] {sv.auto_investigate_cmd}")

            if verdict.observability_summary:
                obs = verdict.observability_summary
                print(f"\n[Observability] {obs.get('total_commands_executed', 0)} commands executed, "
                      f"{obs.get('total_anomalies_detected', 0)} anomalies detected")
                for pname, cnt in obs.get("commands_per_phase", {}).items():
                    print(f"  Phase '{pname}': {cnt} commands")
                print(f"  Results: {run_dir}/")

            write_active_session({"active": False, "completed": now_iso(), "verdict": verdict.overall.value})
            return

        plan = run_recipe_dry(device, recipe, params)
        body = {"prerequisites": pre, "runtime_params": params, "dry_plan": plan}
        write_results(run_dir, device, args.run, "plan", body=body, recipe=recipe)
        write_active_session({"active": False, "completed": now_iso()})
        print(f"[OK] Wrote {run_dir / 'SUMMARY.md'}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
