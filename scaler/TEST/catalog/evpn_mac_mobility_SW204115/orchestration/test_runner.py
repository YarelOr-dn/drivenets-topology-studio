"""Test runner -- hosts :func:`execute_test`.

Extracted from ``mac_mobility_orchestrator.py`` as Slice 6 of the orchestrator
modularization. The function itself is unchanged; only its location (and
consequently its import surface) moved. ``mac_mobility_orchestrator`` re-exports
``execute_test`` so all existing call sites keep working untouched.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from shared.mac_trigger import (
    TrafficMethod,
    detect_traffic_methods,
)
from shared.verdict_engine import (
    LayerResult,
    ScenarioVerdict,
    TestVerdict,
    VerdictStatus,
)
from shared.device_runner import (
    cleanup_all_sessions,
    get_cached_runner,
)
from shared.validators import (
    poll_until,
    wait_for_bgp_state,
)
from shared.device_profile import build_device_profile
from shared.spirent_vpls_provisioner import (
    DUTProfile,
    provision_spirent_evpn_peer,
    provision_spirent_vpls_cp,
    require_dut_profile,
)
from shared.evpn_event_knowledge import enrich_recipe_with_evpn_defaults
from shared.spirent_preflight import run_preflight as spirent_run_preflight

from .constants import (
    ACTION_TRIGGER_MAP,
    RESULTS_DIR,
    _EVPN_FALLBACK,
)
from .reporting import _live_failure_detector
from .runtime_context import (
    _ensure_pw_transport_params,
    _rollback_scenario_config,
)
from .recipe_runtime import substitute
from .scenario_runner import execute_scenario
from .session_io import now_iso, write_active_session

# Tier 1 generic engines (feature-agnostic) mirror the orchestrator shim.
try:
    _test_shared = Path(__file__).resolve().parent.parent.parent.parent / "shared"
    if str(_test_shared) not in sys.path:
        sys.path.insert(0, str(_test_shared.parent))
    from TEST.shared.config_baseline import (  # noqa: F401
        diff_config, load_baseline_config, snapshot_config,
    )
    from TEST.shared.health_guard import (  # noqa: F401
        compare_health, load_health_config, snapshot_health,
    )
    from TEST.shared.test_isolation import (  # noqa: F401
        TestIsolationGuard, load_cleanup_commands,
    )
    from TEST.shared.regression_detector import run_regression_check  # noqa: F401
    from TEST.shared.report_generator import (  # noqa: F401
        FullReport, ScenarioReport, generate_full_report,
    )
    from TEST.shared.post_run_learner import learn_from_run  # noqa: F401
    _ENGINES_AVAILABLE = True
except ImportError:
    _ENGINES_AVAILABLE = False


# ---------------------------------------------------------------------------
# execute_test -- kept verbatim from the orchestrator shim.
# ---------------------------------------------------------------------------

def execute_test(
    device: str,
    recipe: Dict[str, Any],
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    ac1_vlan: int = 100,
    ac2_vlan: int = 200,
    mac_count: int = 1,
    run_dir: Optional[Path] = None,
    scenario_filter: Optional[str] = None,
    infra_required: str = "si_mode",
) -> TestVerdict:
    test_id = recipe.get("id", "unknown")
    params["test_id"] = test_id
    test_verdict = TestVerdict(test_id=test_id, device=device)

    # Enrich recipe with EVPN-specific defaults (Tier 2 knowledge pack)
    recipe = enrich_recipe_with_evpn_defaults(recipe)

    detected = detect_traffic_methods()
    method = detected[0] if detected else TrafficMethod.MANUAL

    # -- Resolve outer VLAN for smoke test --
    vlan_map_raw = params.get("_ac_outer_vlan_map", "{}")
    try:
        _vlan_map: Dict[str, int] = {int(k): int(v) for k, v in json.loads(vlan_map_raw).items()}
    except Exception:
        _vlan_map = {}
    ac1_outer_for_smoke = _vlan_map.get(ac1_vlan)
    if infra_required == "spirent_vpls_cp" and params.get("pw_test_evpn_name"):
        evpn_name_for_smoke = params["pw_test_evpn_name"]
        # B3 follow-up: PW ACs don't appear in _vlan_map (which is built from
        # SI AC interfaces only). For PW tests, the smoke test must use the
        # discovered Q-in-Q outer-tag from pw_outer_vlan -- otherwise the
        # frame goes out single-tagged and DNAAS drops it at the BD edge,
        # producing a misleading "L2 path BROKEN" verdict.
        if not ac1_outer_for_smoke:
            try:
                _pw_outer = int(params.get("pw_outer_vlan") or 0)
                if _pw_outer:
                    ac1_outer_for_smoke = _pw_outer
            except (TypeError, ValueError):
                pass
    else:
        evpn_name_for_smoke = params.get("evpn_name", _EVPN_FALLBACK)

    t0 = time.time()

    # ===================================================================
    # CLEAN SLATE: Remove stale test objects from Spirent session.
    # Previous runs may have been killed (SIGTERM) leaving orphan devices
    # and streams that interfere with the smoke test and new scenarios.
    # Infrastructure devices (EVPN_RT2_Peer, VPLS_PW_Peer) are PRESERVED
    # -- removing them destroys ISIS/LDP/BGP sessions that take 90s to
    # re-establish, and nukes the PW needed for evpn_pw / ac_pw / pw_pw.
    # ===================================================================
    _INFRA_DEVICE_NAMES = {"VPLS_PW_Peer", "EVPN_RT2_Peer", "VPLS_PW_Peer_2"}
    if method == TrafficMethod.SPIRENT:
        try:
            from shared.mac_trigger import _run_spirent, _invalidate_device_cache
            _run_spirent(["stop"], timeout=10)

            status_raw = _run_spirent(["status", "--json"], timeout=15)
            try:
                _status = json.loads(status_raw)
                for dev in _status.get("devices", []):
                    dname = dev.get("name", "")
                    if dname and dname not in _INFRA_DEVICE_NAMES:
                        _run_spirent(["protocol-stop", "--device-name", dname], timeout=10)
                        _run_spirent(["remove-device", "--name", dname], timeout=10)
                for stm in _status.get("streams", []):
                    sname = stm.get("name", "")
                    if sname:
                        _run_spirent(["remove-stream", "--name", sname], timeout=10)
                _invalidate_device_cache()
            except (json.JSONDecodeError, ValueError):
                pass
        except Exception:
            pass

    # ===================================================================
    # UNIFIED PREFLIGHT: 4 layers checked BEFORE any scenario runs
    #   Layer 1: Spirent session alive + port reserved
    #   Layer 2: DNAAS path ready for VLANs
    #   Layer 3: BGP L2VPN EVPN peers ESTABLISHED
    #   Layer 4: L2 smoke test (send frame, check MAC on DUT)
    #
    # G2 fix (2026-04-19): config-validation recipes (e.g. irb_si_rejection)
    # do not send traffic and do not need a healthy L2 path or BGP EVPN
    # convergence. They only do CLI commit-check + rollback. Synthesize a
    # PASS preflight so we don't waste 30-60s on Spirent ops nor block when
    # Spirent infra is partially down.
    # ===================================================================
    _is_config_only = (recipe.get("type") == "config-validation")
    if _is_config_only:
        print("\n  === PREFLIGHT: SKIPPED (config-validation recipe -- no traffic) ===",
              flush=True)
        method = TrafficMethod.MANUAL
    else:
        print("\n  === PREFLIGHT: Spirent + DUT Infrastructure Check ===", flush=True)

    _evpn_peer_triggers = {"spirent_remote_pe", "spirent_ac_to_evpn", "spirent_evpn_to_ac",
                           "spirent_evpn_to_pw", "spirent_pw_to_evpn"}
    _test_scenarios = recipe.get("scenarios", [])
    if scenario_filter:
        _sf = [f.strip().lower() for f in scenario_filter.split(",")]
        _test_scenarios = [s for s in _test_scenarios
                           if any(f in s.get("id", "").lower() for f in _sf)]
    _needs_evpn = any(
        ACTION_TRIGGER_MAP.get(
            (s.get("phases", {}).get("trigger") or {}).get("action", ""), "unknown"
        ) in _evpn_peer_triggers
        and not bool((s.get("phases", {}).get("trigger") or {}).get("spirent_flags_pinned"))
        for s in _test_scenarios
    )

    # B2: pick the correct DUT MAC based on which EVPN we're smoke-testing.
    # PW tests   -> pw_dut_mac (PW peer interface MAC)
    # SI tests   -> _si_dut_mac (HA_TEST_ELAN AC base-port MAC)
    # Sending PW MAC to HA_TEST_ELAN is what caused the bogus "L2 path BROKEN"
    # verdicts for basic_learning -- traffic landed on the wrong AC.
    if infra_required == "spirent_vpls_cp":
        _smoke_dut_mac = params.get("pw_dut_mac", "")
        _smoke_ac_if = params.get("_pw_ac_interface", "")
    else:
        _smoke_dut_mac = params.get("_si_dut_mac", "") or params.get("pw_dut_mac", "")
        _smoke_ac_if = params.get("_evpn_ac1_interface", "")

    # Detect port-mode AC via the canonical helper. Reference:
    # ~/.cursor/spirent-reference/dnaas-port-mode-untagged-ac.md
    # The helper reads the live DUT config and returns mode/vlan/inner_vlan +
    # the EXACT spirent_args list to pass to create-stream.
    _is_port_mode_ac = False
    _smoke_fabric_vlan: Optional[int] = None
    _ac_encap_detection: Optional[Dict[str, Any]] = None
    try:
        from shared.spirent_preflight import detect_ac_encapsulation as _detect_enc
        if _smoke_ac_if and run_show:
            _ac_encap_detection = _detect_enc(device, _smoke_ac_if, run_show)
            _is_port_mode_ac = (_ac_encap_detection.get("mode") == "port_mode")
            if _is_port_mode_ac:
                _siv = params.get("_si_outer_vlan")
                if _siv:
                    _smoke_fabric_vlan = int(_siv)
                print(
                    f"  [PREFLIGHT] Port-mode AC detected: {_smoke_ac_if} "
                    f"(fabric_vlan={_smoke_fabric_vlan}); smoke test will send "
                    f"UNTAGGED frames (no --vlan, no --inner-vlan)",
                    flush=True,
                )
            else:
                print(
                    f"  [PREFLIGHT] AC encap mode: {_ac_encap_detection.get('mode')} "
                    f"(vlan={_ac_encap_detection.get('vlan')}, "
                    f"inner_vlan={_ac_encap_detection.get('inner_vlan')})",
                    flush=True,
                )
    except Exception as _pmexc:
        print(f"  [PREFLIGHT] AC encap detection error: {_pmexc}", flush=True)
        # Conservative fallback to legacy heuristic
        _pm_ac = params.get("_si_port_mode_ac1_interface")
        if _pm_ac and _smoke_ac_if and _pm_ac == _smoke_ac_if:
            _is_port_mode_ac = True
        elif _smoke_ac_if and "." not in _smoke_ac_if.split("/")[-1]:
            _is_port_mode_ac = True
        if _is_port_mode_ac:
            _siv = params.get("_si_outer_vlan")
            if _siv:
                _smoke_fabric_vlan = int(_siv)

    _scenario_pinned_stream_only = bool(scenario_filter) and bool(_test_scenarios) and all(
        isinstance((s.get("phases", {}).get("trigger") or {}).get("spirent_flags_pinned"), list)
        and bool((s.get("phases", {}).get("trigger") or {}).get("spirent_flags_pinned"))
        for s in _test_scenarios
    )

    if _is_config_only:
        preflight = {
            "skipped": True,
            "reason": "type=config-validation: no Spirent traffic, no L2 smoke test",
            "spirent_available": False,
            "warnings": [],
            "smoke_test": None,
            "bgp_check": {},
        }
    elif _scenario_pinned_stream_only:
        preflight = {
            "skipped": True,
            "reason": "scenario-pinned Spirent flags; generic AC1/AC2 smoke skipped",
            "spirent_available": True,
            "warnings": [],
            "smoke_test": {"pass": True, "detail": "scenario-pinned stream preflight skipped", "elapsed_sec": 0.0},
            "bgp_check": {},
        }
        print("  [PREFLIGHT] Generic AC1/AC2 smoke skipped for scenario-pinned stream run.", flush=True)
    else:
        preflight = spirent_run_preflight(
            vlans=[ac1_vlan, ac2_vlan] if not _is_port_mode_ac else (
                [_smoke_fabric_vlan] if _smoke_fabric_vlan else [ac1_vlan, ac2_vlan]
            ),
            require_spirent=(method == TrafficMethod.SPIRENT),
            run_show=run_show,
            device=device,
            evpn_name=evpn_name_for_smoke,
            ac_vlan=ac1_vlan,
            outer_vlan=ac1_outer_for_smoke,
            dut_mac=_smoke_dut_mac,
            require_evpn_peers=_needs_evpn,
            ac_interface=_smoke_ac_if,
            port_mode=_is_port_mode_ac,
            fabric_vlan=_smoke_fabric_vlan,
        )
    test_verdict.preflight = preflight  # type: ignore[attr-defined]

    for w in preflight.get("warnings", []):
        print(f"  [PREFLIGHT] {w}", flush=True)

    if not preflight.get("spirent_available") and method == TrafficMethod.SPIRENT:
        method = TrafficMethod.MANUAL
        print("  [PREFLIGHT] Spirent unavailable, falling back to MANUAL traffic method",
              flush=True)

    # Abort early if smoke test failed -- L2 path is broken, all scenarios
    # would waste time on guaranteed failures.
    #
    # B11 EXCEPTION: with seamless-integration, ACs go 'blocking-all' when
    # BGP EVPN has 0 ESTABLISHED neighbors. The smoke test will then fail
    # not because the path is broken, but because the SI safety mechanism
    # is dropping frames. In that case we DEFER the smoke test until after
    # the infra layer brings BGP up; we'll re-run smoke right before scenarios.
    smoke = preflight.get("smoke_test")
    bgp_pre = preflight.get("bgp_check") or {}
    _smoke_deferred = False
    # G2 fix (2026-04-19): _evpn_bgp_ok is only assigned inside the
    # _evpn_early_provisioned + SPIRENT branch (~line 3879). Tests that take
    # other code paths (config-validation, non-SI tests, MANUAL traffic) hit
    # the deferred-smoke check at ~line 4034 and crash with UnboundLocalError.
    # Pre-initialize to False so the orchestrator degrades gracefully.
    _evpn_bgp_ok = False
    if (smoke and not smoke.get("pass")
            and method == TrafficMethod.SPIRENT
            and bgp_pre.get("established", 0) == 0):
        print("\n  [PREFLIGHT] Smoke test failed AND BGP EVPN has 0 established peers.",
              flush=True)
        print("  [PREFLIGHT] Likely cause: SI puts ACs in 'blocking-all' when no EVPN peer is up.",
              flush=True)
        print("  [PREFLIGHT] Deferring smoke test -- will re-run after infra brings BGP up.",
              flush=True)
        _smoke_deferred = True
    elif smoke and not smoke.get("pass") and method == TrafficMethod.SPIRENT:
        print("\n  [PREFLIGHT FAIL] L2 smoke test FAILED -- infrastructure is broken.",
              flush=True)
        print(f"  [PREFLIGHT FAIL] {smoke.get('detail', 'Unknown')}", flush=True)
        print("  [PREFLIGHT] Aborting -- fix DNAAS path, AC state, or VLAN tags first.",
              flush=True)

        test_verdict.total_elapsed_sec = round(time.time() - t0, 2)
        for sc in recipe.get("scenarios", []):
            sc_id = sc.get("id", "scenario_preflight")
            sv = ScenarioVerdict(scenario_id=sc_id, scenario_name=sc.get("name", sc_id))
            sv.layers.append(LayerResult(
                "preflight_smoke_test", VerdictStatus.FAIL,
                smoke.get("detail", "L2 path broken"),
                evidence=json.dumps(smoke.get("steps", []), indent=2)[:500],
            ))
            sv.compute_overall()
            test_verdict.scenarios.append(sv)
        test_verdict.compute_overall()
        return test_verdict

    # Also abort if BGP peers are all down and recipe needs them
    bgp_check = preflight.get("bgp_check")
    needs_evpn_peer = any(
        (s.get("phases", {}).get("trigger", {}) or {}).get("action", "")
        in ("remote_pe_advertises_rt2", "remote_pe_traffic",
            "evpn_to_ac_move", "ac_to_evpn_move")
        for s in recipe.get("scenarios", [])
    )
    if bgp_check and needs_evpn_peer and bgp_check.get("established", 0) == 0:
        print("\n  [PREFLIGHT] Zero EVPN peers ESTABLISHED -- will auto-provision Spirent EVPN peer.",
              flush=True)

    if smoke and smoke.get("pass"):
        print(f"  [PREFLIGHT] L2 smoke test PASSED in {smoke['elapsed_sec']}s", flush=True)

    # Final gate: if preflight.pass is False for ANY reason, abort.
    # Exception: EVPN BGP failures are auto-fixable via Spirent peer provisioning.
    # B11 Exception: smoke test failures when BGP EVPN is down (SI ACs blocking)
    #               are deferred and re-checked after infra brings BGP up.
    if not preflight.get("pass", True):
        fail_msgs = [w for w in preflight.get("warnings", []) if "[FAIL]" in w]
        _auto_fixable_evpn = [m for m in fail_msgs if "EVPN peers ESTABLISHED" in m]
        _deferred_smoke = (
            [m for m in fail_msgs if "L2 smoke test FAILED" in m]
            if _smoke_deferred else []
        )
        _hard_fails = [m for m in fail_msgs
                       if m not in _auto_fixable_evpn and m not in _deferred_smoke]
        if _hard_fails:
            print("\n  [PREFLIGHT FAIL] One or more preflight checks FAILED:", flush=True)
            for fm in _hard_fails:
                print(f"    {fm}", flush=True)
            print("  [PREFLIGHT] ABORTING -- fix all preflight failures before running tests.",
                  flush=True)

            test_verdict.total_elapsed_sec = round(time.time() - t0, 2)
            for sc in recipe.get("scenarios", []):
                sc_id = sc.get("id", "preflight_fail")
                sv = ScenarioVerdict(scenario_id=sc_id, scenario_name=sc.get("name", sc_id))
                sv.layers.append(LayerResult(
                    "preflight", VerdictStatus.FAIL,
                    "; ".join(_hard_fails) or "Preflight checks failed",
                ))
                sv.compute_overall()
                test_verdict.scenarios.append(sv)
            test_verdict.compute_overall()

            write_active_session({"active": False, "completed": now_iso(), "verdict": "PREFLIGHT_FAIL"})
            return test_verdict
        if _auto_fixable_evpn:
            print("  [PREFLIGHT] EVPN BGP down -- will auto-provision after smoke test.",
                  flush=True)
        if _deferred_smoke:
            print("  [PREFLIGHT] Smoke test deferred -- will re-run after infra brings BGP up.",
                  flush=True)

    print("  === PREFLIGHT COMPLETE: All checks passed ===\n", flush=True)

    # ===================================================================
    # DUT PROFILE: Build DUTProfile from already-resolved params so all
    # provisioners use DUT-derived values instead of hardcoded constants.
    # Check cache first; rebuild if stale or missing.
    # ===================================================================
    _dut_profile: Optional[DUTProfile] = None
    if method == TrafficMethod.SPIRENT:
        try:
            _dut_profile = require_dut_profile(device, params, run_show)
        except Exception as exc:
            print(f"  [DUTProfile] Build failed ({exc}), falling back to constants", flush=True)

    # ===================================================================
    # INFRA PROVISIONING (after smoke test, before scenarios)
    # Creates VPLS_PW_Peer device with deferred protocols.
    # Placed HERE so: (1) clean-slate already ran, (2) smoke test passed
    # on clean session, (3) VPLS device created before scenarios need it.
    # Protocols are NOT started -- PW triggers start/stop per-scenario.
    # ===================================================================
    if infra_required in ("spirent_vpls_cp", "mixed") and method == TrafficMethod.SPIRENT:
        pw_label_ok = bool(params.get("pw_ingress_label"))
        vpls_device_exists = False
        try:
            from shared.mac_trigger import _run_spirent
            _st_raw = _run_spirent(["status", "--json"], timeout=15)
            _st = json.loads(_st_raw)
            vpls_device_exists = any(
                d.get("name") == "VPLS_PW_Peer" for d in _st.get("devices", [])
            )
        except Exception:
            pass

        if not pw_label_ok or not vpls_device_exists:
            reason = "no PW label" if not pw_label_ok else "VPLS_PW_Peer not in Spirent session"
            print(f"  [INFRA] Provisioning VPLS peer ({reason})...", flush=True)
            try:
                prov_result = provision_spirent_vpls_cp(device, run_show, defer_protocol_start=True,
                                                       profile=_dut_profile)
                for line in prov_result.summary_lines():
                    print(f"  {line}", flush=True)
                if prov_result.params:
                    params.update(prov_result.params)
                if prov_result.blocker and not prov_result.ready:
                    print(f"  [INFRA] BLOCKER: {prov_result.blocker}", flush=True)
            except Exception as exc:
                print(f"  [INFRA] Provisioning failed: {exc}", flush=True)
        else:
            print("  [INFRA] VPLS PW already active (label found + device in session).", flush=True)

    # ===================================================================
    # EVPN PEER EARLY PROVISIONING (before protocol-start)
    # Create EVPN_RT2_Peer device + BGP config BEFORE starting any
    # protocols. This prevents STC Lab Server crashes caused by
    # provisioning new devices while ISIS/LDP/BGP are running.
    # ===================================================================
    _evpn_early_provisioned = False
    if method == TrafficMethod.SPIRENT:
        _scenarios_for_check = _test_scenarios
        _evpn_triggers = {"spirent_remote_pe", "spirent_ac_to_evpn", "spirent_evpn_to_ac",
                          "spirent_evpn_to_pw", "spirent_pw_to_evpn"}
        _test_needs_evpn = any(
            ACTION_TRIGGER_MAP.get(
                (s.get("phases", {}).get("trigger") or {}).get("action", ""), "unknown"
            ) in _evpn_triggers
            and not bool((s.get("phases", {}).get("trigger") or {}).get("spirent_flags_pinned"))
            for s in _scenarios_for_check
        )
        if _test_needs_evpn:
            _evpn_device_name = params.get("spirent_evpn_device", "")
            _evpn_exists = False
            try:
                from shared.mac_trigger import _get_existing_device_names
                _evpn_exists = _evpn_device_name in _get_existing_device_names(force_refresh=True)
            except Exception:
                pass
            _evpn_has_bgp = False
            if _evpn_exists:
                try:
                    from shared.mac_trigger import _run_spirent as _run_sp_bgp_check
                    _bgp_st = json.loads(_run_sp_bgp_check(["bgp-status", "--json"]))
                    for _bd in _bgp_st:
                        if _bd.get("device") == _evpn_device_name:
                            _evpn_has_bgp = _bd.get("bgp") != "not configured"
                            break
                except Exception:
                    pass

            _needs_provision = (not _evpn_exists or not _evpn_has_bgp) and _evpn_device_name
            if _needs_provision:
                dut_rt = params.get("pw_rt") or params.get("rt", "100:100")
                _reason = "missing from session" if not _evpn_exists else "device exists but NO BGP configured"
                print(f"  [INFRA] EVPN peer '{_evpn_device_name}' {_reason} -- provisioning BEFORE protocol-start "
                      f"(RT={dut_rt})...", flush=True)
                try:
                    prov_result = provision_spirent_evpn_peer(
                        device, run_show, evpn_rt=dut_rt, bgp_only=True,
                        defer_protocol_start=True, profile=_dut_profile,
                    )
                    for s in prov_result.steps:
                        print(f"    [{s.get('status')}] {s.get('step')}: {s.get('detail', '')}", flush=True)
                    _evpn_early_provisioned = any(
                        s.get("status") in ("PASS", "WARN", "FIX") and "device" in s.get("step", "")
                        for s in prov_result.steps
                    )
                    if not _evpn_early_provisioned:
                        _evpn_early_provisioned = any(
                            s.get("status") == "PASS" and "bgp" in s.get("step", "").lower()
                            for s in prov_result.steps
                        )
                    if _evpn_early_provisioned:
                        print("  [INFRA] EVPN peer device + BGP ready (will establish after protocol-start)", flush=True)
                except Exception as exc:
                    print(f"  [INFRA] EVPN peer early provisioning failed: {exc}", flush=True)
            elif _evpn_exists and _evpn_has_bgp:
                _evpn_early_provisioned = True
                print(f"  [INFRA] EVPN peer '{_evpn_device_name}' already in session with BGP configured.", flush=True)

    # ===================================================================
    # PROTOCOL START + CONVERGENCE for PW tests
    # After infra provisioning created devices with deferred protocols,
    # start them now and wait for the full chain to converge:
    #   ISIS adj (30-45s) -> route (5s) -> LDP OPER (10s) -> BGP ESTAB (10s) -> PW Installed (5s)
    # Total budget: 90s.  Also starts EVPN_RT2_Peer protocols.
    # ===================================================================
    if infra_required in ("spirent_vpls_cp", "mixed") and method == TrafficMethod.SPIRENT:
        from shared.mac_trigger import _run_spirent

        _pw_vlan = int(params.get("pw_inner_vlan", "1010"))
        _pw_dut_mac = params.get("pw_dut_mac", "")
        _test_mac_val = params.get("test_mac", "00:DE:AD:00:01:01")
        if not _pw_dut_mac:
            # B3: try the actual discovered PW AC interface, not ge400-0/0/5
            try:
                import re as _re_mac
                _pw_if_full = params.get("_pw_ac_interface") or params.get("_pw_ac1_interface", "")
                _candidates = []
                if _pw_if_full:
                    _candidates.append(_pw_if_full)
                    _b = _pw_if_full.rsplit(".", 1)[0]
                    if _b != _pw_if_full:
                        _candidates.append(_b)
                for _if in _candidates:
                    _mac_out = run_show(device, f"show interfaces {_if} | no-more")
                    _mac_m = _re_mac.search(r"MAC Address:\s+([\da-fA-F:]+)", _mac_out)
                    if _mac_m:
                        _pw_dut_mac = _mac_m.group(1)
                        params["pw_dut_mac"] = _pw_dut_mac
                        break
            except Exception:
                pass
        if _pw_dut_mac:
            print("  [INFRA] Pre-creating test device + stream before protocol-start (safe -- no active protocols)...", flush=True)
            _pw_ip = f"10.{(_pw_vlan >> 8) & 0xFF}.{_pw_vlan & 0xFF}.10" if _pw_vlan > 255 else f"10.99.{_pw_vlan}.10"
            _pw_gw = f"10.{(_pw_vlan >> 8) & 0xFF}.{_pw_vlan & 0xFF}.1" if _pw_vlan > 255 else f"10.99.{_pw_vlan}.1"
            try:
                _run_spirent([
                    "create-device",
                    "--name", f"pw_test_v{_pw_vlan}",
                    "--ip", _pw_ip,
                    "--gateway", _pw_gw,
                    "--prefix-len", "24",
                    "--vlan", str(_pw_vlan),
                    "--mac", _test_mac_val,
                    "--mac-step", "00:00:00:00:00:01",
                    "--ip-step", "1",
                    "--device-count", "1",
                    "--no-qinq",
                ], timeout=15)
                print(f"  [INFRA]   device pw_test_v{_pw_vlan} created", flush=True)
            except Exception as _de:
                print(f"  [INFRA]   device pw_test_v{_pw_vlan}: {_de}", flush=True)
            try:
                _run_spirent([
                    "create-stream", "--protocol", "l2",
                    "--vlan", str(_pw_vlan),
                    "--src-mac", _test_mac_val,
                    "--dst-mac", _pw_dut_mac,
                    "--rate-mbps", "1",
                    "--frame-size", "96",
                    "--name", f"pw_test_s_v{_pw_vlan}",
                    "--no-qinq",
                ], timeout=15)
                print(f"  [INFRA]   stream pw_test_s_v{_pw_vlan} created", flush=True)
            except Exception as _se:
                print(f"  [INFRA]   stream pw_test_s_v{_pw_vlan}: {_se}", flush=True)
            print("  [INFRA] Pre-created device + stream (safe -- no protocols running yet).", flush=True)
            params["_pw_objects_precreated"] = "true"

        _ac1_vl = ac1_vlan
        _ac1_outer = _vlan_map.get(_ac1_vl)
        if _ac1_vl and _pw_dut_mac:
            for _sname in [f"acpw_learn_v{_ac1_vl}", f"pwac_learn_v{_ac1_vl}"]:
                try:
                    _ac_args = ["create-stream", "--protocol", "l2"]
                    if _ac1_outer:
                        _ac_args.extend(["--vlan", str(_ac1_outer), "--inner-vlan", str(_ac1_vl)])
                    else:
                        _ac_args.extend(["--vlan", str(_ac1_vl), "--no-qinq"])
                    _ac_args.extend([
                        "--src-mac", _test_mac_val,
                        "--dst-mac", _pw_dut_mac,
                        "--rate-mbps", "1",
                        "--frame-size", "128" if _ac1_outer else "96",
                        "--name", _sname,
                    ])
                    _run_spirent(_ac_args, timeout=15)
                    print(f"  [INFRA]   AC stream {_sname} created", flush=True)
                except Exception as _ase:
                    print(f"  [INFRA]   AC stream {_sname}: {_ase}", flush=True)
            params["_pw_objects_precreated"] = "true"

        print("  [INFRA] Starting protocols on all Spirent devices...", flush=True)
        try:
            _run_spirent(["protocol-start"], timeout=30)
        except Exception as exc:
            print(f"  [INFRA] protocol-start call failed: {exc}", flush=True)

        print("  [INFRA] Waiting for convergence chain: ISIS->LDP->BGP->PW (budget: 90s)...", flush=True)
        _isis_seen = {"v": False}
        _bgp_vpls_seen = {"v": False}
        _max_pw_wait = 90
        import re as _re_pw

        def _pw_full_chain():
            try:
                if not _isis_seen["v"]:
                    _isis_out = run_show(device, "show isis neighbors | no-more")
                    if ("VPLS_PW_Peer" in _isis_out or "0000.0000.0003" in _isis_out) and "Up" in _isis_out:
                        _isis_seen["v"] = True

                if _isis_seen["v"] and not _bgp_vpls_seen["v"]:
                    _bgp_out = run_show(device, "show bgp l2vpn vpls summary | include 17.17.17 | no-more")
                    if "17.17.17.2" in _bgp_out:
                        _bcols = _bgp_out.split()
                        _bstate = _bcols[-1].lower() if _bcols else ""
                        _bad = {"idle", "connect", "active", "opensent", "openconfirm", "never"}
                        if _bstate not in _bad:
                            _bgp_vpls_seen["v"] = True

                _pw_out = run_show(device, "show evpn vpls-pw | no-more")
                if "Installed" in _pw_out:
                    _lbl_m = _re_pw.search(
                        r"\|\s*[\d.]+\s+\|\s+\d+\s+\|\s+(\d+)\s+\|\s+\d+\s+\|\s+\d+\s+\|\s+Installed",
                        _pw_out,
                    )
                    if _lbl_m:
                        return True, {
                            "label": _lbl_m.group(1),
                            "isis": True,
                            "bgp": True,
                            "pw": True,
                        }
                return False, {
                    "isis": _isis_seen["v"],
                    "bgp": _bgp_vpls_seen["v"],
                    "pw": False,
                }
            except Exception as exc:
                return False, {"error": str(exc)}

        def _layer_progress(elapsed: float, observed):
            obs = observed if isinstance(observed, dict) else {}
            _layers = []
            if not obs.get("isis"):
                _layers.append("ISIS")
            if not obs.get("bgp"):
                _layers.append("BGP")
            _layers.append("PW")
            print(f"  [INFRA] Waiting for: {', '.join(_layers)} "
                  f"({int(elapsed)}s/{_max_pw_wait}s)", flush=True)

        _pw_chain_val = poll_until(
            _pw_full_chain,
            timeout_sec=float(_max_pw_wait),
            interval_sec=3.0,
            on_progress=_layer_progress,
            progress_every=5,
            progress_label="ISIS+BGP+PW chain",
        )
        _pw_ready = _pw_chain_val.passed
        if _pw_ready and isinstance(_pw_chain_val.last_value, dict):
            _pw_label = str(_pw_chain_val.last_value.get("label") or "")
            if _pw_label:
                params["pw_ingress_label"] = _pw_label
                print(f"  [INFRA] PW Installed (label={_pw_label}) in "
                      f"{_pw_chain_val.elapsed_sec:.0f}s "
                      f"({_pw_chain_val.attempts} polls)", flush=True)
        if not _pw_ready:
            print(f"  [INFRA] WARNING: PW not Installed after "
                  f"{_pw_chain_val.elapsed_sec:.0f}s "
                  f"({_pw_chain_val.attempts} polls). Scenarios may fail.",
                  flush=True)

            # ===================================================================
            # B12-B14: DEAD-PEER DIAGNOSIS for VPLS PW path
            # PW didn't install -- check if the underlying VPLS BGP peer is dead.
            # If so, log clearly so the user knows what failed (PW reprovision is
            # heavier than EVPN because it needs ISIS/LDP -- we surface, not fix).
            # ===================================================================
            try:
                from shared.dead_peer_recovery import detect_dead_peer as _detect_dead_peer
                _vpls_peer_ip = "17.17.17.2"
                _vpls_check = _detect_dead_peer(
                    run_show, device, _vpls_peer_ip,
                    afi="l2vpn vpls", idle_threshold_sec=30,
                )
                if _vpls_check.get("is_dead"):
                    print(f"  [PEER] VPLS BGP peer {_vpls_peer_ip} DEAD: "
                          f"state={_vpls_check.get('raw_state')} "
                          f"idle={_vpls_check.get('idle_sec')}s -- "
                          f"PW cannot install without BGP. "
                          f"Hint: ISIS/LDP not converged -> check spirent protocol-start logs.",
                          flush=True)
                else:
                    print(f"  [PEER] VPLS BGP peer {_vpls_peer_ip} state="
                          f"{_vpls_check.get('state')} ({_vpls_check.get('raw_state')}) -- "
                          f"BGP OK but PW not installing. Likely label-block / VE-ID mismatch.",
                          flush=True)
            except Exception as _vpls_exc:
                print(f"  [PEER] VPLS peer diagnosis error: {_vpls_exc}", flush=True)

        if _pw_ready and (not params.get("pw_outer_vlan") or not params.get("pw_dut_mac")):
            _ensure_pw_transport_params(params, device, run_show)
            _pw_dut_mac = params.get("pw_dut_mac", _pw_dut_mac)

        if _pw_ready and params.get("pw_ingress_label"):
            _vpls_label = params["pw_ingress_label"]
            _vpls_sname = f"vpls_pw_label_{_vpls_label}"
            _vpls_peer_inner = (_dut_profile.vpls_neighbor_inner_vlan if _dut_profile else 3)
            _vpls_peer_outer = (_dut_profile.vpls_neighbor_outer_vlan if _dut_profile else 214)
            params["_vpls_stream_outer_vlan"] = str(_vpls_peer_outer)
            params["_vpls_stream_inner_vlan"] = str(_vpls_peer_inner)
            try:
                _vpls_args = [
                    "vpls-stream",
                    "--mpls-label", str(_vpls_label),
                    "--inner-src-mac", _test_mac_val,
                    "--inner-dst-mac", _pw_dut_mac or "FF:FF:FF:FF:FF:FF",
                    "--rate-mbps", "1",
                    "--frame-size", "128",
                    "--name", _vpls_sname,
                ]
                if _vpls_peer_outer > 0:
                    _vpls_args.extend(["--outer-vlan", str(_vpls_peer_outer)])
                if _vpls_peer_inner > 0:
                    _vpls_args.extend(["--inner-vlan", str(_vpls_peer_inner)])
                if _pw_dut_mac:
                    _vpls_args.extend(["--dst-mac", _pw_dut_mac])
                _run_spirent(_vpls_args, timeout=15)
                print(f"  [INFRA]   VPLS stream {_vpls_sname} pre-created (label={_vpls_label}, "
                      f"outer={_vpls_peer_outer}, inner={_vpls_peer_inner})", flush=True)
            except Exception as _vse:
                print(f"  [INFRA]   VPLS stream {_vpls_sname}: {_vse}", flush=True)

    # -- EVPN BGP convergence (DUT-side FSM polling, 3s intervals) --
    if _evpn_early_provisioned and method == TrafficMethod.SPIRENT:
        if infra_required not in ("spirent_vpls_cp", "mixed"):
            from shared.mac_trigger import _run_spirent as _run_sp_evpn_start
            try:
                _run_sp_evpn_start(["protocol-start", "--device-name", "EVPN_RT2_Peer"], timeout=30)
                print("  [INFRA] Started EVPN_RT2_Peer protocols (si_mode -- PW protocol-start was skipped).", flush=True)
            except Exception as _eps:
                print(f"  [INFRA] EVPN_RT2_Peer protocol-start error: {_eps}", flush=True)
        _evpn_peer_ip = params.get("spirent_peer_ip", "19.19.19.2")
        print(f"  [INFRA] Checking EVPN BGP {_evpn_peer_ip} on DUT (budget: 45s)...", flush=True)
        _evpn_val = wait_for_bgp_state(
            run_show, device, _evpn_peer_ip,
            target="ESTABLISHED",
            afi="l2vpn evpn",
            timeout_sec=45.0,
            interval_sec=3.0,
        )
        _evpn_bgp_ok = _evpn_val.passed
        if _evpn_bgp_ok:
            print(f"  [INFRA] EVPN BGP {_evpn_peer_ip} ESTABLISHED in "
                  f"{_evpn_val.elapsed_sec:.1f}s ({_evpn_val.attempts} polls)",
                  flush=True)
        else:
            print(f"  [INFRA] WARNING: EVPN BGP {_evpn_peer_ip} not ESTABLISHED "
                  f"after {_evpn_val.elapsed_sec:.0f}s "
                  f"({_evpn_val.attempts} polls)", flush=True)

            # ===================================================================
            # B12-B14: DEAD-PEER AUTO-REPROVISION
            # The Spirent BGP peer is stuck (Connect/Active/Idle for too long).
            # Don't waste another 90s waiting for a corpse -- pick a fresh IP +
            # inner VLAN, validate DNOS config via commit-check, apply, and
            # recreate the Spirent device at the new address. This keeps the
            # test moving instead of failing the deferred smoke test below.
            # ===================================================================
            try:
                from shared.dead_peer_recovery import (
                    detect_dead_peer as _detect_dead_peer,
                    reprovision_evpn_peer as _reprovision_evpn_peer,
                )

                _dead_check = _detect_dead_peer(
                    run_show, device, _evpn_peer_ip,
                    afi="l2vpn evpn", idle_threshold_sec=30,
                )
                _is_dead = bool(_dead_check.get("is_dead"))
                _raw_state = _dead_check.get("raw_state", "?")
                _idle = _dead_check.get("idle_sec", 0)

                if _is_dead:
                    print(f"  [PEER] DEAD peer confirmed: {_evpn_peer_ip} "
                          f"state={_raw_state} idle={_idle}s -- triggering auto-reprovision",
                          flush=True)

                    # Prefer the DUTProfile (built earlier via require_dut_profile);
                    # fall back to the device-agnostic DeviceProfile we discover
                    # live via SSH+show config. ONLY resort to a hardcoded ASN if
                    # both fail -- and even then we log loudly so the user sees it.
                    _reprov_asn = 0
                    _reprov_outer = 214
                    if _dut_profile:
                        _reprov_asn = int(_dut_profile.bgp_asn)
                        _reprov_outer = int(_dut_profile.evpn_neighbor_outer_vlan)
                    if _reprov_asn <= 0:
                        try:
                            _live_profile = build_device_profile(
                                run_show, device,
                            )
                            if _live_profile.bgp_asn:
                                _reprov_asn = int(_live_profile.bgp_asn)
                                print(f"  [PEER] Discovered DUT BGP ASN={_reprov_asn} "
                                      f"via live show-config", flush=True)
                            for _w in (_live_profile.discovery_warnings or [])[:3]:
                                print(f"  [PEER] profile warn: {_w}", flush=True)
                        except Exception as _bp_exc:
                            print(f"  [PEER] Live profile build failed: {_bp_exc}",
                                  flush=True)
                    if _reprov_asn <= 0:
                        _reprov_asn = 1234567
                        print("  [PEER] WARNING: could not discover DUT ASN -- "
                              "falling back to legacy default 1234567 "
                              "(reprovision likely to fail)", flush=True)
                    _reprov_rt = params.get("rt") or "100:100"

                    _reprov = _reprovision_evpn_peer(
                        run_show=run_show, device=device,
                        asn=_reprov_asn,
                        dead_peer_ip=_evpn_peer_ip,
                        outer_vlan=_reprov_outer,
                        evpn_rt=_reprov_rt,
                        bgp_verify_budget_sec=45,
                    )
                    preflight["dead_peer_reprovision"] = _reprov
                    _tier = str(_reprov.get("tier", "?"))

                    if _reprov.get("success"):
                        _new_peer_ip = str(_reprov.get("new_peer_ip", ""))
                        _new_dut_ip = str(_reprov.get("new_dut_ip", ""))
                        _new_inner = int(_reprov.get("new_inner_vlan", 0) or 0)
                        _evpn_peer_ip = _new_peer_ip
                        params["spirent_peer_ip"] = _new_peer_ip
                        params["spirent_evpn_neighbor_dut_ip"] = _new_dut_ip
                        params["spirent_evpn_inner_vlan"] = str(_new_inner)
                        if _dut_profile:
                            _dut_profile.evpn_neighbor_ip = _new_peer_ip
                            _dut_profile.evpn_neighbor_gw = _new_dut_ip
                            if _new_inner:
                                _dut_profile.evpn_neighbor_inner_vlan = _new_inner
                        _evpn_bgp_ok = True
                        _tier_msg = ("in-place rebuild (same path)"
                                     if _tier == "in_place"
                                     else f"fresh allocation tier={_tier}")
                        print(f"  [PEER] Reprovision SUCCESS via {_tier_msg} -- "
                              f"peer {_new_peer_ip} (vlan {_reprov_outer}/{_new_inner})",
                              flush=True)
                    else:
                        if _tier == "abort_dnaas_down":
                            _l2 = _reprov.get("spirent_l2_health", {}) or {}
                            _broken_vlans = sorted(set(
                                int(v) for v, cnt in
                                (_l2.get("outer_vlan_failure_count", {}) or {}).items()
                                if cnt > 0
                            ))
                            print("", flush=True)
                            print("=" * 76, flush=True)
                            print("  [PEER] *** DNAAS L2 PATH IS DOWN -- "
                                  "RECOVERY ABORTED ***", flush=True)
                            print("=" * 76, flush=True)
                            print(f"  [PEER] Outer VLAN(s) with broken ARP: "
                                  f"{_broken_vlans}", flush=True)
                            print(f"  [PEER] {_l2.get('summary', '')}", flush=True)
                            print("  [PEER] Auto-reprovision SKIPPED -- this is an "
                                  "infra-layer fault, not a Spirent or DNOS config "
                                  "issue. No DUT config was changed.", flush=True)
                            print("  [PEER] Action required: network-admin must "
                                  "verify DNAAS-LEAF-B14 bridge-domain on outer "
                                  "VLAN(s) above (LLP, port-link, MAC-learning).",
                                  flush=True)
                            print("=" * 76, flush=True)
                        elif _tier == "fresh_smoke_blocked":
                            _smoke = _reprov.get("smoke_check", {}) or {}
                            print(f"  [PEER] Reprovision BLOCKED at DNAAS smoke probe: "
                                  f"{_smoke.get('detail', 'unknown')}", flush=True)
                            print("  [PEER] No DUT config was committed -- "
                                  "the candidate inner VLAN is not on a DNAAS path. "
                                  "Ask network-admin to extend the bridge-domain.",
                                  flush=True)
                        else:
                            print(f"  [PEER] Reprovision did not establish a fresh peer "
                                  f"(tier={_tier}, elapsed={_reprov.get('elapsed_sec','?')}s) "
                                  "-- continuing with degraded infra "
                                  "(scenarios will surface issues)", flush=True)
                else:
                    print(f"  [PEER] Peer {_evpn_peer_ip} not classified as DEAD "
                          f"(state={_raw_state}, idle={_idle}s, threshold=30s) -- "
                          f"skipping auto-reprovision",
                          flush=True)
            except Exception as _reprov_exc:
                print(f"  [PEER] Auto-reprovision error: {_reprov_exc} -- "
                      f"continuing with original peer", flush=True)

    # ===================================================================
    # B11: DEFERRED SMOKE TEST RE-RUN
    # If preflight smoke was deferred because BGP EVPN was down (SI ACs
    # would block all frames), re-run it now that infra has brought BGP up.
    # If it STILL fails, abort -- the L2 path is genuinely broken.
    #
    # B12 GATE: only re-run if the BGP EVPN actually came up. If BGP is
    # still DOWN (e.g. reprovision failed), the smoke WILL fail again --
    # don't waste 12s on a guaranteed-failure poll. Skip directly to the
    # scenarios with a clear infra warning so the user sees the real cause.
    # ===================================================================
    if _smoke_deferred and method == TrafficMethod.SPIRENT and not _evpn_bgp_ok:
        print("\n  [PREFLIGHT] Skipping deferred smoke re-run -- "
              "EVPN BGP never converged AND reprovision did not succeed.",
              flush=True)
        print("  [PREFLIGHT] Smoke would fail (SI keeps ACs blocking-all). "
              "Scenarios will surface the underlying BGP issue.",
              flush=True)
    elif _smoke_deferred and method == TrafficMethod.SPIRENT:
        print("\n  [PREFLIGHT] BGP EVPN converged -- re-running deferred smoke test...", flush=True)
        # NOTE: removed `time.sleep(3)` -- smoke_test_l2_path internally polls
        # the DUT MAC table via wait_for_mac_in_table, which already absorbs
        # any small post-convergence settle window. No need to gate it.
        try:
            from shared.spirent_preflight import smoke_test_l2_path as _smoke_rerun
            _smoke2 = _smoke_rerun(
                run_show=run_show,
                device=device,
                evpn_name=evpn_name_for_smoke,
                ac_vlan=ac1_vlan,
                outer_vlan=ac1_outer_for_smoke,
                dut_mac=_smoke_dut_mac,
                ac_interface=_smoke_ac_if,
                port_mode=_is_port_mode_ac,
                fabric_vlan=_smoke_fabric_vlan,
            )
            preflight["smoke_test_rerun"] = _smoke2
            if _smoke2.get("pass"):
                print(f"  [PREFLIGHT] Deferred smoke test PASSED in "
                      f"{_smoke2.get('elapsed_sec', 0)}s -- proceeding with scenarios.",
                      flush=True)
            else:
                print(f"  [PREFLIGHT FAIL] Deferred smoke STILL fails: "
                      f"{_smoke2.get('detail', 'unknown')}", flush=True)
                print("  [PREFLIGHT] Aborting -- L2 path is genuinely broken even with BGP up.",
                      flush=True)
                test_verdict.total_elapsed_sec = round(time.time() - t0, 2)
                for sc in recipe.get("scenarios", []):
                    sc_id = sc.get("id", "scenario_preflight")
                    sv = ScenarioVerdict(scenario_id=sc_id,
                                         scenario_name=sc.get("name", sc_id))
                    sv.layers.append(LayerResult(
                        "preflight_smoke_test_rerun", VerdictStatus.FAIL,
                        _smoke2.get("detail", "L2 path broken after BGP up"),
                        evidence=json.dumps(_smoke2.get("steps", []), indent=2)[:500],
                    ))
                    sv.compute_overall()
                    test_verdict.scenarios.append(sv)
                test_verdict.compute_overall()
                return test_verdict
        except Exception as exc:
            print(f"  [PREFLIGHT] Deferred smoke re-run errored: {exc} -- "
                  f"continuing anyway (scenarios will surface issues).", flush=True)

    # -- ENGINE: Config baseline (golden config before test) --
    config_before = None
    health_before = None
    isolation_guard = None
    if _ENGINES_AVAILABLE:
        resilient = get_cached_runner(device, agent_callback=run_show)
        try:
            baseline_cfg = load_baseline_config(recipe)
            baseline_sections = [
                substitute(str(section), params)
                for section in (baseline_cfg.get("sections") or [])
            ]
            config_before = snapshot_config(
                device, "before_test", resilient,
                sections=baseline_sections,
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

    scenarios = recipe.get("scenarios", [])
    if scenario_filter:
        filters = [f.strip().lower() for f in scenario_filter.split(",")]
        scenarios = [
            s for s in scenarios
            if any(f in s.get("id", "").lower() for f in filters)
        ]
        if not scenarios:
            print(f"  [WARN] No scenario matching '{scenario_filter}' found in recipe")
    # ===================================================================
    # PREREQUISITE GATE: Check ALL scenario infra requirements BEFORE
    # running ANY scenario. If any scenario has unmet prerequisites,
    # abort the entire test with a clear report of what's missing.
    # ===================================================================
    _TRIGGERS_NEEDING_EVPN_PEER = {"spirent_remote_pe", "spirent_ac_to_evpn", "spirent_evpn_to_ac",
                                   "spirent_evpn_to_pw", "spirent_pw_to_evpn"}
    _TRIGGERS_NEEDING_PW = {"spirent_pw_traffic", "spirent_ac_to_pw", "spirent_pw_to_pw",
                            "spirent_evpn_to_pw", "spirent_pw_to_evpn", "spirent_pw_then_ac"}

    evpn_peer_device = params.get("spirent_evpn_device", "")
    evpn_peer_live = False
    if evpn_peer_device and preflight.get("spirent_available"):
        try:
            sess = preflight.get("spirent", {}).get("session", {})
            for d in sess.get("devices", []):
                if d.get("name") == evpn_peer_device:
                    evpn_peer_live = True
                    break
        except Exception:
            pass

    pw_infra_ready = bool(params.get("pw_ingress_label"))
    if not pw_infra_ready:
        try:
            from shared.mac_trigger import _get_existing_device_names
            _existing = _get_existing_device_names(force_refresh=True)
            if "VPLS_PW_Peer" in _existing:
                pw_infra_ready = True
        except Exception:
            pass

    _any_scenario_needs_pw = any(
        ACTION_TRIGGER_MAP.get(
            (s.get("phases", {}).get("trigger") or {}).get("action", ""), "unknown"
        ) in _TRIGGERS_NEEDING_PW
        or s.get("infra_required") in ("spirent_vpls_cp", "spirent_vpls_cp_dual")
        for s in scenarios
    )
    if not pw_infra_ready and _any_scenario_needs_pw and preflight.get("spirent_available"):
        print("\n  [PW-AUTO] Scenario(s) need VPLS PW -- auto-provisioning spirent_vpls_cp...",
              flush=True)
        try:
            prov = provision_spirent_vpls_cp(device, run_show, defer_protocol_start=True,
                                             profile=_dut_profile)
            for s in prov.steps:
                print(f"    [{s.get('status')}] {s.get('step')}: {s.get('detail', '')}", flush=True)
            if prov.ready:
                pw_infra_ready = True
                params.update(prov.params)
                print(f"  [PW-AUTO] VPLS PW provisioned: label={prov.ingress_label}", flush=True)
                if prov.protocols_deferred:
                    print("  [PW-AUTO] Starting protocols now for early convergence...", flush=True)
                    try:
                        from shared.mac_trigger import _run_spirent
                        _run_spirent(["protocol-start"], timeout=15)
                        print("  [PW-AUTO] Protocols started. ISIS+LDP+BGP converging in background.", flush=True)
                    except Exception as _pse:
                        print(f"  [PW-AUTO] Protocol-start warning: {_pse}", flush=True)
            else:
                print(f"  [PW-AUTO] Provisioning incomplete: {prov.blocker or 'unknown'}", flush=True)
        except Exception as exc:
            print(f"  [PW-AUTO] Provisioning failed: {exc}", flush=True)

    # -- AUTO-PROVISION: If EVPN peer is missing and scenarios need it,
    #    provision it now using DUT-derived params (RD/RT/EVI).
    #    Skip if early provisioning already handled it.
    if _evpn_early_provisioned:
        evpn_peer_live = True
        try:
            from shared.mac_trigger import _get_existing_device_names
            if evpn_peer_device in _get_existing_device_names(force_refresh=True):
                evpn_peer_live = True
        except Exception:
            pass
    needs_evpn = any(
        ACTION_TRIGGER_MAP.get(
            (s.get("phases", {}).get("trigger") or {}).get("action", ""), "unknown"
        ) in _TRIGGERS_NEEDING_EVPN_PEER
        and not bool((s.get("phases", {}).get("trigger") or {}).get("spirent_flags_pinned"))
        for s in scenarios
    )
    if needs_evpn and not evpn_peer_live and preflight.get("spirent_available"):
        dut_rt = params.get("pw_rt") or params.get("rt", "100:100")
        print(f"  [PREREQ] EVPN peer '{evpn_peer_device}' missing -- auto-provisioning "
              f"with DUT-derived RT={dut_rt}", flush=True)
        try:
            prov_result = provision_spirent_evpn_peer(
                device, run_show, evpn_rt=dut_rt, bgp_only=True,
                profile=_dut_profile,
            )
            _prov_ok = prov_result.ready or any(
                s.get("status") in ("PASS", "WARN") and "bgp" in s.get("step", "")
                for s in prov_result.steps
            )
            if not _prov_ok:
                _device_created = any(
                    s.get("status") == "PASS" and "device" in s.get("step", "")
                    for s in prov_result.steps
                )
                if _device_created:
                    _prov_ok = True
            if _prov_ok:
                evpn_peer_live = True
                print("  [PREREQ] EVPN peer auto-provisioned successfully", flush=True)
                for s in prov_result.steps:
                    print(f"    [{s.get('status')}] {s.get('step')}: {s.get('detail', '')}", flush=True)
            else:
                print("  [PREREQ] EVPN peer auto-provisioning FAILED:", flush=True)
                for s in prov_result.steps:
                    print(f"    [{s.get('status')}] {s.get('step')}: {s.get('detail', '')}", flush=True)
                if prov_result.blocker:
                    print(f"  [PREREQ] Blocker: {prov_result.blocker}", flush=True)
        except Exception as exc:
            print(f"  [PREREQ] EVPN peer auto-provisioning exception: {exc}", flush=True)

    print("  === SCENARIO PREREQUISITE GATE ===", flush=True)
    unmet: Dict[str, Dict[str, str]] = {}
    for sc in scenarios:
        sc_id = sc.get("id", "?")
        trigger = (sc.get("phases", {}).get("trigger") or {})
        action = trigger.get("action", "")
        mapped = ACTION_TRIGGER_MAP.get(action, "unknown")
        _needs_evpn_peer = (
            mapped in _TRIGGERS_NEEDING_EVPN_PEER
            and not bool(trigger.get("spirent_flags_pinned"))
        )
        _needs_pw = mapped in _TRIGGERS_NEEDING_PW
        if _needs_evpn_peer and not evpn_peer_live:
            unmet[sc_id] = {
                "scenario": sc_id,
                "need": "Spirent EVPN BGP peer",
                "detail": f"Device '{evpn_peer_device}' not in Spirent session",
                "fix": "Run: /SPIRENT bgp PE-1 (create EVPN_RT2_Peer device)",
            }
        elif _needs_pw and not pw_infra_ready:
            unmet[sc_id] = {
                "scenario": sc_id,
                "need": "VPLS PW infrastructure",
                "detail": "No PW ingress label -- SI instance has BNI PW (needs non-SI instance)",
                "fix": "Create non-SI EVPN instance + Spirent VPLS BGP peer",
            }

    runnable = [sc for sc in scenarios if sc.get("id", "?") not in unmet]

    if unmet:
        print(f"\n  [PREREQ] {len(unmet)} scenario(s) have unmet prerequisites (will SKIP):")
        for u in unmet.values():
            print(f"    {u['scenario']}: needs {u['need']} -- {u['detail']}")
        for sc_id, u in unmet.items():
            sc_match = next((s for s in scenarios if s.get("id") == sc_id), None)
            sv = ScenarioVerdict(scenario_id=sc_id,
                                 scenario_name=(sc_match or {}).get("name", sc_id))
            sv.layers.append(LayerResult(
                "prereq_gate", VerdictStatus.SKIP,
                f"SKIP: {u['need']} -- {u['detail']}",
            ))
            sv.compute_overall()
            test_verdict.scenarios.append(sv)

    if not runnable:
        print("\n  [PREREQ FAIL] ALL scenarios blocked -- no runnable scenarios.")
        test_verdict.total_elapsed_sec = round(time.time() - t0, 2)
        test_verdict.compute_overall()
        write_active_session({"active": False, "completed": now_iso(), "verdict": "PREREQ_FAIL"})
        return test_verdict

    if unmet:
        print(f"  [PREREQ] {len(runnable)}/{len(scenarios)} scenario(s) will run, "
              f"{len(unmet)} SKIPPED", flush=True)
    else:
        print("  [PREREQ] All scenario infrastructure requirements met", flush=True)
    print("  === SCENARIO PREREQUISITE GATE PASSED ===\n", flush=True)

    _MAX_RETRIES_PER_SCENARIO = 1
    _last_provision: Dict[str, Any] = {}

    for idx, scenario in enumerate(runnable):
        sc_id = scenario.get("id", f"scenario_{idx}")

        # Rollback guard: ensure previous scenario's config does not leak.
        if _last_provision.get("applied"):
            try:
                _rollback_scenario_config(device, _last_provision, run_show)
                print("  [ROLLBACK-GUARD] Cleaned residual config from prior scenario", flush=True)
            except Exception:
                pass
            _last_provision = {}

        print(f"  [{idx + 1}/{len(runnable)}] Running {sc_id}...")

        sv = execute_scenario(
            device, scenario, params, run_show,
            ac1_vlan, ac2_vlan, mac_count, method,
            run_dir=run_dir,
            recipe=recipe,
            dut_profile=_dut_profile,
        )

        if sv.overall in (VerdictStatus.FAIL, VerdictStatus.ERROR):
            diag = _live_failure_detector(
                device, scenario, sv, params, run_show,
                ac1_vlan, ac2_vlan, method,
            )
            sv.failure_diagnosis = diag  # type: ignore[attr-defined]

            if diag.get("should_retry") and diag.get("fix_applied"):
                print(f"  [RETRY] Re-running {sc_id} after fix ({diag['fix_description']})...",
                      flush=True)
                sv_retry = execute_scenario(
                    device, scenario, params, run_show,
                    ac1_vlan, ac2_vlan, mac_count, method,
                    run_dir=run_dir,
                    recipe=recipe,
                    dut_profile=_dut_profile,
                )
                if sv_retry.overall.value <= sv.overall.value:
                    sv = sv_retry
                    sv.retried = True  # type: ignore[attr-defined]
                    print(f"  [RETRY] Result: {sv.overall.value.upper()}", flush=True)
                else:
                    print(f"  [RETRY] Retry did not improve: {sv_retry.overall.value.upper()}",
                          flush=True)

        test_verdict.scenarios.append(sv)
        _last_provision = getattr(sv, "_provision_state", {}) or {}

        if sv.overall in (VerdictStatus.FAIL, VerdictStatus.ERROR) and recipe.get("verdict", {}).get("stop_on_fail"):
            print(
                f"  [FLOW] Stopping on {sv.overall.value.upper()} in {sv.scenario_id} "
                "per recipe stop_on_fail. Treat as bug-candidate/infra blocker before rerun.",
                flush=True,
            )
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
                baseline_sections = [
                    substitute(str(section), params)
                    for section in (baseline_cfg.get("sections") or [])
                ]
                config_after = snapshot_config(
                    device, "after_test", resilient,
                    sections=baseline_sections,
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


__all__ = ["execute_test"]
