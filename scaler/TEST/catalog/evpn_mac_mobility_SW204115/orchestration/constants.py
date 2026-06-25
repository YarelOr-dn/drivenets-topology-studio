"""Module-level constants shared across the orchestration package.

Extracted from the monolithic ``mac_mobility_orchestrator.py`` so that the
per-phase helper modules (session_io, reporting, scenario_runner, test_runner)
can import the dispatch tables and budgets without pulling in the whole
orchestrator -- and without creating circular imports.

All values here are read-only at module load time (the env-var knobs are
evaluated once on import, which matches the original behavior).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

# ``Path(__file__).resolve().parent`` is ``orchestration/``.
# The suite root is one level up (contains mac_mobility_orchestrator.py,
# recipes, results, etc.).
SUITE_ROOT: Path = Path(__file__).resolve().parent.parent

MANIFEST_PATH: Path = SUITE_ROOT / "suite_manifest.json"
RESULTS_DIR: Path = SUITE_ROOT / "results"
ACTIVE_SESSION: Path = Path.home() / "SCALER" / "TEST" / "active_test_session.json"
CORRECTIONS_PATH: Path = SUITE_ROOT / "runtime_corrections.json"

# ---------------------------------------------------------------------------
# Dispatch tables: recipe ``trigger.action`` -> canonical mac_trigger verb.
# ---------------------------------------------------------------------------

ACTION_TRIGGER_MAP: Dict[str, str] = {
    "traffic_on_ac1": "learn_on_ac1",
    "move_mac_ac1_to_ac2": "local_to_local",
    "rapid_move_ac1_ac2": "rapid_flap",
    "sequence_moves": "back_and_forth",
    "sequence_moves_multi_ac": "back_and_forth",
    "local_to_local_moves": "local_to_local",
    "attempt_move_to_sticky_ac": "sticky_test",
    "remote_pe_traffic": "spirent_remote_pe",
    "remote_pe_advertises_rt2": "spirent_remote_pe",
    "traffic_via_pw": "spirent_pw_traffic",
    "send_mac_via_pw": "spirent_pw_traffic",
    "send_configured_sticky_mac_via_pw": "spirent_pw_traffic",
    "ncp_warm_restart": "ha_cli_command",
    "parallel_flap_and_restart": "spirent_parallel_flap_ha",
    "move_ac_to_pw": "spirent_ac_to_pw",
    "shift_to_remote_evpn": "spirent_ac_to_evpn",
    "move_pw1_to_pw2": "spirent_pw_to_pw",
    "execute_mac_move_pw_to_pw": "spirent_pw_to_pw",
    "evpn_to_ac_move": "spirent_evpn_to_ac",
    "move_evpn_to_pw": "spirent_evpn_to_pw",
    "move_pw_to_evpn": "spirent_pw_to_evpn",
    "learn_3_macs_on_ac1": "learn_multi_macs_ac1",
    "learn_sticky_mac_plus_2_normal_macs": "learn_multi_macs_ac1",
    "stop_traffic_wait_3x_aging": "wait_aging",
    "stop_traffic_and_wait": "wait_aging",
    "learn_on_pw_then_on_sticky_ac": "spirent_pw_then_ac",
    "learn_on_pw_then_configure_sticky": "spirent_pw_then_ac",
    "move_pw_to_ac": "spirent_pw_then_ac",
    "spirent_inject_evpn_rt2": "spirent_inject_rt2",
    "spirent_create_vpls_stream": "spirent_vpls_stream",
    "clear_mac_table": "clear_command",
    "clear_mac": "clear_command",
    "clear_with_assertion": "clear_command",
    "set_custom_aging": "config_command",
    "move_ac_across_pe": "spirent_ac_across_pe",
    # G2 (irb_si_rejection): commit-check assertion handlers.
    "attempt_irb_config": "commit_check_assert",
    "create_irb_instance_then_add_si": "commit_check_assert",
    "remove_si_add_irb": "commit_check_assert",
    # G1 (evpn_evpn): sequence-race RT-2 families routed through a single
    # replay handler in scenario_runner ("spirent_evpn_seq_race"). The handler
    # reads trigger.params.sequence (or .steps) to cover seq0->seq1,
    # same-seq-two-labels, and two-then-withdraw-winner flows from one codepath.
    "inject_rt2_seq0_then_seq1": "spirent_evpn_seq_race",
    "inject_rt2_same_seq_two_labels": "spirent_evpn_seq_race",
    "inject_two_then_withdraw_winner": "spirent_evpn_seq_race",
    # G3 (scale_64k): bulk RT-2 injection / move / flap on top of the existing
    # spirent_inject_rt2 handler. The handler now honors trigger.params.count
    # and trigger.params.base_mac so we don't need new codepaths.
    "spirent_send_64k_macs_ac1": "spirent_inject_rt2",
    "spirent_move_64k_ac1_to_ac2": "spirent_inject_rt2",
    "rapid_64k_flap_3_times": "spirent_inject_rt2",
    # G4 (pw_suppression_sanctions): sanction application + rapid flap combo
    # and remote rapid seq-updates without a local sanction.
    "rapid_ac_evpn_flap": "spirent_sanction_flap",
    "rapid_remote_seq_updates": "spirent_remote_seq_updates",
    # ac_ac variants that map to existing rapid-flap / sanction handlers.
    # `sanction_ac_ac_rapid_flap` is the AC<->AC sanction firing scenario; reuse
    # the same sanction-flap dispatcher introduced for G4. The other two are
    # timing/topology variants of the existing rapid_flap handler.
    "sanction_ac_ac_rapid_flap": "spirent_sanction_flap",
    "subsecond_rapid_flap_ac_ac": "rapid_flap",
    "sh_sh_coverage_flap": "rapid_flap",
    # ac_ac SC10: rapid-flap raced against an AC1 admin-state disable/enable.
    "admin_flap_during_move": "admin_flap_during_move",
    # clear_operations SC*: setup_trigger phase actions. They share the
    # rapid_flap mechanism (with different counts/intervals) to populate the
    # suppress / restore-cycle state that the actual `trigger` clear command
    # then asserts against.
    "rapid_flap_to_create_suppression": "rapid_flap",
    "suppress_multiple_macs": "rapid_flap",
    "trigger_multiple_suppress_restore_cycles": "rapid_flap",
}

_PW_TRIGGERS = {
    "spirent_pw_traffic", "spirent_ac_to_pw", "spirent_pw_to_pw",
    "spirent_evpn_to_pw", "spirent_pw_to_evpn", "spirent_pw_then_ac",
}

_EVPN_PEER_TRIGGERS = {
    "spirent_remote_pe", "spirent_ac_to_evpn", "spirent_evpn_to_ac",
    "spirent_evpn_to_pw", "spirent_pw_to_evpn",
    "spirent_inject_rt2",
    # G1/G4 additions -- all require the Spirent EVPN peer to be Established.
    "spirent_evpn_seq_race", "spirent_sanction_flap",
    "spirent_remote_seq_updates",
}

# Verbs handled directly by ``_run_spirent_phase_actions`` (setup.spirent[]
# and cleanup.spirent[]). When a recipe places one of these as
# trigger.action, the trigger executor's fallback routes it through the same
# dispatcher so recipes stay expressive without a parallel ACTION_TRIGGER_MAP.
_SPIRENT_PHASE_TRIGGER_VERBS = {
    "create_l2_device", "protocol_start", "protocol_stop", "remove_device", "wait",
    "inject_rt2", "inject_rt4", "inject_rt1_per_es", "inject_rt1_per_evi",
    "withdraw_rt4",
}

_EVPN_FALLBACK = "HA_TEST_ELAN"

# ---------------------------------------------------------------------------
# Time budgets (seconds). Override via env vars for slow CI / lab environments.
# These replace previously hardcoded values and the undefined `_pw_budget`
# variable that referenced PW recovery timeouts inside the trigger pre-check.
# ---------------------------------------------------------------------------

_PW_MOVE_BUDGET_SEC: int = int(os.environ.get("MAC_MOB_PW_MOVE_BUDGET_SEC", "60"))
_BGP_RECOVERY_BUDGET_SEC: int = int(os.environ.get("MAC_MOB_BGP_RECOVERY_BUDGET_SEC", "60"))
_SETUP_SPIRENT_DEFAULT_WAIT_SEC: int = int(
    os.environ.get("MAC_MOB_SPIRENT_SETUP_WAIT_SEC", "5"),
)
_SETUP_SPIRENT_MAX_WAIT_SEC: int = int(
    os.environ.get("MAC_MOB_SPIRENT_SETUP_MAX_WAIT_SEC", "30"),
)

# ---------------------------------------------------------------------------
# Per-scenario config provisioning -- auto-configure DUT before each scenario
# ---------------------------------------------------------------------------

SCENARIO_CONFIG_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "sticky_test": {
        "description": "Enable sticky-interface on AC1 for sticky MAC enforcement",
        "config_template": (
            "network-services evpn instance {evpn_name} "
            "interface {ac1_interface} sticky-interface enabled"
        ),
        "rollback_template": (
            "no network-services evpn instance {evpn_name} "
            "interface {ac1_interface} sticky-interface"
        ),
        "check_command": (
            "show config network-services evpn instance {evpn_name} "
            "| flatten | include sticky-interface | no-more"
        ),
        "check_pass_pattern": "sticky-interface enabled",
        "needs_mac_relearn": True,
    },
}


__all__ = [
    "SUITE_ROOT", "MANIFEST_PATH", "RESULTS_DIR", "ACTIVE_SESSION",
    "CORRECTIONS_PATH",
    "ACTION_TRIGGER_MAP", "_PW_TRIGGERS", "_EVPN_PEER_TRIGGERS",
    "_SPIRENT_PHASE_TRIGGER_VERBS", "_EVPN_FALLBACK",
    "_PW_MOVE_BUDGET_SEC", "_BGP_RECOVERY_BUDGET_SEC",
    "_SETUP_SPIRENT_DEFAULT_WAIT_SEC", "_SETUP_SPIRENT_MAX_WAIT_SEC",
    "SCENARIO_CONFIG_REQUIREMENTS",
]
