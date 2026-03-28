#!/usr/bin/env python3
"""
EVPN MAC Mobility Knowledge Pack (Tier 2).

Feature-specific event knowledge for EVPN Seamless Integration.
Provides default counter commands, counter expectations, event expectations,
health checks, and cleanup commands that populate recipe JSON.

Sources:
  - Confluence: "Enable all system events" design doc
  - Confluence: "evpn-mac-mobility" spec
  - Jira SW-178648 (EVPN ELAN SI Epic)
  - Jira SW-204115 (MAC Mobility Testing Category)

This is the first Tier 2 knowledge pack. Future features (FlowSpec, ISIS, MPLS)
add their own knowledge packs without modifying the generic Tier 1 engines.
"""

from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# EVPN System Events (12 events from Confluence + additional observed events)
# ---------------------------------------------------------------------------

EVPN_SYSTEM_EVENTS = {
    "L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED": {
        "description": "MAC address suppressed due to excessive mobility",
        "severity": "WARN",
        "trigger_scenarios": ["rapid_flap", "ac_ac_flap", "ac_evpn_flap", "ac_pw_flap"],
        "absent_scenarios": ["basic_learning", "aging_timers", "withdraw_flush"],
    },
    "L2_LOOP_DETECTION_INTERFACE_SHUTDOWN": {
        "description": "Interface shut down by loop detection",
        "severity": "ERROR",
        "trigger_scenarios": ["rapid_flap_with_shutdown_sanction"],
        "absent_scenarios": ["basic_learning", "ac_evpn", "evpn_pw"],
    },
    "L2_MAC_MOBILITY_LOOP_DETECTED": {
        "description": "MAC mobility loop detected between interfaces",
        "severity": "WARN",
        "trigger_scenarios": ["ac_ac_flap", "rapid_flap"],
        "absent_scenarios": ["basic_learning", "withdraw_flush"],
    },
    "L2_MAC_MOBILITY_SEQUENCE_WRAP": {
        "description": "MAC mobility sequence number wrapped around",
        "severity": "WARN",
        "trigger_scenarios": [],
        "absent_scenarios": ["basic_learning", "ac_ac", "ac_evpn"],
    },
    "L2_MAC_FLUSH_RECEIVED": {
        "description": "MAC flush received from peer",
        "severity": "INFO",
        "trigger_scenarios": ["withdraw_flush", "ha_mac_mobility"],
        "absent_scenarios": ["basic_learning"],
    },
    "L2_MAC_TABLE_FULL": {
        "description": "MAC table capacity reached",
        "severity": "ERROR",
        "trigger_scenarios": [],
        "absent_scenarios": ["basic_learning", "ac_ac", "ac_evpn", "ac_pw"],
    },
    "BGP_NEIGHBOR_ESTABLISHED": {
        "description": "BGP session reached Established state",
        "severity": "INFO",
        "trigger_scenarios": ["ha_mac_mobility"],
        "absent_scenarios": [],
    },
    "BGP_NOTIFICATION_RECEIVED": {
        "description": "BGP NOTIFICATION message received from peer",
        "severity": "ERROR",
        "trigger_scenarios": [],
        "absent_scenarios": ["basic_learning", "ac_ac", "ac_evpn", "ac_pw", "evpn_pw", "pw_pw"],
    },
    "BGP_NOTIFICATION_SENT": {
        "description": "BGP NOTIFICATION message sent to peer",
        "severity": "ERROR",
        "trigger_scenarios": [],
        "absent_scenarios": ["basic_learning", "ac_ac", "ac_evpn", "ac_pw", "evpn_pw", "pw_pw"],
    },
    "EVPN_INSTANCE_STATE_CHANGE": {
        "description": "EVPN instance operational state changed",
        "severity": "WARN",
        "trigger_scenarios": ["ha_mac_mobility"],
        "absent_scenarios": ["basic_learning", "ac_ac"],
    },
    "SYSTEM_PROCESS_RESTART": {
        "description": "System process restarted",
        "severity": "WARN",
        "trigger_scenarios": ["ha_mac_mobility"],
        "absent_scenarios": ["basic_learning", "ac_ac", "ac_evpn"],
    },
    "NCC_SWITCHOVER_COMPLETE": {
        "description": "NCC switchover completed",
        "severity": "INFO",
        "trigger_scenarios": ["ha_mac_mobility"],
        "absent_scenarios": ["basic_learning", "ac_ac", "ac_evpn", "ac_pw"],
    },
}


# ---------------------------------------------------------------------------
# Default Counter Commands (EVPN MAC mobility)
# ---------------------------------------------------------------------------

