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


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def check_prerequisites(
    device: str,
    ctx: Dict[str, Any],
    test_id: str,
    run_show: RunShowFn | None = None,
) -> Dict[str, Any]:
    """
    Return structured prerequisite report.

    Backward-compatible: returns dict with 'rows' key matching old format,
    plus enriched 'report' key with PrereqReport.
    """
    report = PrereqReport(test_id=test_id, device=device)

    report.results.append(_check_evpn_instance(ctx))
    report.results.append(_check_bgp_evpn(ctx))
    report.results.append(_check_seamless_integration(ctx))
    report.results.append(_check_mac_table(ctx))
    report.results.append(_check_two_acs(ctx, test_id))
    report.results.append(_check_pseudowire(ctx, test_id))
    report.results.append(_check_multihoming(ctx, test_id))
    report.results.append(_check_cluster(ctx, test_id))
    report.results.append(_check_spirent_session(ctx))
    report.results.append(_check_dnaas_path(ctx, device, run_show))

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
        except Exception:
            pass

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
