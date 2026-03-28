#!/usr/bin/env python3
"""
EVPN Seamless-Integration configuration knowledge base.

Authoritative source: Jira SW-203654 "QA | EVPN (ELAN) Seamless-integration | CLI"
and Confluence "EVPN (ELAN) Seamless integration with VPLS (BGP)".

This module:
  1. Defines the complete DNOS CLI hierarchy for EVPN SI
  2. Parses a device's running config to detect what's present vs missing
  3. Generates config snippets to fill gaps (propose-only, never auto-commits)

Usage:
    from shared.config_knowledge import (
        detect_config_gaps,
        generate_fix_snippets,
        EVPN_SI_CONFIG_TREE,
    )

    gaps = detect_config_gaps(running_config_text, test_id="ac_evpn")
    if gaps:
        snippets = generate_fix_snippets(gaps, evpn_name="EVPN1", ...)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# EVPN SI config tree definition (from SW-203654 + learned_rules.md)
# ---------------------------------------------------------------------------

@dataclass
class ConfigRequirement:
    """A configuration block that may be required for a test scenario."""
    path: str
    description: str
    required_for: List[str] = field(default_factory=list)
    detect_keyword: str = ""
    example_value: str = ""
    auto_fixable: bool = False


EVPN_SI_CONFIG_TREE: Dict[str, ConfigRequirement] = {
    # -- Core EVPN instance --
    "evpn_instance": ConfigRequirement(
        path="network-services evpn instance {evpn_name}",
        description="EVPN ELAN service instance",
        required_for=["all"],
        detect_keyword="evpn",
    ),
    "evpn_transport_mpls": ConfigRequirement(
        path="network-services evpn instance {evpn_name} transport-protocol mpls",
        description="MPLS transport for EVPN",
        required_for=["all"],
        detect_keyword="transport-protocol",
    ),
    "evpn_bgp_rt": ConfigRequirement(
        path="network-services evpn instance {evpn_name} protocols bgp {asn}",
        description="BGP protocol binding with RT import/export",
        required_for=["all"],
        detect_keyword="export-l2vpn-evpn route-target",
    ),
    "evpn_interface": ConfigRequirement(
        path="network-services evpn instance {evpn_name} interface {iface}",
        description="Attachment circuit (AC) interface under EVPN instance",
        required_for=["all"],
        detect_keyword="interface ",
    ),

    # -- Seamless Integration (SW-203654 CLI hierarchy) --
    "seamless_integration": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration",
        description="Enable VPLS seamless integration on EVPN instance",
        required_for=["ac_evpn", "ac_pw", "pw_pw", "evpn_pw", "ha_mac_mobility", "multihoming"],
        detect_keyword="seamless-integration",
        auto_fixable=True,
    ),
    "si_label_block_size": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration label-block-size {size}",
        description="VPLS label block size (2, 4, 8, or 16)",
        required_for=["ac_pw", "pw_pw", "evpn_pw"],
        detect_keyword="label-block-size",
        example_value="8",
    ),
    "si_source_if": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration source-if {loopback}",
        description="Source interface for VPLS tunnels (loopback)",
        required_for=["ac_pw", "pw_pw", "evpn_pw"],
        detect_keyword="source-if",
        example_value="lo0",
    ),
    "si_site_id": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration site-id {id}",
        description="VE-ID for this PE in the VPLS domain (1-65534, unique per service)",
        required_for=["ac_pw", "pw_pw", "evpn_pw", "multihoming"],
        detect_keyword="site-id",
        example_value="1",
    ),
    "si_site_interface": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration site-id {id} interface {iface}",
        description="AC interface assignment under site-id",
        required_for=["ac_pw", "pw_pw"],
        detect_keyword="site-id",
    ),
    "si_site_preference": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration site-id {id} site-preference {pref}",
        description="Site preference for DF election (1-65535, default 100)",
        required_for=["multihoming"],
        detect_keyword="site-preference",
        example_value="100",
    ),
    "si_bgp_rt": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration bgp",
        description="BGP RT import/export for VPLS auto-discovery",
        required_for=["ac_pw", "pw_pw", "evpn_pw"],
        detect_keyword="import-vpn route-target",
    ),
    "si_transport_cw": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration transport-protocol mpls control-word {state}",
        description="Control-word for VPLS pseudowires (enabled/disabled, default enabled)",
        required_for=["ac_pw", "pw_pw"],
        detect_keyword="control-word",
        example_value="enabled",
    ),

    # -- MAC handling (from learned_rules.md) --
    "mac_learning": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling mac-learning {state}",
        description="Enable/disable MAC learning on EVPN instance",
        required_for=["basic_learning"],
        detect_keyword="mac-learning",
        example_value="on",
    ),
    "mac_aging": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling mac-table-aging-time {sec}",
        description="MAC aging timer in seconds",
        required_for=["aging_timers"],
        detect_keyword="mac-table-aging-time",
        example_value="300",
        auto_fixable=True,
    ),
    "mac_limit": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling mac-table-limit {count}",
        description="Maximum MAC entries per instance",
        required_for=[],
        detect_keyword="mac-table-limit",
    ),
    "loop_prevention": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling loop-prevention admin-state enabled",
        description="Enable loop prevention for MAC mobility detection",
        required_for=["ac_ac", "withdraw_flush"],
        detect_keyword="loop-prevention",
        auto_fixable=True,
    ),
    "loop_prevention_action": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling loop-prevention action {action}",
        description="Loop prevention action (e.g., suppress-and-notify)",
        required_for=["ac_ac"],
        detect_keyword="loop-prevention",
    ),
    "loop_prevention_threshold": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling loop-prevention loop-detection-threshold {n}",
        description="Number of moves before loop is declared",
        required_for=["ac_ac"],
        detect_keyword="loop-detection-threshold",
    ),
    "loop_prevention_window": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling loop-prevention loop-detection-window {sec}",
        description="Time window for counting MAC moves",
        required_for=["ac_ac"],
        detect_keyword="loop-detection-window",
    ),
    "local_loop_prevention": ConfigRequirement(
        path="network-services evpn instance {evpn_name} mac-handling loop-prevention local-loop-prevention admin-state enabled",
        description="Local loop prevention (per-AC)",
        required_for=["ac_ac"],
        detect_keyword="local-loop-prevention",
        auto_fixable=True,
    ),
    "sticky_mac": ConfigRequirement(
        path="network-services evpn instance {evpn_name} interface {iface} sticky-interface enabled",
        description="Interface-level sticky: all MACs learned on this AC are sticky (Confluence: sticky-interface enabled). Per-MAC sticky uses sticky-mac <mac-address> under the same interface subtree, not enabled/disabled.",
        required_for=["sticky"],
        detect_keyword="sticky-interface",
        auto_fixable=True,
    ),

    # -- Bridge domain --
    "bridge_domain": ConfigRequirement(
        path="network-services bridge-domain instance {bd_name}",
        description="Bridge domain instance (required for DNAAS/Spirent path)",
        required_for=["spirent_traffic"],
        detect_keyword="bridge-domain",
    ),
    "bd_mac_aging": ConfigRequirement(
        path="network-services bridge-domain instance {bd_name} mac-handling mac-table-aging-time {sec}",
        description="Bridge domain MAC aging timer",
        required_for=["aging_timers"],
        detect_keyword="mac-table-aging-time",
    ),

    # -- Multihoming --
    "multihoming_global": ConfigRequirement(
        path="network-services multihoming",
        description="Global multihoming configuration",
        required_for=["multihoming"],
        detect_keyword="multihoming",
    ),
    "multihoming_esi": ConfigRequirement(
        path="network-services multihoming ethernet-segment {es_name} identifier {esi}",
        description="Ethernet Segment Identifier for multihoming",
        required_for=["multihoming"],
        detect_keyword="ethernet-segment",
    ),

    # -- VPLS-specific SI config (from Confluence design doc + SW-178648 EPIC) --
    # The dual-protocol service serves both EVPN and VPLS in a single instance.
    # Remote PE selection: if PE sent any EVPN type-1/2/3 -> EVPN mode, else -> VPLS PW.
    "si_l2_mtu": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration l2-mtu {mtu}",
        description="L2 MTU for VPLS pseudowires (must match remote PE)",
        required_for=["ac_pw", "pw_pw", "evpn_pw"],
        detect_keyword="l2-mtu",
        example_value="9100",
    ),
    "si_vpls_counters": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration vpls-counters {remote_ips}",
        description="VPLS per-PW counters (comma-separated remote PE IPs)",
        required_for=[],
        detect_keyword="vpls-counters",
    ),
    "si_transport_fat_label": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration transport-protocol mpls fat-label {mode}",
        description="FAT label for VPLS PWs (enabled/disabled/received-only/send-only)",
        required_for=[],
        detect_keyword="fat-label",
        example_value="disabled",
    ),
    "si_site_multihoming": ConfigRequirement(
        path="network-services evpn instance {evpn_name} seamless-integration site-id {id} multihoming",
        description="Mark site-id as multi-homed (for VPLS MH DF election)",
        required_for=["multihoming"],
        detect_keyword="multihoming",
    ),
    "label_pool": ConfigRequirement(
        path="system label-pool vpls-pool range {start} {end}",
        description="Dedicated MPLS label pool for VPLS (required before SI can allocate blocks)",
        required_for=["ac_pw", "pw_pw", "evpn_pw"],
        detect_keyword="label-pool",
    ),

    # -- BGP address-families --
    "bgp_l2vpn_evpn_af": ConfigRequirement(
        path="protocols bgp {asn} address-family l2vpn-evpn",
        description="BGP L2VPN EVPN address-family (required for EVPN peering)",
        required_for=["all"],
        detect_keyword="l2vpn-evpn",
    ),
    "bgp_l2vpn_vpls_af": ConfigRequirement(
        path="protocols bgp {asn} address-family l2vpn-vpls",
        description="BGP L2VPN VPLS address-family (required for VPLS auto-discovery via BGP)",
        required_for=["ac_pw", "pw_pw", "evpn_pw"],
        detect_keyword="l2vpn-vpls",
    ),
    "bgp_neighbor_group": ConfigRequirement(
        path="protocols bgp {asn} neighbor-group {group} address-family l2vpn-evpn",
        description="Neighbor-group with L2VPN EVPN AF for route exchange",
        required_for=["all"],
        detect_keyword="neighbor-group",
    ),

    # -- Second AC (for AC<->AC tests) --
    "second_ac": ConfigRequirement(
        path="network-services evpn instance {evpn_name} interface {iface2}",
        description="Second AC interface for local MAC mobility tests",
        required_for=["ac_ac"],
        detect_keyword="interface ",
    ),
}


# ---------------------------------------------------------------------------
# VPLS-specific verification show commands (from Confluence design doc)
# Agents use these during test verification phases.
# ---------------------------------------------------------------------------

VPLS_SHOW_COMMANDS: Dict[str, Dict[str, str]] = {
    "vpls_pw_status": {
        "command": "show evpn vpls-pw instance {evpn_name}",
        "description": "VPLS pseudowire status (up/down, egress/ingress labels, remote PE)",
        "required_for": "ac_pw,pw_pw,evpn_pw",
    },
    "evpn_instance_detail": {
        "command": "show evpn instance {evpn_name} detail",
        "description": "Service detail including migration phase (EVPN+VPLS), DF info",
        "required_for": "all",
    },
    "bgp_evpn_vpls_routes": {
        "command": "show bgp instance evpn instance {evpn_name} vpls",
        "description": "Filter only VPLS (VSI safi) routes for this service",
        "required_for": "ac_pw,pw_pw,evpn_pw",
    },
    "bgp_evpn_all_routes": {
        "command": "show bgp instance evpn instance {evpn_name}",
        "description": "All routes (EVPN + VPLS) for this service",
        "required_for": "ac_pw,pw_pw,evpn_pw",
    },
    "evpn_mac_table_detail": {
        "command": "show evpn mac-table instance {evpn_name} detail",
        "description": "MAC table with PW-learned MACs (VPLS_PW flag), nexthop type",
        "required_for": "all",
    },
    "evpn_summary": {
        "command": "show evpn summary",
        "description": "Global counters: total VPLS MACs, VPLS neighbors, PW count",
        "required_for": "all",
    },
    "loop_prevention_evpn_mac": {
        "command": "show loop-prevention evpn mac instance {evpn_name}",
        "description": "Loop prevention status showing suppressed MACs (AC vs PW moves)",
        "required_for": "ac_ac,ac_pw",
    },
}


# ---------------------------------------------------------------------------
# VPLS MAC Mobility rules (from Confluence design doc section "MAC handling")
# Tests use these rules to validate mobility behavior.
# ---------------------------------------------------------------------------

VPLS_MAC_MOBILITY_RULES: Dict[str, Dict[str, Any]] = {
    "ac_to_pw_move": {
        "description": "MAC learned on local AC, then learned from PW -> withdraw Type-2, forward via PW",
        "counts_for_suppression": True,
        "sequence_increment": False,
        "event_type": "MOVE_LOCAL_TO_PW",
    },
    "pw_to_ac_move": {
        "description": "MAC learned from PW, then learned on local AC -> advertise Type-2, forward via AC",
        "counts_for_suppression": True,
        "sequence_increment": True,
        "event_type": "MOVE_PW_TO_LOCAL",
    },
    "evpn_vs_pw_move": {
        "description": "MAC learned from remote EVPN vs PW -> NOT counted for mobility suppression",
        "counts_for_suppression": False,
        "event_type": "UPDATE_PW / UPDATE_REMOTE",
    },
    "pw_mac_bgp_advertise": {
        "description": "PW-learned MACs MUST NOT be advertised as EVPN Type-2 routes",
        "rule": "no_bgp_advertise",
    },
    "pw_mac_in_table": {
        "description": "PW-learned MACs MUST appear in show evpn mac-table (control plane + DP)",
        "rule": "visible_in_mac_table",
        "flag": "VPLS_PW",
    },
    "suppressed_pw_mac_forwarding": {
        "description": "Suppressed VPLS_PW MAC is still forwarding (unlike suppressed EVPN MAC)",
        "rule": "forwarding_even_if_suppressed",
    },
}

# Map test folder names to their required config blocks
TEST_CONFIG_REQUIREMENTS: Dict[str, List[str]] = {
    "basic_learning": ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "bgp_l2vpn_evpn_af", "mac_learning"],
    "ac_ac":          ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "second_ac", "loop_prevention", "bgp_l2vpn_evpn_af"],
    "ac_evpn":        ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "seamless_integration", "bgp_l2vpn_evpn_af"],
    "ac_pw":          ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "seamless_integration", "si_site_id", "si_source_if",
                        "si_label_block_size", "si_bgp_rt",
                        "bgp_l2vpn_evpn_af", "bgp_l2vpn_vpls_af", "label_pool"],
    "pw_pw":          ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt",
                        "seamless_integration", "si_site_id", "si_source_if",
                        "si_label_block_size", "si_bgp_rt",
                        "bgp_l2vpn_evpn_af", "bgp_l2vpn_vpls_af", "label_pool"],
    "evpn_pw":        ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "seamless_integration", "si_site_id", "si_source_if",
                        "si_label_block_size", "si_bgp_rt",
                        "bgp_l2vpn_evpn_af", "bgp_l2vpn_vpls_af", "label_pool"],
    "multihoming":    ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "seamless_integration", "si_site_id", "si_site_preference",
                        "si_site_multihoming", "si_source_if", "si_label_block_size",
                        "multihoming_global", "multihoming_esi",
                        "bgp_l2vpn_evpn_af", "bgp_l2vpn_vpls_af", "label_pool"],
    "ha_mac_mobility": ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                         "seamless_integration", "bgp_l2vpn_evpn_af"],
    "withdraw_flush": ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "loop_prevention", "bgp_l2vpn_evpn_af"],
    "aging_timers":   ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt", "evpn_interface",
                        "mac_aging", "bgp_l2vpn_evpn_af"],
}


# ---------------------------------------------------------------------------
# Gap detection: parse running config and find missing blocks
# ---------------------------------------------------------------------------

@dataclass
class ConfigGap:
    """A missing or incomplete configuration block."""
    requirement_id: str
    requirement: ConfigRequirement
    status: str  # "missing", "incomplete", "present"
    detail: str = ""
    fix_snippet: str = ""


def _normalize_config(text: str) -> str:
    """Collapse whitespace, lowercase for keyword matching."""
    return re.sub(r"\s+", " ", text.lower())


def _count_interfaces_in_evpn(evpn_config: str) -> int:
    """Count AC interfaces directly under the EVPN instance (not under seamless-integration)."""
    count = 0
    in_si = False
    for line in evpn_config.splitlines():
        stripped = line.strip()
        if "seamless-integration" in stripped:
            in_si = True
        elif in_si and stripped == "!":
            in_si = False
        elif not in_si and re.match(r"interface\s+(ge|bundle|lag)\S+", stripped):
            count += 1
    return count


def detect_config_gaps(
    running_config: str,
    test_id: str,
    evpn_config: str = "",
    bgp_config: str = "",
    multihoming_config: str = "",
) -> List[ConfigGap]:
    """Detect missing config blocks for a specific test scenario.

    Args:
        running_config: Full 'show config' or combined config output.
        test_id: Test folder name (e.g., 'ac_evpn', 'multihoming').
        evpn_config: 'show config network-services evpn' output (more specific).
        bgp_config: 'show config protocols bgp' output.
        multihoming_config: 'show config network-services multihoming' output.

    Returns:
        List of ConfigGap objects for missing or incomplete blocks.
    """
    required_ids = TEST_CONFIG_REQUIREMENTS.get(test_id)
    if not required_ids:
        base_ids = ["evpn_instance", "evpn_transport_mpls", "evpn_bgp_rt",
                     "evpn_interface", "bgp_l2vpn_evpn_af"]
        required_ids = base_ids

    evpn_norm = _normalize_config(evpn_config)
    bgp_norm = _normalize_config(bgp_config)
    mh_norm = _normalize_config(multihoming_config)
    all_norm = _normalize_config(
        "\n".join(filter(None, [running_config, evpn_config, bgp_config, multihoming_config]))
    )

    _SECTION_MAP: Dict[str, str] = {
        "bgp_l2vpn_evpn_af": bgp_norm,
        "bgp_l2vpn_vpls_af": bgp_norm,
        "bgp_neighbor_group": bgp_norm,
        "multihoming_global": mh_norm,
        "multihoming_esi": mh_norm,
        "label_pool": all_norm,
    }

    ac_count = _count_interfaces_in_evpn(evpn_config)

    gaps: List[ConfigGap] = []
    for req_id in required_ids:
        req = EVPN_SI_CONFIG_TREE.get(req_id)
        if not req:
            continue

        # Special handling: second_ac needs >= 2 AC interfaces
        if req_id == "second_ac":
            if ac_count < 2:
                gaps.append(ConfigGap(
                    requirement_id=req_id,
                    requirement=req,
                    status="missing",
                    detail=f"Only {ac_count} AC interface(s) found, need >= 2",
                ))
            continue

        # bgp_l2vpn_evpn_af must be detected in BGP config specifically,
        # not in EVPN config where "l2vpn-evpn" appears as RT keyword
        search_text = _SECTION_MAP.get(req_id, evpn_norm if "evpn" in req.path or "bridge" in req.path else all_norm)

        if req_id == "bgp_l2vpn_evpn_af":
            found = "address-family l2vpn-evpn" in search_text
        elif req_id == "bgp_l2vpn_vpls_af":
            found = "address-family l2vpn-vpls" in search_text
        else:
            keyword = req.detect_keyword.lower()
            found = bool(keyword and keyword in search_text)

        if not found:
            gaps.append(ConfigGap(
                requirement_id=req_id,
                requirement=req,
                status="missing",
                detail=f"Config block not found: {req.description}",
            ))

    return gaps


# ---------------------------------------------------------------------------
# Snippet generation: produce CLI commands to fill gaps
# ---------------------------------------------------------------------------

def generate_fix_snippets(
    gaps: List[ConfigGap],
    evpn_name: str = "EVPN1",
    asn: str = "65000",
    iface: str = "ge400-0/0/4.1000",
    iface2: str = "ge400-0/0/5.1001",
    rt: str = "100:100",
    rd: str = "1.1.1.1:500",
    site_id: str = "1",
    loopback: str = "lo0",
    bd_name: str = "BD1",
    es_name: str = "ES1",
    esi: str = "00:11:22:33:44:55:66:77:88:99",
    neighbor_group: str = "EVPN_PEERS",
) -> Dict[str, str]:
    """Generate DNOS CLI snippets to fix detected config gaps.

    Returns dict of requirement_id -> CLI snippet (ready for copy-paste into config mode).
    These are PROPOSALS only -- the framework never auto-commits.
    """
    params = {
        "{evpn_name}": evpn_name,
        "{asn}": asn,
        "{iface}": iface,
        "{iface2}": iface2,
        "{rt}": rt,
        "{rd}": rd,
        "{id}": site_id,
        "{size}": "8",
        "{loopback}": loopback,
        "{bd_name}": bd_name,
        "{es_name}": es_name,
        "{esi}": esi,
        "{group}": neighbor_group,
    }

    snippets: Dict[str, str] = {}

    for gap in gaps:
        if gap.status != "missing":
            continue

        req = gap.requirement
        req_id = gap.requirement_id

        snippet = _SNIPPET_TEMPLATES.get(req_id)
        if snippet:
            for k, v in params.items():
                snippet = snippet.replace(k, v)
            snippets[req_id] = snippet
        else:
            path = req.path
            for k, v in params.items():
                path = path.replace(k, v)
            val = req.example_value
            if val:
                snippets[req_id] = f"# {req.description}\n{path}"
            else:
                snippets[req_id] = f"# {req.description}\n# {path}"

    return snippets


_SNIPPET_TEMPLATES: Dict[str, str] = {
    "evpn_instance": """\
