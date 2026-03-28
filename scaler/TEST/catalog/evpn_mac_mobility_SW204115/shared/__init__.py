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
"""

from .mac_parsers import (
    MAC_ADDR_RE,
    MacDetailEntry,
    MacSuppressEntry,
    FwdTableEntry,
    LoopPreventionMacEntry,
    LoopPreventionIfEntry,
    FibMacEntry,
    parse_bgp_l2vpn_evpn_summary,
    parse_bestpath_compare,
    parse_evpn_mac_count,
    parse_evpn_mac_entries,
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
from .mac_trigger import TrafficMethod, detect_traffic_methods, plan_mac_move
from .mac_verifiers import (
    verify_mac_present,
    verify_mac_source,
    verify_mac_flags,
    verify_forwarding_state,
    verify_suppress_list,
    verify_loop_prevention_state,
    verify_loop_count_incremented,
    verify_restore_timer_reset,
    verify_mobility_counter,
    verify_no_ghost_macs,
    verify_fib_mac_state,
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
