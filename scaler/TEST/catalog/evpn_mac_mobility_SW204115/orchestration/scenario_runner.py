"""Scenario runner -- hosts :func:`execute_scenario`.

Extracted from ``mac_mobility_orchestrator.py`` as Slice 5 of the orchestrator
modularization. The function itself is unchanged; only its location (and
consequently its import surface) moved. ``mac_mobility_orchestrator`` re-exports
``execute_scenario`` so all existing call sites keep working untouched.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from shared.mac_parsers import (
    extract_first_mac, parse_evpn_mac_count, parse_evpn_mac_entries,
    parse_bgp_l2vpn_evpn_summary, strip_ansi,
)
from shared.mac_trigger import (
    TrafficMethod,
    cleanup_current_scenario,
    detect_traffic_methods,
    ensure_spirent_ready,
    execute_back_and_forth,
    execute_mac_move_ac_to_evpn,
    execute_mac_move_evpn_to_ac,
    execute_mac_move_evpn_to_pw,
    execute_mac_move_local_to_local,
    execute_mac_move_pw_to_evpn,
    execute_mac_move_pw_to_pw,
    execute_parallel_flap_and_restart,
    execute_rapid_flap,
    execute_remote_pe_traffic,
    execute_traffic_via_pw,
    is_spirent_healthy,
    plan_mac_move,
    poll_until_mac_absent,
    poll_until_mac_present,
    reset_scenario_registry,
    set_device_poller,
    set_dut_mac,
    spirent_capture_ha_loss,
    spirent_create_l2_stream,
    spirent_create_mac_block,
    spirent_create_vpls_stream,
    spirent_inject_evpn_mac_route,
    spirent_inject_evpn_rt1_route,
    spirent_inject_evpn_rt4_route,
    spirent_protocol_start,
    spirent_protocol_stop,
    spirent_remove_device,
    spirent_start,
    spirent_start_ha_baseline,
    spirent_stop,
    spirent_stop_ha_baseline,
    spirent_withdraw_evpn_mac_route,
)
from shared.cross_layer_check import run_cross_layer_check
from shared.mac_verifiers import (
    check_bgp_health_during_poll,
    compare_mac_count,
    poll_mac_recovery,
    verify_mac_source,
    verify_mac_table_recovered,
    verify_sequence_incremented,
    verify_sticky_mac,
    verify_suppression_active,
)
from shared.verdict_engine import (
    LayerResult,
    ScenarioVerdict,
    VerdictStatus,
    check_all_sources_present,
    check_bgp_session_stable,
    check_control_plane,
    check_convergence_time,
    check_forwarding_state_layer,
    check_ghost_macs_layer,
    check_loop_prevention_layer,
    check_mac_flags_layer,
    check_mobility_counter_layer,
    check_no_bgp_notification_layer,
    check_no_trace_errors,
    check_rt2_recovery_layer,
    check_suppress_list_layer,
)
from shared.trace_analyzer import (
    analyze_failure,
    auto_investigate,
    clear_trace_cache,
    collect_debug_traces_window,
    collect_deep_evidence,
    disable_debug_traces,
    enable_debug_traces,
)
from shared.jira_bug_matcher import (
    search_known_bugs,
)
from shared.observability import ObservabilityCollector
from shared.device_runner import (
    get_cached_runner,
    get_persistent_ssh_session,
)
from shared.validators import (
    poll_until,
    wait_for_bgp_state,
    wait_for_pw_installed,
)
from shared.spirent_vpls_provisioner import (
    DUTProfile,
    provision_spirent_evpn_peer,
)

from .constants import (
    ACTION_TRIGGER_MAP,
    SCENARIO_CONFIG_REQUIREMENTS,
    _EVPN_FALLBACK,
    _EVPN_PEER_TRIGGERS,
    _PW_MOVE_BUDGET_SEC,
    _PW_TRIGGERS,
    _SPIRENT_PHASE_TRIGGER_VERBS,
)
from .recipe_runtime import (
    substitute,
    _apply_recipe_runtime_parameters,
    _run_recipe_phase,
    _run_spirent_phase_actions,
)
from .runtime_context import (
    _discover_spirent_ldp_loopback,
    _ensure_pw_transport_params,
    _provision_scenario_config,
    _rollback_scenario_config,
)
from .session_io import now_hhmm

# Tier 1 generic engines (feature-agnostic).  They live under TEST.shared but
# are optional -- old installations may not have them.  The orchestrator shim
# uses the same ``_ENGINES_AVAILABLE`` guard; we mirror that here so the body
# of :func:`execute_scenario` can remain verbatim.
try:
    _test_shared = Path(__file__).resolve().parent.parent.parent.parent / "shared"
    if str(_test_shared) not in sys.path:
        sys.path.insert(0, str(_test_shared.parent))
    from TEST.shared.counter_tracker import (  # noqa: F401
        CounterCommand, snapshot_counters, diff_counters,
        load_counter_commands, load_counter_expectations,
    )
    from TEST.shared.event_tracker import (  # noqa: F401
        audit_events, load_event_expectations,
    )
    _ENGINES_AVAILABLE = True
except ImportError:
    _ENGINES_AVAILABLE = False


def _load_rendered_counter_commands(recipe: Dict[str, Any], params: Dict[str, str]) -> List[Any]:
    """Load counter commands and render recipe placeholders before execution."""

    counter_cmds = load_counter_commands(recipe)
    rendered: List[Any] = []
    for cc in counter_cmds:
        rendered.append(
            CounterCommand(
                label=cc.label,
                command=substitute(cc.command, params),
                parser=cc.parser,
                regex=cc.regex,
                description=cc.description,
            )
        )
    return rendered


# ---------------------------------------------------------------------------
# Inline verdict table (chat observability)
# ---------------------------------------------------------------------------
#
# Prints a compact per-layer verdict table to stdout right after the scenario
# verdict is computed, so the operator can see in chat:
#   - Which layer of the 12-layer EVPN MAC mobility verdict failed
#   - What detail string the verdict produced
#   - A short snippet of the device output that PROVED the failure
#
# Without this, the only chat-visible failure signal was "[verdict] FAIL"
# with no breakdown -- forcing the user to read verdict.json or wait for
# SUMMARY.md (written at run-end). For long debug sessions this hides the
# actual failure cause behind hundreds of lines of timeline noise.
#
# Hard rules (intentionally narrow):
#   1. Read-only: only inspect verdict + obs; never touch device or recipe.
#   2. Never raise: caller wraps in try/except so a verdict-table bug cannot
#      mask the underlying scenario failure.
#   3. Bounded output: each evidence snippet trimmed to ~12 lines so chat
#      stays readable.

_LAYER_STATUS_GLYPH = {
    "PASS": "[PASS]",
    "FAIL": "[FAIL]",
    "WARN": "[WARN]",
    "ERROR": "[ERR ]",
    "SKIP": "[SKIP]",
}


# Mapping of layer name -> (probe regex used by the parser, "what the parser
# was looking for"). The renderer uses this to print a "Searched for: ..."
# line so the operator immediately sees WHY a layer failed without grokking
# verdict_engine.py source.
#
# Keys are matched as substrings against `LayerResult.layer`.
_LAYER_SEARCH_HINTS = {
    "rt2_advertised":   ("BGP route-type 2 entry containing the test MAC",
                          "show bgp l2vpn evpn | no-more"),
    "control_plane":    ("`Protocol: Local` line for the test MAC",
                          "show evpn mac-table mac <MAC> | no-more"),
    "mac_flags":        ("`L` (local) flag in the MAC's flag set",
                          "show evpn mac-table mac <MAC> | no-more"),
    "forwarding":       ("`forwarding` state in NCP forwarding-table",
                          "show evpn forwarding-table mac-address-table instance <EVI> mac <MAC>"),
    "ghost_macs":       ("Stale / ghost entry for the test MAC",
                          "show dnos-internal routing evpn instance <EVI> mac-table-ghost detail"),
    "no_stuck_blackhole": ("blackhole flag in forwarding table",
                            "show evpn forwarding-table mac-address-table instance <EVI>"),
    "bgp_session":      ("ESTABLISHED state for EVPN BGP peer",
                          "show bgp l2vpn evpn summary | no-more"),
    "traces":           ("ERROR / WARN lines near the trigger timestamp",
                          "show file traces routing_engine/bgpd_traces | include <HH:MM>"),
    "sequence_consistent": ("Same MAC sequence across detail+brief views",
                              "show evpn mac-table detail instance <EVPN> | no-more"),
    "cross_layer":      ("Consistent MAC presence across all 20+ layers",
                          "(synthesized from snapshot+verify show outputs)"),
    "timing":           ("Convergence within scenario threshold",
                          "(measured trigger->verify elapsed time)"),
    "trigger":          ("MAC count delta after Spirent traffic",
                          "show evpn mac-table instance <EVI> | count"),
}


def _hint_for_layer(layer_name: str):
    n = (layer_name or "").lower()
    for key, hint in _LAYER_SEARCH_HINTS.items():
        if key in n:
            return hint
    return None


def _find_evidence_command(obs: Any, evidence: str, layer_name: str):
    """Return the (command, full_output, ts) capture that produced the evidence.

    The verdict layers store the first 500 chars of a show output in their
    `evidence` field. We scan the run's command captures to find the show
    that matches, so we can print the FULL output to chat (collapsibly).
    Falls back to None if no match.
    """
    captures = getattr(obs, "_all_captures", None) or []
    if not captures:
        return None
    if evidence:
        # The evidence is rt2_out[:500] -- match by prefix on the captured output
        ev_head = evidence[:200].strip()
        if ev_head:
            for cap in reversed(captures):  # most recent first
                cap_out = (getattr(cap, "output", "") or "").strip()
                if cap_out.startswith(ev_head[:80]):
                    return cap
    # Fallback: match by layer-name -> command keyword
    layer_kw = {
        "rt2_advertised": "bgp l2vpn evpn",
        "bgp_session": "bgp l2vpn evpn summary",
        "control_plane": "show evpn mac-table mac",
        "mac_flags": "show evpn mac-table mac",
        "forwarding": "forwarding-table mac-address-table",
        "ghost_macs": "mac-table-ghost",
        "traces": "show file traces",
    }
    n = (layer_name or "").lower()
    for key, kw in layer_kw.items():
        if key in n:
            for cap in reversed(captures):
                if kw in (getattr(cap, "command", "") or "").lower():
                    return cap
    return None


def _render_collapsible_output(prefix: str, command: str, output: str,
                                 searched_for: str = "",
                                 head_lines: int = 8,
                                 tail_lines: int = 4) -> None:
    """Render a command's output as a collapsible markdown block.

    Format -- works in both terminals and chat panes that interpret markdown:

        <details><summary>Collapsed: show xxx (123 chars)</summary>

            (full output)

        </details>

    For terminals we also print the first/last few lines outside the details
    block so the operator sees the gist without expanding. The middle is
    elided with `... (+N more) ...` when it would otherwise dominate the
    chat view.
    """
    lines = (output or "").splitlines()
    n = len(lines)
    char_count = len(output or "")
    short = command if len(command) <= 90 else command[:87] + "..."
    print(f"{prefix}Command: `{short}`  ({char_count} chars, {n} lines)", flush=True)
    if searched_for:
        print(f"{prefix}Searched for: {searched_for}", flush=True)
    if n == 0:
        print(f"{prefix}Output: (empty)", flush=True)
        return

    # Always show a few head lines (visible without expanding)
    show_head = lines[:head_lines]
    show_tail = lines[-tail_lines:] if n > head_lines + tail_lines else []
    elided = max(0, n - len(show_head) - len(show_tail))

    # Open the collapsible block with a brief summary
    print(f"{prefix}<details><summary>Output ({n} lines, {char_count} chars) -- expand for full</summary>", flush=True)
    print(f"{prefix}", flush=True)
    print(f"{prefix}```", flush=True)
    for ln in show_head:
        ln = ln.rstrip()
        if len(ln) > 130:
            ln = ln[:127] + "..."
        print(f"{prefix}{ln}", flush=True)
    if elided > 0:
        print(f"{prefix}... ({elided} line(s) elided -- full output in verdict.json) ...", flush=True)
    for ln in show_tail:
        ln = ln.rstrip()
        if len(ln) > 130:
            ln = ln[:127] + "..."
        print(f"{prefix}{ln}", flush=True)
    print(f"{prefix}```", flush=True)
    print(f"{prefix}", flush=True)
    print(f"{prefix}</details>", flush=True)


def _emit_inline_verdict_table(
    *,
    scenario_id: str,
    verdict: Any,
    obs: Any,
    test_mac: str,
) -> None:
    """Print a compact verdict table + failing-layer evidence to stdout.

    Called once per scenario, immediately after `verdict.compute_overall()`.

    The chat output has three parts (chat-friendly markdown, terminal-safe):
      1. A compact "Verdict breakdown" table (every layer, status, detail).
      2. For each FAIL / WARN layer:
         - The exact show command the parser ran
         - What the parser was looking for (parsed from layer name + detail)
         - The FULL command output, in a collapsible <details> block
         - Head + elided + tail rendering so chat stays readable
      3. The verdict's debug_hint (one line at the bottom).
    """
    layers = list(getattr(verdict, "layers", []) or [])
    if not layers:
        return

    print("", flush=True)
    print(f"    ┌─ Verdict breakdown: {scenario_id} (test MAC {test_mac}) ─", flush=True)
    print(f"    │", flush=True)

    name_w = max((len(str(getattr(l, "layer", ""))) for l in layers), default=12)
    name_w = min(max(name_w, 12), 28)
    detail_w = 70
    for lr in layers:
        layer_name = str(getattr(lr, "layer", "?"))
        status_obj = getattr(lr, "status", None)
        status_str = getattr(status_obj, "value", str(status_obj or "?")).upper()
        glyph = _LAYER_STATUS_GLYPH.get(status_str, f"[{status_str[:4]:<4}]")
        detail = str(getattr(lr, "detail", "") or "").replace("\n", " ")
        if len(detail) > detail_w:
            detail = detail[: detail_w - 3] + "..."
        elapsed = getattr(lr, "elapsed_sec", 0.0) or 0.0
        print(
            f"    │ {glyph} {layer_name:<{name_w}} {detail:<{detail_w}} ({elapsed:>5.2f}s)",
            flush=True,
        )

    failing = [
        lr for lr in layers
        if getattr(getattr(lr, "status", None), "value", "").upper() in ("FAIL", "ERROR")
    ]
    warning = [
        lr for lr in layers
        if getattr(getattr(lr, "status", None), "value", "").upper() == "WARN"
    ]
    if failing or warning:
        print(f"    │", flush=True)
        prefix = "    │   "
        for lr in failing + warning:
            layer_name = str(getattr(lr, "layer", "?"))
            status_str = getattr(
                getattr(lr, "status", None), "value", "?"
            ).upper()
            detail = str(getattr(lr, "detail", "") or "")
            print(f"    │ ── Evidence for {layer_name} ({status_str}) ──", flush=True)
            print(f"{prefix}Why it failed: {detail[:140]}", flush=True)

            # What was the parser looking for
            hint = _hint_for_layer(layer_name)
            searched_for = hint[0] if hint else ""

            # Find the show command + full output that produced this evidence
            cap = _find_evidence_command(obs, str(getattr(lr, "evidence", "") or ""), layer_name)
            if cap is not None:
                cmd = getattr(cap, "command", "") or (hint[1] if hint else "(unknown)")
                full_output = getattr(cap, "output", "") or ""
                _render_collapsible_output(
                    prefix=prefix,
                    command=cmd,
                    output=full_output,
                    searched_for=searched_for,
                )
            else:
                # No matching capture; fall back to the snippet stored on the
                # layer itself + the documented expected command.
                fallback_cmd = hint[1] if hint else "(no command captured)"
                snippet = str(getattr(lr, "evidence", "") or "")
                _render_collapsible_output(
                    prefix=prefix,
                    command=fallback_cmd,
                    output=snippet,
                    searched_for=searched_for,
                )
            print(f"    │", flush=True)

    hint = getattr(verdict, "debug_hint", "") or ""
    if hint:
        print(f"    │ Hint: {hint[:240]}", flush=True)
    print(f"    └─", flush=True)
    print("", flush=True)


# ---------------------------------------------------------------------------
# execute_scenario -- kept verbatim from the orchestrator shim.
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
    dut_profile: Optional[DUTProfile] = None,
) -> ScenarioVerdict:
    sc_id = scenario.get("id", "unknown")
    sc_name = scenario.get("name", sc_id)
    verdict = ScenarioVerdict(scenario_id=sc_id, scenario_name=sc_name)
    phases = scenario.get("phases") or {}
    test_mac = params.get("test_mac", "00:DE:AD:00:01:01")

    # Tag every device command issued during this scenario in the per-run
    # transcript (EXECUTION_LOG.md / execution_log.jsonl).
    try:
        from shared.run_transcript import set_context as _xset
        _xset(phase=f"{sc_id}", scenario=sc_id, role="DUT")
    except Exception:
        pass

    # Pre-populate expected_warns so known-benign WARNs don't downgrade the verdict.
    # PW scenarios don't require EVPN peers -> bgp_session WARN is expected.
    # Sticky+PW scenarios involve relearn + PW convergence -> timing WARN is expected.
    _trigger_for_warns = (phases.get("trigger") or {}).get("action", "")
    _mapped_for_warns = ACTION_TRIGGER_MAP.get(_trigger_for_warns, "unknown")
    if _mapped_for_warns in _PW_TRIGGERS and _mapped_for_warns not in _EVPN_PEER_TRIGGERS:
        verdict.expected_warns.add("bgp_session")
    _trigger_dict_warns = phases.get("trigger")
    if isinstance(_trigger_dict_warns, dict) and _trigger_dict_warns.get("sticky"):
        verdict.expected_warns.add("timing")
    sc_mac_override = scenario.get("test_mac_override")
    if sc_mac_override:
        test_mac = sc_mac_override

    trigger_action = (phases.get("trigger") or {}).get("action", "")
    mapped_trigger = ACTION_TRIGGER_MAP.get(trigger_action, "unknown")
    _is_pw_scenario = mapped_trigger in _PW_TRIGGERS
    if _is_pw_scenario and params.get("pw_evpn_name"):
        evpn_name = params["pw_evpn_name"]
    else:
        evpn_name = params.get("evpn_name", _EVPN_FALLBACK)

    sub_params = dict(params)
    # Scenario commands should target the active instance for this scenario.
    # PW scenarios intentionally verify the PW EVI, not the suite's primary
    # AC EVI, so override the token before substituting recipe show commands.
    sub_params["evpn_name"] = evpn_name
    sub_params["scenario_evpn_name"] = evpn_name

    traffic_cfg = (recipe or {}).get("traffic_config", {})
    traffic_rate = traffic_cfg.get("rate_mbps", 1)

    reset_scenario_registry()
    clear_trace_cache()

    if method == TrafficMethod.SPIRENT and not is_spirent_healthy():
        if not ensure_spirent_ready():
            verdict.layers.append(LayerResult(
                "spirent_health", VerdictStatus.SKIP,
                "Spirent session unhealthy and auto-reconnect failed; skipping scenario",
            ))
            verdict.compute_overall()
            return verdict

    vlan_map_raw = params.get("_ac_outer_vlan_map", "{}")
    try:
        ac_outer_vlan_map: Dict[int, int] = {int(k): int(v) for k, v in json.loads(vlan_map_raw).items()}
    except Exception:
        ac_outer_vlan_map = {}
    ac1_outer = ac_outer_vlan_map.get(ac1_vlan)
    ac2_outer = ac_outer_vlan_map.get(ac2_vlan)

    resilient_show = get_cached_runner(device, agent_callback=run_show)

    obs = ObservabilityCollector(
        test_id=params.get("test_id", "unknown"),
        scenario_id=sc_id,
        device=device,
    )
    if run_dir:
        obs.set_intermediate_dir(run_dir / sc_id)

    recorded_run_show = obs.wrapping_run_show(resilient_show)

    # Merge recipe-declared runtime parameters (static + runtime + fallback)
    # so recipe placeholders such as {si_instance_name}, {test_irb_name},
    # {non_si_instance_name} resolve in snapshot / trigger / verify phases.
    # Dynamic discovery (resolve_runtime_params) wins over static values --
    # this only fills holes, never overrides.
    _apply_recipe_runtime_parameters(recipe, sub_params, recorded_run_show, device)

    before_output = ""
    before_count = 0
    before_bgp_output = ""

    # -- Snapshot phase --
    print("    [snapshot] Collecting baseline state...", flush=True)
    obs.begin_phase("snapshot")
    snapshot = phases.get("snapshot") or phases.get("before_snapshot")
    if snapshot and isinstance(snapshot, dict):
        for cmd in snapshot.get("show_commands", []):
            expanded = substitute(cmd, sub_params)
            out = recorded_run_show(device, expanded)
            cmd_l = cmd.lower()
            if cmd_l.startswith("show evpn mac-table"):
                before_output = out
                before_count = parse_evpn_mac_count(out)
                obs.record_parsed("before_mac_count", before_count)
            if "bgp" in cmd_l and "evpn" in cmd_l and "summary" in cmd_l:
                before_bgp_output = out
    if not before_bgp_output and phases.get("poll_recovery"):
        before_bgp_output = recorded_run_show(device, "show bgp l2vpn evpn summary | no-more")
    obs.save_snapshot("before", {"mac_count": before_count, "mac_output_len": len(before_output)})
    obs.end_phase()
    print(f"    [snapshot] Before MAC count: {before_count}", flush=True)

    # -- ENGINE: Counter snapshot BEFORE trigger --
    counter_before = None
    counter_cmds = []
    if _ENGINES_AVAILABLE and recipe:
        try:
            counter_cmds = _load_rendered_counter_commands(recipe, sub_params)
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
        # Justified bounded wait: STC's `start streams` returns ~500-1000ms
        # before the first packet hits the wire. 1s warmup ensures the HA
        # trigger (kill bgpd) starts against actively-flowing baseline traffic,
        # not a quiescent bridge-domain.
        time.sleep(1)
        obs.end_phase()

    # -- Config phase (legacy: phases.config.commands) --
    _run_recipe_phase(
        phases.get("config"), recipe, params, sub_params, device,
        recorded_run_show, obs, evpn_name, "config",
    )

    # -- Pre-trigger MAC cleanup (each scenario must start with clean MAC state) --
    trigger_preview = phases.get("trigger")
    _is_remote_trigger = False
    if trigger_preview and isinstance(trigger_preview, dict):
        _trigger_action = trigger_preview.get("action", "")
        _is_remote_trigger = _trigger_action in (
            "remote_pe_traffic", "remote_pe_advertises_rt2",
        )
    if trigger_preview and isinstance(trigger_preview, dict) and trigger_preview.get("action"):
        obs.begin_phase("mac_cleanup")
        if _is_remote_trigger and method == TrafficMethod.SPIRENT:
            spirent_stop()
            obs.record_event("spirent_stop_for_cleanup",
                             "Stopped L2 traffic to prevent immediate re-learning")
        cleanup_scope = str(
            trigger_preview.get("cleanup_scope")
            or recipe.get("default_cleanup_scope")
            or "all"
        ).lower()
        if cleanup_scope in {"preserve", "none", "skip"}:
            if method == TrafficMethod.SPIRENT and trigger_preview.get("stop_spirent_before_trigger"):
                spirent_stop()
                obs.record_event(
                    "spirent_stop_for_preserved_move",
                    "Stopped existing traffic while preserving DUT MAC state",
                )
            obs.record_event(
                "mac_cleanup_skipped",
                f"Preserving MAC {test_mac} before trigger (cleanup_scope={cleanup_scope})",
            )
        elif cleanup_scope == "test_mac":
            clear_cmd = f"clear evpn mac-table instance {evpn_name} mac {test_mac}"
            clear_out = recorded_run_show(device, clear_cmd)
            _clear_fail_markers = ("ERROR", "Unknown", "Invalid", "Ambiguous", "Incomplete")
            if any(m in clear_out for m in _clear_fail_markers):
                obs.record_anomaly(
                    f"Per-MAC cleanup failed for {test_mac}; preserving existing source history",
                )
            cleared = poll_until_mac_absent(
                test_mac, timeout=3.0, evpn_name=evpn_name, fallback_sleep=0.5,
            )
            obs.record_event("mac_cleanup", f"Cleared MAC table for {evpn_name}",
                             {"test_mac": test_mac, "poll_elapsed_sec": cleared})
        else:
            clear_cmd = "clear evpn mac-table"
            clear_out = recorded_run_show(device, clear_cmd)
            _clear_fail_markers = ("ERROR", "Unknown", "Invalid", "Ambiguous", "Incomplete")
            if any(m in clear_out for m in _clear_fail_markers):
                recorded_run_show(device, f"clear evpn mac-table instance {evpn_name}")
            cleared = poll_until_mac_absent(
                test_mac, timeout=3.0, evpn_name=evpn_name, fallback_sleep=0.5,
            )
            obs.record_event("mac_cleanup", f"Cleared MAC table for {evpn_name}",
                             {"test_mac": test_mac, "poll_elapsed_sec": cleared})
        obs.end_phase()
        if _ENGINES_AVAILABLE and recipe and counter_cmds:
            try:
                # Use the post-cleanup state as the real trigger baseline.
                # Pre-clean leftovers from earlier scenarios must not make a
                # fresh successful learn look like a MAC-count decrease.
                counter_before = snapshot_counters(
                    device, "before_trigger_clean", counter_cmds, resilient_show,
                )
                obs.record_counter_snapshot(counter_before.to_dict())
            except Exception as exc:
                obs.record_anomaly(f"Counter snapshot after cleanup failed: {exc}")

    # -- Setup phase (new schema: phases.setup.{config,spirent}) --
    # Runs explicit per-scenario setup from the recipe (e.g. enable
    # sticky-interface and start a Spirent L2 device to learn the MAC) BEFORE
    # the auto-detection-driven scenario_provision step. The auto-provisioner
    # below sees `already_configured` and becomes a no-op.
    _run_recipe_phase(
        phases.get("setup"), recipe, params, sub_params, device,
        recorded_run_show, obs, evpn_name, "setup",
    )

    # -- Per-scenario config provisioning (auto-configure DUT before trigger) --
    trigger = phases.get("trigger")
    _scenario_provision: Dict[str, Any] = {}
    if trigger and isinstance(trigger, dict):
        _pre_action = trigger.get("action", "")
        _pre_mapped = ACTION_TRIGGER_MAP.get(_pre_action, "unknown")
        _config_key = _pre_mapped
        if trigger.get("sticky") and _pre_mapped not in SCENARIO_CONFIG_REQUIREMENTS:
            _config_key = "sticky_test"
        if _config_key in SCENARIO_CONFIG_REQUIREMENTS:
            _scenario_provision = _provision_scenario_config(
                device, _config_key, params, recorded_run_show,
                evpn_name_override=evpn_name,
            )
            needs_relearn = (
                _scenario_provision.get("applied")
                or _scenario_provision.get("already_configured")
            ) and SCENARIO_CONFIG_REQUIREMENTS.get(_config_key, {}).get("needs_mac_relearn")
            if _scenario_provision.get("applied"):
                obs.record_event("scenario_config_provisioned",
                                 _scenario_provision.get("description", ""))
            if needs_relearn and method == TrafficMethod.SPIRENT:
                _relearn_dev = f"sticky_learn_v{ac1_vlan}"
                print("    [CONFIG-PROVISION] Re-learning MAC with sticky config active...",
                      flush=True)
                spirent_create_mac_block(
                    _relearn_dev, ac1_vlan, mac_count, test_mac,
                    outer_vlan=ac1_outer,
                )
                spirent_protocol_start(device_name=_relearn_dev)
                poll_until_mac_present(test_mac, timeout=5.0, fallback_sleep=1.5,
                                      evpn_name=evpn_name)
                spirent_protocol_stop(device_name=_relearn_dev)
                spirent_remove_device(_relearn_dev)
                print("    [CONFIG-PROVISION] MAC re-learned with sticky flag", flush=True)

    # -- Trigger phase --
    print("    [trigger] Executing trigger...", flush=True)
    obs.begin_phase("trigger")
    trigger_time = now_hhmm()
    verdict.trigger_timestamp = trigger_time
    t_start = time.time()

    if trigger and isinstance(trigger, dict):
        action = trigger.get("action", "")
        ha_command = trigger.get("ha_command")
        mapped = ACTION_TRIGGER_MAP.get(action, "unknown")

        obs.record_event("trigger", f"Action={action}, mapped={mapped}, method={method.value}",
                         {"action": action, "mapped": mapped, "mac_count": mac_count})

        pinned_flags = trigger.get("spirent_flags_pinned") if isinstance(trigger, dict) else None
        _uses_pinned_remote_ac_stream = isinstance(pinned_flags, list) and bool(pinned_flags)
        _needs_evpn = (
            mapped in ("spirent_remote_pe", "spirent_ac_to_evpn",
                       "spirent_evpn_to_ac", "spirent_evpn_to_pw",
                       "spirent_pw_to_evpn")
            and not _uses_pinned_remote_ac_stream
        )
        if _needs_evpn and method == TrafficMethod.SPIRENT:
            bgp_out = recorded_run_show(device, "show bgp l2vpn evpn summary | no-more")
            _peer_ip = params.get("spirent_peer_ip", "19.19.19.2")
            _peer_ok = False
            _bad_states = {"idle", "connect", "active", "opensent", "openconfirm"}
            for line in bgp_out.splitlines():
                if _peer_ip not in line:
                    continue
                cols = line.split()
                state_col = cols[-1].lower() if cols else ""
                if state_col not in _bad_states and _peer_ip in line:
                    _peer_ok = True
                    break
            if not _peer_ok:
                _bgp_dev = params.get("spirent_evpn_device", "") or params.get("spirent_bgp_device", "")
                _device_exists = False
                try:
                    from shared.mac_trigger import _get_existing_device_names
                    _device_exists = _bgp_dev in _get_existing_device_names(force_refresh=True)
                except Exception:
                    pass

                if not _device_exists and _bgp_dev:
                    obs.record_event("bgp_precheck_fail",
                                     f"EVPN peer device {_bgp_dev} NOT in Spirent session -- auto-provisioning")
                    print(f"    [trigger] Device {_bgp_dev} missing from session -- provisioning...", flush=True)
                    try:
                        dut_rt = params.get("pw_rt") or params.get("rt", "100:100")
                        prov_result = provision_spirent_evpn_peer(
                            device, recorded_run_show, evpn_rt=dut_rt, bgp_only=True,
                            profile=dut_profile,
                        )
                        if prov_result.ready:
                            print("    [trigger] EVPN peer provisioned successfully", flush=True)
                            _device_exists = True
                        else:
                            for s in prov_result.steps:
                                print(f"      [{s.get('status')}] {s.get('step')}: {s.get('detail', '')}", flush=True)
                    except Exception as _prov_exc:
                        print(f"    [trigger] Auto-provisioning failed: {_prov_exc}", flush=True)
                else:
                    obs.record_event("bgp_precheck_fail",
                                     f"EVPN peer {_peer_ip} NOT ESTABLISHED -- attempting protocol-start recovery")
                    print(f"    [trigger] BGP peer {_peer_ip} down -- running protocol-start recovery...", flush=True)

                if _device_exists and _bgp_dev:
                    spirent_protocol_start(device_name=_bgp_dev)
                    # Replace fixed 5s sleep loop with poll-until-ESTABLISHED.
                    # Returns the moment the peer flips out of bad state instead
                    # of always burning 5s per check.
                    _bgp_val = wait_for_bgp_state(
                        recorded_run_show, device, _peer_ip,
                        target="ESTABLISHED",
                        afi="l2vpn evpn",
                        timeout_sec=60.0,
                        interval_sec=2.0,
                    )
                    _wait_bgp = round(_bgp_val.elapsed_sec, 1)
                    _peer_ok = _bgp_val.passed
                    if _peer_ok:
                        obs.record_event("bgp_precheck_recovered",
                                         f"EVPN peer {_peer_ip} recovered after {_wait_bgp}s "
                                         f"({_bgp_val.attempts} polls)")
                        print(f"    [trigger] BGP peer recovered after {_wait_bgp}s "
                              f"({_bgp_val.attempts} polls)", flush=True)
                if not _peer_ok:
                    _recovery_msg = (
                        f"Device {_bgp_dev} missing from Spirent session and auto-provisioning failed"
                        if not _device_exists else
                        f"EVPN BGP peer {_peer_ip} not ESTABLISHED after 60s recovery"
                    )
                    obs.record_event("bgp_precheck_abort", _recovery_msg)
                    verdict.layers.append(LayerResult(
                        "trigger", VerdictStatus.FAIL,
                        f"EVPN BGP peer {_peer_ip} not ESTABLISHED -- cannot inject RT-2. "
                        f"Run: spirent_tool.py protocol-start --device-name {_bgp_dev}",
                    ))
                    obs.end_phase()
                    verdict.compute_overall()
                    return verdict

        # -- PW pre-check: verify VPLS PW is still installed before PW triggers --
        _needs_pw = mapped in _PW_TRIGGERS
        if _needs_pw and method == TrafficMethod.SPIRENT:
            pw_label = int(params.get("pw_ingress_label", "0"))
            if pw_label > 0:
                _pw_inst = params.get("pw_evpn_name", "") or evpn_name
                pw_out = recorded_run_show(device, "show evpn vpls-pw | no-more")
                _pw_ok = "Installed" in pw_out
                if not _pw_ok:
                    obs.record_event("pw_precheck_fail",
                                     "PW not Installed -- restarting VPLS protocols")
                    print("    [trigger] PW not Installed -- running protocol-start recovery...",
                          flush=True)
                    spirent_protocol_start(device_name="VPLS_PW_Peer")
                    # Replace fixed 5s sleep loop with poll-until-Installed.
                    _pw_val = wait_for_pw_installed(
                        recorded_run_show, device,
                        timeout_sec=60.0,
                        interval_sec=2.0,
                    )
                    _pw_wait = round(_pw_val.elapsed_sec, 1)
                    _pw_ok = _pw_val.passed
                    if _pw_ok:
                        if isinstance(_pw_val.last_value, dict):
                            pw_out = str(_pw_val.last_value.get("raw") or pw_out)
                        obs.record_event("pw_precheck_recovered",
                                         f"PW recovered after {_pw_wait}s "
                                         f"({_pw_val.attempts} polls)")
                        print(f"    [trigger] PW recovered after {_pw_wait}s "
                              f"({_pw_val.attempts} polls)", flush=True)
                    else:
                        obs.record_event("pw_precheck_abort",
                                         f"PW NOT Installed after 60s recovery "
                                         f"({_pw_val.attempts} polls)")
                        verdict.layers.append(LayerResult(
                            "trigger", VerdictStatus.FAIL,
                            f"VPLS PW not Installed after {_PW_MOVE_BUDGET_SEC}s recovery. "
                            f"Run: spirent_tool.py protocol-start --device-name VPLS_PW_Peer",
                        ))
                        obs.end_phase()
                        verdict.compute_overall()
                        return verdict
                # Refresh PW label in case it changed after recovery
                _label_m = re.search(r"Ingress-label\s*\n.*?\|\s*(\d+)", pw_out)
                if not _label_m:
                    for _pw_line in pw_out.splitlines():
                        _lm = re.search(r"\|\s*(\d{4,})\s*\|", _pw_line)
                        if _lm and "Installed" in _pw_line:
                            _label_m = _lm
                            break
                if _label_m:
                    _new_label = int(_label_m.group(1))
                    if _new_label != pw_label:
                        print(f"    [trigger] PW label changed: {pw_label} -> {_new_label}",
                              flush=True)
                        params["pw_ingress_label"] = str(_new_label)

        if mapped == "local_to_local" and method == TrafficMethod.SPIRENT:
            result = execute_mac_move_local_to_local(
                ac1_vlan, ac2_vlan, mac_count, test_mac, method=method,
                ac1_outer_vlan=ac1_outer, ac2_outer_vlan=ac2_outer,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Executed {mapped} ({len(result.get('steps', []))} steps)",
            ))

        elif mapped == "rapid_flap" and method == TrafficMethod.SPIRENT:
            result = execute_rapid_flap(
                ac1_vlan, ac2_vlan, flap_count=10, mac_count=mac_count,
                base_mac=test_mac, method=method,
                ac1_outer_vlan=ac1_outer, ac2_outer_vlan=ac2_outer,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Executed rapid_flap (10 flaps, {mac_count} MACs)",
            ))

        elif mapped == "back_and_forth" and method == TrafficMethod.SPIRENT:
            result = execute_back_and_forth(
                ac1_vlan, ac2_vlan, mac_count=mac_count,
                base_mac=test_mac, method=method,
                ac1_outer_vlan=ac1_outer, ac2_outer_vlan=ac2_outer,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS, "Executed back_and_forth sequence",
            ))

        elif mapped == "learn_on_ac1" and method == TrafficMethod.SPIRENT:
            forbidden_flags = trigger.get("spirent_flags_forbidden", [])
            pinned_untagged = (
                bool(trigger.get("port_mode"))
                or (
                    isinstance(pinned_flags, list)
                    and "--no-qinq" in pinned_flags
                    and isinstance(forbidden_flags, list)
                    and "--vlan" in forbidden_flags
                )
            )
            stream_vlan = 0 if pinned_untagged else ac1_vlan
            stream_outer = None if pinned_untagged else ac1_outer
            stream_name = "learn_s_untagged" if pinned_untagged else f"learn_s_v{ac1_vlan}"
            spirent_create_l2_stream(
                stream_name, stream_vlan, test_mac, rate_mbps=traffic_rate,
                outer_vlan=stream_outer,
            )
            spirent_start()
            poll_timeout = float(
                trigger.get("smoke_poll_timeout_sec")
                or trigger.get("poll_timeout_sec")
                or 8.0
            )
            waited = poll_until_mac_present(
                test_mac, timeout=poll_timeout, fallback_sleep=1.0,
                evpn_name=evpn_name,
            )
            if pinned_untagged:
                encap_info = " (untagged port-mode)"
            else:
                encap_info = f" (Q-in-Q outer={ac1_outer})" if ac1_outer else ""
            trigger_status = VerdictStatus.PASS if waited > 0 else VerdictStatus.FAIL
            verdict.layers.append(LayerResult(
                "trigger", trigger_status,
                f"Learning {mac_count} MACs on AC1{encap_info} at "
                f"{traffic_rate}Mbps (poll_timeout={poll_timeout}s, polled {waited}s)",
            ))

        elif mapped == "spirent_ac_to_evpn" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_evpn_device", "") or params.get("spirent_bgp_device", "")
            evi_val = int(params.get("evi", "0"))
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            nh_val = params.get("spirent_evpn_next_hop", "") or _discover_spirent_ldp_loopback()
            if nh_val and not params.get("spirent_evpn_next_hop"):
                params["spirent_evpn_next_hop"] = nh_val
                print(f"  [LDP-NH] Late-bound EVPN RT-2 next-hop: {nh_val}")
            result = execute_mac_move_ac_to_evpn(
                ac1_vlan, bgp_dev, test_mac,
                evi=evi_val, rd=rd_val, rt=rt_val, method=method,
                next_hop=nh_val,
            )
            fallback = any(s.get("action") == "fallback" for s in result.get("steps", []))
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.WARN if fallback else VerdictStatus.PASS,
                f"AC->EVPN move via Spirent ({len(result.get('steps', []))} steps)"
                + (" [RT-2 fallback needed]" if fallback else ""),
            ))

        elif mapped == "spirent_evpn_to_ac" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_evpn_device", "") or params.get("spirent_bgp_device", "")
            nh_val = params.get("spirent_evpn_next_hop", "") or _discover_spirent_ldp_loopback()
            if nh_val and not params.get("spirent_evpn_next_hop"):
                params["spirent_evpn_next_hop"] = nh_val
                print(f"  [LDP-NH] Late-bound EVPN RT-2 next-hop: {nh_val}")
            result = execute_mac_move_evpn_to_ac(
                ac1_vlan, bgp_dev, test_mac, method=method, next_hop=nh_val,
            )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"EVPN->AC move via Spirent ({len(result.get('steps', []))} steps)",
            ))

        elif mapped == "spirent_ac_to_pw" and method == TrafficMethod.SPIRENT:
            pw_mpls_label = int(params.get("pw_ingress_label", "0"))
            pw_outer = int(params.get("pw_outer_vlan", "0"))
            pw_inner = int(params.get("pw_inner_vlan", "0"))
            pw_dut_mac = params.get("pw_dut_mac", "")
            _pw_instance = params.get("pw_evpn_name", "") or params.get("pw_source_instance", "")

            if pw_mpls_label > 0 and (pw_outer == 0 or not pw_dut_mac):
                _ensure_pw_transport_params(params, device, recorded_run_show)
                pw_outer = int(params.get("pw_outer_vlan", "0"))
                pw_inner = int(params.get("pw_inner_vlan", "0"))
                pw_dut_mac = params.get("pw_dut_mac", "")

            if pw_mpls_label == 0:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "AC->PW: pw_ingress_label=0 -- PW not established in infra phase",
                ))
                obs.end_phase()
                verdict.compute_overall()
                return verdict

            _precreated = params.get("_pw_objects_precreated") == "true"
            _ac_stream = f"acpw_learn_v{ac1_vlan}"
            if not _precreated:
                spirent_create_l2_stream(
                    _ac_stream, ac1_vlan, src_mac=test_mac, rate_mbps=1,
                    outer_vlan=ac1_outer,
                )
            spirent_start()
            poll_until_mac_present(test_mac, timeout=8.0, fallback_sleep=2.0,
                                  evpn_name=evpn_name)
            spirent_stop()

            _vpls_sname = f"vpls_pw_label_{pw_mpls_label}"
            if _precreated:
                spirent_start()
                poll_until_mac_present(test_mac, timeout=8.0, fallback_sleep=2.0,
                                      evpn_name=_pw_instance or evpn_name)
                spirent_stop()
            else:
                _vs_o = int(params.get("_vpls_stream_outer_vlan", "0")) or pw_outer
                _vs_i = int(params.get("_vpls_stream_inner_vlan", "0")) or pw_inner
                if dut_profile and _vs_i == pw_inner:
                    _vs_i = dut_profile.vpls_neighbor_inner_vlan
                    _vs_o = dut_profile.vpls_neighbor_outer_vlan
                execute_traffic_via_pw(
                    0, test_mac, mac_count, method=method,
                    mpls_label=pw_mpls_label,
                    pw_outer_vlan=_vs_o,
                    pw_inner_vlan=_vs_i,
                    dut_mac=pw_dut_mac,
                    pw_evpn_name=_pw_instance,
                )
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"AC->PW: learned on AC (inner {ac1_vlan}), then sent via MPLS label {pw_mpls_label}",
            ))

        elif mapped == "spirent_remote_pe" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_evpn_device", "") or params.get("spirent_bgp_device", "")
            evi_val = int(params.get("evi", "0"))
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            if isinstance(pinned_flags, list) and pinned_flags:
                # Basic-learning B>/v> sources use real remote DUT ACs, not a
                # synthetic Spirent EVPN peer. Honor the recipe's teach-plan
                # flags and activate only this StreamBlock so stale streams
                # cannot mask the source-qualified MAC assertion.
                from shared.mac_trigger import _register_spirent_object, _run_spirent

                ownership = str(trigger.get("ownership_tag") or "").strip("[]")
                suffix = ownership or f"{sc_id}_{test_mac.replace(':', '')}"
                stream_name = str(trigger.get("stream_name") or f"{sc_id}_{suffix}")[:96]
                forbidden_flags = trigger.get("spirent_flags_forbidden", [])
                pinned_flag_set = {str(x) for x in pinned_flags}
                forbidden_present = [
                    str(flag) for flag in forbidden_flags
                    if isinstance(forbidden_flags, list) and str(flag) in pinned_flag_set
                ]
                if forbidden_present:
                    verdict.layers.append(LayerResult(
                        "trigger", VerdictStatus.FAIL,
                        "Remote AC Spirent flags violate recipe forbiddens: "
                        + ", ".join(forbidden_present),
                    ))
                    return verdict
                try:
                    _run_spirent(["remove-stream", "--name", stream_name], timeout=10)
                except Exception:
                    pass
                create_args = [
                    "create-stream", "--protocol", "l2",
                    *[str(x) for x in pinned_flags],
                    "--src-mac", test_mac.lower(),
                    "--dst-mac", str(trigger.get("dst_mac") or "ff:ff:ff:ff:ff:ff").lower(),
                    "--rate-mbps", str(trigger.get("rate_mbps") or traffic_rate or 1),
                    "--frame-size", str(trigger.get("frame_size") or 128),
                    "--name", stream_name,
                ]
                _run_spirent(create_args, timeout=30)
                _register_spirent_object(stream_name, "stream")
                _run_spirent(["start", "--stream-name", stream_name, "--exclusive"], timeout=20)
                duration = float(trigger.get("duration_sec") or 5)
                waited = poll_until_mac_present(
                    test_mac,
                    timeout=max(duration, 5.0),
                    fallback_sleep=1.0,
                    evpn_name=evpn_name,
                )
                trigger_status = VerdictStatus.PASS if waited > 0 else VerdictStatus.FAIL
                verdict.layers.append(LayerResult(
                    "trigger",
                    trigger_status,
                    (
                        f"Remote AC traffic via Spirent stream {stream_name} "
                        f"flags={' '.join(str(x) for x in pinned_flags)} "
                        f"(exclusive start, polled {waited}s)"
                    ),
                ))
            else:
                nh_val = params.get("spirent_evpn_next_hop", "") or _discover_spirent_ldp_loopback()
                if nh_val and not params.get("spirent_evpn_next_hop"):
                    params["spirent_evpn_next_hop"] = nh_val
                    print(f"  [LDP-NH] Late-bound EVPN RT-2 next-hop: {nh_val}")
                result = execute_remote_pe_traffic(
                    bgp_dev, test_mac, evi=evi_val, rd=rd_val, rt=rt_val, method=method,
                    next_hop=nh_val,
                )
                verdict.layers.append(LayerResult(
                    "trigger",
                    VerdictStatus.PASS if bgp_dev else VerdictStatus.SKIP,
                    f"Remote PE traffic via Spirent EVPN peer {bgp_dev} ({test_mac})"
                    if bgp_dev else "No spirent_evpn_device configured for remote PE",
                ))

        elif mapped == "spirent_pw_traffic" and method == TrafficMethod.SPIRENT:
            pw_vlan = int(params.get("pw_vlan", "0"))
            pw_mpls_label = int(params.get("pw_ingress_label", "0"))
            pw_outer = int(params.get("pw_outer_vlan", "0"))
            pw_inner = int(params.get("pw_inner_vlan", "0"))
            pw_dut_mac = params.get("pw_dut_mac", "")
            _pw_instance = params.get("pw_evpn_name", "") or params.get("pw_source_instance", "")

            if pw_mpls_label == 0:
                try:
                    from shared.mac_trigger import _get_existing_device_names, _run_spirent
                    _devs = _get_existing_device_names(force_refresh=True)
                    if "VPLS_PW_Peer" in _devs:
                        print("    [PW-CONVERGE] Starting VPLS protocols + waiting for PW...", flush=True)
                        _run_spirent(["protocol-start"], timeout=15)
                        _pw_evpn = _pw_instance or params.get("pw_test_evpn_name", "PW_TEST_ELAN")
                        _budget = int((recipe or {}).get("convergence_budget_seconds", 300))

                        def _pw_label_check():
                            _pw_out = strip_ansi(
                                recorded_run_show(device, "show evpn vpls-pw | no-more"),
                            )
                            _label_m = (
                                re.search(r"Ingress-label\s*:\s*(\d+)", _pw_out)
                                or re.search(
                                    r"\|\s*\d+\.\d+\.\d+\.\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|",
                                    _pw_out,
                                )
                            )
                            if _label_m and int(_label_m.group(1)) > 0 and _pw_evpn in _pw_out:
                                return True, {
                                    "label": int(_label_m.group(1)),
                                    "raw": _pw_out[:300],
                                }
                            return False, {"label": 0, "raw": _pw_out[:300]}

                        def _on_progress(elapsed: float, observed):
                            print(f"    [PW-CONVERGE] Waiting... ({elapsed:.0f}s)",
                                  flush=True)

                        _pw_val = poll_until(
                            _pw_label_check,
                            timeout_sec=float(_budget),
                            interval_sec=5.0,
                            on_progress=_on_progress,
                            progress_every=3,
                            progress_label=f"PW Installed for {_pw_evpn}",
                        )
                        if _pw_val.passed and isinstance(_pw_val.last_value, dict):
                            pw_mpls_label = int(_pw_val.last_value.get("label") or 0)
                            params["pw_ingress_label"] = str(pw_mpls_label)
                            print(f"    [PW-CONVERGE] PW Installed in "
                                  f"{_pw_val.elapsed_sec:.1f}s, label={pw_mpls_label} "
                                  f"({_pw_val.attempts} polls)", flush=True)
                        if pw_mpls_label == 0:
                            print(f"    [PW-CONVERGE] PW NOT installed after "
                                  f"{_pw_val.elapsed_sec:.0f}s "
                                  f"({_pw_val.attempts} polls)", flush=True)
                except Exception as exc:
                    print(f"    [PW-CONVERGE] Error: {exc}", flush=True)

            if pw_mpls_label > 0 and (pw_outer == 0 or not pw_dut_mac):
                _ensure_pw_transport_params(params, device, recorded_run_show)
                pw_outer = int(params.get("pw_outer_vlan", "0"))
                pw_inner = int(params.get("pw_inner_vlan", "0"))
                pw_dut_mac = params.get("pw_dut_mac", "")

            _vs_outer = int(params.get("_vpls_stream_outer_vlan", "0")) or pw_outer
            _vs_inner = int(params.get("_vpls_stream_inner_vlan", "0")) or pw_inner
            if dut_profile and _vs_inner == pw_inner:
                _vs_inner = dut_profile.vpls_neighbor_inner_vlan
                _vs_outer = dut_profile.vpls_neighbor_outer_vlan

            result = execute_traffic_via_pw(
                pw_vlan, test_mac, mac_count, method=method,
                mpls_label=pw_mpls_label,
                pw_outer_vlan=_vs_outer,
                pw_inner_vlan=_vs_inner,
                dut_mac=pw_dut_mac,
                pw_evpn_name=_pw_instance,
            )
            has_label = pw_mpls_label > 0
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if has_label else VerdictStatus.SKIP,
                f"PW traffic via MPLS label {pw_mpls_label} (outer={_vs_outer}, inner={_vs_inner})"
                if has_label else "No VPLS PW label found -- PW not installed after convergence wait",
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
            bgp_dev = params.get("spirent_evpn_device", "") or params.get("spirent_bgp_device", "")
            pw_vlan = int(params.get("pw_vlan", "0"))
            evi_val = 0
            rd_val = ""
            rt_val = params.get("pw_rt") or params.get("rt", "")
            nh_val = params.get("spirent_evpn_next_hop", "") or _discover_spirent_ldp_loopback()
            if nh_val and not params.get("spirent_evpn_next_hop"):
                params["spirent_evpn_next_hop"] = nh_val
                print(f"  [LDP-NH] Late-bound EVPN RT-2 next-hop: {nh_val}")
            _sticky = trigger.get("sticky", False) if trigger else False
            result = execute_mac_move_evpn_to_pw(
                pw_vlan, bgp_dev, test_mac, mac_count,
                evi=evi_val, rd=rd_val, rt=rt_val, method=method,
                sticky=_sticky, next_hop=nh_val,
            )
            _label = "sticky " if _sticky else ""
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if (pw_vlan > 0 and bgp_dev) else VerdictStatus.SKIP,
                f"{_label}EVPN->PW move via RT-2 inject + PW VLAN {pw_vlan}"
                if (pw_vlan > 0 and bgp_dev) else "Missing pw_vlan or bgp_device for EVPN->PW",
            ))

        elif mapped == "spirent_pw_to_evpn" and method == TrafficMethod.SPIRENT:
            bgp_dev = params.get("spirent_evpn_device", "") or params.get("spirent_bgp_device", "")
            pw_vlan = int(params.get("pw_vlan", "0"))
            evi_val = 0
            rd_val = ""
            rt_val = params.get("pw_rt") or params.get("rt", "")
            nh_val = params.get("spirent_evpn_next_hop", "") or _discover_spirent_ldp_loopback()
            if nh_val and not params.get("spirent_evpn_next_hop"):
                params["spirent_evpn_next_hop"] = nh_val
                print(f"  [LDP-NH] Late-bound EVPN RT-2 next-hop: {nh_val}")
            _sticky = trigger.get("sticky", False) if trigger else False
            result = execute_mac_move_pw_to_evpn(
                pw_vlan, bgp_dev, test_mac, mac_count,
                evi=evi_val, rd=rd_val, rt=rt_val, method=method,
                sticky=_sticky, next_hop=nh_val,
            )
            _label = "sticky " if _sticky else ""
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if (pw_vlan > 0 and bgp_dev) else VerdictStatus.SKIP,
                f"PW->{_label}EVPN move via PW VLAN {pw_vlan} + RT-2 inject"
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

        elif mapped == "learn_multi_macs_ac1" and method == TrafficMethod.SPIRENT:
            multi_count = max(mac_count, 3)
            spirent_create_mac_block(
                f"multi_v{ac1_vlan}", ac1_vlan, multi_count, test_mac,
                outer_vlan=ac1_outer,
            )
            spirent_create_l2_stream(
                f"multi_s_v{ac1_vlan}", ac1_vlan, test_mac, rate_mbps=traffic_rate,
                outer_vlan=ac1_outer,
            )
            spirent_start()
            waited = poll_until_mac_present(test_mac, timeout=8.0, fallback_sleep=2.0, evpn_name=evpn_name)
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Learning {multi_count} MACs on AC1 vlan {ac1_vlan} (polled {waited}s)",
            ))

        elif mapped == "wait_aging":
            hold_sec = int(params.get("custom_aging_sec", "300")) * 3
            hold_sec = min(hold_sec, 600)
            spirent_stop()
            obs.record_event("wait_aging",
                f"Stopped Spirent, waiting {hold_sec}s for MAC aging")
            # Justified test-step sleep: this IS the assertion. We are verifying
            # the device DOESN'T do something (MAC reappears) within the aging
            # window. There is no positive event to poll for -- the test point
            # is "did the absence persist for 3x aging?". Capped at 600s.
            time.sleep(hold_sec)
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"Stopped traffic, waited {hold_sec}s (3x aging)",
            ))

        elif mapped == "spirent_pw_then_ac" and method == TrafficMethod.SPIRENT:
            pw_mpls_label = int(params.get("pw_ingress_label", "0"))
            pw_outer = int(params.get("pw_outer_vlan", "0"))
            pw_inner = int(params.get("pw_inner_vlan", "0"))
            pw_dut_mac = params.get("pw_dut_mac", "")
            _pw_instance = params.get("pw_evpn_name", "") or params.get("pw_source_instance", "")

            if pw_mpls_label > 0 and (pw_outer == 0 or not pw_dut_mac):
                _ensure_pw_transport_params(params, device, recorded_run_show)
                pw_outer = int(params.get("pw_outer_vlan", "0"))
                pw_inner = int(params.get("pw_inner_vlan", "0"))
                pw_dut_mac = params.get("pw_dut_mac", "")

            if pw_mpls_label == 0:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "PW->AC: pw_ingress_label=0 -- PW not established in infra phase",
                ))
                obs.end_phase()
                verdict.compute_overall()
                return verdict

            _precreated_pw = params.get("_pw_objects_precreated") == "true"
            if _precreated_pw:
                spirent_start()
                poll_until_mac_present(test_mac, timeout=8.0, fallback_sleep=2.0,
                                      evpn_name=_pw_instance or evpn_name)
                spirent_stop()
            else:
                _vs_o2 = int(params.get("_vpls_stream_outer_vlan", "0")) or pw_outer
                _vs_i2 = int(params.get("_vpls_stream_inner_vlan", "0")) or pw_inner
                if dut_profile and _vs_i2 == pw_inner:
                    _vs_i2 = dut_profile.vpls_neighbor_inner_vlan
                    _vs_o2 = dut_profile.vpls_neighbor_outer_vlan
                execute_traffic_via_pw(
                    0, test_mac, mac_count, method=method,
                    mpls_label=pw_mpls_label,
                    pw_outer_vlan=_vs_o2,
                    pw_inner_vlan=_vs_i2,
                    dut_mac=pw_dut_mac,
                    pw_evpn_name=_pw_instance,
                )
                spirent_stop()

            _pw_then_ac_sticky = trigger.get("sticky", False) if trigger else False
            if _pw_then_ac_sticky:
                _sticky_prov = _provision_scenario_config(
                    device, "sticky_test", params, recorded_run_show,
                    evpn_name_override=evpn_name,
                )
                if _sticky_prov.get("applied"):
                    _scenario_provision = _sticky_prov
                    print("    [TRIGGER] Sticky config applied mid-trigger (PW->AC)", flush=True)

            _ac_stream = f"pwac_learn_v{ac1_vlan}"
            if not _precreated_pw:
                spirent_create_l2_stream(
                    _ac_stream, ac1_vlan, src_mac=test_mac, rate_mbps=1,
                    outer_vlan=ac1_outer,
                )
            spirent_start()
            poll_until_mac_present(test_mac, timeout=8.0, fallback_sleep=2.0,
                                  evpn_name=evpn_name)
            spirent_stop()
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.PASS,
                f"PW learn (MPLS label {pw_mpls_label}) then AC learn (inner {ac1_vlan})",
            ))

        elif mapped == "spirent_inject_rt2" and method == TrafficMethod.SPIRENT:
            # Recipe shapes supported:
            #   legacy top-level: trigger.{mac, seq, sticky, count, next_hop}
            #   G3 "params" shape: trigger.params.{base_mac|mac, count, seq, next_hop}
            _rt2_params = trigger.get("params") if isinstance(trigger.get("params"), dict) else {}
            bgp_dev = (
                params.get("spirent_evpn_device", "")
                or params.get("spirent_bgp_device", "")
            )
            _rt2_mac_raw = (
                trigger.get("mac")
                or _rt2_params.get("mac")
                or _rt2_params.get("base_mac")
                or test_mac
            )
            rt2_mac = substitute(str(_rt2_mac_raw), sub_params)
            try:
                rt2_seq = int(
                    trigger.get("seq", _rt2_params.get("seq", 0)) or 0
                )
            except (TypeError, ValueError):
                rt2_seq = 0
            try:
                rt2_count = int(
                    trigger.get("count", _rt2_params.get("count", 1)) or 1
                )
            except (TypeError, ValueError):
                rt2_count = 1
            rt2_count = max(1, rt2_count)
            rt2_sticky = bool(
                trigger.get("sticky", _rt2_params.get("sticky", False))
            )
            evi_val = int(params.get("evi", "0") or 0)
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            # Allow per-trigger next_hop override (e.g. G3 move phase pointing to AC2 LDP loopback)
            _nh_override = trigger.get("next_hop") or _rt2_params.get("next_hop")
            nh_val = (
                str(_nh_override)
                if _nh_override
                else (
                    params.get("spirent_evpn_next_hop", "")
                    or _discover_spirent_ldp_loopback()
                )
            )
            if nh_val and not params.get("spirent_evpn_next_hop") and not _nh_override:
                params["spirent_evpn_next_hop"] = nh_val
            if bgp_dev:
                rt2_result = spirent_inject_evpn_mac_route(
                    bgp_dev, rt2_mac,
                    evi=evi_val, rd=rd_val, rt=rt_val,
                    sticky=rt2_sticky, seq=rt2_seq, next_hop=nh_val,
                    count=rt2_count,
                )
                ok = bool(rt2_result.get("pass"))
                verdict.layers.append(LayerResult(
                    "trigger",
                    VerdictStatus.PASS if ok else VerdictStatus.FAIL,
                    f"RT-2 inject mac={rt2_mac} seq={rt2_seq} sticky={rt2_sticky} "
                    f"count={rt2_count} nh={nh_val}: {rt2_result.get('detail', '')}",
                    evidence=str(rt2_result.get("output", ""))[:500],
                ))
            else:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "spirent_inject_rt2: no spirent_evpn_device configured",
                ))

        elif mapped == "spirent_evpn_seq_race" and method == TrafficMethod.SPIRENT:
            # G1 evpn_evpn sequence-race family. The recipe shape is:
            #   trigger.params.{mac, seq1, seq2, nh1, nh2}
            # The dispatch action drives the semantics:
            #   inject_rt2_seq0_then_seq1      -> inject(seq1, nh1); inject(seq2, nh2)
            #   inject_rt2_same_seq_two_labels -> same mac, same seq, two distinct nh
            #   inject_two_then_withdraw_winner-> inject(seq1, nh1); inject(seq2, nh2);
            #                                     withdraw the step with higher seq
            #                                     (RFC 7432 winner). If seq1 == seq2,
            #                                     withdraws the first advertiser.
            race_action = str(trigger.get("action", "")).lower()
            bgp_dev = (
                params.get("spirent_evpn_device", "")
                or params.get("spirent_bgp_device", "")
            )
            race_params = trigger.get("params") if isinstance(trigger.get("params"), dict) else {}
            default_nh = (
                params.get("spirent_evpn_next_hop", "")
                or _discover_spirent_ldp_loopback()
            )
            race_mac = substitute(
                str(race_params.get("mac", test_mac)), sub_params,
            )
            try:
                race_seq1 = int(race_params.get("seq1", 0) or 0)
            except (TypeError, ValueError):
                race_seq1 = 0
            try:
                race_seq2 = int(race_params.get("seq2", 0) or 0)
            except (TypeError, ValueError):
                race_seq2 = 0
            race_nh1 = substitute(
                str(race_params.get("nh1", default_nh)), sub_params,
            ) or default_nh
            race_nh2 = substitute(
                str(race_params.get("nh2", default_nh)), sub_params,
            ) or default_nh
            pause_sec = float(race_params.get("pause_sec", 0.75) or 0.75)
            evi_val = int(params.get("evi", "0") or 0)
            rd_val = params.get("rd", "")
            rt_val = params.get("rt", "")
            if not bgp_dev:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "spirent_evpn_seq_race: no spirent_evpn_device configured",
                ))
            else:
                race_ok_all = True
                race_evidence = []
                # Step 1: inject (seq1, nh1)
                r1 = spirent_inject_evpn_mac_route(
                    bgp_dev, race_mac,
                    evi=evi_val, rd=rd_val, rt=rt_val,
                    sticky=False, seq=race_seq1, next_hop=race_nh1, count=1,
                )
                s1_ok = bool(r1.get("pass"))
                race_ok_all = race_ok_all and s1_ok
                race_evidence.append(
                    f"[1] inject mac={race_mac} seq={race_seq1} nh={race_nh1} "
                    f"-> {'OK' if s1_ok else 'FAIL'}"
                )
                time.sleep(pause_sec)
                # Step 2: inject (seq2, nh2)
                r2 = spirent_inject_evpn_mac_route(
                    bgp_dev, race_mac,
                    evi=evi_val, rd=rd_val, rt=rt_val,
                    sticky=False, seq=race_seq2, next_hop=race_nh2, count=1,
                )
                s2_ok = bool(r2.get("pass"))
                race_ok_all = race_ok_all and s2_ok
                race_evidence.append(
                    f"[2] inject mac={race_mac} seq={race_seq2} nh={race_nh2} "
                    f"-> {'OK' if s2_ok else 'FAIL'}"
                )
                # Step 3: withdraw winner if recipe asks. Because in the lab
                # both RT-2 advertisements come from the same Spirent BGP peer,
                # we model "withdraw winner" as withdraw-mac + re-advertise-loser
                # so the DUT sees only the loser path remaining.
                if race_action == "inject_two_then_withdraw_winner":
                    time.sleep(pause_sec)
                    # Winner = the advertisement with the higher seq (RFC 7432).
                    # On tie we consider step 1 as the first arrival.
                    if race_seq1 >= race_seq2:
                        winner_nh, winner_seq = race_nh1, race_seq1
                        loser_nh, loser_seq = race_nh2, race_seq2
                    else:
                        winner_nh, winner_seq = race_nh2, race_seq2
                        loser_nh, loser_seq = race_nh1, race_seq1
                    wd = spirent_withdraw_evpn_mac_route(
                        bgp_dev, race_mac, rd=rd_val,
                    )
                    wd_ok = bool(wd.get("pass"))
                    race_ok_all = race_ok_all and wd_ok
                    race_evidence.append(
                        f"[3a] withdraw all RT-2 for mac={race_mac} "
                        f"method={wd.get('method','?')} "
                        f"-> {'OK' if wd_ok else 'FAIL'}: {wd.get('detail','')}"
                    )
                    # Re-advertise loser so the DUT installs only the loser path.
                    time.sleep(pause_sec)
                    rl = spirent_inject_evpn_mac_route(
                        bgp_dev, race_mac,
                        evi=evi_val, rd=rd_val, rt=rt_val,
                        sticky=False, seq=loser_seq, next_hop=loser_nh, count=1,
                    )
                    rl_ok = bool(rl.get("pass"))
                    race_ok_all = race_ok_all and rl_ok
                    race_evidence.append(
                        f"[3b] re-advertise loser seq={loser_seq} nh={loser_nh} "
                        f"-> {'OK' if rl_ok else 'FAIL'} "
                        f"(winner was seq={winner_seq} nh={winner_nh})"
                    )
                verdict.layers.append(LayerResult(
                    "trigger",
                    VerdictStatus.PASS if race_ok_all else VerdictStatus.FAIL,
                    f"EVPN seq-race [{race_action}] mac={race_mac}",
                    evidence="\n".join(race_evidence)[:1000],
                ))

        elif mapped == "spirent_sanction_flap" and method == TrafficMethod.SPIRENT:
            # G4 pw_suppression_sanctions / rapid_ac_evpn_flap.
            #
            # Handler flow (matches recipe status_note):
            #   1. Commit the loop-prevention action (blackhole/shutdown/suppress)
            #      on the DUT via the active SSH session.
            #   2. Drive a cross-domain flap by alternating:
            #        a. Local L2 learn on AC1 (Spirent creates device, protocol-start,
            #           poll_until_mac_present, protocol-stop, remove_device).
            #        b. Remote RT-2 inject from the Spirent EVPN peer with
            #           incrementing seq number.
            #      Repeat for `flap_count` full cycles (a+b). Incrementing seq is
            #      what actually produces "cross-domain mobility" from the DUT's
            #      perspective -- same (MAC, instance) bouncing between local and
            #      remote sources, which is exactly what the loop-prevention
            #      engine is supposed to detect and sanction.
            sanction_params = trigger.get("params") if isinstance(trigger.get("params"), dict) else {}
            sanction = str(
                trigger.get("sanction") or sanction_params.get("sanction") or ""
            ).strip().lower()
            # DNOS 26.2 validated keywords only; drop/freeze fail commit-check.
            SANCTION_CLI = {
                "blackhole": "network-services evpn instance {evpn_name} mac-handling loop-prevention action blackhole",
                "shutdown": "network-services evpn instance {evpn_name} mac-handling loop-prevention action shutdown",
                "suppress": "network-services evpn instance {evpn_name} mac-handling loop-prevention action suppress",
            }
            try:
                flap_count = int(
                    trigger.get("flap_count", sanction_params.get("flap_count", 10)) or 10
                )
            except (TypeError, ValueError):
                flap_count = 10
            try:
                interval_sec = float(
                    trigger.get("interval_sec", sanction_params.get("interval_sec", 0.5)) or 0.5
                )
            except (TypeError, ValueError):
                interval_sec = 0.5
            # ac1_vlan arrives as a named function argument (int); only let
            # params override it when the recipe explicitly sets a positive
            # value. Previously this line unconditionally shadowed the arg
            # with int(params.get("ac1_vlan", "0") or 0), which silently
            # zeroed out the real AC1 inner VLAN and caused
            # `FLAP SKIP: ac1_vlan not set`.
            try:
                _ac1_override = int(params.get("ac1_vlan", "0") or 0)
            except (TypeError, ValueError):
                _ac1_override = 0
            if _ac1_override > 0:
                ac1_vlan = _ac1_override
            bgp_dev = (
                params.get("spirent_evpn_device", "")
                or params.get("spirent_bgp_device", "")
            )
            evpn_name_local = params.get("evpn_name", "") or evpn_name
            sanction_evidence = []
            # 1. Apply sanction config (if recipe supplied a known keyword).
            sanction_applied = False
            if sanction in SANCTION_CLI and evpn_name_local:
                s_cmd = SANCTION_CLI[sanction].format(evpn_name=evpn_name_local)
                try:
                    runner = get_cached_runner(device, agent_callback=recorded_run_show)
                    runner(device, "config")
                    runner(device, s_cmd)
                    commit_out = runner(device, "commit")
                    runner(device, "end")
                    commit_lower = strip_ansi(commit_out).lower()
                    sanction_applied = "error" not in commit_lower and "failed" not in commit_lower
                    sanction_evidence.append(
                        f"SANCTION [{sanction}] applied via: {s_cmd}"
                        f" -> {'OK' if sanction_applied else 'FAIL'}"
                        f" ({strip_ansi(commit_out)[:120]})"
                    )
                except Exception as exc:  # noqa: BLE001
                    sanction_evidence.append(
                        f"SANCTION [{sanction}] apply raised: {exc}"
                    )
            elif sanction:
                sanction_evidence.append(
                    f"SANCTION [{sanction}] SKIP: unknown keyword (expected "
                    f"{sorted(SANCTION_CLI.keys())})"
                )
            else:
                sanction_evidence.append("SANCTION: recipe did not ask for one")
                sanction_applied = True  # nothing to apply, don't fail on it
            # 2. Drive cross-domain flap. Needs both AC1 vlan AND the EVPN peer.
            flap_ok = True
            if not bgp_dev:
                flap_ok = False
                sanction_evidence.append(
                    "FLAP SKIP: spirent_evpn_device missing"
                )
            elif ac1_vlan <= 0:
                flap_ok = False
                sanction_evidence.append("FLAP SKIP: ac1_vlan not set")
            else:
                evi_val = int(params.get("evi", "0") or 0)
                rd_val = params.get("rd", "")
                rt_val = params.get("rt", "")
                nh_val = (
                    params.get("spirent_evpn_next_hop", "")
                    or _discover_spirent_ldp_loopback()
                )
                flap_dev = f"sanction_flap_v{ac1_vlan}"
                # Persist the local-learn device across cycles instead of
                # create/destroy per iteration. The original per-cycle churn
                # cost ~3-4s each and frequently outlived the 1.5s MAC
                # learn poll (observed ~11s for a fresh device to broadcast
                # ARP and have the DUT install the MAC). Creating once and
                # toggling protocol-start/stop per cycle is O(1) cost after
                # the first spin-up and matches SC04's tight cadence.
                flap_dev_ready = False
                try:
                    spirent_create_mac_block(
                        flap_dev, ac1_vlan, 1, test_mac,
                        outer_vlan=ac1_outer,
                    )
                    flap_dev_ready = True
                except Exception as exc:  # noqa: BLE001
                    flap_ok = False
                    sanction_evidence.append(
                        f"FLAP INIT: local device create raised: {exc}"
                    )
                # Per-cycle MAC learn timeout: floor at 5s so a cold
                # local learn has enough time to land in the bridge FDB.
                _learn_timeout = max(interval_sec, 5.0)
                _learn_poll = min(interval_sec, 1.0) if interval_sec > 0 else 0.5
                for cycle in range(flap_count):
                    if not flap_dev_ready:
                        break
                    # (a) re-learn the MAC locally on AC1 by bouncing the
                    # protocol stack; DUT will see a local learn event.
                    try:
                        spirent_protocol_start(device_name=flap_dev)
                        poll_until_mac_present(
                            test_mac,
                            timeout=_learn_timeout,
                            fallback_sleep=_learn_poll,
                            evpn_name=evpn_name_local,
                        )
                        spirent_protocol_stop(device_name=flap_dev)
                    except Exception as exc:  # noqa: BLE001
                        flap_ok = False
                        sanction_evidence.append(
                            f"FLAP[{cycle}] local-learn raised: {exc}"
                        )
                        break
                    # (b) remote RT-2 inject (monotonically incrementing seq)
                    inj = spirent_inject_evpn_mac_route(
                        bgp_dev, test_mac,
                        evi=evi_val, rd=rd_val, rt=rt_val,
                        sticky=False, seq=cycle + 1,
                        next_hop=nh_val, count=1,
                    )
                    step_ok = bool(inj.get("pass"))
                    flap_ok = flap_ok and step_ok
                    sanction_evidence.append(
                        f"FLAP[{cycle}] local->remote seq={cycle + 1} "
                        f"-> {'OK' if step_ok else 'FAIL'}"
                    )
                    time.sleep(interval_sec)
                # Tear down the persistent flap device once, regardless of
                # per-cycle outcome, so we don't leak a half-configured
                # device between scenario runs.
                if flap_dev_ready:
                    try:
                        spirent_remove_device(flap_dev)
                    except Exception as exc:  # noqa: BLE001
                        sanction_evidence.append(
                            f"FLAP TEARDOWN: remove_device raised: {exc}"
                        )
            overall_ok = sanction_applied and flap_ok
            verdict.layers.append(LayerResult(
                "trigger",
                VerdictStatus.PASS if overall_ok else VerdictStatus.FAIL,
                f"Sanction=[{sanction or 'none'}] flap_count={flap_count} "
                f"interval={interval_sec}s",
                evidence="\n".join(sanction_evidence)[:1200],
            ))

        elif mapped == "spirent_remote_seq_updates" and method == TrafficMethod.SPIRENT:
            # G4 rapid_remote_seq_updates (SC04 / SW-192019):
            #   Configure the sanction action (if specified) then fire N RT-2
            #   updates for the SAME MAC with monotonically incrementing
            #   sequence numbers from the remote peer. There is NO local leg,
            #   so cross-domain suppression MUST NOT trigger. This validates
            #   that pure remote churn is not conflated with local mobility.
            bgp_dev = (
                params.get("spirent_evpn_device", "")
                or params.get("spirent_bgp_device", "")
            )
            seq_params = trigger.get("params") if isinstance(trigger.get("params"), dict) else {}
            # The recipe uses flap_count (#RT-2 updates) as the primary knob;
            # count/updates is kept for back-compat with other callers.
            try:
                updates = int(
                    trigger.get("flap_count",
                        seq_params.get("flap_count",
                            trigger.get("count",
                                seq_params.get("count", 10)))) or 10
                )
            except (TypeError, ValueError):
                updates = 10
            try:
                start_seq = int(
                    trigger.get("start_seq", seq_params.get("start_seq", 1)) or 1
                )
            except (TypeError, ValueError):
                start_seq = 1
            try:
                interval_sec = float(
                    trigger.get("interval_sec", seq_params.get("interval_sec", 0.3)) or 0.3
                )
            except (TypeError, ValueError):
                interval_sec = 0.3
            seq_mac = substitute(
                str(trigger.get("mac", seq_params.get("mac", test_mac))),
                sub_params,
            )
            nh_val = (
                str(trigger.get("next_hop") or seq_params.get("next_hop") or "")
                or params.get("spirent_evpn_next_hop", "")
                or _discover_spirent_ldp_loopback()
            )
            sanction = str(
                trigger.get("sanction") or seq_params.get("sanction") or ""
            ).strip().lower()
            SANCTION_CLI = {
                "blackhole": "network-services evpn instance {evpn_name} mac-handling loop-prevention action blackhole",
                "shutdown": "network-services evpn instance {evpn_name} mac-handling loop-prevention action shutdown",
                "suppress": "network-services evpn instance {evpn_name} mac-handling loop-prevention action suppress",
            }
            evpn_name_local = params.get("evpn_name", "") or evpn_name
            seq_evidence = []
            # Apply sanction config first if requested.
            sanction_applied = True  # no-op by default
            if sanction and sanction in SANCTION_CLI and evpn_name_local:
                s_cmd = SANCTION_CLI[sanction].format(evpn_name=evpn_name_local)
                try:
                    runner = get_cached_runner(device, agent_callback=recorded_run_show)
                    runner(device, "config")
                    runner(device, s_cmd)
                    commit_out = runner(device, "commit")
                    runner(device, "end")
                    commit_lower = strip_ansi(commit_out).lower()
                    sanction_applied = "error" not in commit_lower and "failed" not in commit_lower
                    seq_evidence.append(
                        f"SANCTION [{sanction}]: {s_cmd} -> "
                        f"{'OK' if sanction_applied else 'FAIL'}"
                    )
                except Exception as exc:  # noqa: BLE001
                    sanction_applied = False
                    seq_evidence.append(
                        f"SANCTION [{sanction}] raised: {exc}"
                    )
            if not bgp_dev:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "spirent_remote_seq_updates: no spirent_evpn_device configured",
                    evidence="\n".join(seq_evidence)[:500],
                ))
            else:
                seq_ok_all = True
                evi_val = int(params.get("evi", "0") or 0)
                rd_val = params.get("rd", "")
                rt_val = params.get("rt", "")
                for i in range(updates):
                    this_seq = start_seq + i
                    inj = spirent_inject_evpn_mac_route(
                        bgp_dev, seq_mac,
                        evi=evi_val, rd=rd_val, rt=rt_val,
                        sticky=False, seq=this_seq, next_hop=nh_val, count=1,
                    )
                    step_ok = bool(inj.get("pass"))
                    seq_ok_all = seq_ok_all and step_ok
                    seq_evidence.append(
                        f"[{i}] seq={this_seq} -> {'OK' if step_ok else 'FAIL'}"
                    )
                    time.sleep(interval_sec)
                overall_ok = sanction_applied and seq_ok_all
                verdict.layers.append(LayerResult(
                    "trigger",
                    VerdictStatus.PASS if overall_ok else VerdictStatus.FAIL,
                    f"Remote seq updates: {updates} at interval={interval_sec}s "
                    f"mac={seq_mac} nh={nh_val} sanction=[{sanction or 'none'}]",
                    evidence="\n".join(seq_evidence)[:1200],
                ))

        elif mapped == "spirent_vpls_stream" and method == TrafficMethod.SPIRENT:
            try:
                pw_label = int(params.get("pw_ingress_label", "0") or 0)
            except (TypeError, ValueError):
                pw_label = 0
            args = trigger.get("args", {}) if isinstance(trigger.get("args"), dict) else {}
            inner_mac = substitute(
                str(args.get("inner_src_mac", test_mac)), sub_params,
            )
            pw_outer_v = int(params.get("pw_outer_vlan", "0") or 0)
            pw_inner_v = int(params.get("pw_inner_vlan", "0") or 0)
            pw_dut_mac = params.get("pw_dut_mac", "")
            if pw_label > 0 and (pw_outer_v == 0 or not pw_dut_mac):
                _ensure_pw_transport_params(params, device, recorded_run_show)
                pw_outer_v = int(params.get("pw_outer_vlan", "0") or 0)
                pw_inner_v = int(params.get("pw_inner_vlan", "0") or 0)
                pw_dut_mac = params.get("pw_dut_mac", "")
            if pw_label > 0:
                stream_name = f"vpls_pw_label_{pw_label}"
                spirent_create_vpls_stream(
                    stream_name,
                    mpls_label=pw_label,
                    inner_src_mac=inner_mac,
                    outer_vlan=pw_outer_v or None,
                    inner_vlan=pw_inner_v or None,
                    dst_mac_outer=pw_dut_mac or None,
                )
                spirent_start()
                _pw_evpn = params.get("pw_evpn_name") or evpn_name
                poll_until_mac_present(
                    inner_mac, timeout=8.0, fallback_sleep=2.0,
                    evpn_name=_pw_evpn,
                )
                spirent_stop()
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.PASS,
                    f"VPLS stream sent inner_mac={inner_mac} via MPLS label {pw_label}",
                ))
            else:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "spirent_vpls_stream: pw_ingress_label=0 -- PW not installed",
                ))

        elif mapped == "clear_command":
            cli_cmd = trigger.get("command", "")
            if cli_cmd:
                expanded_clear = substitute(cli_cmd, sub_params)
                clear_out = recorded_run_show(device, expanded_clear)
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.PASS,
                    f"Clear command: {expanded_clear}",
                    evidence=clear_out[:500],
                ))
            else:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "clear_command requires 'command' field in trigger",
                ))

        elif mapped == "config_command":
            cfg_path = trigger.get("config_path", "")
            if cfg_path:
                expanded_cfg = substitute(cfg_path, sub_params)
                try:
                    runner = get_cached_runner(device, agent_callback=recorded_run_show)
                    runner(device, "config")
                    runner(device, expanded_cfg)
                    commit_out = runner(device, "commit")
                    runner(device, "end")
                    ok = "error" not in strip_ansi(commit_out).lower()
                    verdict.layers.append(LayerResult(
                        "trigger",
                        VerdictStatus.PASS if ok else VerdictStatus.FAIL,
                        f"Config trigger: {expanded_cfg}",
                        evidence=commit_out[:500],
                    ))
                except Exception as exc:  # noqa: BLE001
                    verdict.layers.append(LayerResult(
                        "trigger", VerdictStatus.FAIL,
                        f"Config trigger failed: {exc}",
                    ))
            else:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "config_command requires 'config_path' in trigger",
                ))

        elif mapped == "commit_check_assert":
            # Negative/positive commit-check trigger (G2 irb_si_rejection).
            # Reads:
            #   trigger.config_commands  -- list[str], lines to apply in candidate
            #   trigger.expect           -- "fail" (default if recipe verify says
            #                                so) or "pass" for positive control
            #   trigger.expected_error_regex -- optional list[str] or single str
            #
            # Falls back to the scenario verify.expect block when trigger does
            # not carry these fields (lets old recipes work without rewriting).
            #
            # Always runs ``rollback 0`` then exits config mode -- never commits.
            cmds = trigger.get("config_commands") or []
            verify_block = phases.get("verify", {}) or {}
            expect_block = verify_block.get("expect", {}) or {}
            recipe_says_fail = bool(
                expect_block.get("cli_rejects_with_error")
                or expect_block.get("commit_fails_or_config_rejected")
            )
            expect_arg = trigger.get("expect")
            if expect_arg in ("fail", "reject"):
                expect_fail = True
            elif expect_arg in ("pass", "succeed", "success"):
                expect_fail = False
            else:
                expect_fail = recipe_says_fail

            patterns = (
                trigger.get("expected_error_regex")
                or expect_block.get("expected_error_patterns")
                or []
            )
            if isinstance(patterns, str):
                patterns = [patterns]

            if not cmds:
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.SKIP,
                    "commit_check_assert requires 'config_commands' list",
                ))
            else:
                # Resolve placeholders BEFORE driving SSH so we never send raw
                # ``{si_instance_name}`` etc. to the device. Drop empty/control
                # tokens recipe authors sometimes embed.
                expanded_cmds: List[str] = []
                for raw_line in cmds:
                    if not raw_line:
                        continue
                    ln = raw_line.strip()
                    if ln in ("config", "configure", "commit", "end", "rollback 0",
                              "rollback", "abort"):
                        continue
                    expanded_cmds.append(substitute(raw_line, sub_params))

                # Refuse to drive the device if any placeholder survived
                # substitution -- the candidate would be syntactically broken
                # and ``commit check`` would report "no configuration changes",
                # masking the real assertion.
                unresolved = [c for c in expanded_cmds if "{" in c and "}" in c]
                if unresolved:
                    verdict.layers.append(LayerResult(
                        "trigger", VerdictStatus.SKIP,
                        "commit_check_assert: unresolved placeholders in "
                        f"config_commands -- check recipe.runtime_parameters: {unresolved}",
                    ))
                else:
                    # MCP run_show_command is stateless -- it cannot drive
                    # ``configure`` ... ``commit check`` because each call
                    # opens a fresh shell. Use a persistent SSH session so the
                    # candidate config persists between sends.
                    session = get_persistent_ssh_session(device)
                    if session is None:
                        verdict.layers.append(LayerResult(
                            "trigger", VerdictStatus.SKIP,
                            f"commit_check_assert needs SSH credentials for "
                            f"'{device}' (add to ~/SCALER/db/devices.json or "
                            f"export DNOS_SSH_IP/USER/PASS)",
                        ))
                    else:
                        # Wrap the SSH session in the orchestrator's run_show
                        # signature so obs.run_and_record can capture each
                        # step into the trigger phase JSON / HTML report.
                        def _ssh_run(_dev: str, command: str) -> str:
                            try:
                                return session.send_command(
                                    command, auto_no_more=False,
                                )
                            except Exception as exc:  # noqa: BLE001
                                return f"[SSH ERROR] {type(exc).__name__}: {exc}"

                        cc_out = ""
                        cc_clean = ""
                        try:
                            obs.run_and_record(device, "configure", _ssh_run)
                            for idx, line in enumerate(expanded_cmds):
                                # Reset to config root before each command so
                                # full-path statements never ride on top of
                                # the previous command's descended subcontext
                                # (DNOS enters e.g. "...router-interface irb9099"
                                # after such a set, which makes the next
                                # "network-services ..." fail with "Unknown
                                # word: 'network-services'").
                                if idx > 0:
                                    obs.run_and_record(device, "top", _ssh_run)
                                obs.run_and_record(device, line, _ssh_run)
                            obs.run_and_record(device, "top", _ssh_run)
                            cc_out = obs.run_and_record(
                                device, "commit check", _ssh_run,
                            )
                        finally:
                            # Always roll back and exit config mode -- this
                            # handler must NEVER commit, even on partial
                            # failure. ``rollback 0`` is safe even with no
                            # pending changes. Order is intentional:
                            #   1. ``top``   -- in case a mid-loop command
                            #                   raised while DNOS was in a
                            #                   descended subcontext (e.g.
                            #                   ``...router-interface irbN``);
                            #                   rollback from root is always
                            #                   safe.
                            #   2. ``rollback 0`` -- discard the whole
                            #                   candidate (no partial
                            #                   commits possible).
                            #   3. ``end``   -- exit config mode so the
                            #                   SSH session is reusable for
                            #                   the next scenario / test.
                            try:
                                obs.run_and_record(device, "top", _ssh_run)
                            except Exception:
                                pass
                            try:
                                obs.run_and_record(
                                    device, "rollback 0", _ssh_run,
                                )
                            except Exception:
                                pass
                            try:
                                obs.run_and_record(device, "end", _ssh_run)
                            except Exception:
                                pass

                        cc_clean = strip_ansi(cc_out or "")
                        cc_lower = cc_clean.lower()
                        # DNOS rejection signals (any of these implies the
                        # commit-check refused the candidate):
                        cc_failed = (
                            "[ssh error]" in cc_lower
                            or (
                                "passed successfully" not in cc_lower
                                and "completed without error" not in cc_lower
                                and (
                                    "error" in cc_lower
                                    or "failed" in cc_lower
                                    or "cannot be configured" in cc_lower
                                    or "not allowed" in cc_lower
                                    or "incompatible" in cc_lower
                                    or "rejected" in cc_lower
                                    or "must be configured" in cc_lower
                                )
                            )
                        )
                        # ``no configuration changes were made`` means the
                        # candidate is empty -- treat as a hard handler failure
                        # in BOTH expect_fail and expect_pass modes since the
                        # config commands clearly didn't apply.
                        cc_no_changes = "no configuration changes were made" in cc_lower

                        if cc_no_changes:
                            verdict.layers.append(LayerResult(
                                "trigger", VerdictStatus.FAIL,
                                "commit_check_assert: candidate was empty "
                                "(\"no configuration changes were made\") -- "
                                "config commands did not apply. Check SSH "
                                "session config-mode persistence.",
                                evidence=cc_clean[:500],
                            ))
                        elif expect_fail:
                            regex_hit = (
                                True if not patterns
                                else any(
                                    re.search(p, cc_clean, re.IGNORECASE)
                                    for p in patterns
                                )
                            )
                            ok = cc_failed and regex_hit
                            if ok:
                                msg = (
                                    "commit check rejected as expected"
                                    + (f" (matched any of {patterns})" if patterns else "")
                                )
                            else:
                                msg = (
                                    "commit check did NOT reject as expected. "
                                    f"failed={cc_failed} regex_hit={regex_hit} "
                                    f"output[:300]={cc_clean[:300]!r}"
                                )
                            verdict.layers.append(LayerResult(
                                "trigger",
                                VerdictStatus.PASS if ok else VerdictStatus.FAIL,
                                msg,
                                evidence=cc_clean[:500],
                            ))
                        else:
                            ok = not cc_failed
                            msg = (
                                "commit check passed (positive control succeeded)"
                                if ok
                                else f"commit check unexpectedly failed: {cc_clean[:300]!r}"
                            )
                            verdict.layers.append(LayerResult(
                                "trigger",
                                VerdictStatus.PASS if ok else VerdictStatus.FAIL,
                                msg,
                                evidence=cc_clean[:500],
                            ))

        elif mapped == "spirent_ac_across_pe":
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.SKIP,
                f"AC-across-PE multihoming move requires DNAAS dual-path: {action} "
                f"(not yet implemented in /SPIRENT)",
            ))

        elif action in _SPIRENT_PHASE_TRIGGER_VERBS and method == TrafficMethod.SPIRENT:
            # Fallback: trigger.action is a SPIRENT-runner verb (e.g. withdraw_rt4,
            # inject_rt2, inject_rt4). Route the trigger through the same dispatcher
            # that setup.spirent[]/cleanup.spirent[] use so the recipe can express the
            # trigger as a single SPIRENT-runner directive.
            try:
                _run_spirent_phase_actions(
                    [trigger], params, sub_params, obs,
                    evpn_name, "trigger",
                )
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.PASS,
                    f"SPIRENT-phase trigger executed: action={action}",
                ))
            except Exception as exc:  # noqa: BLE001
                verdict.layers.append(LayerResult(
                    "trigger", VerdictStatus.FAIL,
                    f"SPIRENT-phase trigger {action} raised: {exc}",
                ))

        else:
            verdict.layers.append(LayerResult(
                "trigger", VerdictStatus.SKIP,
                f"Unknown trigger: {action} (mapped={mapped})",
            ))

    t_trigger_done = time.time()
    trigger_dur = round(t_trigger_done - t_start, 3)
    obs.record_parsed("trigger_duration_sec", trigger_dur)
    obs.end_phase()
    print(f"    [trigger] Done ({trigger_dur}s)", flush=True)

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
        # Justified bounded warmup (<= 5s): give the just-restarted DUT process
        # a moment to recreate its SSH session before slamming it with show
        # commands. The remaining wait was rolled into the poll timeout so the
        # poll itself returns the moment recovery is observed.
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
        trigger_dict = trigger if isinstance(trigger, dict) else {}
        max_wait = int(trigger_dict.get("propagation_wait_sec", 10 if mac_count <= 100 else 15))
        obs.record_event("wait", f"Polling MAC table (up to {max_wait}s, persistent SSH)")
        waited = poll_until_mac_present(
            test_mac, timeout=max_wait, poll_interval=0.5,
            evpn_name=evpn_name, fallback_sleep=2.0,
        )
        obs.record_event("propagation_done", f"MAC poll completed in {waited}s")

    # -- Verify phase (single pass -- MAC already confirmed by poll above) --
    print("    [verify] Running verification checks...", flush=True)
    obs.begin_phase("verify")
    verify = phases.get("verify")
    after_snapshot = phases.get("after_snapshot")
    after_output = ""
    captured_outputs: Dict[str, str] = {}

    show_cmds = []
    if after_snapshot and isinstance(after_snapshot, dict):
        show_cmds.extend(after_snapshot.get("show_commands", []))
    if verify and isinstance(verify, dict):
        show_cmds.extend(verify.get("show_commands", []))

    for cmd in show_cmds:
        expanded = substitute(cmd, sub_params)
        out = recorded_run_show(device, expanded)
        captured_outputs[expanded] = out
        cmd_l = cmd.lower()
        if cmd_l.startswith("show evpn mac-table"):
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

    def _captured_or_recorded_run_show(dev: str, command: str) -> str:
        expanded = substitute(command, sub_params)
        if dev == device and expanded in captured_outputs:
            return captured_outputs[expanded]
        return recorded_run_show(dev, expanded)

    if expect.get("source_contains"):
        layer = check_control_plane(
            device, evpn_name, test_mac, expect["source_contains"], recorded_run_show,
        )
        verdict.layers.append(layer)

    source_mac_flags = (
        expect.get("source_mac_flags")
        or expect.get("expected_source_mac_flags")
        or expect.get("source_mac_expectations")
    )
    if source_mac_flags:
        verdict.layers.append(check_all_sources_present(
            device, evpn_name, source_mac_flags, _captured_or_recorded_run_show,
            forbidden_flags=expect.get("forbidden_flags", []),
        ))
    elif expect.get("all_three_sources_present"):
        verdict.layers.append(check_all_sources_present(
            device, evpn_name, expect["all_three_sources_present"],
            _captured_or_recorded_run_show,
            forbidden_flags=expect.get("forbidden_flags", []),
        ))

    if expect.get("seq_increment"):
        seq_result = verify_sequence_incremented(before_output, after_output, test_mac)
        seq_status = VerdictStatus.PASS if seq_result["pass"] else VerdictStatus.FAIL
        if seq_result.get("warn") == "sequence_not_exposed":
            seq_status = VerdictStatus.PASS
        verdict.layers.append(LayerResult(
            "sequencing", seq_status,
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
        mobility_before = recorded_run_show(device, "show evpn mac summary | no-more")
        verdict.layers.append(check_mobility_counter_layer(
            device, mobility_before, recorded_run_show, expected_increment=mac_count,
        ))

    if expect.get("check_ghost_macs"):
        verdict.layers.append(check_ghost_macs_layer(
            device, evpn_name, _captured_or_recorded_run_show,
        ))

    # -- Previously dead expect keys (now wired) --

    if expect.get("rt2_advertised"):
        rt2_out = recorded_run_show(
            device,
            "show bgp l2vpn evpn | no-more",
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
            _s = summary_entry.get("sequence")
            if _s is not None:
                summary_seq = _s
            else:
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
        elif mac_detail and summary_entry:
            verdict.layers.append(LayerResult(
                "sequence_consistent", VerdictStatus.PASS,
                "MAC present in both views. Sequence not exposed in CLI (non-sticky AC).",
            ))
        else:
            verdict.layers.append(LayerResult(
                "sequence_consistent", VerdictStatus.FAIL,
                f"MAC missing: detail={'found' if mac_detail else 'MISSING'}, "
                f"summary={'found' if summary_entry else 'MISSING'}",
            ))

    if "local_loop_count_increments" in expect:
        from shared.mac_parsers import parse_loop_prevention_local
        after_lp_raw = recorded_run_show(
            device, f"show evpn instance {evpn_name} loop-prevention local | no-more",
        )
        after_lp = parse_loop_prevention_local(after_lp_raw)
        mac_l = test_mac.lower()
        mac_move_info = after_lp.get("mac_moves", {}).get(mac_l)
        expect_increment = bool(expect.get("local_loop_count_increments"))
        rationale = expect.get("rationale", "")
        if mac_move_info:
            moves = mac_move_info["moves"]
            threshold = mac_move_info["threshold"]
            if expect_increment:
                ok = moves > 0
                detail = (
                    f"MAC {mac_l} moves: {moves}/{threshold} in detection window"
                    + (" (move detected)" if ok else " (no moves detected -- expected > 0)")
                )
            else:
                ok = moves == 0
                detail = (
                    f"MAC {mac_l} moves: {moves}/{threshold} (expect 0 per spec -- SH->SH move is ignored)"
                    + (f" [{rationale}]" if rationale else "")
                    + (" -- MATCH spec" if ok else " -- UNEXPECTED increment for SH->SH pair")
                )
            verdict.layers.append(LayerResult(
                "local_loop_count",
                VerdictStatus.PASS if ok else VerdictStatus.FAIL,
                detail,
            ))
        elif mac_l in [m.lower() for m in after_lp.get("macs", [])]:
            if expect_increment:
                verdict.layers.append(LayerResult(
                    "local_loop_count", VerdictStatus.WARN,
                    f"MAC {mac_l} found but move count not parseable from LLP table",
                ))
            else:
                verdict.layers.append(LayerResult(
                    "local_loop_count", VerdictStatus.PASS,
                    f"MAC {mac_l} has no moves recorded (expected -- SH->SH ignored per spec)"
                    + (f" [{rationale}]" if rationale else ""),
                ))
        else:
            if expect_increment:
                verdict.layers.append(LayerResult(
                    "local_loop_count", VerdictStatus.WARN,
                    f"MAC {mac_l} not in loop-prevention local table (LLP enabled={after_lp.get('admin_state')})",
                ))
            else:
                verdict.layers.append(LayerResult(
                    "local_loop_count", VerdictStatus.PASS,
                    f"MAC {mac_l} not in LLP table -- consistent with SH->SH ignore per spec"
                    + (f" [{rationale}]" if rationale else ""),
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

    if expect.get("no_bgp_notification_in_traces"):
        verdict.layers.append(check_no_bgp_notification_layer(
            device, _captured_or_recorded_run_show,
            timestamp_hhmm=trigger_time,
            relevant_neighbors=expect.get("bgp_notification_neighbors"),
        ))

    if expect.get("bgp_session_stable"):
        vpls_out = _captured_or_recorded_run_show(
            device, "show bgp l2vpn vpls summary | no-more",
        )
        vpls_parsed = parse_bgp_l2vpn_evpn_summary(vpls_out)
        vpls_ok = vpls_parsed["established"] > 0
        verdict.layers.append(LayerResult(
            "bgp_vpls_session",
            VerdictStatus.PASS if vpls_ok else VerdictStatus.FAIL,
            f"{vpls_parsed['established']}/{vpls_parsed['total']} VPLS ESTABLISHED",
            vpls_out[:500],
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

    # -- Detect infra failure early: skip ALL expensive checks if MAC never learned --
    infra_fail = after_count == 0 and before_count == 0

    if not infra_fail:
        # -- Cross-layer mismatch detection --
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

    # -- BGP session stable (fast, always run) + trace errors (skip on infra fail) --
    _needs_evpn_peers = mapped_trigger in _EVPN_PEER_TRIGGERS
    verdict.layers.append(check_bgp_session_stable(device, recorded_run_show,
                                                   required=_needs_evpn_peers))
    # Defer trace analysis: only run if functional layers have a FAIL.
    # Trace greps take 20-23s per scenario (2 SSH commands to scan large files).
    # For PASS/WARN scenarios, traces add zero diagnostic value but ~40% of runtime.
    _has_functional_fail = any(
        lr.status == VerdictStatus.FAIL for lr in verdict.layers
    )
    _skip_trace_check = infra_fail or not _has_functional_fail
    _skip_trace_reason = "infra_fail" if infra_fail else ("all_pass" if not _has_functional_fail else "")
    verdict.layers.append(check_no_trace_errors(
        device, trigger_time, recorded_run_show,
        skip_if_infra_fail=_skip_trace_check,
        skip_reason=_skip_trace_reason,
        relevant_neighbors=expect.get("bgp_notification_neighbors"),
    ))

    # -- ENGINE: Counter diff + Event audit + BGP health --
    # Skip expensive trace greps (audit_events ~100s) on fully-passing or infra-fail scenarios.
    # Counter diff is cheap (~2s) so always run it unless infra failed.
    _primary_all_pass = all(
        lr.status in (VerdictStatus.PASS, VerdictStatus.WARN)
        for lr in verdict.layers
    )
    _skip_audit_events = infra_fail or _primary_all_pass
    if _ENGINES_AVAILABLE and recipe and not infra_fail:
        if counter_before:
            try:
                counter_cmds = _load_rendered_counter_commands(recipe, sub_params)
                counter_after = snapshot_counters(device, "after_verify", counter_cmds, resilient_show)
                obs.record_counter_snapshot(counter_after.to_dict())
                counter_exps = load_counter_expectations(recipe)
                if counter_exps:
                    counter_diff = diff_counters(counter_before, counter_after, counter_exps)
                    obs.record_counter_diff(counter_diff.to_dict())
                    if not counter_diff.passed:
                        for item in counter_diff.items:
                            if not item.passed:
                                is_unparseable = "non-numeric" in (item.assessment or "")
                                verdict.layers.append(LayerResult(
                                    f"counter_{item.label}",
                                    VerdictStatus.WARN if is_unparseable else VerdictStatus.FAIL,
                                    item.assessment,
                                ))
            except Exception as exc:
                obs.record_anomaly(f"Counter diff failed: {exc}")

        if not _skip_audit_events:
            try:
                event_exps = load_event_expectations(recipe)
                sc_events = scenario.get("phases", {}).get("verify", {}).get("event_expectations", [])
                if sc_events:
                    from TEST.shared.event_tracker import load_event_expectations as _load_ev
                    sc_event_objs = _load_ev({"event_expectations": sc_events})
                    if sc_event_objs:
                        event_exps = (event_exps or []) + sc_event_objs
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
        if mapped_trigger == "rapid_flap":
            threshold_key = "rapid_flap_sec"
        elif mac_count > 1000:
            threshold_key = "scale_64k_move_sec"
        else:
            threshold_key = "single_mac_move_sec"
        verdict.layers.append(check_convergence_time(convergence, threshold_key))

    # -- Auto-diagnose failures (enhanced: deep evidence + Jira + auto-investigate) --
    verdict.compute_overall()
    pass_count = sum(1 for lr in verdict.layers if lr.status == VerdictStatus.PASS)
    fail_count = sum(1 for lr in verdict.layers if lr.status == VerdictStatus.FAIL)
    print(f"    [verdict] {verdict.overall.value.upper()} "
          f"({pass_count} pass, {fail_count} fail, after_mac={after_count})",
          flush=True)

    # -- Inline verdict table (chat observability, 2026-04-30) --
    #
    # Without this block the only chat-visible signal for SC01 was a single
    # "[verdict] FAIL" line. Operators had to dig into verdict.json or
    # SUMMARY.md (written at run-end) to learn WHICH layer failed and WHY.
    # Per-layer detail + a snippet of failing evidence is now printed
    # directly to stdout so the user can see the failure cause without
    # context-switching to the results dir.
    try:
        _emit_inline_verdict_table(
            scenario_id=sc_id,
            verdict=verdict,
            obs=obs,
            test_mac=test_mac,
        )
    except Exception as _vt_exc:  # never let observability crash the run
        print(f"    [verdict-table] (skipped: {_vt_exc})", flush=True)
    if verdict.overall in (VerdictStatus.FAIL, VerdictStatus.ERROR):
        obs.begin_phase("auto_diagnose")
        failed_layers = [lr.layer for lr in verdict.layers if lr.status == VerdictStatus.FAIL]

        if infra_fail:
            verdict.debug_hint = (
                "Infrastructure failure: MAC never appeared in mac-table. "
                "Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic."
            )
            print("    [DIAG] Infra failure detected -- skipping deep trace analysis")
            obs.record_event("auto_diagnose_skip",
                             "Skipped trace greps (infra fail, MAC never learned)")
            obs.end_phase()
        else:
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

            def _jira_callback(jql: str, fields: str, _limit: int) -> str:  # noqa: ARG001  -- callback signature dictated by jira_bug_matcher
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

    # -- Per-scenario cleanup (rollback config + spirent state) --
    # Handles all three shapes: legacy `commands`, named `config` template
    # lookup, and `spirent` action lists. Each piece is best-effort and isolated
    # so a single failure does not skip subsequent cleanup steps.
    _run_recipe_phase(
        phases.get("cleanup"), recipe, params, sub_params, device,
        recorded_run_show, obs, evpn_name, "cleanup",
    )

    # -- Rollback per-scenario config provisioning --
    if _scenario_provision.get("applied"):
        _rollback_scenario_config(device, _scenario_provision, recorded_run_show)

    # -- Restart L2 traffic if it was stopped for a remote-only scenario --
    if _is_remote_trigger and method == TrafficMethod.SPIRENT:
        try:
            spirent_start()
        except Exception:
            pass

    # -- Spirent object cleanup --
    # When PW test objects were pre-created before protocol-start, use
    # destroy=False to avoid stc.apply() while protocols are active.
    if method == TrafficMethod.SPIRENT:
        try:
            spirent_stop()
        except Exception:
            pass
        _precreated = params.get("_pw_objects_precreated") == "true"
        cleanup_current_scenario(destroy=not _precreated)

    # -- Attach observability log and provision state to verdict --
    obs_log = obs.finalize()
    verdict.observability_log = obs_log
    verdict._provision_state = _scenario_provision  # type: ignore[attr-defined]

    return verdict


__all__ = ["execute_scenario"]