EVPN_COUNTER_COMMANDS: List[Dict[str, str]] = [
    {
        "label": "mac_count",
        "command": "show evpn mac summary | no-more",
        "parser": "first_integer",
        "description": "Total EVPN MAC count across all instances",
    },
    {
        "label": "mac_instance_count",
        "command": "show evpn mac-table instance {evpn_name} | no-more",
        "parser": "line_count",
        "description": "MAC entries in the test EVPN instance",
    },
    {
        "label": "bgp_evpn_prefixes",
        "command": "show bgp l2vpn evpn summary | no-more",
        "parser": "key_value",
        "description": "BGP L2VPN EVPN peer summary with prefix counts",
    },
    {
        "label": "mobility_counter",
        "command": "show dnos-internal routing evpn mac-mobility-redis-count | no-more",
        "parser": "key_value",
        "description": "MAC mobility redis counter (total moves)",
    },
    {
        "label": "ghost_mac_count",
        "command": "show dnos-internal routing evpn instance {evpn_name} mac-table-ghost | no-more",
        "parser": "line_count",
        "description": "Ghost MAC entries (should be 0 normally)",
    },
    {
        "label": "fwd_table_count",
        "command": "show evpn forwarding-table mac-address-table instance {evpn_name} | no-more",
        "parser": "line_count",
        "description": "NCP forwarding table entry count",
    },
]


# ---------------------------------------------------------------------------
# Scenario-specific counter expectations
# ---------------------------------------------------------------------------

def get_counter_expectations(scenario_type: str) -> List[Dict[str, Any]]:
    """Return counter expectations for a specific scenario type."""
    base = [
        {"label": "ghost_mac_count", "rule": "zero", "description": "No ghost MACs after scenario"},
    ]

    if scenario_type in ("basic_learning", "ac_evpn", "evpn_pw", "ac_pw", "pw_pw"):
        base.extend([
            {"label": "mac_count", "rule": "no_decrease", "description": "MAC count must not drop"},
            {"label": "mac_instance_count", "rule": "no_decrease", "description": "Instance MAC count stable/grows"},
        ])

    elif scenario_type == "ac_ac":
        base.extend([
            {"label": "mac_count", "rule": "no_decrease", "description": "MAC count stable during moves"},
            {"label": "mobility_counter", "rule": "increase", "description": "Mobility counter should increase on moves"},
        ])

    elif scenario_type == "ha_mac_mobility":
        base.extend([
            {"label": "mac_count", "rule": "no_decrease", "description": "MAC count must recover after HA"},
            {"label": "fwd_table_count", "rule": "no_decrease", "description": "Forwarding table must recover"},
        ])

    elif scenario_type == "withdraw_flush":
        base.extend([
            {"label": "mac_count", "rule": "no_increase", "description": "MAC count should decrease on withdraw"},
        ])

    elif scenario_type == "multihoming":
        base.extend([
            {"label": "mac_count", "rule": "no_decrease", "description": "MAC count stable on MH failover"},
            {"label": "fwd_table_count", "rule": "no_decrease", "description": "Forwarding table stable"},
        ])

    elif scenario_type == "aging_timers":
        pass

    return base


def get_event_expectations(scenario_type: str) -> List[Dict[str, Any]]:
    """Return event expectations for a specific scenario type."""
    expectations: List[Dict[str, Any]] = []

    # Always expect no BGP NOTIFICATIONs on non-HA tests
    if scenario_type not in ("ha_mac_mobility",):
        expectations.extend([
            {"event": "BGP_NOTIFICATION_RECEIVED", "expect": "absent",
             "description": "No BGP NOTIFICATION received during test"},
            {"event": "BGP_NOTIFICATION_SENT", "expect": "absent",
             "description": "No BGP NOTIFICATION sent during test"},
        ])

    if scenario_type == "ac_ac":
        expectations.extend([
            {"event": "L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED", "expect": "present",
             "min_count": 1, "description": "Suppression expected on rapid flap (SC02)"},
            {"event": "L2_MAC_MOBILITY_LOOP_DETECTED", "expect": "present",
             "min_count": 1, "description": "Loop detection expected on local moves (SC03)"},
        ])

    elif scenario_type == "ha_mac_mobility":
        expectations.extend([
            {"event": "BGP_NEIGHBOR_ESTABLISHED", "expect": "present",
             "min_count": 1, "description": "BGP should re-establish after HA trigger"},
            {"event": "SYSTEM_PROCESS_RESTART", "expect": "present",
             "min_count": 1, "description": "Process restart expected (HA trigger)"},
        ])

    elif scenario_type in ("basic_learning", "ac_evpn", "evpn_pw", "ac_pw", "pw_pw"):
        expectations.extend([
            {"event": "L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED", "expect": "absent",
             "description": "No suppression expected for normal learning/moves"},
            {"event": "L2_LOOP_DETECTION_INTERFACE_SHUTDOWN", "expect": "absent",
             "description": "No loop-detection interface shutdown"},
        ])

    elif scenario_type == "multihoming":
        expectations.extend([
            {"event": "L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED", "expect": "absent",
             "description": "No suppression on MH failover (legitimate move)"},
        ])

    return expectations


