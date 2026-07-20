# Expected Behavior -- `EVPN AC-to-AC (local->local) MAC/IP mobility counting: null-ESI = UPDATE_LOCAL (not counted) vs distinct-ESI = MOVE_LOCAL_TO_LOCAL (counted)`

- **feature_id:** `evpn_ac2ac_mac_ip_mobility_counting`
- **primary device:** `YOR_CL_PE-4`
- **epics:** SW-228552
- **captured at:** 2026-07-09T14:39:06Z
- **live-validated at:** 2026-07-09T14:39:06Z

For EVPN (incl. EVPN-VPLS-SI IRB) services, a single-homed NULL-ESI AC-to-AC move of the same MAC (e.g. ge100-x.601 -> ge100-x.602) is treated as UPDATE_LOCAL: the owning interface follows the host for BOTH MAC and MAC-IP, but the move is NOT counted -- RT-2 Sequence number is not bumped, no Mobility History block is printed, mac-table suppress is empty, and mac-mobility-redis-count stays 0. Move counting (MOVE_LOCAL_TO_LOCAL) happens ONLY when the ESI or path-type changes: assigning a DISTINCT ESI to each AC makes the same move bump the Sequence number 0->1, populate the MAC Mobility 'Moves per Detection Window' counter (=1), print a Mobility History block, and increment mac-mobility-redis-count 0->2. Therefore moved=0 on a null-ESI AC-to-AC move is CORRECT behavior, not a bug. Live-proven 2026-07-09 on PE-4 EVPN_CLTEST_IRB EVI 203 build 9b1112366c98.

## Configuration Paths

| Hierarchy | Syntax | Purpose | Live Status |
|---|---|---|---|
| network-services multihoming interface <if> | network-services multihoming interface <if> esi arbitrary value <9-hex-octets> | Assign a Type-0 arbitrary ESI to an AC. Value is 9 octets (e.g. 00:00:00:00:00:00:00:06:01); DNOS prepends the type byte so show renders 10 octets. 10-octet value is REJECTED. Distinct ESI per AC is what turns an AC-to-AC move into a COUNTED MOVE_LOCAL_TO_LOCAL. | LIVE_VALIDATED |
| network-services multihoming interface <if> | network-services multihoming interface <if> redundancy-mode <all-active|single-active|port-active> | Redundancy mode for the ES; single-active used in the repro. Adding esi+redundancy-mode forms a single-homed ES after a brief DF-election transient. | LIVE_VALIDATED |
| delete-form | no network-services multihoming interface <if> | Delete via dnos_atomic_commit needs a LEADING full-path 'no'; mid-hierarchy 'no interface' is rejected as Unknown word 'no'. | LIVE_VALIDATED |

## Show Commands (live-validated)

_Live Status legend: **LIVE_VALIDATED** = accepted + real data; **LIVE_VALID_NO_ENTRIES** = valid command, empty table / object-not-found now; **LIVE_EMPTY** = blank output; **LIVE_INCOMPLETE** = valid stem, missing argument (auto `?`-discovery ran -- see Syntax Discovery below); **LIVE_REJECTED** = wrong command (fix syntax); **LIVE_ERROR** = valid command, run failed (auth/transport/timeout/crash -- retry)._

| Command | Device Role | Expected Keywords | Live Status |
|---|---|---|---|
| show evpn instance EVPN_CLTEST_IRB mac-table detail | no-more | PE | MAC address, Protocol, Interface | LIVE_VALIDATED |
| show evpn mac-ip-table instance EVPN_CLTEST_IRB | no-more | PE | IP Address, Source | LIVE_VALIDATED |
| show dnos-internal routing evpn mac-mobility-redis-count | no-more | PE | entries in redis | LIVE_VALIDATED |
| show evpn instance EVPN_CLTEST_IRB mac-table suppress | no-more | PE |  | LIVE_EMPTY |
| show ethernet-segments detail | no-more | PE | ESI, Interface | LIVE_VALIDATED |

## Trace Patterns

| Process | Pattern | Meaning | Expected When |
|---|---|---|---|
| fibmgrd | MOVE_LOCAL_TO_LOCAL | Kernel-level confirmation of a COUNTED local-to-local move (distinct ESI). Absent for null-ESI UPDATE_LOCAL. | pass |

## Cross-Feature Interactions

| Scenario | Expected | Anti-Pattern |
|---|---|---|
| Single-homed null-ESI AC-to-AC move of same MAC (.601 -> .602) | UPDATE_LOCAL: MAC + MAC-IP owner interface follow the host; Sequence number NOT bumped (no seq line for the host MAC); no Mobility History block; mac-table suppress empty; mac-mobility-redis-count stays 0. | Reporting moved=0 / seq=0 as a bug. It is CORRECT for null-ESI AC-to-AC. Do NOT open a defect. |
| Distinct-ESI AC-to-AC move of same MAC (.602 ESI-B -> .601 ESI-A) | MOVE_LOCAL_TO_LOCAL (counted): Sequence number 0->1; MAC Mobility 'Moves per Detection Window' = 1; Mobility History block (Local <ac1> #seq0 -> Local <ac2> #seq1); mac-mobility-redis-count 0->2. | Expecting the counter to move for a null-ESI setup. Counting requires an ESI/path-type change. |
| IP vs MAC move counter on the first counted move | MAC 'Moves per Detection Window' = 1 while IP 'Moves per Detection Window' = 0, even though IP Sequence bumped to 1 and IP Mobility History recorded the move. | Treating the IP window-counter lag as MAC/IP inconsistency without noting the IP Sequence + IP Mobility History DID update. |

## Sources

- **[agent_evidence]** Repro A live: null-ESI .601->.602 = UPDATE_LOCAL, moved=0/seq=0/redis=0 -- fetched None
- **[agent_evidence]** Repro B live: distinct-ESI .602->.601 = MOVE_LOCAL_TO_LOCAL, seq0->1/Moves-per-Window=1/redis0->2 -- fetched None

