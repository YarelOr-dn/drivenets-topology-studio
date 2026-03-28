# EVPN MAC Mobility Test Automation (SW-204115)

Test category: [SW-204115](https://drivenets.atlassian.net/browse/SW-204115) -- QA | EVPN (ELAN) Seamless-integration | MAC Mobility.

This suite implements ten **Testing Task** recipes (SW-205160 through SW-205199) plus shared discovery, prerequisites, and a master orchestrator.

## Layout

| Path | Purpose |
|------|---------|
| `suite_manifest.json` | Index of all test IDs and recipe paths |
| `mac_mobility_orchestrator.py` | CLI: discover, prereq, list, dry-run, execute (show only) |
| `device_discovery.py` | Builds `DeviceContext` from `show` output |
| `config_generator.py` | Incremental config snippets; **IRB + seamless-integration forbidden** |
| `prerequisite_engine.py` | Per-test prerequisite table |
| `shared/` | Parsers, trigger planning, verifiers |
| `tests/*/recipe.json` | JSON recipes |
| `results/` | Run outputs |

## DNOS syntax

- Validate operational commands with `search_cli_docs` before use.
- Process restarts use container names such as `routing:bgpd`, `routing:fibmgrd` (see `dnos-cli-completions.json`).
- HA triggers in `tests/ha_mac_mobility/recipe.json` follow the same pattern as `TEST_evpn_elan_ha_SW248907`.

## Running

```bash
cd scaler/TEST/catalog/evpn_mac_mobility_SW204115
export PYTHONPATH="$(pwd)"
python3 mac_mobility_orchestrator.py --device PE-4 --discover
python3 mac_mobility_orchestrator.py --device PE-4 --list
python3 mac_mobility_orchestrator.py --device PE-4 --prereq TEST_mac_mob_basic_SW205160
python3 mac_mobility_orchestrator.py --device PE-4 --run TEST_mac_mob_basic_SW205160 --dry-run
```

Integrate real CLI output by setting `DNOS_SHOW_HELPER` to an executable that accepts `device` and `command` arguments, or run under Cursor with Network Mapper MCP and `DNOS_USE_MCP=1` for traffic method detection.

## References

- SW-192019: MAC move handling (EVPN-VPLS)
- SW-194578: Sticky MAC handling
- `~/.cursor/rules/dnos-test-automation-blueprint.mdc`
- `~/SCALER/TEST/catalog/TEST_evpn_elan_ha_SW248907/` (HA pattern reference)

## No emojis

Status prefixes: `[OK]`, `[WARN]`, `[ERROR]`, `[INFO]`.