# ---------------------------------------------------------------------------
# Default health checks (EVPN-specific processes)
# ---------------------------------------------------------------------------

EVPN_HEALTH_CONFIG: Dict[str, Any] = {
    "processes": [
        "routing:bgpd",
        "routing:fibmgrd",
        "routing:rib_manager",
        "neighbour_manager",
    ],
    "check_crashes": True,
    "check_cpu_memory": True,
    "check_alarms": True,
    "cpu_threshold_pct": 90,
    "memory_threshold_pct": 90,
    "error_counter_commands": [],
}


# ---------------------------------------------------------------------------
# Default cleanup commands (EVPN)
# ---------------------------------------------------------------------------

EVPN_CLEANUP_COMMANDS: List[str] = [
    "no debug evpn mac-mobility",
    "no debug evpn mac-learning",
    "no debug evpn mac-table",
    "no set logging terminal",
]


# ---------------------------------------------------------------------------
# Config baseline sections (EVPN)
# ---------------------------------------------------------------------------

EVPN_CONFIG_BASELINE: Dict[str, Any] = {
    "sections": [
        "network-services evpn",
        "protocols bgp",
        "network-services bridge-domain",
    ],
    "full_config": False,
    "ignore_patterns": [
        "last-modified",
        "commit-id",
        "Commit performed",
    ],
}


# ---------------------------------------------------------------------------
# Poll configuration defaults (EVPN)
# ---------------------------------------------------------------------------

EVPN_POLL_CONFIG: Dict[str, Any] = {
    "interval_sec": 5,
    "max_duration_sec": 120,
    "convergence_check": {
        "command": "show bgp l2vpn evpn summary | no-more",
        "pattern": "Established",
        "min_stable_polls": 3,
    },
    "poll_commands": [
        {"label": "bgp_state", "command": "show bgp l2vpn evpn summary | no-more"},
        {"label": "mac_count", "command": "show evpn mac summary | no-more"},
        {"label": "mac_table", "command": "show evpn mac-table instance {evpn_name} | no-more"},
    ],
}


# ---------------------------------------------------------------------------
# Enrichment API: populate recipe with EVPN defaults
# ---------------------------------------------------------------------------

def enrich_recipe_with_evpn_defaults(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Add EVPN-specific defaults to a recipe if not already present.

    Preserves any user-specified values -- only fills in missing keys.
    """
    if "counter_commands" not in recipe:
        recipe["counter_commands"] = EVPN_COUNTER_COMMANDS

    # Determine scenario type from test directory or recipe feature
    scenario_type = _infer_scenario_type(recipe)

    if "counter_expectations" not in recipe:
        recipe["counter_expectations"] = get_counter_expectations(scenario_type)

    if "event_expectations" not in recipe:
        recipe["event_expectations"] = get_event_expectations(scenario_type)

    if "health_checks" not in recipe:
        recipe["health_checks"] = EVPN_HEALTH_CONFIG.copy()

    if "cleanup_commands" not in recipe:
        recipe["cleanup_commands"] = list(EVPN_CLEANUP_COMMANDS)

    if "config_baseline" not in recipe:
        recipe["config_baseline"] = EVPN_CONFIG_BASELINE.copy()

    for scenario in recipe.get("scenarios", []):
        phases = scenario.get("phases", {})
        if "poll_recovery" in phases and "poll_config" not in scenario:
            scenario["poll_config"] = EVPN_POLL_CONFIG.copy()

    return recipe


def _infer_scenario_type(recipe: Dict[str, Any]) -> str:
    """Infer the scenario type from the recipe ID or name."""
    rid = recipe.get("id", "").lower()
    name = recipe.get("name", "").lower()

    if "ha" in rid or "ha" in name:
        return "ha_mac_mobility"
    if "ac_ac" in rid or "ac_ac" in name or "ac <-> ac" in name:
        return "ac_ac"
    if "ac_evpn" in rid or "ac_evpn" in name or "ac <-> evpn" in name:
        return "ac_evpn"
    if "ac_pw" in rid or "ac_pw" in name or "ac <-> pw" in name:
        return "ac_pw"
    if "evpn_pw" in rid or "evpn_pw" in name:
        return "evpn_pw"
    if "pw_pw" in rid or "pw_pw" in name:
        return "pw_pw"
    if "withdraw" in rid or "flush" in name:
        return "withdraw_flush"
    if "multihoming" in rid or "multi" in name:
        return "multihoming"
    if "aging" in rid or "timer" in name:
        return "aging_timers"
    return "basic_learning"