network-services
  evpn
    instance {evpn_name}
      admin-state enabled
      transport-protocol
        mpls
      !
      protocols
        bgp {asn}
          export-l2vpn-evpn route-target {rt}
          import-l2vpn-evpn route-target {rt}
          route-distinguisher {rd}
        !
      !
      interface {iface}
      !
    !
  !
!""",

    "evpn_interface": """\
network-services evpn instance {evpn_name}
  interface {iface}
!""",

    "second_ac": """\
network-services evpn instance {evpn_name}
  interface {iface2}
!""",

    "seamless_integration": """\
network-services evpn instance {evpn_name}
  seamless-integration
    source-if {loopback}
    label-block-size 8
    site-id {id}
      interface {iface}
      site-preference 100
    !
  !
!""",

    "si_site_id": """\
network-services evpn instance {evpn_name}
  seamless-integration
    site-id {id}
      interface {iface}
      site-preference 100
    !
  !
!""",

    "si_label_block_size": """\
network-services evpn instance {evpn_name}
  seamless-integration
    label-block-size 8
  !
!""",

    "si_source_if": """\
network-services evpn instance {evpn_name}
  seamless-integration
    source-if {loopback}
  !
!""",

    "si_bgp_rt": """\
network-services evpn instance {evpn_name}
  seamless-integration
    bgp
      import-vpn route-target {rt}
      export-vpn route-target {rt}
    !
  !
