# Recipe Schema v2 (backward-compatible)

Authoritative source of truth for `/TEST` recipe JSON files.

| Field | Path | Introduced | Status |
|-------|------|-----------|--------|
| v1 fields | everywhere you see today | schema v1 | UNCHANGED |
| `recipe_schema_version` | top-level | v2 | optional, recommended |
| `test_config` | top-level | v2 | optional; loaded by `TestConfiguration.from_recipe()` |
| `test_config.additional_pre_validations[]` | test_config | v2 | optional |
| `test_config.snapshot_expected_changes{}` | test_config | v2 | optional |
| `test_config.fsm_guards{}` | test_config | v2 | optional |

**Backward compatibility guarantee:** a recipe authored under v1 MUST load
cleanly under v2. `test_config` is optional; when absent, defaults from
`TestConfiguration()` are used. No orchestrator behaviour changes unless the
block is present.

## Top-Level Shape (v2)

```json
{
  "id": "TEST_<feature>_<kind>_<jira>",
  "name": "Human-readable title",
  "type": "functional|ha|regression|config|traffic",
  "feature": "evpn-mac-mobility|flowspec-vpn|...",
  "source": "jira:SW-XXXXXX",
  "jira_key": "SW-XXXXXX",
  "parent_category": "SW-XXXXXX",
  "created": "YYYY-MM-DD",
  "updated": "YYYY-MM-DD",

  "recipe_schema_version": 2,

  "device_requirements": {
    "type": "cluster|standalone|any",
    "features": ["evpn", "mpls"],
    "min_ncp_count": 1
  },

  "prerequisites": [
    {"id": "...", "check": "...", "fix_via": "..."}
  ],

  "phases": [
    {"name": "setup", "sub_commands": [], "timeout_sec": 120},
    {"name": "before_snapshot", "show_commands": [], "parsers": []},
    {"name": "trigger", "ha_command": "...", "ha_type": "process_restart"},
    {"name": "poll_recovery", "timeout_sec": 120, "poll_interval_sec": 10},
    {"name": "after_snapshot", "show_commands": []},
    {"name": "verify", "sub_commands": [], "trace_greps": []}
  ],

  "verdict": {"layers": 14, "thresholds": {}},

  "test_config": {
    "test_id": "TEST_<same-as-id>",
    "test_mode": "dnos_mode",
    "cluster_requirement": "any",
    "jira_component": "<team label on the parent Jira>",
    "owner": "<jira-user>",
    "additional_pre_validations": [
      {
        "type": "ShowCommandContains",
        "command": "show bgp summary",
        "substring": "Established",
        "device": "PE-4",
        "name": "bgp_up"
      }
    ],
    "snapshot_expected_changes": {
      "process_restart:ncc/0/routing_engine/bgpd": "INCREASE_BY(1)",
      "container_restart:ncc/0/routing_engine": "INCREASE_BY(1)",
      "new_core_dumps": "FORBIDDEN",
      "interface_oper_down:any": "INCREASE_BY_AT_MOST(2)",
      "alarm:any": "FORBIDDEN"
    },
    "fsm_guards": {
      "max_ssh_retries": 5,
      "max_spirent_reconnects": 3,
      "max_scenario_retries": 2,
      "max_heavy_ops_per_session": 1,
      "hard_timeout_sec": 900,
      "ssh_backoff_sec": 5,
      "spirent_backoff_sec": 5
    }
  }
}
```

## `test_config` Field Reference

### `test_id` (string, default `""`)
The globally unique test ID. Should match the top-level `id`. Used in logs,
verdict reports, and `active_test_session.json` so the orchestrator can
cross-reference.

### `test_mode` (enum, default `"dnos_mode"`)
- `"dnos_mode"` -- DUT runs DNOS, all validations run inside the routing
  container.
- `"baseos_mode"` -- DUT runs base OS (container-less). Skips DNOS-specific
  validations.

Enforced by `TestConfiguration._validate_literals()`. Invalid values raise
`TestConfigurationError` at load time.

### `cluster_requirement` (enum, default `"any"`)
- `"sa_only"` -- requires a standalone chassis (device type contains `"SA"`
  like `SA-36CD-S`, `SA-12P`).
- `"cl_only"` -- requires a cluster chassis (device type contains `"CL"`
  like `CL-86`, `CL-144`).
- `"any"` -- any resolved device works.

Matching is case-insensitive substring via
`cluster_requirement_matches(requirement, device_type)`. When the
orchestrator resolves the device, it MUST call `cfg.matches_device(...)`
before running prerequisites and abort with a clear message if False.

### `jira_component` (string, default `""`)
The Jira component label (e.g. `"flowspec-vpn"`, `"evpn-mac-mobility"`). Lands
in the verdict table and result SUMMARY.md for ownership lookup.

### `owner` (string, default `""`)
Jira username or email of the primary owner. Tagged in auto-generated
notifications / Jira comments.

### `additional_pre_validations` (list of spec dicts, default `[]`)
Each entry is a spec of the form `{"type": "<name>", ...kwargs}` that gets
deserialised into a `BaseValidation` via `load_validation_spec()` and
prepended to the first Action's pre-validation list by the orchestrator.

Built-in types (registered by `e2e_lite/__init__.py`):

| `type`                 | Class                   | Required kwargs                 |
|------------------------|-------------------------|---------------------------------|
| `ShowCommandContains`  | `ShowCommandContains`   | `command`, `substring`, `device`|
| `WaitForCondition`     | `WaitForCondition`      | `predicate_name` (via registry) |
| `CallableValidation`   | `CallableValidation`    | `predicate_name` (via registry) |

