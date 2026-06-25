"""Shared helpers for EVPN MAC mobility tests (SW-204115).

Modules:
  mac_parsers        -- Parse DNOS CLI output (basic + detail + suppress + fwd-table
                        + loop-prevention + dnos-internal)
  mac_verifiers      -- Verification functions for MAC flags, suppression, sticky,
                        loop-prevention, mobility counter, ghost MACs, FIB state
  mac_trigger        -- Spirent MAC move execution (local-to-local, rapid flap,
                        back-and-forth, scale) with post-move polling
  verdict_engine     -- Multi-layer verdict evaluation with enhanced layers
  trace_analyzer     -- Trace analysis + deep evidence collection + debug trace
                        management + auto-investigate generation
  jira_bug_matcher   -- Local known-bug search on failure
  device_runner      -- Resilient device command runner: MCP -> helper -> SSH fallback
  spirent_preflight  -- Pre-flight checks for Spirent session + DNAAS path

Action+validate contract (mandatory for all new orchestration code):
  validators         -- poll_until() + wait_for_{bgp_state,arp_resolve,
                        interface_up,mac_in_table,mac_absent,evi_label_pool,
                        route_in_rib,pw_installed}; replaces fixed time.sleep()
  step_reporter      -- StepReporter context manager that emits structured
                        '[STEP N/M] action=X validate=Y ... PASS/FAIL in Ns' lines
  device_profile     -- DeviceProfile + build_device_profile(); discover ASN,
                        router-id, sub-ifs, BGP neighbors, EVPN instances,
                        free inner VLANs, parent interface from any device
                        (no hardcoded PE-1/PE-4/AS-1234567 assumptions)
"""

from .mac_parsers import (
    MAC_ADDR_RE,
    MacDetailEntry,
    MacSuppressEntry,
    MacTableEntry,
    FwdTableEntry,
    LoopPreventionMacEntry,
    LoopPreventionIfEntry,
    FibMacEntry,
    find_mac,
    parse_bgp_l2vpn_evpn_summary,
    parse_bestpath_compare,
    parse_evpn_mac_count,
    parse_evpn_mac_entries,
    parse_mac_table_piped,
    parse_fib_evpn_mac,
    parse_forwarding_table_flags,
    parse_ghost_macs,
    parse_loop_prevention_interface,
    parse_loop_prevention_local,
    parse_loop_prevention_mac_table,
    parse_mac_detail,
    parse_mac_mobility_redis_count,
    parse_mac_suppress,
    parse_system_nodes,
    strip_ansi,
)
from .mac_trigger import (
    TrafficMethod,
    detect_traffic_methods,
    plan_mac_move,
    check_si_mode,
    check_pw_data_plane,
)
from .mac_verifiers import (
    verify_mac_present,
    verify_mac_source,
    verify_mac_flags,
    verify_mac_per_view,
    verify_forwarding_state,
    verify_suppress_list,
    verify_loop_prevention_state,
    verify_loop_count_incremented,
    verify_restore_timer_reset,
    verify_mobility_counter,
    verify_no_ghost_macs,
    verify_fib_mac_state,
    parse_evi_moved_events,
    verify_evi_moved_events_increment,
)
from .jira_bug_matcher import BugMatch, search_known_bugs, format_bug_matches
from .trace_analyzer import (
    DeepEvidence,
    collect_deep_evidence,
    enable_debug_traces,
    disable_debug_traces,
    auto_investigate,
)
from .observability import (
    ObservabilityCollector,
    CommandCapture,
    TimelineEvent,
    PhaseSummary,
    SnapshotDiff,
    TrafficSnapshot,
)
from .device_runner import (
    create_device_runner,
    get_cached_runner,
    cleanup_all_sessions,
)
from .ssh_session import InteractiveSSHSession
from .spirent_preflight import (
    run_preflight,
    check_spirent_session,
    check_dnaas_path,
)
from .spirent_vpls_provisioner import (
    provision_spirent_vpls_cp,
    provision_spirent_vpls_cp_dual,
    rebuild_spirent_session,
)
from .config_knowledge import (
    detect_config_gaps,
    generate_fix_snippets,
    run_config_gap_analysis,
    EVPN_SI_CONFIG_TREE,
    TEST_CONFIG_REQUIREMENTS,
    VPLS_SHOW_COMMANDS,
    VPLS_MAC_MOBILITY_RULES,
)
from .cross_layer_check import ProactiveXray
from .mac_verifiers import (
    verify_spirent_dut_crossref,
    check_bgp_health_during_poll,
)
from .evpn_event_knowledge import (
    EVPN_SYSTEM_EVENTS,
    EVPN_COUNTER_COMMANDS,
    EVPN_HEALTH_CONFIG,
    EVPN_CLEANUP_COMMANDS,
    EVPN_CONFIG_BASELINE,
    EVPN_POLL_CONFIG,
    enrich_recipe_with_evpn_defaults,
    get_counter_expectations,
    get_event_expectations,
)
from .validators import (
    ValidationResult,
    poll_until,
    wait_for_bgp_state,
    wait_for_bgp_state_in,
    wait_for_arp_resolve,
    wait_for_interface_up,
    wait_for_mac_in_table,
    wait_for_mac_absent,
    wait_for_evi_label_pool,
    wait_for_route_in_rib,
    wait_for_pw_installed,
    action_then_validate,
)
from .step_reporter import StepReporter, StepRecord
from .device_profile import (
    DeviceProfile,
    SubInterface,
    BgpNeighbor,
    build_device_profile,
)