!""",

    "loop_prevention": """\
network-services evpn instance {evpn_name}
  mac-handling
    loop-prevention
      admin-state enabled
      action suppress-and-notify
      loop-detection-threshold 5
      loop-detection-window 180
    !
  !
!""",

    "local_loop_prevention": """\
network-services evpn instance {evpn_name}
  mac-handling
    loop-prevention
      local-loop-prevention
        admin-state enabled
        restore-timer 300
        restore-max-cycles 3
      !
    !
  !
!""",

    "mac_aging": """\
network-services evpn instance {evpn_name}
  mac-handling
    mac-table-aging-time 300
  !
!""",

    "sticky_mac": """\
network-services evpn instance {evpn_name}
  interface {iface}
    sticky-interface enabled
  !
!""",

    "bgp_l2vpn_evpn_af": """\
protocols bgp {asn}
  address-family l2vpn-evpn
!""",

    "bgp_neighbor_group": """\
protocols bgp {asn}
  neighbor-group {group}
    address-family l2vpn-evpn
      admin-state enabled
    !
  !
!""",

    "multihoming_global": """\
network-services
  multihoming
    redundancy-mode all-active
  !
!""",

    "multihoming_esi": """\
network-services
  multihoming
    ethernet-segment {es_name}
      identifier {esi}
    !
  !
