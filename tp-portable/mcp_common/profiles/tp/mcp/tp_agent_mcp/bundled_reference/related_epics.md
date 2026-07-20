# Related epics and enablers (TP context)

When planning tests for epic **SW-XXXX**, also consider:

- **Datapath (DP)** enabler epics that must be covered in integration or called out as prerequisites.
- **Infra / platform** epics (restart behavior, packaging, upgrade paths).
- **Neighbor Manager / BGP / EVPN** cross-epic dependencies.
- **Parent initiative** or **child** stories that change acceptance scope.

## How to use this in a TP

1. List each related epic key in `linked_epics` / `related_epics_data` from MCP prefetch.
2. For each enabler, either add explicit TCs or document **skip with reason** in the quality gate report.
3. When converting to `/TEST`, copy keys into recipe `traceability.linked_epics`.

Override this file in `~/.cursor/tp-reference/related_epics.md` for team-specific correlation rules.