# Explicit re-export surface. Without this, ruff F401 flags every name as
# "imported but unused"; with it, the suite's intended API stays documented
# and discoverable. Update when new helpers move into shared/.
__all__ = [
    # mac_parsers
    "MAC_ADDR_RE",
    "MacDetailEntry",
    "MacSuppressEntry",
    "MacTableEntry",
    "FwdTableEntry",
    "LoopPreventionMacEntry",
    "LoopPreventionIfEntry",
    "FibMacEntry",
    "find_mac",
    "parse_bgp_l2vpn_evpn_summary",
    "parse_bestpath_compare",
    "parse_evpn_mac_count",
    "parse_evpn_mac_entries",
    "parse_mac_table_piped",
    "parse_fib_evpn_mac",
    "parse_forwarding_table_flags",
    "parse_ghost_macs",
    "parse_loop_prevention_interface",
    "parse_loop_prevention_local",
    "parse_loop_prevention_mac_table",
    "parse_mac_detail",
    "parse_mac_mobility_redis_count",
    "parse_mac_suppress",
    "parse_system_nodes",
    "strip_ansi",
    # mac_trigger
    "TrafficMethod",
    "detect_traffic_methods",
    "plan_mac_move",
    "check_si_mode",
    "check_pw_data_plane",
    # mac_verifiers
    "verify_mac_present",
    "verify_mac_source",
    "verify_mac_flags",
    "verify_mac_per_view",
    "verify_forwarding_state",
    "verify_suppress_list",
    "verify_loop_prevention_state",
    "verify_loop_count_incremented",
    "verify_restore_timer_reset",
    "verify_mobility_counter",
    "verify_no_ghost_macs",
    "verify_fib_mac_state",
    "parse_evi_moved_events",
    "verify_evi_moved_events_increment",
    "verify_spirent_dut_crossref",
    "check_bgp_health_during_poll",
    # jira_bug_matcher
    "BugMatch",
    "search_known_bugs",
    "format_bug_matches",
    # trace_analyzer
    "DeepEvidence",
    "collect_deep_evidence",
    "enable_debug_traces",
    "disable_debug_traces",
    "auto_investigate",
    # observability
    "ObservabilityCollector",
    "CommandCapture",
    "TimelineEvent",
    "PhaseSummary",
    "SnapshotDiff",
    "TrafficSnapshot",
    # device runner / ssh
    "create_device_runner",
    "get_cached_runner",
    "cleanup_all_sessions",
    "InteractiveSSHSession",
    # spirent preflight
    "run_preflight",
    "check_spirent_session",
    "check_dnaas_path",
    # spirent vpls provisioner (referenced by infrastructure_modes.json
    # and recipe-level provisioner_function fields; kept in the public
    # surface so suite consumers can dispatch them dynamically)
    "provision_spirent_vpls_cp",
    "provision_spirent_vpls_cp_dual",
    "rebuild_spirent_session",
    # config knowledge
    "detect_config_gaps",
    "generate_fix_snippets",
    "run_config_gap_analysis",
    "EVPN_SI_CONFIG_TREE",
    "TEST_CONFIG_REQUIREMENTS",
    "VPLS_SHOW_COMMANDS",
    "VPLS_MAC_MOBILITY_RULES",
    # cross-layer
    "ProactiveXray",
    # event/health/poll/baseline knowledge
    "EVPN_SYSTEM_EVENTS",
    "EVPN_COUNTER_COMMANDS",
    "EVPN_HEALTH_CONFIG",
    "EVPN_CLEANUP_COMMANDS",
    "EVPN_CONFIG_BASELINE",
    "EVPN_POLL_CONFIG",
    "enrich_recipe_with_evpn_defaults",
    "get_counter_expectations",
    "get_event_expectations",
    # validators (action-then-validate primitives)
    "ValidationResult",
    "poll_until",
    "wait_for_bgp_state",
    "wait_for_bgp_state_in",
    "wait_for_arp_resolve",
    "wait_for_interface_up",
    "wait_for_mac_in_table",
    "wait_for_mac_absent",
    "wait_for_evi_label_pool",
    "wait_for_route_in_rib",
    "wait_for_pw_installed",
    "action_then_validate",
    # step reporting
    "StepReporter",
    "StepRecord",
    # device profile
    "DeviceProfile",
    "SubInterface",
    "BgpNeighbor",
    "build_device_profile",
]
