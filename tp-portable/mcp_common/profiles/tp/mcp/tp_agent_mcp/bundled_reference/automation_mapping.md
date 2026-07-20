# Mapping TP TCs to /TEST recipes

When importing a generated test plan into `/TEST create`:

1. Read `~/SCALER/TEST/tp/<EPIC>/manifest.json` and `test_plan_<EPIC>.md`.
2. For each selected `TC-NNN`, copy:
   - Test Name -> `recipe.name` suffix or phase label
   - Test Steps -> ordered `phases[].show_commands`, config steps, or orchestrator calls
   - Pass Criteria -> parser expectations / assertions
3. Set `recipe.source_tp` to the manifest path or epic id; set `recipe.traceability`:
   - `source_epic`, `source_tc`, `source_user_story` (if referenced in TC title/body)
   - `quality_gate_id` = request_id or manifest timestamp
4. Run DNOS syntax validation (`search_cli_docs`, `validate_config`, live `commit check` + `rollback 0`) before saving the recipe.
5. Attach `debug_layers` when the epic is dataplane-heavy (EVPN VPLS SI, etc.) per `/TEST` command rules.
