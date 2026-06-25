#!/usr/bin/env python3
"""
Prerequisite checks + auto-remediation for EVPN MAC mobility suite (SW-204115).

Each check returns pass/fail + a remediation action that can be executed
via /SPIRENT, config_generator, or MCP commands.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config_generator import plan_config_delta
from shared.config_knowledge import run_config_gap_analysis, generate_fix_snippets
from shared.evpn_service_selector import (
    evaluate_evpn_service_for_recipe,
    DECISION_REUSE,
    DECISION_EXTEND,
    DECISION_CREATE,
    DECISION_NONE,
)

RunShowFn = Callable[[str, str], str]


@dataclass
class PrereqResult:
    check_id: str
    status: str  # PASS, FAIL, WARN
    detail: str
    fix_via: str
    auto_fixable: bool = False
    fix_commands: List[str] = field(default_factory=list)
    spirent_action: Optional[str] = None


@dataclass
class PrereqReport:
    test_id: str
    device: str
    results: List[PrereqResult] = field(default_factory=list)
    overall: str = "PASS"
    config_delta: Dict[str, Any] = field(default_factory=dict)

    def compute_overall(self) -> None:
        if any(r.status == "FAIL" for r in self.results):
            self.overall = "FAIL"
        elif any(r.status == "WARN" for r in self.results):
            self.overall = "WARN"
        else:
            self.overall = "PASS"


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_evpn_instance(ctx: Dict[str, Any]) -> PrereqResult:
    ok = bool(ctx.get("evpn_name_primary"))
    return PrereqResult(
        check_id="evpn_instance",
        status="PASS" if ok else "FAIL",
        detail=ctx.get("evpn_name_primary") or "none found",
        fix_via="config_generator.build_minimal_si_evpn_snippet + validate_config",
        auto_fixable=False,
        fix_commands=[
            "! Use config_generator.build_minimal_si_evpn_snippet(name, bd, acs)",
            "! Then validate_config(device, snippet) and commit",
        ],
    )


def _check_bgp_evpn(ctx: Dict[str, Any]) -> PrereqResult:
    est = ctx.get("bgp_evpn_established", 0)
    total = ctx.get("bgp_evpn_total", 0)
    ok = est > 0
    return PrereqResult(
        check_id="bgp_l2vpn_evpn",
        status="PASS" if ok else "FAIL",
        detail=f"{est}/{total} Established",
        fix_via="Manual BGP L2VPN EVPN peering or scaler wizard",
        auto_fixable=False,
    )


def _check_seamless_integration(ctx: Dict[str, Any]) -> PrereqResult:
    ok = bool(ctx.get("seamless_integration_configured"))
    return PrereqResult(
        check_id="seamless_integration",
        status="PASS" if ok else "FAIL",
        detail=str(ok),
        fix_via="Add seamless-integration under EVPN instance (no IRB allowed)",
        auto_fixable=False,
        fix_commands=[
            "network-services",
            " evpn",
            f"  instance {ctx.get('evpn_name_primary', 'EVPN_INSTANCE')}",
            "   seamless-integration",
            "   !",
        ],
    )


def _check_mac_table(ctx: Dict[str, Any]) -> PrereqResult:
    count = ctx.get("mac_table_count", 0)
    ok = count > 0
    return PrereqResult(
        check_id="mac_table_populated",
        status="PASS" if ok else "FAIL",
        detail=f"count={count}",
        fix_via="/SPIRENT l2 -- create L2 devices to learn MACs",
        auto_fixable=True,
        spirent_action="spirent_create_l2_devices",
    )


def _check_two_acs(ctx: Dict[str, Any], test_id: str) -> PrereqResult:
    needs = "ac_ac" in test_id or "SW205161" in test_id
    ac_hints = ctx.get("ac_interface_hints") or []
    ok = len(ac_hints) >= 2 or not needs
    status = "PASS" if ok else ("FAIL" if needs else "WARN")
    return PrereqResult(
        check_id="two_acs",
        status=status,
        detail=f"AC interfaces found: {len(ac_hints)}",
        fix_via="Add second AC on bridge-domain / /SPIRENT dnaas fix for second VLAN path",
        auto_fixable=needs and not ok,
        spirent_action="spirent_dnaas_fix_second_vlan" if (needs and not ok) else None,
    )


def _check_pseudowire(ctx: Dict[str, Any], test_id: str) -> PrereqResult:
    needs = any(x in test_id for x in ("pw_pw", "ac_pw", "evpn_pw", "SW205162", "SW205198", "SW205199"))
    ok = bool(ctx.get("pw_configured_hint")) or not needs
    return PrereqResult(
        check_id="pseudowire",
        status="PASS" if ok else "FAIL",
        detail=str(ctx.get("pw_configured_hint")),
        fix_via="Configure VPLS pseudowire attachment",
        auto_fixable=False,
    )


def _check_multihoming(ctx: Dict[str, Any], test_id: str) -> PrereqResult:
    needs = "mh" in test_id or "SW205195" in test_id
    ok = bool(ctx.get("esi_present")) or not needs
    return PrereqResult(
        check_id="multihoming_esi",
        status="PASS" if ok else "FAIL",
        detail=str(ctx.get("esi_present")),
        fix_via="Configure ethernet-segment / multihoming",
        auto_fixable=False,
    )


def _check_cluster(ctx: Dict[str, Any], test_id: str) -> PrereqResult:
    needs = "ha" in test_id or "SW205165" in test_id
    ok = ctx.get("device_type") == "cluster" or not needs
    return PrereqResult(
        check_id="cluster_for_ha",
        status="PASS" if ok else "FAIL",
        detail=ctx.get("device_type", "unknown"),
        fix_via="NCC cluster with standby required for switchover tests",
        auto_fixable=False,
    )


def _check_evpn_si_rt_complete(
    ctx: Dict[str, Any],
    device: str,
    recipe: Optional[Dict[str, Any]],
    run_show: Optional[RunShowFn],
) -> PrereqResult:
    """Validate that the EVPN service the test will drive has the RT lines
    required by the recipe's `service_capabilities` block.

    Why this exists
    ---------------
    On 2026-04-30 the basic_learning SC01 test failed `rt2_advertised` with
    a healthy session, an up AC, and a locally-learned MAC. /debug-dnos
    found the EVI was missing native EVPN RTs (only had SI VPLS RTs), so
    DNOS was working as configured -- it just had no export RT to advertise
    RT-2 with. This check turns that finding into a permanent gate.

    Backward compatibility
    ----------------------
    Recipes without `service_capabilities` skip this check (PASS). New
    recipes opt in by declaring required capabilities in the recipe JSON.
    """
    # If no run_show or no recipe, we cannot evaluate -- skip cleanly.
    if recipe is None or run_show is None:
        return PrereqResult(
            check_id="evpn_si_rt_complete",
            status="PASS",
            detail="skipped (no recipe / no live run_show)",
            fix_via="-",
            auto_fixable=False,
        )

    try:
        report = evaluate_evpn_service_for_recipe(
            run_show=run_show,
            device=device,
            recipe=recipe,
            evpn_name_hint=ctx.get("evpn_name_primary"),
        )
    except Exception as exc:
        return PrereqResult(
            check_id="evpn_si_rt_complete",
            status="WARN",
            detail=f"selector crashed: {type(exc).__name__}: {exc}",
            fix_via="Inspect shared/evpn_service_selector.py",
            auto_fixable=False,
        )

    decision = report.get("decision") or {}
    action = decision.get("action") or DECISION_NONE
    fix_snippet = decision.get("fix_snippet") or ""

    # Stash the full structured decision into ctx so the orchestrator can
    # surface an AskQuestion (REUSE / EXTEND / CREATE / Abort) without
    # re-deriving it. The PrereqResult has no rich field for this so we
    # piggy-back on ctx (already a shared dict by reference).
    ctx["evpn_service_decision"] = decision
    ctx["evpn_service_inventory"] = report.get("instances") or {}

    if action == DECISION_NONE:
        return PrereqResult(
            check_id="evpn_si_rt_complete",
            status="PASS",
            detail=report.get("detail") or "no service_capabilities declared",
            fix_via="-",
            auto_fixable=False,
        )

    if action == DECISION_REUSE:
        return PrereqResult(
            check_id="evpn_si_rt_complete",
            status="PASS",
            detail=report.get("detail") or "REUSE existing instance",
            fix_via="-",
            auto_fixable=False,
        )

    if action == DECISION_EXTEND:
        return PrereqResult(
            check_id="evpn_si_rt_complete",
            status="FAIL",
            detail=report.get("detail")
                   or "EXTEND existing instance with missing RT lines",
            fix_via=("Surgical RT add via dnos_atomic_commit. "
                     f"Inspect ctx['evpn_service_decision']['fix_snippet'] "
                     f"({len(fix_snippet)} chars) before approving."),
            auto_fixable=True,
            fix_commands=[fix_snippet] if fix_snippet else [],
        )

    if action == DECISION_CREATE:
        return PrereqResult(
            check_id="evpn_si_rt_complete",
            status="FAIL",
            detail=report.get("detail") or "CREATE new EVPN instance required",
            fix_via=("config_generator.build_minimal_si_evpn_snippet + "
                     "validate_config + user-approved dnos_atomic_commit"),
            auto_fixable=False,
        )

    return PrereqResult(
        check_id="evpn_si_rt_complete",
        status="WARN",
        detail=f"unknown decision action: {action}",
        fix_via="-",
        auto_fixable=False,
    )


def _check_spirent_session(ctx: Dict[str, Any]) -> PrereqResult:
    """Check if Spirent is reachable and a session exists for L2 traffic."""
    from shared.mac_trigger import SPIRENT_TOOL, detect_traffic_methods, TrafficMethod
    has_spirent = TrafficMethod.SPIRENT in detect_traffic_methods()
    return PrereqResult(
        check_id="spirent_available",
        status="PASS" if has_spirent else "WARN",
        detail="spirent_tool.py found" if has_spirent else "Not found -- manual traffic only",
        fix_via="Install spirent_tool.py or set SPIRENT_HOME",
        auto_fixable=False,
    )


def _check_dnaas_path(
    ctx: Dict[str, Any],
    device: str,
    run_show: Optional[RunShowFn],
) -> PrereqResult:
    """Basic check for DNAAS bridge-domain path readiness."""
    bd_hint = ctx.get("bridge_domain_hint")
    if bd_hint:
        return PrereqResult(
            check_id="dnaas_path",
            status="PASS",
            detail="Bridge-domain instances found",
            fix_via="/SPIRENT dnaas fix",
            auto_fixable=True,
            spirent_action="spirent_dnaas_check",
        )
    return PrereqResult(
        check_id="dnaas_path",
        status="WARN",
        detail="No bridge-domain detected -- may need DNAAS setup",
        fix_via="/SPIRENT dnaas fix to create BD path for L2 traffic",
        auto_fixable=True,
        spirent_action="spirent_dnaas_fix",
    )


def _check_spirent_sync_live(
    ctx: Dict[str, Any],
    device: str,
    test_id: str,
) -> List[PrereqResult]:
    """Run live /SPIRENT sync checks: fabric health + description tagging.

    Per user mandate ("/SPIRENT must be CALLED and synced with any /TEST that
    requires devices"), this wraps spirent_sync.py to run dnaas-diagnose on
    the Spirent transport VLAN and dry-run mark-dnos on the DUT. Both are
    reported as individual prereq rows with `auto_fixable=True` pointing to
    spirent_sync.run_full_sync for remediation.
    """
    results: List[PrereqResult] = []

    fabric_vlan = ctx.get("spirent_fabric_vlan") or 214  # default for this lab
    if not ctx.get("requires_spirent", True):
        results.append(PrereqResult(
            check_id="spirent_sync",
            status="SKIP",
            detail="requires_spirent=false",
            fix_via="-",
            auto_fixable=False,
        ))
        return results

    try:
        from spirent_sync import check_fabric_health, sync_descriptions
    except Exception as e:
        results.append(PrereqResult(
            check_id="spirent_sync_import",
            status="WARN",
            detail=f"spirent_sync module not importable: {e}",
            fix_via="Verify TEST catalog deploy includes spirent_sync.py",
            auto_fixable=False,
        ))
        return results

    # 1) Fabric health
    try:
        fabric = check_fabric_health(int(fabric_vlan), dut=device)
        results.append(PrereqResult(
            check_id=f"spirent_fabric_v{fabric_vlan}",
            status=fabric.status,
            detail=fabric.detail,
            fix_via=(
                f"dnos_dnaas_diagnose(vlan={fabric_vlan}, dut={device})"
                " then user-approved dnos_dnaas_clear_llp/stabilize_plan if needed"
            ),
            auto_fixable=True,
            spirent_action="mcp_dnaas_blocker" if fabric.status == "FAIL" else None,
        ))
    except Exception as e:
        results.append(PrereqResult(
            check_id=f"spirent_fabric_v{fabric_vlan}",
            status="WARN",
            detail=f"fabric-health probe failed: {e}",
            fix_via=f"Run dnos_dnaas_diagnose(vlan={fabric_vlan}, dut={device})",
            auto_fixable=False,
        ))

    # 2) Description tagging coverage (dry-run)
    dut_host = ctx.get("device_mgmt_ip") or device
    try:
        tag_results = sync_descriptions(dut=dut_host, dry_run=True)
        tagr = tag_results[0] if tag_results else None
        if tagr and tagr.status == "PASS" and tagr.patches_applied == 0:
            detail = "all Spirent objects already tagged on DUT"
            status = "PASS"
        else:
            status = "WARN"
            detail = (f"{tagr.patches_applied if tagr else '?'} description "
                      f"patches missing on DUT; run spirent_tool.py mark-dnos --dut {dut_host}")
        results.append(PrereqResult(
            check_id="spirent_desc_tags",
            status=status,
            detail=detail,
            fix_via=f"spirent_tool.py mark-dnos --dut {dut_host}",
            auto_fixable=True,
            spirent_action="spirent_mark_dnos",
        ))
    except Exception as e:
        results.append(PrereqResult(
            check_id="spirent_desc_tags",
            status="WARN",
            detail=f"tag dry-run failed: {e}",
            fix_via="Run spirent_tool.py mark-dnos manually",
            auto_fixable=True,
        ))

    return results


# ---------------------------------------------------------------------------
# MCP-driven DNAAS teach_plan check (writes active_test_session.expected_traffic)
# ---------------------------------------------------------------------------
# Recipe contract (basic_learning/recipe.json line 28):
#   {"id": "spirent_ac_teach_plan",
#    "check": "mcp_dnaas_teach_plan",
#    "fix_via_mcp": {"tool": "dnos_dnaas_teach_plan",
#                    "args": {"vlan": "{_si_outer_vlan}",
#                             "dut": "{device}",
#                             "test_mac": "{test_mac}"}},
#    "pass_when": "frame_recipe.recipe_blockers == []",
#    "feeds": "active_test_session.expected_traffic"}
#
# Until 2026-05-01 the engine had NO handler for `mcp_dnaas_teach_plan`, so
# the prereq was a silent no-op and the SC02 runner re-invented Spirent
# encapsulation flags by hand -- causing VLAN-tagged frames to be sent to a
# port-mode AC. This check fixes that by:
#   1. Calling dnos_dnaas_teach_plan via the in-process MCP handle_tool_call
#   2. Failing the prereq if frame_recipe.recipe_blockers is non-empty
#   3. Writing frame_recipe + dut_target into active_test_session.expected_traffic
#      so downstream stream creation can consume the canonical recipe instead
#      of inventing its own VLAN math.

import json as _json_mcp_dnaas
import sys as _sys_mcp_dnaas
import urllib.request as _urlreq_mcp_dnaas

_DNOS_CONFIG_MCP_HEALTH = "http://localhost:9300/health"
_DNOS_CONFIG_MCP_PATH = "/home/dn/dnos_config_mcp"


def _probe_dnos_config_mcp():
    """Return dnos-config MCP handle_tool_call when the local service is healthy.

    Mirrors the probe pattern in shared/test_description_tagger.py and
    shared/device_runner.py. Returns None on any failure so callers can
    degrade gracefully (the prereq becomes WARN with a clear reason).
    """
    try:
        with _urlreq_mcp_dnaas.urlopen(_DNOS_CONFIG_MCP_HEALTH, timeout=2) as resp:
            if resp.status != 200:
                return None
    except Exception:
        return None

    if _DNOS_CONFIG_MCP_PATH not in _sys_mcp_dnaas.path:
        _sys_mcp_dnaas.path.insert(0, _DNOS_CONFIG_MCP_PATH)
    try:
        from dnos_config_mcp.tools import handle_tool_call
    except Exception:
        return None
    return handle_tool_call


def _pick_teach_plan_vlan(
    ctx: Dict[str, Any],
    recipe: Optional[Dict[str, Any]],
) -> Optional[int]:
    """Resolve the transport VLAN to teach against.

    Preference order (first hit wins):
      1. ctx['_si_outer_vlan'] / ctx['si_outer_vlan'] -- runtime-resolved
      2. ctx['spirent_fabric_vlan'] -- legacy device_discovery hint
      3. First outer VLAN found on a discovered SI AC (ctx['si_acs'])
    Returns None if nothing resolves -- caller should mark WARN, not FAIL,
    because the recipe's _si_outer_vlan placeholder may be expanded later.
    """
    for key in ("_si_outer_vlan", "si_outer_vlan"):
        v = ctx.get(key)
        if v:
            try:
                return int(v)
            except (TypeError, ValueError):
                pass
    v = ctx.get("spirent_fabric_vlan")
    if v:
        try:
            return int(v)
        except (TypeError, ValueError):
            pass
    for ac in ctx.get("si_acs") or []:
        outer = ac.get("outer_vlan") if isinstance(ac, dict) else None
        if outer:
            try:
                return int(outer)
            except (TypeError, ValueError):
                pass
    return None


def _pick_teach_plan_test_mac(
    ctx: Dict[str, Any],
    recipe: Optional[Dict[str, Any]],
) -> str:
    """Resolve a deterministic test MAC for teach_plan.

    teach_plan uses test_mac to stamp ownership_tag-bearing src MAC into
    the frame_recipe. We prefer the recipe's first scenario test_mac_override
    so the prereq stamp matches what SC01 will eventually inject. Fallback:
    the suite-wide deterministic MAC.
    """
    if recipe:
        for sc in recipe.get("scenarios") or []:
            override = sc.get("test_mac_override")
            if override:
                return str(override).lower()
    return "00:de:ad:be:ef:01"


def _write_expected_traffic(
    device: str,
    test_id: str,
    teach_plan: Dict[str, Any],
    *,
    feed_key: Optional[str] = None,
) -> bool:
    """Merge teach_plan output into ~/SCALER/TEST/active_test_session.json
    under the `expected_traffic` key. Best-effort: returns True on success,
    False on any I/O failure. A failure here does NOT fail the prereq; the
    teach_plan is still useful in the report rows.
    """
    try:
        from orchestration.session_io import write_active_session
        from orchestration.constants import ACTIVE_SESSION
    except Exception:
        return False

    existing: Dict[str, Any] = {}
    try:
        if ACTIVE_SESSION.exists():
            existing = _json_mcp_dnaas.loads(ACTIVE_SESSION.read_text())
    except Exception:
        existing = {}

    fr = teach_plan.get("frame_recipe") or {}
    dt = teach_plan.get("dut_target") or {}
    expected = {
        "source": "dnos_dnaas_teach_plan",
        "vlan": dt.get("fabric_vlan"),
        "dut": dt.get("device_short") or device,
        "frame_recipe": {
            "encapsulation": fr.get("encapsulation"),
            "outer_vlan": fr.get("outer_vlan"),
            "inner_vlan": fr.get("inner_vlan"),
            "src_mac": fr.get("src_mac"),
            "dst_mac": fr.get("dst_mac"),
            "frame_size_bytes": fr.get("frame_size_bytes"),
            "rate_mbps": fr.get("rate_mbps"),
            "min_rx_packet_delta": fr.get("min_rx_packet_delta"),
            "ownership_tag": fr.get("ownership_tag"),
            "spirent_flags": fr.get("spirent_flags") or [],
            "vlan_manipulation_hint": fr.get("vlan_manipulation_hint"),
            "recipe_blockers": fr.get("recipe_blockers") or [],
        },
        "dut_target": {
            "device": dt.get("device"),
            "ac_interface": dt.get("ac_interface"),
            "ac_physical": dt.get("ac_physical"),
            "expected_bd": dt.get("expected_bd"),
            "ac_admin_state": dt.get("ac_admin_state"),
            "ac_oper_state": dt.get("ac_oper_state"),
        },
        "ownership_tag": fr.get("ownership_tag"),
        "test_id": test_id,
    }
    if feed_key:
        current = existing.get("expected_traffic")
        if not isinstance(current, dict) or isinstance(current.get("frame_recipe"), dict):
            current = {}
        current[feed_key] = expected
        existing["expected_traffic"] = current
    else:
        existing["expected_traffic"] = expected
    existing.setdefault("test_id", test_id)
    existing.setdefault("device", device)
    try:
        write_active_session(existing)
        return True
    except Exception:
        return False


def _check_mcp_dnaas_teach_plan(
    ctx: Dict[str, Any],
    device: str,
    recipe: Optional[Dict[str, Any]],
    test_id: str,
) -> PrereqResult:
    """Run dnos_dnaas_teach_plan and gate on frame_recipe.recipe_blockers.

    PASS  -> recipe_blockers == [] AND active_test_session was updated
    FAIL  -> recipe_blockers non-empty (real DNAAS/AC misconfiguration)
    WARN  -> MCP unreachable, no VLAN resolved, or response malformed
             (we don't want to block tests when the MCP itself is down --
              downstream code can still proceed, just without the
              authoritative frame_recipe)
    """
    teach_prereqs = [
        p for p in ((recipe or {}).get("prerequisites") or [])
        if p.get("check") == "mcp_dnaas_teach_plan"
    ]
    if not teach_prereqs:
        # Recipe doesn't ask for this check -- skip silently.
        return PrereqResult(
            check_id="mcp_dnaas_teach_plan",
            status="SKIP",
            detail="recipe does not declare mcp_dnaas_teach_plan",
            fix_via="-",
            auto_fixable=False,
        )

    handle_tool_call = _probe_dnos_config_mcp()
    if handle_tool_call is None:
        return PrereqResult(
            check_id="mcp_dnaas_teach_plan",
            status="WARN",
            detail="dnos-config MCP not reachable on localhost:9300; "
                   "downstream stream creation will fall back to recipe defaults",
            fix_via="systemctl --user start dnos-config-mcp; curl http://localhost:9300/health",
            auto_fixable=False,
        )

    def _feed_key(prereq: Dict[str, Any]) -> Optional[str]:
        feeds = str(prereq.get("feeds") or "")
        marker = "expected_traffic."
        if marker in feeds:
            tail = feeds.split(marker, 1)[1].strip()
            return tail or None
        return None

    def _source_mac_for_feed(feed_key: Optional[str]) -> str:
        if feed_key and recipe:
            src = ((recipe.get("expected_traffic") or {}).get(feed_key) or {}).get("src_mac_base")
            if src:
                return str(src).lower()
        return _pick_teach_plan_test_mac(ctx, recipe)

    def _expand_arg(value: Any, feed_key: Optional[str]) -> Any:
        if value == "{test_mac}":
            return _source_mac_for_feed(feed_key)
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            key = value[1:-1]
            if key in ctx:
                return ctx[key]
        return value

    summaries: List[str] = []
    failures: List[str] = []
    warnings: List[str] = []
    wrote_any = False

    for prereq in teach_prereqs:
        feed_key = _feed_key(prereq)
        mcp_args = (((prereq.get("fix_via_mcp") or {}).get("args")) or {}).copy()
        args = {k: _expand_arg(v, feed_key) for k, v in mcp_args.items()}
        if "vlan" not in args:
            vlan = _pick_teach_plan_vlan(ctx, recipe)
            if vlan is None:
                warnings.append(f"{feed_key or 'default'}: no vlan resolved")
                continue
            args["vlan"] = vlan
        if "dut" not in args:
            args["dut"] = device
        args.setdefault("test_mac", _source_mac_for_feed(feed_key))
        args.setdefault("refresh", False)

        try:
            result = handle_tool_call("dnos_dnaas_teach_plan", args)
        except Exception as exc:
            warnings.append(
                f"{feed_key or args.get('dut', device)}: call raised "
                f"{type(exc).__name__}: {str(exc)[:120]}"
            )
            continue

        if not isinstance(result, dict):
            warnings.append(
                f"{feed_key or args.get('dut', device)}: non-dict response {type(result).__name__}"
            )
            continue

        fr = result.get("frame_recipe") or {}
        blockers = fr.get("recipe_blockers") or []
        if _write_expected_traffic(device, test_id, result, feed_key=feed_key):
            wrote_any = True

        label = feed_key or str(args.get("dut", device))
        if blockers:
            codes = ", ".join(b.get("code", "?") for b in blockers if isinstance(b, dict))
            first_why = next(
                (b.get("why", "") for b in blockers if isinstance(b, dict) and b.get("why")),
                "",
            )
            failures.append(f"{label}: blockers=[{codes}] {first_why[:140]}")
            continue

        pass_when = str(prereq.get("pass_when") or "").strip()
        if pass_when:
            # Minimal safe evaluator for the recipe contract strings used by
            # mcp_dnaas_teach_plan prerequisites. Do not use eval here.
            if "frame_recipe.recipe_blockers == []" in pass_when and blockers:
                failures.append(f"{label}: pass_when failed -- recipe_blockers not empty")
                continue
            import re as _re_pass_when
            encap_match = _re_pass_when.search(
                r"frame_recipe\.encapsulation\s*==\s*['\"]([^'\"]+)['\"]",
                pass_when,
            )
            if encap_match:
                expected_encap = encap_match.group(1)
                observed_encap = fr.get("encapsulation")
                if observed_encap != expected_encap:
                    failures.append(
                        f"{label}: pass_when failed -- expected encap={expected_encap}, "
                        f"observed encap={observed_encap}"
                    )
                    continue

        dt = result.get("dut_target") or {}
        parts = [
            f"{label}",
            f"vlan={args.get('vlan')}",
            f"dut={result.get('dut', args.get('dut'))}",
            f"encap={fr.get('encapsulation') or 'unknown'}",
        ]
        if fr.get("outer_vlan") is not None:
            parts.append(f"outer={fr.get('outer_vlan')}")
        if fr.get("inner_vlan") is not None:
            parts.append(f"inner={fr.get('inner_vlan')}")
        if dt.get("ac_interface"):
            parts.append(f"ac={dt.get('ac_interface')}")
        summaries.append(" ".join(parts))

    if failures:
        return PrereqResult(
            check_id="mcp_dnaas_teach_plan",
            status="FAIL",
            detail="; ".join(failures),
            fix_via="dnos_dnaas_diagnose / dnos_dnaas_stabilize_plan or fix DUT AC config",
            auto_fixable=False,
            spirent_action="mcp_dnaas_blocker",
        )
    if not summaries:
        return PrereqResult(
            check_id="mcp_dnaas_teach_plan",
            status="WARN",
            detail="; ".join(warnings) or "no teach_plan prerequisites were executable",
            fix_via="check dnos-config MCP version / recipe fix_via_mcp args",
            auto_fixable=False,
        )

    suffix = "expected_traffic=written" if wrote_any else "expected_traffic=write-failed(non-fatal)"
    if warnings:
        suffix += "; warnings=" + " | ".join(warnings[:2])
    return PrereqResult(
        check_id="mcp_dnaas_teach_plan",
        status="PASS" if not warnings else "WARN",
        detail="; ".join(summaries + [suffix]),
        fix_via="-",
        auto_fixable=False,
    )


# ---------------------------------------------------------------------------
# B6: Live device verification layer
# ---------------------------------------------------------------------------
# The static checks above evaluate a stale ctx snapshot. When called with
# run_show available, this layer queries the device and overrides FAIL/WARN
# with the actual current state. This is what was missing -- the engine
# would happily report PASS based on a 5-minute-old ctx while the device
# was in a totally different state.
#
# Each verifier is best-effort: any exception during the live query keeps
# the original (ctx-based) result so the engine still produces output.

import re as _re_b6


# ---------------------------------------------------------------------------
# Description-driven BGP neighbor discovery
# ---------------------------------------------------------------------------
# Legacy lab peers (e.g. 2.2.2.2 pointing at a non-existent PE) hang in the
# "Connect"/"Active" state forever and poison static health gates. The DUT
# configuration already encodes which peers belong to a given test via
# description tags (SPIRENT:..., TEST:..., HA:...). This helper parses those
# tags so the live gates count ONLY test-relevant peers as required, and
# treat untagged stale neighbors as "out of scope".

def _discover_bgp_asn(device: str, run_show: RunShowFn) -> Optional[str]:
    try:
        out = run_show(device, "show bgp summary | no-more")
        m = _re_b6.search(r"local AS number\s+(\d+)", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _load_bgp_neighbor_map(
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Return { neighbor_ip: {description, afis, description_owner} }.

    description_owner is one of: SPIRENT, TEST, HA, USER, "" (untagged).
    """
    neighbors: Dict[str, Dict[str, Any]] = {}
    asn = ctx.get("bgp_asn") or _discover_bgp_asn(device, run_show)
    if not asn:
        return neighbors
    ctx["bgp_asn"] = asn
    try:
        cfg = run_show(device, f"show config protocols bgp {asn} | no-more")
    except Exception:
        return neighbors
    current: Optional[str] = None
    for raw in cfg.splitlines():
        line = raw.strip()
        m = _re_b6.match(r"neighbor\s+(\d+\.\d+\.\d+\.\d+)\s*$", line)
        if m:
            current = m.group(1)
            neighbors[current] = {
                "description": "",
                "afis": set(),
                "description_owner": "",
            }
            continue
        if current is None:
            continue
        m = _re_b6.match(r"description\s+(.+)$", line)
        if m:
            desc = m.group(1).strip()
            neighbors[current]["description"] = desc
            owner = ""
            up = desc.upper()
            for tag in ("SPIRENT:", "TEST:", "HA:", "USER:"):
                if up.startswith(tag) or f" {tag}" in f" {up}":
                    owner = tag.rstrip(":")
                    break
            neighbors[current]["description_owner"] = owner
            continue
        m = _re_b6.match(r"address-family\s+(\S+)", line)
        if m:
            neighbors[current]["afis"].add(m.group(1).lower())
            continue
        if line == "!":
            # end of current neighbor block only when indent returns to root
            # (cheap heuristic: a plain '!' on its own line). Keep current so
            # nested address-family blocks still attribute correctly.
            pass
    return neighbors


def _live_verify_evpn_instance(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
) -> PrereqResult:
    name = ctx.get("evpn_name_primary") or ""
    if not name:
        return result
    try:
        out = run_show(device, f"show evpn instance {name} | no-more")
        if name in out and "no such" not in out.lower():
            result.status = "PASS"
            result.detail = f"{name} present (live)"
        else:
            result.status = "FAIL"
            result.detail = f"{name} NOT present on device (live)"
    except Exception:
        pass
    return result


def _live_verify_bgp_evpn(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
) -> PrereqResult:
    """Dynamic BGP-EVPN health gate.

    Filters peers by DUT description tag (SPIRENT:/TEST:/HA:). Untagged
    legacy stubs like 2.2.2.2 that never come up are excluded from the
    required count. A test PASSes when at least one test-relevant peer
    is Established, or when no tagged peers exist but some legacy peer
    happens to be up (fallback for pre-tagged labs).
    """
    try:
        # 1) BGP EVPN summary -> per-peer state
        #    DNOS summary columns: Neighbor V AS MsgRcvd MsgSent InQ OutQ AdjOut Up/Down State/PfxAccepted
        #    State column: "Connect" / "Active" / "Established" / numeric pfx count when established.
        #    We detect by splitting on whitespace and inspecting tokens -- robust against column spacing.
        out = run_show(device, "show bgp l2vpn evpn summary | no-more")
        peer_state: Dict[str, str] = {}
        for line in out.splitlines():
            toks = line.split()
            if len(toks) < 10:
                continue
            if not _re_b6.match(r"^\d+\.\d+\.\d+\.\d+$", toks[0]):
                continue
            # Up/Down is 9th token (index 8), State is last
            peer_state[toks[0]] = toks[-1]

        # 2) Description-based classification from BGP config
        neighbors = _load_bgp_neighbor_map(device, run_show, ctx)

        relevant_total = 0
        relevant_est = 0
        legacy_total = 0
        legacy_est = 0
        tagged_peers: List[str] = []
        for peer, state in peer_state.items():
            nb = neighbors.get(peer, {})
            owner = nb.get("description_owner", "")
            is_est = (state.isdigit() and int(state) >= 0) or state == "Established"
            if owner in ("SPIRENT", "TEST", "HA"):
                relevant_total += 1
                if is_est:
                    relevant_est += 1
                tagged_peers.append(f"{peer}[{owner}]")
            else:
                legacy_total += 1
                if is_est:
                    legacy_est += 1

        if relevant_total > 0:
            if relevant_est > 0:
                result.status = "PASS"
                result.detail = (
                    f"{relevant_est}/{relevant_total} test-relevant peers Established "
                    f"({', '.join(tagged_peers)}); "
                    f"ignoring {legacy_total} untagged legacy peer(s)"
                )
            else:
                result.status = "FAIL"
                result.detail = (
                    f"0/{relevant_total} test-relevant peers Established "
                    f"({', '.join(tagged_peers)}); "
                    f"{legacy_est}/{legacy_total} untagged peers up"
                )
        else:
            if legacy_est > 0:
                result.status = "PASS"
                result.detail = (
                    f"no SPIRENT/TEST-tagged peers; "
                    f"{legacy_est}/{legacy_total} untagged peers Established (fallback)"
                )
            elif legacy_total > 0:
                result.status = "WARN"
                result.detail = (
                    f"no tagged peers; {legacy_total} untagged peers, 0 Established "
                    f"(lab stubs - not required for test)"
                )
            else:
                result.status = "WARN"
                result.detail = "no BGP L2VPN EVPN neighbors configured"
    except Exception as exc:
        result.detail = f"live check failed: {exc}"
    return result


def _live_verify_seamless_integration(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
) -> PrereqResult:
    name = ctx.get("evpn_name_primary") or ""
    if not name:
        return result
    try:
        out = run_show(device, f"show config network-services evpn instance {name} | flatten | no-more")
        if "seamless-integration" in out:
            result.status = "PASS"
            result.detail = "seamless-integration present (live)"
        else:
            result.status = "FAIL"
            result.detail = "seamless-integration NOT in instance config (live)"
    except Exception:
        pass
    return result


def _live_verify_mac_table(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
) -> PrereqResult:
    try:
        out = run_show(device, "show evpn mac-table | no-more")
        count = sum(1 for line in out.splitlines() if _re_b6.search(r"\b[\da-f]{2}(:[\da-f]{2}){5}\b", line, _re_b6.I))
        result.detail = f"count={count} (live)"
        result.status = "PASS" if count > 0 else "FAIL"
    except Exception:
        pass
    return result


def _live_verify_two_acs(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
    test_id: str,
) -> PrereqResult:
    needs = "ac_ac" in test_id or "SW205161" in test_id
    name = ctx.get("evpn_name_primary") or ""
    if not name:
        return result
    try:
        out = run_show(device, f"show config network-services evpn instance {name} | flatten | no-more")
        ac_count = len(_re_b6.findall(r"\binterface\s+[\w/.-]+", out))
        result.detail = f"AC interfaces (live): {ac_count}"
        if ac_count >= 2:
            result.status = "PASS"
        elif needs:
            result.status = "FAIL"
        else:
            result.status = "WARN"
    except Exception:
        pass
    return result


def _live_verify_pseudowire(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
    test_id: str,
) -> PrereqResult:
    needs = any(x in test_id for x in ("pw_pw", "ac_pw", "evpn_pw", "SW205162", "SW205198", "SW205199"))
    if not needs:
        return result
    try:
        out = run_show(device, "show evpn vpls-pw | no-more")
        installed = "Installed" in out
        result.detail = "VPLS PW Installed (live)" if installed else "No Installed VPLS PW (live)"
        result.status = "PASS" if installed else "FAIL"
    except Exception:
        pass
    return result


def _live_verify_multihoming(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
    test_id: str,
) -> PrereqResult:
    needs = "mh" in test_id or "SW205195" in test_id
    if not needs:
        return result
    try:
        out = run_show(device, "show config network-services evpn ethernet-segment | no-more")
        has_es = bool(_re_b6.search(r"esi\s+\S+", out))
        result.detail = "ESI configured (live)" if has_es else "No ethernet-segment ESI (live)"
        result.status = "PASS" if has_es else "FAIL"
    except Exception:
        pass
    return result


def _live_verify_dnaas_path(
    result: PrereqResult,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
) -> PrereqResult:
    """L2 endpoint readiness gate.

    A PE can be a valid L2 endpoint via either:
      (a) network-services bridge-domain instance ... (classic BD), OR
      (b) network-services evpn instance ... seamless-integration
          (SI-EVPN on NCR PEs -- no BD required on this side).
    """
    try:
        bd_out = run_show(device, "show config network-services bridge-domain | flatten | no-more")
        bd_count = len(_re_b6.findall(r"bridge-domain\s+instance\s+\S+", bd_out))
    except Exception:
        bd_count = 0
    si_present = False
    try:
        evpn_out = run_show(device, "show config network-services evpn | flatten | no-more")
        si_present = "seamless-integration" in evpn_out
    except Exception:
        pass
    if bd_count > 0:
        result.status = "PASS"
        result.detail = f"{bd_count} bridge-domain(s) present (live)"
    elif si_present:
        result.status = "PASS"
        result.detail = "seamless-integration EVPN endpoint (no BD required on PE)"
    else:
        result.status = "WARN"
        result.detail = "No bridge-domain or seamless-integration endpoint detected"
    return result


def _run_live_verifications(
    report: PrereqReport,
    device: str,
    run_show: RunShowFn,
    ctx: Dict[str, Any],
    test_id: str,
) -> None:
    """Override each static check with live device evidence."""
    by_id = {r.check_id: r for r in report.results}
    if "evpn_instance" in by_id:
        _live_verify_evpn_instance(by_id["evpn_instance"], device, run_show, ctx)
    if "bgp_l2vpn_evpn" in by_id:
        _live_verify_bgp_evpn(by_id["bgp_l2vpn_evpn"], device, run_show, ctx)
    if "seamless_integration" in by_id:
        _live_verify_seamless_integration(by_id["seamless_integration"], device, run_show, ctx)
    if "mac_table_populated" in by_id:
        _live_verify_mac_table(by_id["mac_table_populated"], device, run_show, ctx)
    if "two_acs" in by_id:
        _live_verify_two_acs(by_id["two_acs"], device, run_show, ctx, test_id)
    if "pseudowire" in by_id:
        _live_verify_pseudowire(by_id["pseudowire"], device, run_show, ctx, test_id)
    if "multihoming_esi" in by_id:
        _live_verify_multihoming(by_id["multihoming_esi"], device, run_show, ctx, test_id)
    if "dnaas_path" in by_id:
        _live_verify_dnaas_path(by_id["dnaas_path"], device, run_show, ctx)


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def check_prerequisites(
    device: str,
    ctx: Dict[str, Any],
    test_id: str,
    run_show: RunShowFn | None = None,
    recipe: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Return structured prerequisite report.

    Backward-compatible: returns dict with 'rows' key matching old format,
    plus enriched 'report' key with PrereqReport.
    """
    # Tag the per-run transcript so prerequisite show commands are grouped
    # under "prerequisite_gate" in EXECUTION_LOG.md.
    try:
        from shared.run_transcript import set_context as _xset
        _xset(phase="prerequisite_gate", scenario=None, role="DUT")
    except Exception:
        pass

    report = PrereqReport(test_id=test_id, device=device)

    report.results.append(_check_evpn_instance(ctx))
    report.results.append(_check_bgp_evpn(ctx))
    report.results.append(_check_seamless_integration(ctx))
    # New 2026-04-30: prove the EVI carries the RT pairs the recipe needs.
    # Driven by recipe["service_capabilities"]; legacy recipes auto-skip.
    report.results.append(
        _check_evpn_si_rt_complete(ctx, device, recipe, run_show)
    )
    report.results.append(_check_mac_table(ctx))
    report.results.append(_check_two_acs(ctx, test_id))
    report.results.append(_check_pseudowire(ctx, test_id))
    report.results.append(_check_multihoming(ctx, test_id))
    report.results.append(_check_cluster(ctx, test_id))
    report.results.append(_check_spirent_session(ctx))
    report.results.append(_check_dnaas_path(ctx, device, run_show))

    # Per user mandate: /TEST must call /SPIRENT for every test that needs
    # devices. Two live checks below delegate to spirent_sync.py:
    #   * spirent_fabric_v<vlan>: dnaas-diagnose on the transport VLAN,
    #     auto-fix sticky faults (LLP shutdown, oper-down) via dnaas-fix.
    #   * spirent_desc_tags: ensure SPIRENT:... descriptions are pushed on
    #     DUT sub-ifs + BGP neighbors (show config | include SPIRENT).
    for check in _check_spirent_sync_live(ctx, device, test_id):
        report.results.append(check)

    # MCP-driven DNAAS teach_plan: writes active_test_session.expected_traffic
    # so downstream stream creation consumes the canonical frame_recipe instead
    # of inventing its own VLAN/encapsulation math. Only runs when the recipe
    # explicitly declares the `mcp_dnaas_teach_plan` prerequisite.
    report.results.append(
        _check_mcp_dnaas_teach_plan(ctx, device, recipe, test_id)
    )

    # B6: override each static check with live device evidence so the engine
    # reflects the actual current state, not a possibly stale ctx snapshot.
    if run_show is not None:
        try:
            _run_live_verifications(report, device, run_show, ctx, test_id)
        except Exception as exc:
            print(f"[WARN] prerequisite_engine live verification failed: {exc}", flush=True)

    report.compute_overall()
    report.config_delta = plan_config_delta(ctx)

    rows = [
        {
            "check": r.check_id,
            "status": r.status,
            "detail": r.detail,
            "fix_via": r.fix_via,
            "auto_fixable": r.auto_fixable,
            "spirent_action": r.spirent_action,
        }
        for r in report.results
    ]

    # Attach the full evpn_service_decision struct (including fix_snippet)
    # to its row so the orchestrator can render REUSE/EXTEND/CREATE without
    # parsing the human-readable detail string.
    for row in rows:
        if row["check"] == "evpn_si_rt_complete":
            decision = ctx.get("evpn_service_decision")
            if decision:
                row["service_decision"] = decision
                row["service_inventory"] = ctx.get("evpn_service_inventory") or {}
            break

    # Deep config gap analysis via config_knowledge module.
    # Uses the actual SW-203654 CLI hierarchy to detect missing config blocks
    # and generate ready-to-paste DNOS snippets.
    config_gap_report: Dict[str, Any] = {}
    if run_show:
        try:
            config_gap_report = run_config_gap_analysis(
                run_show, device, test_id,
                evpn_name=ctx.get("evpn_name_primary"),
            )
            for gap in config_gap_report.get("gaps", []):
                snippet = config_gap_report["snippets"].get(gap.requirement_id, "")
                rows.append({
                    "check": f"config:{gap.requirement_id}",
                    "status": "FAIL",
                    "detail": gap.detail,
                    "fix_via": f"Config snippet available ({len(snippet)} chars)",
                    "auto_fixable": gap.requirement.auto_fixable,
                    "spirent_action": None,
                    "fix_snippet": snippet,
                })
            if config_gap_report.get("gaps"):
                report.overall = "FAIL"
        except Exception as e:
            # Audit 2026-04: this handler used to be a silent `pass`, which
            # meant any crash inside run_config_gap_analysis() made the
            # prerequisite gate falsely report "no config gaps" and let the
            # test run with latent config drift.  Surface the failure as an
            # explicit row so the gate is forced into WARN instead of silent
            # PASS, and the user sees the real exception.
            import traceback
            tb_last = traceback.format_exc().strip().splitlines()[-1][:200]
            rows.append({
                "check": "config:gap_analysis_crash",
                "status": "WARN",
                "detail": f"config-gap analysis raised {type(e).__name__}: "
                          f"{str(e)[:200]} ({tb_last})",
                "fix_via": "Inspect run_config_gap_analysis() in "
                           "shared/config_knowledge.py",
                "auto_fixable": False,
                "spirent_action": None,
            })
            if report.overall == "PASS":
                report.overall = "WARN"
            print(f"[WARN] config_gap_analysis crashed on {device}: {e}",
                  flush=True)

    return {
        "test_id": test_id,
        "device": device,
        "rows": rows,
        "overall": report.overall,
        "config_delta": report.config_delta,
        "config_gaps": config_gap_report,
        "auto_fixable_items": [r.check_id for r in report.results if r.auto_fixable and r.status != "PASS"],
    }


def get_auto_fix_plan(prereq_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    From prerequisite check results, build a list of auto-fix actions.

    Each action is a dict with 'check_id', 'action_type', 'command_or_description'.
    The orchestrator or agent executes these.
    """
    fixes: List[Dict[str, str]] = []

    for row in prereq_result.get("rows", []):
        if row.get("status") == "PASS" or not row.get("auto_fixable"):
            continue

        check = row["check"]
        spirent = row.get("spirent_action")

        if check == "mac_table_populated" and spirent:
            fixes.append({
                "check_id": check,
                "action_type": "spirent",
                "description": "Create L2 device blocks on discovered ACs to populate MAC table",
                "spirent_command": (
                    "spirent_tool.py create-device --name mac_mob_test "
                    "--vlan {ac1_vlan} --mac 00:DE:AD:00:01:01 "
                    "--mac-step 00:00:00:00:00:01 --device-count 4 --no-qinq"
                ),
                "post_action": (
                    "spirent_tool.py create-stream --protocol l2 --vlan {ac1_vlan} "
                    "--src-mac 00:DE:AD:00:01:01 --dst-mac FF:FF:FF:FF:FF:FF "
                    "--rate-mbps 1 --frame-size 64 --name mac_learn --no-qinq"
                ),
            })

        elif check == "two_acs" and spirent:
            fixes.append({
                "check_id": check,
                "action_type": "spirent_dnaas",
                "description": "Create DNAAS BD path for second VLAN to enable AC<->AC tests",
                "spirent_command": "/SPIRENT dnaas fix -- allocate second VLAN from 210-219",
            })

        elif check == "dnaas_path" and spirent:
            fixes.append({
                "check_id": check,
                "action_type": "spirent_dnaas",
                "description": "Verify/create DNAAS bridge-domain path for L2 traffic",
                "spirent_command": "/SPIRENT dnaas -- check BD path status",
            })

        elif check.startswith("spirent_fabric_v") and spirent == "spirent_dnaas_fix":
            # Extract VLAN from check_id suffix
            try:
                vlan = int(check.split("_v")[-1])
            except Exception:
                vlan = 214
            fixes.append({
                "check_id": check,
                "action_type": "spirent_fabric_fix",
                "description": (
                    f"Fabric sticky faults detected on VLAN {vlan}. Apply "
                    f"delete-and-recreate recovery via dnaas-fix."
                ),
                "spirent_command": (
                    f"python3 ~/SCALER/SPIRENT/spirent_tool.py dnaas-fix --vlan {vlan}"
                ),
                "post_action": (
                    f"python3 ~/SCALER/SPIRENT/spirent_tool.py dnaas-diagnose --vlan {vlan}"
                ),
            })

        elif check == "spirent_desc_tags" and spirent == "spirent_mark_dnos":
            fixes.append({
                "check_id": check,
                "action_type": "spirent_mark_dnos",
                "description": (
                    "Push SPIRENT:<session>/<device> descriptions on DUT "
                    "sub-interfaces and BGP neighbors for fast debug."
                ),
                "spirent_command": (
                    f"python3 ~/SCALER/SPIRENT/spirent_tool.py mark-dnos "
                    f"--dut {{device_mgmt_ip}}"
                ),
            })

    return fixes


def format_prereq_table(result: Dict[str, Any]) -> str:
    lines = [
        f"## Prerequisite Check: {result.get('test_id')} on {result.get('device')}",
        "",
        "| Check | Status | Detail | Fix | Auto? |",
        "|-------|--------|--------|-----|-------|",
    ]
    for r in result.get("rows", []):
        auto = "[auto]" if r.get("auto_fixable") else ""
        lines.append(f"| {r['check']} | {r['status']} | {r['detail']} | {r['fix_via']} | {auto} |")
    lines.append("")
    lines.append(f"**Overall:** {result.get('overall')}")

    auto_fixable = result.get("auto_fixable_items", [])
    if auto_fixable:
        lines.append(f"\n**Auto-fixable items:** {', '.join(auto_fixable)}")
        lines.append("Run with `--auto-fix` to apply Spirent/DNAAS remediation automatically.")

    # Render the EVPN service decision (REUSE / EXTEND / CREATE) if present.
    for r in result.get("rows", []):
        if r.get("check") != "evpn_si_rt_complete":
            continue
        decision = r.get("service_decision") or {}
        action = decision.get("action")
        if not action or action == "NONE":
            break
        lines.append("")
        lines.append("## EVPN Service Selection")
        lines.append("")
        lines.append(f"**Decision:** {action}")
        if decision.get("instance_name"):
            lines.append(f"**Instance:** `{decision['instance_name']}`")
        if decision.get("reason"):
            lines.append(f"**Reason:** {decision['reason']}")
        missing = decision.get("missing_capabilities") or []
        if missing:
            lines.append(f"**Missing capabilities:** {', '.join(missing)}")
        inventory = r.get("service_inventory") or {}
        if inventory:
            lines.append("")
            lines.append("**Existing instances on DUT:**")
            lines.append("")
            lines.append("| Instance | Classification |")
            lines.append("|----------|----------------|")
            for inst, cls in sorted(inventory.items()):
                lines.append(f"| {inst} | {cls} |")
        snippet = decision.get("fix_snippet") or ""
        if snippet:
            lines.append("")
            lines.append("**Surgical fix snippet (review before commit):**")
            lines.append("```")
            lines.append(snippet)
            lines.append("```")
        break

    config_gaps = result.get("config_gaps", {})
    snippets = config_gaps.get("snippets", {})
    if snippets:
        lines.append("")
        lines.append(f"## Missing Config Blocks ({len(snippets)} gaps)")
        lines.append("")
        lines.append("Config snippets below are ready for copy-paste into `config` mode.")
        lines.append("Review and adjust values before committing.")
        for req_id, snippet in snippets.items():
            lines.append(f"\n### {req_id}")
            lines.append("```")
            lines.append(snippet)
            lines.append("```")

    return "\n".join(lines)