!""",

    "bridge_domain": """\
network-services
  bridge-domain
    instance {bd_name}
      admin-state enabled
    !
  !
!""",

    "bgp_l2vpn_vpls_af": """\
protocols bgp {asn}
  address-family l2vpn-vpls
!""",

    "label_pool": """\
# VPLS requires a dedicated label pool before seamless-integration can allocate blocks.
# Adjust the range to avoid overlap with other label pools on this device.
system label-pool vpls-pool range 900000 999999
!""",

    "si_l2_mtu": """\
network-services evpn instance {evpn_name}
  seamless-integration
    l2-mtu 9100
  !
!""",

    "si_site_multihoming": """\
network-services evpn instance {evpn_name}
  seamless-integration
    site-id {id}
      multihoming
    !
  !
!""",
}


# ---------------------------------------------------------------------------
# High-level helper: run gap analysis on a live device via SSH
# ---------------------------------------------------------------------------

def run_config_gap_analysis(
    run_show,
    device: str,
    test_id: str,
    evpn_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Run full config gap analysis on a live device.

    Uses run_show(device, command) to fetch config sections, then
    detects gaps against test requirements.

    Returns:
        {
            "evpn_name": str,
            "test_id": str,
            "gaps": [ConfigGap, ...],
            "snippets": {req_id: str, ...},
            "gap_count": int,
            "all_present": bool,
            "auto_fixable_count": int,
        }
    """
    evpn_cfg = run_show(device, "show config network-services evpn")
    bgp_cfg = run_show(device, "show config protocols bgp")
    mh_cfg = run_show(device, "show config network-services multihoming")

    if not evpn_name:
        # Try show evpn summary first
        evpn_summary = run_show(device, "show evpn summary")
        match = re.search(r"instance\s+(\S+)", evpn_summary, re.IGNORECASE)
        if match:
            evpn_name = match.group(1)
        else:
            # Fallback: parse from config text
            cfg_match = re.search(r"instance\s+(\S+)", evpn_cfg)
            evpn_name = cfg_match.group(1) if cfg_match else "EVPN1"

    gaps = detect_config_gaps(
        running_config="",
        test_id=test_id,
        evpn_config=evpn_cfg,
        bgp_config=bgp_cfg,
        multihoming_config=mh_cfg,
    )

    asn_match = re.search(r"bgp\s+(\d+)", bgp_cfg)
    asn = asn_match.group(1) if asn_match else "65000"

    iface_match = re.search(r"interface\s+((?:ge|bundle)\S+)", evpn_cfg)
    iface = iface_match.group(1) if iface_match else "ge400-0/0/4.1000"

    rt_match = re.search(r"route-target\s+(\S+)", evpn_cfg)
    rt = rt_match.group(1) if rt_match else "100:100"

    rd_match = re.search(r"route-distinguisher\s+(\S+)", evpn_cfg)
    rd = rd_match.group(1) if rd_match else "1.1.1.1:500"

    snippets = generate_fix_snippets(
        gaps, evpn_name=evpn_name, asn=asn, iface=iface, rt=rt, rd=rd,
    )

    auto_fixable = sum(1 for g in gaps if g.requirement.auto_fixable)

    return {
        "evpn_name": evpn_name,
        "test_id": test_id,
        "gaps": gaps,
        "snippets": snippets,
        "gap_count": len(gaps),
        "all_present": len(gaps) == 0,
        "auto_fixable_count": auto_fixable,
    }
