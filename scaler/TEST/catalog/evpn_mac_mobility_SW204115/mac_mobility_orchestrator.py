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
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SUITE_ROOT = Path(__file__).resolve().parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

# All imports below intentionally follow the sys.path setup above so that
# sibling files (device_discovery, prerequisite_engine) and the optional
# TEST.shared/* generic engines resolve correctly when this script is run
# directly. ruff's E402 ("module level import not at top of file") is
# suppressed for the rest of this file's imports.
# ruff: noqa: E402
from device_discovery import discover_device_context, format_context_summary
from prerequisite_engine import check_prerequisites, format_prereq_table, get_auto_fix_plan
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
    TestVerdict,
    VerdictStatus,
    check_bgp_session_stable,
    check_control_plane,
    check_convergence_time,
    check_forwarding_state_layer,
    check_ghost_macs_layer,
    check_loop_prevention_layer,
    check_mac_flags_layer,
    check_mobility_counter_layer,
    check_no_trace_errors,
    check_rt2_recovery_layer,
    check_suppress_list_layer,
    format_detailed_report,
)
from shared.trace_analyzer import (
    analyze_failure,
    auto_investigate,
    clear_trace_cache,
    collect_debug_traces_window,
    collect_deep_evidence,
    disable_debug_traces,
    enable_debug_traces,
    quick_error_scan,
)
from shared.jira_bug_matcher import (
    search_known_bugs,
)
from shared.observability import ObservabilityCollector
from shared.device_runner import (
    create_device_runner,
    get_cached_runner,
    get_persistent_ssh_session,
    cleanup_all_sessions,
)
from shared.spirent_preflight import run_preflight as spirent_run_preflight
# Slice 1 (2026-04-20): /SPIRENT <-> /TEST sync mandate lives in orchestration/.
from orchestration.spirent_integration import (
    _requires_spirent,
    _resolve_spirent_vlan,
    _dev_ip,
    auto_invoke_spirent_sync,
    _spirent_full_sync,
    _spirent_sync_err,
)
# Slice 2 (2026-04-20): module constants + session I/O + reporting extracted.
from orchestration.constants import (
    MANIFEST_PATH, RESULTS_DIR, ACTIVE_SESSION, CORRECTIONS_PATH,
    ACTION_TRIGGER_MAP, _PW_TRIGGERS, _EVPN_PEER_TRIGGERS,
    _SPIRENT_PHASE_TRIGGER_VERBS, _EVPN_FALLBACK,
    _PW_MOVE_BUDGET_SEC, _BGP_RECOVERY_BUDGET_SEC,
    _SETUP_SPIRENT_DEFAULT_WAIT_SEC, _SETUP_SPIRENT_MAX_WAIT_SEC,
    SCENARIO_CONFIG_REQUIREMENTS,
)
from orchestration.session_io import (
    now_iso, now_hhmm, write_active_session,
    load_manifest, load_recipe,
    _load_corrections, _apply_corrections,
    _record_runtime_failure, _record_runtime_success,
    _default_run_show,
)
from orchestration.reporting import (
    _generate_repro_steps,
    write_results,
    _live_failure_detector,
)
from orchestration.runtime_context import (
    _provision_scenario_config,
    _rollback_scenario_config,
    _discover_ac_outer_vlans,
    _discover_instance_ac_vlans,
    _ensure_pw_transport_params,
    _discover_spirent_ldp_loopback,
    resolve_runtime_params,
)
from orchestration.recipe_runtime import (
    substitute,
    _apply_recipe_runtime_parameters,
    _resolve_named_config,
    _run_spirent_phase_actions,
    _run_recipe_phase,
    validate_recipe_commands,
    live_validate_prerequisites,
    run_recipe_dry,
)
from orchestration.scenario_runner import execute_scenario
from orchestration.test_runner import execute_test
from shared.validators import (
    poll_until,
    wait_for_bgp_state,
    wait_for_pw_installed,
)
from shared.device_profile import build_device_profile
from shared.spirent_vpls_provisioner import (
    DUTProfile,
    check_spirent_vpls_cp_ready,
    provision_spirent_evpn_peer,
    provision_spirent_vpls_cp,
    require_dut_profile,
)
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
    from TEST.shared.continuous_poller import (  # noqa: F401
        poll_until_converged, load_poll_config,
    )
    from TEST.shared.regression_detector import run_regression_check
    from TEST.shared.report_generator import (
        FullReport, ScenarioReport, generate_full_report,
    )
    from TEST.shared.post_run_learner import learn_from_run
    from TEST.shared.vtysh_runner import VtyshRunner  # noqa: F401
    _ENGINES_AVAILABLE = True