Orchestrators can register custom types at startup via
`register_validation_type("MyValidation", MyValidationClass)` -- see
`test_config.py` docstring.

Unknown `type` or kwargs that the class constructor rejects raise
`TestConfigurationError` at load time. This means bad recipes fail the linter
instead of causing mid-run surprises.

### `snapshot_expected_changes` (dict of rules, default `{}`)

Declares the deltas between pre/post `SystemSnapshot` captures that the
orchestrator SHOULD see. Any counter / event that changes and is NOT covered
by a rule -> `SnapshotDiff.violations` -> test fails with a clear message.

Key format: `<metric_family>:<identifier>` (e.g. `process_restart:routing:bgpd`,
`alarm:any`, `new_core_dumps`). `:any` is a wildcard matching any identifier
within the family.

Rule DSL (parsed by `system_snapshot.parse_rule`):

| Rule                          | Meaning                                   |
|-------------------------------|-------------------------------------------|
| `UNCHANGED`                   | after == before (strict)                  |
| `ALLOWED`                     | any change allowed, no assertion          |
| `FORBIDDEN`                   | after MUST NOT introduce new items        |
| `EXACTLY(n)`                  | after == n (integer value, not delta)     |
| `INCREASE_BY(n)`              | after - before == n                       |
| `INCREASE_BY_AT_LEAST(n)`     | after - before >= n                       |
| `INCREASE_BY_AT_MOST(n)`      | after - before <= n                       |
| `INCREASE_BY` (no arg)        | `INCREASE_BY(1)` (sugar)                  |

Detailed semantics in `system_snapshot.py` -- this section is a quick reference.

### `fsm_guards` (dict, default: `RecoveryGuards()`)

Replaces the suite-scoped FSM's guards when the test runs. All fields
optional; unspecified fields keep the `RecoveryGuards` dataclass defaults.

| Field                      | Default | Purpose                                                    |
|----------------------------|---------|------------------------------------------------------------|
| `max_ssh_retries`          | 5       | Max reconnects against the DUT SSH session                 |
| `max_spirent_reconnects`   | 3       | Max Lab Server session recreations                         |
| `max_scenario_retries`     | 2       | Per-scenario retries in scenario_runner                    |
| `max_heavy_ops_per_session`| 1       | Cap on reboots / container restarts                        |
| `hard_timeout_sec`         | 900     | Total recovery budget across the whole suite               |
| `ssh_backoff_sec`          | 5       | Starting backoff between SSH retries                       |
| `spirent_backoff_sec`      | 5       | Starting backoff between Spirent reconnects                |

Unknown fields raise `TestConfigurationError` at load time so typos fail loud.

## Loading Pattern (orchestrator template)

```python
from e2e_lite import TestConfiguration, RecoveryFsmLite

def load_and_apply(recipe_path: Path, device_type: str, fsm: RecoveryFsmLite):
    cfg = TestConfiguration.from_recipe_file(recipe_path)

    if not cfg.matches_device(device_type):
        raise RuntimeError(
            f"{cfg.test_id}: requires cluster_requirement={cfg.cluster_requirement!r}, "
            f"but resolved device is {device_type!r}"
        )

    cfg.apply_guards_to(fsm)
    return cfg
```

Pre-validations returned by `cfg.additional_pre_validations` are expected to
be prepended to the first action's `pre_validations` list by the
orchestrator. They run before the action's own pre-checks.

## Linter Expectations

A recipe linter should:

1. Parse the file as JSON (fail on syntax errors).
2. Reject recipes declaring `recipe_schema_version` > the version understood by
   the running e2e_lite (graceful forward-incompat gate).
3. When `test_config` is present, build it via `TestConfiguration.from_recipe()`
   and let `TestConfigurationError` propagate with the file path prefixed.
4. Warn (not error) when a v2 field is used but `recipe_schema_version` is
   unset -- suite owners should bump explicitly.

## Suite Manifest Metadata

`suite_manifest.json` MAY add a top-level `recipe_schema_version` key to
declare the version used by all recipes in the suite:

```json
{
  "suite_id": "...",
  "recipe_schema_version": 2,
  "tests": [ ... ]
}
```

Suites that want to enforce `test_config` across every recipe can add an
optional `test_config_required: true` flag -- the linter then errors when a
listed recipe is missing the block.

## Migration Notes

| From | To | Action |
|------|----|--------|
| v1 recipe, no `test_config` | v2 | Add `recipe_schema_version: 2`. No other changes required. |
| v1 recipe, ad-hoc "expected changes" in phase docs | v2 `snapshot_expected_changes` | Move rules into `test_config.snapshot_expected_changes` as DSL strings. |
| Hard-coded `RecoveryGuards()` in the orchestrator | v2 `fsm_guards` | Move overrides into the recipe so they're reproducible. |
| Device type guards in orchestrator code | v2 `cluster_requirement` | Delete the guard; the loader enforces it. |

## Examples

### Minimal v2 upgrade (no behaviour change)

```json
{
  "id": "TEST_foo",
  "recipe_schema_version": 2,
  "phases": [...]
}
```

### Full v2 recipe extract

See `scaler/TEST/catalog/evpn_mac_mobility_SW204115/tests/<test>/recipe.json`
examples once migrated. A full sample is also embedded in `test_config.py`'s
module docstring.
