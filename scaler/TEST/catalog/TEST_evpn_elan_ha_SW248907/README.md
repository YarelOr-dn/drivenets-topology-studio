# TEST_evpn_elan_ha_SW248907

**EVPN (ELAN) SI -- EVPN High-Availability**

- **Source:** [SW-248907](https://drivenets.atlassian.net/browse/SW-248907)
- **Type:** HA
- **Feature:** EVPN
- **Created:** 2026-03-19
- **Assignee:** Yarel Or

## Description

9 EVPN HA test scenarios from Jira SW-248907 covering BGP Graceful Restart,
LLGR, GR/LLGR failure timer expiry, process restarts (fib-manager, zebra/rib_manager,
neighbor-manager), MAC recovery, NCC switchover, and MAC move during GR window.

## Scenarios

| # | ID | Name | HA Type | Process |
|---|-----|------|---------|---------|
| 1 | SC01_bgp_graceful_restart | BGP Graceful Restart | process_restart | routing:bgpd |
| 2 | SC02_llgr | LLGR (Long-Lived Graceful Restart) | process_restart_extended | routing:bgpd |
| 3 | SC03_gr_llgr_failure | GR/LLGR Failure (Timer Expiry) | process_stop_extended | routing:bgpd |
| 4 | SC04_fibmgrd_restart | Process Restart -- fib-manager | process_restart | routing:fibmgrd |
| 5 | SC05_zebra_restart | Process Restart -- zebra (rib_manager) | process_restart | routing:rib_manager |
| 6 | SC06_neighbour_manager_restart | Process Restart -- neighbor-manager | process_restart | neighbour_manager |
| 7 | SC07_mac_recovery | MAC Recovery Post-Restart | process_restart | routing:bgpd |
| 8 | SC08_ncc_switchover | NCC / RE Switchover | ncc_switchover | N/A |
| 9 | SC09_mac_move_during_gr | MAC Move During Restart Window | process_restart + mac_move | routing:bgpd |

## Device Requirements

- **Type:** Cluster
- **Features:** EVPN, BGP L2VPN EVPN
- **Min NCP count:** 1
- **Requires:** Standby NCC (for SC08), EVPN instances, bridge-domain

## DNOS Process Name Mapping

The Jira ticket uses generic names. Validated DNOS process names:

| Jira name | DNOS process | Container | Restart command |
|-----------|-------------|-----------|-----------------|
| BGP | routing:bgpd | routing-engine | `request system process restart ncc {id} routing-engine bgpd` |
| fib-manager | routing:fibmgrd | routing-engine | `request system process restart ncc {id} routing-engine fibmgrd` |
| zebra | routing:rib_manager | routing-engine | `request system process restart ncc {id} routing-engine rib_manager` |
| neighbor-manager | neighbour_manager | management-engine | `request system process restart ncc {id} management-engine neighbour_manager` |

## Show Command Corrections

Commands from Jira that needed correction (validated via `search_cli_docs`):

| Jira command | Issue | Corrected DNOS command |
|-------------|-------|----------------------|
| `show evpn detail instance <name>` | Does not exist | `show evpn instance <name>` or `show network-services evpn <name>` |
| `show evpn mac-table evi <evi>` | `evi` keyword does not exist | `show evpn mac-table instance <name>` |

## Running

```bash
# All scenarios
python3 orchestrator.py --device PE-4 --all

# Specific scenario
python3 orchestrator.py --device PE-4 --scenario SC01_bgp_graceful_restart

# Dry run (print commands only)
python3 orchestrator.py --device PE-4 --all --dry-run

# Override EVPN instance name
python3 orchestrator.py --device PE-4 --all --evpn-name EVPN_ELAN_001

# Resume from a scenario
python3 orchestrator.py --device PE-4 --resume SC05_zebra_restart
```

## Estimated Duration

- Per scenario: 2-6 minutes
- LLGR scenarios: +10 minutes (timer hold-down)
- GR/LLGR failure: +15 minutes (both timers)
- Full suite: ~40-60 minutes

## Files

- `recipe.json` -- JSON test definition (source of truth)
- `orchestrator.py` -- Python orchestrator script
- `README.md` -- This file
- `results/` -- Run results (created per execution)