except ImportError:
    _ENGINES_AVAILABLE = False

# ---------------------------------------------------------------------------
# This module is now a thin shim.  All orchestration logic lives in
# ``orchestration/``:
#
#   * ``orchestration.constants``        -- paths, trigger maps, time budgets
#   * ``orchestration.session_io``       -- timestamps, session file, recipe loader,
#                                           self-healing command-correction cache
#   * ``orchestration.reporting``        -- repro steps, write_results, live failure
#                                           detector
#   * ``orchestration.runtime_context``  -- DUT discovery + resolve_runtime_params
#   * ``orchestration.recipe_runtime``   -- substitute(), recipe-phase runners,
#                                           validators, dry-run planner
#   * ``orchestration.spirent_integration`` -- /SPIRENT <-> /TEST sync mandate
#   * ``orchestration.scenario_runner``  -- execute_scenario
#   * ``orchestration.test_runner``      -- execute_test
#
# Every public name is re-exported at the top of this file so all existing
# callers keep working unchanged.  The only code that still lives here is
# the ``main()`` CLI entry point.
# ---------------------------------------------------------------------------


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
    parser.add_argument("--scenario", metavar="SC_ID", help="Run only this scenario (e.g. SC02_learn_remote_evpn)")
    parser.add_argument(
        "--evpn-instance", metavar="NAME", default=None,
        help="Pin EVPN instance name (overrides recipe.service_capabilities.preferred_instance "
             "and ctx auto-pick). Use when DUT has multiple instances and you need to force one.",
    )
    parser.add_argument(
        "--ac-interface", metavar="IF", default=None,
        help="Pin AC interface (e.g. ge100-18/0/1 for PE-4 untagged port-mode AC). "
             "Overrides auto-discovered first AC.",
    )
    parser.add_argument(
        "--fabric-vlan", type=int, default=None,
        help="Pin fabric VLAN (the DNAAS transport VLAN; what dnos_dnaas_teach_plan expects). "
             "For port-mode ACs this is the VLAN the fabric prepends. NOT a frame tag.",
    )
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
        # Load the recipe so MCP-driven checks (e.g. mcp_dnaas_teach_plan)
        # can read the prerequisites[] block. Best-effort: if the test id
        # isn't in the manifest, recipe stays None and the checks skip
        # silently instead of failing the gate.
        _prereq_recipe: Optional[Dict[str, Any]] = None
        try:
            _m = load_manifest()
            _t_entry = next(
                (t for t in _m.get("tests", []) if t["id"] == args.prereq),
                {},
            )
            _rel = _t_entry.get("path")
            if _rel:
                _prereq_recipe = load_recipe(_rel)
        except Exception:
            _prereq_recipe = None
        # Resolve runtime parameters early so MCP teach_plan can read
        # _si_outer_vlan from ctx instead of WARN'ing about a missing VLAN.
        # Best-effort: failures here just leave ctx as-is (the WARN is
        # informational, not fatal).
        try:
            _early_params = resolve_runtime_params(
                device, run_show, ctx,
                recipe=_prereq_recipe,
                evpn_instance_override=args.evpn_instance,
                ac_interface_override=args.ac_interface,
                fabric_vlan_override=args.fabric_vlan,
            )
            for _k in ("_si_outer_vlan", "si_outer_vlan",
                       "spirent_fabric_vlan", "evpn_name_primary"):
                if _k in _early_params and _k not in ctx:
                    ctx[_k] = _early_params[_k]
        except Exception:
            pass
        result = check_prerequisites(
            device, ctx, args.prereq, run_show, recipe=_prereq_recipe,
        )
        print(format_prereq_table(result))
        if args.auto_fix and result.get("auto_fixable_items"):
            fixes = get_auto_fix_plan(result)
            print(f"\n[INFO] Auto-fix plan ({len(fixes)} items):")
            for f in fixes:
                print(f"  - {f['check_id']}: {f['description']}")
                if f.get("spirent_command"):
                    print(f"    CMD: {f['spirent_command']}")
            # /SPIRENT <-> /TEST sync mandate: auto-run fabric fix + description tagging
            try:
                _m = load_manifest()
                _t_entry = next((t for t in _m.get("tests", []) if t["id"] == args.prereq), {})
                _rel = _t_entry.get("path")
                _recipe = load_recipe(_rel) if _rel else {}
                _infra = _t_entry.get("infra_required", _recipe.get("infra_required", "si_mode"))
                _params = resolve_runtime_params(
                    device, run_show, ctx,
                    recipe=_recipe,
                    evpn_instance_override=args.evpn_instance,
                    ac_interface_override=args.ac_interface,
                    fabric_vlan_override=args.fabric_vlan,
                )
                auto_invoke_spirent_sync(
                    device=device,
                    recipe=_recipe,
                    infra_required=_infra,
                    params=_params,
                    auto_fix=True,
                    dry_run=False,
                )
            except Exception as _sx:  # noqa: BLE001
                print(f"[SPIRENT-SYNC] could not auto-invoke: {_sx}", flush=True)
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
        test_entry = next((t for t in m.get("tests", []) if t["id"] == args.run), {})
        infra_required = test_entry.get("infra_required", recipe.get("infra_required", "si_mode"))

        if args.dry_run and not args.execute:
            dry_params: Dict[str, str] = {
                "device": device,
                "device_name": device,
                "dut": device,
                "asn": "1234567",
                "ncp_id": "0",
                "active_ncc_id": "0",
                "evpn_name": (
                    (recipe.get("service_capabilities") or {}).get("preferred_instance")
                    or "EVPN_SI_VPLS_1"
                ),
                "pw_evpn_name": "EVPN_SI_VPLS_1",
                "pw_test_evpn_name": "EVPN_SI_VPLS_1",
                "_si_outer_vlan": str(args.ac1_vlan),
                "test_mac": "00:DE:AD:00:01:01",
            }
            for key, spec in (recipe.get("runtime_parameters") or {}).items():
                if key in dry_params:
                    continue
                if isinstance(spec, dict) and spec.get("value") not in (None, ""):
                    dry_params[key] = str(spec["value"])
                elif not isinstance(spec, dict):
                    dry_params[key] = str(spec)

            notes = validate_recipe_commands(recipe, dry_params)
            guard_notes = [
                n for n in notes
                if n.get("validation_method") == "static_command_guard"
            ]
            print(json.dumps({
                "mode": "dry_run_static",
                "test_id": args.run,
                "device": device,
                "guard_blockers": guard_notes,
                "validation_notes": notes,
                "plan": run_recipe_dry(device, recipe, dry_params),
            }, indent=2))
            if guard_notes:
                sys.exit(2)
            return

        ctx = discover_device_context(device, run_show)
        pre = check_prerequisites(device, ctx, args.run, run_show, recipe=recipe)
        params = resolve_runtime_params(
            device, run_show, ctx,
            recipe=recipe,
            evpn_instance_override=args.evpn_instance,
            ac_interface_override=args.ac_interface,
            fabric_vlan_override=args.fabric_vlan,
        )
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        run_dir = RESULTS_DIR / f"RUN_{ts}_{device}" / args.run

        # Open per-run command transcript (captures every show command's
        # output, regardless of routing strategy). Hooked into device_runner
        # via shared.run_transcript -- no per-test wiring required.
        try:
            from shared.run_transcript import (
                start_transcript as _xs,
                set_context as _xc,
            )
            _xs(run_dir=run_dir, test_id=args.run, primary_device=device,
                dry_run=(not args.execute))
            _xc(phase="setup", role="DUT")
        except Exception as _xexc:
            print(f"[WARN] transcript not initialized: {_xexc}", flush=True)

        # /SPIRENT <-> /TEST sync mandate (user 2026-04-20): any test requiring
        # Spirent devices/BGP/traffic MUST auto-invoke fabric fix + description
        # tagging before execution. Dry-run also runs (in dry-mode) so operators
        # can see what would be fixed.
        spirent_sync_status = auto_invoke_spirent_sync(
            device=device,
            recipe=recipe,
            infra_required=infra_required,
            params=params,
            auto_fix=bool(args.execute),
            dry_run=(not args.execute),
        )
        if spirent_sync_status and spirent_sync_status.get("overall") == "FAIL" and args.execute:
            print("\n[ABORT] /SPIRENT <-> /TEST sync FAILED -- fabric/description prerequisites "
                  "cannot be auto-fixed. Run 'spirent_tool.py dnaas-fix --vlan <vlan>' and "
                  "'spirent_tool.py mark-dnos --dut <dut_ip>' manually, then retry.",
                  flush=True)
            sys.exit(2)

        try:
            _main_profile: Optional[DUTProfile] = require_dut_profile(device, params, run_show)
        except Exception as _bp_exc:
            _main_profile = None
            print(f"[DUTProfile] Build failed ({_bp_exc}), using defaults", flush=True)

        # DUT-side INFRA check only (Spirent-side provisioning moved to execute_test)
        if infra_required in ("spirent_vpls_cp", "mixed"):
            print(f"\n[INFRA] Test requires '{infra_required}' -- DUT config check...")
            quick = check_spirent_vpls_cp_ready(device, run_show, profile=_main_profile)
            if not quick.get("ready"):
                missing = quick.get("missing", [])
                print(f"[INFRA] DUT missing: {', '.join(missing)}. Provisioning DUT side only...")
                prov_result = provision_spirent_vpls_cp(device, run_show, skip_spirent=True,
                                                       profile=_main_profile)
                for line in prov_result.summary_lines():
                    print(line)
                if prov_result.params:
                    params.update(prov_result.params)
            else:
                print("[INFRA] DUT config ready. Spirent peer will be provisioned after smoke test.")

        active_session_payload = {
            "active": True,
            "suite": "evpn_mac_mobility_SW204115",
            "test_id": args.run,
            "device": device,
            "ac1_vlan": args.ac1_vlan,
            "ac2_vlan": args.ac2_vlan,
            "scale": args.scale,
            "infra_required": infra_required,
            "updated": now_iso(),
        }
        try:
            existing_active = json.loads(ACTIVE_SESSION.read_text()) if ACTIVE_SESSION.exists() else {}
            expected_traffic = existing_active.get("expected_traffic")
            if isinstance(expected_traffic, dict):
                active_session_payload["expected_traffic"] = expected_traffic
        except Exception:
            pass
        write_active_session(active_session_payload)

        live_val = live_validate_prerequisites(device, recipe, params, run_show)
        failed_cmds = [v for v in live_val if v["status"] in ("FAILED",)]
        if failed_cmds:
            print(f"\n[WARN] {len(failed_cmds)} prerequisite command(s) FAILED on live device:")
            for fc in failed_cmds:
                print(f"  [{fc['prereq_id']}] {fc['command']}")
                print(f"    ERROR: {fc.get('error', '?')}")
                if fc.get("alt_command"):
                    print(f"    ALT OK: {fc['alt_command']} -> {fc.get('alt_output_preview', '')[:80]}")
            print("\n  Fix these commands before running. Use '?' on device to discover correct syntax.")
            if not args.execute:
                print("  (Continuing dry-run with flagged commands for review)")
        else:
            validated_count = sum(1 for v in live_val if v["status"] == "VALID")
            print(f"[OK] All {validated_count} prerequisite commands validated on live device")

        cmd_validation = validate_recipe_commands(recipe, params)
        guard_blockers = [
            cv for cv in cmd_validation
            if cv.get("corrected") == "[COMMAND-GUARD] blocked before DUT"
        ]
        if guard_blockers:
            print(f"\n[ERROR] {len(guard_blockers)} command(s) blocked by pre-DUT command guard:")
            for cv in guard_blockers:
                print(f"  {cv['original']}")
                print(f"    {cv.get('concern', '')}")
            print("  Refusing to execute until recipe rendering/syntax is fixed.")
            write_active_session({"active": False, "completed": now_iso()})
            if args.execute:
                sys.exit(1)

        if args.dry_run:
            plan = run_recipe_dry(device, recipe, params)
            body = {
                "prerequisites": pre,
                "runtime_params": params,
                "dry_plan": plan,
                "command_validation": cmd_validation,
                "live_validation": live_val,
            }
            if cmd_validation:
                print(f"\n[WARN] {len(cmd_validation)} command(s) flagged during pre-validation:")
                for cv in cmd_validation:
                    if "[UNVERIFIED]" in cv.get("corrected", ""):
                        print(f"  [UNVERIFIED] {cv['original']}")
                        print(f"    Concern: {cv['corrected'].replace('[UNVERIFIED] ', '')}")
                    else:
                        print(f"  [CORRECTED] {cv['original']}")
                        print(f"           -> {cv['corrected']}")
            else:
                print("[OK] All recipe commands pass pre-validation")
            print(json.dumps(body, indent=2, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o)))
            write_results(run_dir, device, args.run, "dry-run", body=body)
            write_active_session({"active": False, "completed": now_iso()})
            return

        if args.execute:
            if failed_cmds:
                print("[ERROR] Cannot execute with failed prerequisite commands. Fix syntax first.")
                write_active_session({"active": False, "completed": now_iso()})
                sys.exit(1)

            # VLAN selection contract (2026-04-30, /SPIRENT-DNAAS sync rule):
            #
            # The Spirent traffic MUST match the DUT-discovered AC VLANs. The
            # DUT is the source of truth -- not the CLI args. The previous
            # behavior only auto-overrode when args were the legacy defaults
            # (100/200), which silently sent traffic on whatever the user
            # passed (e.g. 1000/1001) even when those VLANs had no DUT AC,
            # producing a "MAC never appeared" failure that LOOKS like a
            # forwarding bug but is actually a stream-vs-AC mismatch.
            #
            # New rule:
            #   1. If the live DUT has discovered SI inner VLANs, USE THEM.
            #      Print a [VLAN-AUTO] line so the operator sees the override.
            #   2. CLI args become hints/fallbacks: only used when the DUT
            #      yielded nothing (rare).
            #   3. PW tests override AC1 with pw_vlan as before.
            #
            # Per the /SPIRENT command doctrine "Mandatory teach-plan source"
            # AND /TEST recipe prerequisite spirent_ac_teach_plan, the
            # canonical traffic flags come from `dnos_dnaas_teach_plan`. The
            # smoke test reads `_si_outer_vlan` + `_si_ac1_inner_vlan` from
            # `params`, both populated by runtime_context._build_si_params
            # from the same live DUT discovery that backs the teach_plan.
            ac1 = args.ac1_vlan
            ac2 = args.ac2_vlan
            if "_si_ac1_inner_vlan" in params:
                _disc_ac1 = int(params["_si_ac1_inner_vlan"])
                if _disc_ac1 != ac1:
                    print(
                        f"[VLAN-AUTO] AC1 VLAN {ac1} (CLI) -> {_disc_ac1} "
                        f"(discovered SI inner VLAN from {params.get('evpn_name', '?')}). "
                        f"DUT is source of truth; overriding to match the AC.",
                        flush=True,
                    )
                ac1 = _disc_ac1
            else:
                print(
                    f"[VLAN-AUTO] No SI inner VLAN discovered on DUT; "
                    f"using CLI ac1_vlan={ac1} as a fallback.",
                    flush=True,
                )
            if "_si_ac2_inner_vlan" in params:
                _disc_ac2 = int(params["_si_ac2_inner_vlan"])
                if _disc_ac2 != ac2:
                    print(
                        f"[VLAN-AUTO] AC2 VLAN {ac2} (CLI) -> {_disc_ac2} "
                        f"(discovered SI inner VLAN from {params.get('evpn_name', '?')}).",
                        flush=True,
                    )
                ac2 = _disc_ac2

            if infra_required == "spirent_vpls_cp" and "pw_vlan" in params:
                _pw_vl = int(params["pw_vlan"])
                if _pw_vl != ac1:
                    print(
                        f"[VLAN-AUTO] PW test: AC1 VLAN -> {_pw_vl} "
                        f"(pw_vlan from {params.get('pw_test_evpn_name', 'PW_TEST_ELAN')}).",
                        flush=True,
                    )
                ac1 = _pw_vl

            evpn_name = params.get("evpn_name", _EVPN_FALLBACK)
            set_device_poller(run_show, device, evpn_name)

            # Discover DUT interface MAC for unicast streams (avoids DNAAS LLP).
            # B3 fix: prefer the discovered SI/PW AC interface; fall back to the
            # base port of whichever AC interface params already discovered.
            # Drop hardcoded ge400-0/0/5 (PE-4-only) -- it returns no MAC on
            # PE-1, which forced streams onto broadcast and tripped LLP.
            if infra_required == "spirent_vpls_cp":
                _dut_mac = params.get("pw_dut_mac", "")
                _dut_ac_if = params.get("_pw_ac_interface", "")
            else:
                _dut_mac = params.get("_si_dut_mac", "") or params.get("pw_dut_mac", "")
                _dut_ac_if = params.get("_evpn_ac1_interface", "")
            if not _dut_mac and _dut_ac_if:
                try:
                    _mac_out = run_show(device, f"show interfaces {_dut_ac_if} | no-more")
                    _mac_m = re.search(r"MAC Address:\s+([\da-fA-F:]+)", _mac_out)
                    if _mac_m:
                        _dut_mac = _mac_m.group(1)
                    else:
                        _base_if = _dut_ac_if.rsplit(".", 1)[0]
                        _mac_out = run_show(device, f"show interfaces {_base_if} | no-more")
                        _mac_m = re.search(r"MAC Address:\s+([\da-fA-F:]+)", _mac_out)
                        if _mac_m:
                            _dut_mac = _mac_m.group(1)
                except Exception:
                    pass
            if _dut_mac:
                set_dut_mac(_dut_mac)
                print(f"[INFO] DUT interface MAC: {_dut_mac} (unicast dst for streams)")
            else:
                print("[WARN] Could not discover DUT MAC -- streams may use broadcast (LLP risk)")

            sc_label = f", scenario={args.scenario}" if args.scenario else ""
            print(f"[INFO] Executing {args.run} on {device} (VLANs {ac1}/{ac2}, scale={args.scale}{sc_label})")
            verdict = execute_test(
                device, recipe, params, run_show,
                ac1_vlan=ac1,
                ac2_vlan=ac2,
                mac_count=args.scale,
                run_dir=run_dir,
                scenario_filter=args.scenario,
                infra_required=infra_required,
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
            try:
                from shared.run_transcript import finalize_transcript as _xf
                _xf(verdict=verdict.overall.value)
            except Exception:
                pass
            return

        plan = run_recipe_dry(device, recipe, params)

        def _serialize_safe(obj):
            if hasattr(obj, "__dict__"):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            return str(obj)

        body = {"prerequisites": pre, "runtime_params": params, "dry_plan": plan}
        write_results(run_dir, device, args.run, "plan", body=body, recipe=recipe)
        write_active_session({"active": False, "completed": now_iso()})
        try:
            from shared.run_transcript import finalize_transcript as _xf
            _xf(verdict="DRY_RUN")
        except Exception:
            pass
        print(f"[OK] Wrote {run_dir / 'SUMMARY.md'}")
        print(f"[OK] Wrote {run_dir / 'EXECUTION_LOG.md'}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
