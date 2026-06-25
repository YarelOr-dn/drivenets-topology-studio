"""Orchestration package for the EVPN MAC Mobility suite (SW-204115).

Splits the former monolithic ``mac_mobility_orchestrator.py`` into focused
modules. Each module keeps its public functions importable from the top-level
``mac_mobility_orchestrator`` module via a backward-compat re-export so that
existing CLI invocations and any legacy importers keep working unchanged.

Modules (populated incrementally per refactor slice):
  spirent_integration  -- /SPIRENT <-> /TEST sync mandate (auto_invoke_spirent_sync,
                          _requires_spirent, _resolve_spirent_vlan, _dev_ip)
  session_io           -- active_test_session.json writers + runtime corrections
  reporting            -- results writer, repro-steps generator, live failure detector
  runtime_context      -- resolve_runtime_params + discovery helpers
  recipe_runtime       -- recipe expansion, substitution, phase running, validation
  scenario_runner      -- execute_scenario + per-phase helpers
  test_runner          -- execute_test + per-phase helpers

Public API remains: ``from mac_mobility_orchestrator import <name>``.
"""
