# Expected Behavior -- `EVPN mac-ip-table-limit + threshold system events (EVPN_MAC_IP_TABLE_THRESHOLD_EXCEEDED/CLEARED) incl. via VPLS-PW`

- **feature_id:** `evpn_mac_ip_table_limit_threshold_event`
- **primary device:** `PE-1`
- **epics:** SW-228552
- **captured at:** 2026-07-09T15:24:08Z
- **live-validated at:** 2026-07-09T15:24:08Z

Per-service EVPN mac-ip-handling mac-ip-table-limit (min 16). fib-manager fires system event EVPN_MAC_IP_TABLE_THRESHOLD_EXCEEDED (WARNING, group fib-manager) when the service instance mac-ip-table crosses 90% of the configured limit, and EVPN_MAC_IP_TABLE_THRESHOLD_CLEARED when it drops below 85% (hysteresis). The limit is WARN-ONLY, not a hard cap: learning continues past the limit. PW-sourced (v flag) mac-ips learned over a VPLS-PW DO count toward the limit and DO trigger the event. Box-wide variants: TOTAL_EVPN_MAC_IP_TABLE_THRESHOLD_EXCEEDED/CLEARED. Verify occurrences in the fibmgrd trace (FibMgrMacIpTableSysEvents.cpp onServiceInstanceMacIpTableThresholdExceeded/Cleared) or a configured syslog server -- NOT via `show system logging system-events <NAME>` which shows only the event catalog/schema. Live-proven PE-1 EVPN_SI_VPLS_1 2026-07-09: limit 16, 20 PW hosts injected, Exceeded value=14 then Cleared value=12.

## Configuration Paths

| Hierarchy | Syntax | Purpose | Live Status |
|---|---|---|---|
| network-services evpn instance <svc> mac-ip-handling | network-services evpn instance <svc> mac-ip-handling mac-ip-table-limit <16-1048575> | Per-service MAC-IP table limit (min 16). Threshold event fires at 90%, clears at 85%. Warn-only (not a hard cap). | LIVE_VALIDATED |

## Show Commands (live-validated)

_Live Status legend: **LIVE_VALIDATED** = accepted + real data; **LIVE_VALID_NO_ENTRIES** = valid command, empty table / object-not-found now; **LIVE_EMPTY** = blank output; **LIVE_INCOMPLETE** = valid stem, missing argument (auto `?`-discovery ran -- see Syntax Discovery below); **LIVE_REJECTED** = wrong command (fix syntax); **LIVE_ERROR** = valid command, run failed (auth/transport/timeout/crash -- retry)._

| Command | Device Role | Expected Keywords | Live Status |
|---|---|---|---|
| show evpn instance EVPN_SI_VPLS_1 mac-ip-table | no-more | PE | IP Address, Source | LIVE_VALIDATED |
| show file traces routing_engine/fibmgrd_traces | include regex "MacIpTableThreshold" | no-more | PE | ThresholdExceeded, ServiceInstance, limit | LIVE_VALIDATED |
| show system logging system-events group fib-manager event EVPN_MAC_IP_TABLE_THRESHOLD_EXCEEDED | no-more | PE | service_name, limit, numeric_value | LIVE_VALIDATED |

## Trace Patterns

| Process | Pattern | Meaning | Expected When |
|---|---|---|---|
| fibmgrd | onServiceInstanceMacIpTableThresholdExceeded | Event fired: mac-ip count crossed 90% of limit for the service instance (incl PW v mac-ips). | pass |
| fibmgrd | onServiceInstanceMacIpTableThresholdCleared | Event fired: mac-ip count dropped below 85% of limit. | pass |

## Cross-Feature Interactions

| Scenario | Expected | Anti-Pattern |
|---|---|---|
| Cross the mac-ip-table-limit via MAC-IPs advertised over a VPLS-PW (remote hosts' ARP/ND snooped on the PW -> v mac-ips) | EVPN_MAC_IP_TABLE_THRESHOLD_EXCEEDED fires at 90% with correct service_name+limit; CLEARED at 85%. PW v mac-ips count toward the limit. | Assuming PW-sourced mac-ips are excluded from the limit -- they are included. |
| Verifying the event fired | Read fibmgrd trace (FibMgrMacIpTableSysEvents.cpp) or configured syslog. | Using `show system logging system-events <NAME>` to see occurrences -- it only prints the catalog/schema, not fired events. |
| Expecting the limit to block new mac-ip learning | Learning continues past the limit; the event is informational (WARNING). | Treating mac-ip-table-limit as a hard cap. |

## Sources

- **[agent_evidence]** Live PE-1 test: mac-ip limit threshold event via VPLS-PW PASSED -- fetched None

