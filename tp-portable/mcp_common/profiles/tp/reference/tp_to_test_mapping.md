# TP-to-TEST Category Mapping

Maps each TP Checklist category to the appropriate `/TEST` automation type,
sub-commands, prerequisite checks, and snapshot commands.

## Category Mappings

### Interface Types/Services
- **Automation Type:** `traffic_test`
- **/TEST Sub-command:** `/TEST traffic <EPIC> --interface-matrix`
- **Prerequisite Checks:** Interface operstate UP, bundles configured, VLANs provisioned
- **Snapshot Commands:** `show interfaces description`, `show interfaces counters`, `show system npu-resources`
- **Recipe Pattern:** For each interface type: apply config, send traffic, verify counters, check throughput

### Sanity
- **Automation Type:** `config_apply`
- **/TEST Sub-command:** `/TEST sanity <EPIC>`
- **Prerequisite Checks:** Feature enabled, basic config present
- **Snapshot Commands:** `show config | filter <feature>`, `show system alarms`
- **Recipe Pattern:** Enable feature, verify ON state, disable, verify OFF state, re-enable

### CLI
- **Automation Type:** `cli_verify`
- **/TEST Sub-command:** `/TEST cli <EPIC>`
- **Prerequisite Checks:** Device reachable, CLI responsive
- **Snapshot Commands:** `show config compare`, `show system core-dumps`
- **Recipe Pattern:** For each CLI command: enter config, show config compare, commit, verify, rollback

### Negative Testing
- **Automation Type:** `cli_verify`
- **/TEST Sub-command:** `/TEST negative <EPIC>`
- **Prerequisite Checks:** Same as CLI
- **Snapshot Commands:** `show system core-dumps`, `show system alarms`
- **Recipe Pattern:** Apply invalid config, verify rejection/error message, confirm no crash

### Various RIBs
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST rib <EPIC>`
- **Prerequisite Checks:** Routes installed, RIB populated
- **Snapshot Commands:** `show route summary`, `show route forwarding-table`, `show bgp summary`
- **Recipe Pattern:** Check RIB entry, verify FIB programming, check across VRFs

### System Resources
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST resources <EPIC>`
- **Prerequisite Checks:** Feature loaded, baseline captured
- **Snapshot Commands:** `show system npu-resources`, `show system details`, `show system memory`
- **Recipe Pattern:** Capture baseline, apply feature config, measure delta, compare thresholds

### DNOR
- **Automation Type:** `manual_only`
- **/TEST Sub-command:** N/A (DNOR tests require DNOR cluster access)
- **Notes:** Flag for manual execution, provide verification checklist

### IPv4/IPv6
- **Automation Type:** `traffic_test`
- **/TEST Sub-command:** `/TEST dual-stack <EPIC>`
- **Prerequisite Checks:** IPv4 and IPv6 addresses configured, routes present
- **Snapshot Commands:** `show route ipv4 summary`, `show route ipv6 summary`
- **Recipe Pattern:** Test with IPv4 traffic, test with IPv6 traffic, test dual-stack

### Counters
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST counters <EPIC>`
- **Prerequisite Checks:** Counters cleared, traffic generators ready
- **Snapshot Commands:** `show interfaces counters`, `show system npu-resources`
- **Recipe Pattern:** Clear counters, send traffic, verify increment, compare before/after

### Logs/Traces
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST logs <EPIC>`
- **Prerequisite Checks:** Logging enabled
- **Snapshot Commands:** `show file log routing_engine/system-events.log | tail 50`
- **Recipe Pattern:** Trigger event, grep logs for expected message, verify no errors

### Traps
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST traps <EPIC>`
- **Prerequisite Checks:** SNMP trap receiver configured
- **Snapshot Commands:** `show snmp trap-host`, `show snmp statistics`
- **Recipe Pattern:** Trigger trap condition, verify trap sent, check trap content

### HA
- **Automation Type:** `ha_trigger`
- **/TEST Sub-command:** `/TEST ha <EPIC>`
- **Prerequisite Checks:** HA pair configured, standby ready, traffic flowing
- **Snapshot Commands:** Before/after: `show system`, `show bgp summary`, `show system alarms`, `show system core-dumps`, `show interfaces description`
- **Recipe Pattern:** Take before snapshot, trigger HA event, poll recovery, take after snapshot, compare 14 layers

### SNMP
- **Automation Type:** `cli_verify`
- **/TEST Sub-command:** `/TEST snmp <EPIC>`
- **Prerequisite Checks:** SNMP agent configured
- **Snapshot Commands:** `show snmp statistics`, `show snmp mib-walk`
- **Recipe Pattern:** Query MIB OID, verify value, set via SNMP, verify change

### System Events
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST events <EPIC>`
- **Prerequisite Checks:** Syslog configured
- **Snapshot Commands:** `show system alarms`, `show system events`
- **Recipe Pattern:** Trigger event, verify alarm raised, verify severity, check auto-clear

### Netconf
- **Automation Type:** `config_apply`
- **/TEST Sub-command:** `/TEST netconf <EPIC>`
- **Prerequisite Checks:** NETCONF service enabled, port 830 reachable
- **Snapshot Commands:** `show system services netconf`
- **Recipe Pattern:** Get-config, edit-config, commit, verify via CLI and get-config

### GNMI
- **Automation Type:** `config_apply`
- **/TEST Sub-command:** `/TEST gnmi <EPIC>`
- **Prerequisite Checks:** gNMI service enabled, port 50051 reachable
- **Snapshot Commands:** `show system services gnmi`
- **Recipe Pattern:** Subscribe, set, get, verify via CLI

### Scale
- **Automation Type:** `scale_ramp`
- **/TEST Sub-command:** `/TEST scale <EPIC>`
- **Prerequisite Checks:** Sufficient resources, traffic generators ready
- **Snapshot Commands:** `show system npu-resources`, `show system memory`, `show system details`
- **Recipe Pattern:** Ramp up (10%, 25%, 50%, 75%, 100%), measure at each level, check resource usage

### Load + Stress
- **Automation Type:** `scale_ramp`
- **/TEST Sub-command:** `/TEST stress <EPIC>`
- **Prerequisite Checks:** Same as Scale + sustained traffic capability
- **Snapshot Commands:** Same as Scale + `show system cpu`, process memory
- **Recipe Pattern:** Apply max load, sustain for duration, monitor stability, check for leaks

### Upgrade/Downgrade
- **Automation Type:** `upgrade_cycle`
- **/TEST Sub-command:** `/TEST upgrade <EPIC>`
- **Prerequisite Checks:** Target image available, backup config saved
- **Snapshot Commands:** `show system version`, `show config | hash`, before/after diffs
- **Recipe Pattern:** Save config, upgrade, verify feature state, downgrade, verify rollback

### Defaults
- **Automation Type:** `config_apply`
- **/TEST Sub-command:** `/TEST defaults <EPIC>`
- **Prerequisite Checks:** Clean config state
- **Snapshot Commands:** `show config | filter <feature>`, `show running-config`
- **Recipe Pattern:** Check default values, modify, verify non-default, reset, verify default restored

### VRF Testing
- **Automation Type:** `traffic_test`
- **/TEST Sub-command:** `/TEST vrf <EPIC>`
- **Prerequisite Checks:** VRFs configured, route targets set
- **Snapshot Commands:** `show route vrf <name>`, `show bgp vrf <name> summary`
- **Recipe Pattern:** Test feature in default VRF, test in custom VRF, test cross-VRF

### Logs Rotation
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST log-rotation <EPIC>`
- **Prerequisite Checks:** Logging enabled
- **Snapshot Commands:** `show file log`, file sizes
- **Recipe Pattern:** Fill log to rotation threshold, verify rotation occurs, verify old logs archived

### Sanitizer
- **Automation Type:** `show_compare`
- **/TEST Sub-command:** `/TEST sanitizer <EPIC>`
- **Prerequisite Checks:** Sanitizer enabled (if available)
- **Snapshot Commands:** `show system sanitizer`, `show system core-dumps`
- **Recipe Pattern:** Run feature operations, check sanitizer output, verify no violations

## Automation Type Definitions

| Type | Description | Recipe Template |
|------|-------------|-----------------|
| `cli_verify` | Apply config, verify CLI output matches expected | `recipe_cli_verify.json` |
| `ha_trigger` | Take snapshots, trigger HA event, poll recovery, compare | `recipe_ha_trigger.json` |
| `traffic_test` | Configure, start traffic, measure, verify counters | `recipe_traffic_test.json` |
| `config_apply` | Apply config block, commit, verify state | `recipe_config_apply.json` |
| `show_compare` | Run show commands, parse output, compare against expected | `recipe_show_compare.json` |
| `scale_ramp` | Incrementally increase load, measure at each level | `recipe_scale_ramp.json` |
| `upgrade_cycle` | Full upgrade/downgrade with before/after comparison | `recipe_upgrade_cycle.json` |
| `manual_only` | Cannot be automated, generate checklist only | N/A |

## Feature Mapping: EVPN-SI IRB / IP Mobility

Applies to:

- `SW-228552` -- EVPN-SI IRB routing component
- `SW-241473` -- EVPN-SI IRB datapath component
- parent/related epics: `SW-82446`, `SW-178814`, `SW-174736`, `SW-178648`, `SW-183400`

Always read:

- `~/.cursor/skills/evpn-si-irb-mobility/SKILL.md`
- `~/.cursor/skills/evpn-si-irb-mobility/sections/scenario-matrix.md`
- `~/.cursor/skills/evpn-si-irb-mobility/sections/arp-nd-punt-rules.md`
- `~/.cursor/skills/evpn-si-irb-mobility/sections/show-commands.md`
- `~/.cursor/skills/evpn-si-irb-mobility/sections/mobility-rules.md`
- `~/.cursor/tp-reference/evpn_proxy_arp_sources.md`

### Category to Automation Mapping

| TP Category | Automation Type | Required `/TEST` hints |
|---|---|---|
| Sanity | `traffic_test` | DNAAS teach/preflight, EVPN-SI EVI present, IRB present, PW installed |
| Interface Types/Services | `traffic_test` | AC vs PW vs remote EVPN source roles; traffic source encoded per scenario |
| CLI | `cli_verify` or `config_apply` | Validate IRB service lifecycle CLI: add IRB to a service, remove IRB, move IRB between services, no-command, rollback, show config. For EVPN IRB hierarchy, CLI coverage must include behavioral RUN proof for `router-interface`, `default-gateway`, `host-routes`, and `irb-mac-ip`; commit-check alone is insufficient for pass/fail. |
| Negative Testing | `cli_verify` or `traffic_test` | Proxy-ARP never replies toward PW; PW MAC-IP never advertised as RT-2 |
| Various RIBs | `show_compare` | EVPN RT-2 presence/absence, VPLS A-D state, route withdrawal |
| Counters | `show_compare` | Proxy-ARP rx/tx/xray counters tagged `CHEATSHEET_DEBUG` unless live-validated |
| Logs/Traces | `show_compare` | rib-manager, fibmgrd, wb_agent proxy-ARP traces |
| HA | `ha_trigger` | Restart routing/fibmgrd/wb_agent/NCP/NCC with before/after MAC-IP and traffic proof |
| Scale | `scale_ramp` | Multi-EVI, multi-PW, multi-host MAC-IP table scale and modifier-stream traffic |
| Load + Stress | `scale_ramp` | Sustained AC/PW move loops and ARP/NDP load |
| Upgrade/Downgrade | `upgrade_cycle` | Config persistence across upgrade; SI+IRB validation survives reload |
| Defaults | `config_apply` | Default behavior with no IRB, IRB added, IRB removed, and IRB moved between services |
| Netconf/GNMI | `config_apply` | YANG path for router-interface/seamless-integration when available |
| System Resources | `show_compare` | MAC-IP table, fib-manager, NCP memory/counters before/after scale |
| Tech-Support / Sanitizer | `manual_only` or `show_compare` | Evidence collection; no traffic verdict unless live path is proven |

### EVPN IRB Hierarchy Behavioral Mapping

When a TP section mentions EVPN as IRB, IRB hierarchy options, `router-interface`,
`default-gateway`, `host-routes`, or `irb-mac-ip`, generate or improve the TP as
behavioral coverage, not parser-only coverage.

| Hierarchy option | `/TEST create` validation | `/TEST run` proof |
|---|---|---|
| `network-services bridge-domain instance <bd> router-interface irbX` | `cmd search`/CLI docs plus `commit check && rollback 0` for add/remove/move | BD owns the IRB attachment and illegal duplicate ownership is rejected cleanly |
| `network-services evpn instance <evi> router-interface irbX` | `commit check && rollback 0` for attach/no-attach/no-form | EVPN instance exposes IRB state and remains consistent with BD membership |
| `default-gateway enabled/disabled` | Syntax validated for both values | RT-2 evidence shows default-gateway extended-community only when enabled |
| `host-routes enabled/disabled` | Syntax validated for both values | Type-2 host-route evidence includes VRF label/RT context only when enabled |
| `irb-mac-ip enabled/disabled` | Syntax validated for both values | Local IRB MAC-IP route is generated/advertised only when enabled |

Packing rule: these may be one TC covering `CLI`, `Sanity`, and `Defaults` only
when each option has its own pass criterion and `/TEST` import hints separate
CREATE commit-check validation from RUN behavioral proof.

### IRB Service Lifecycle Mapping

When the user asks to add, remove, rebind, or move IRB between EVPN services,
keep the lifecycle test independent from PW/VPLS-source datapath logic. The
test may use an EVPN-SI capable service as the target, but the assertions are
IRB ownership and option behavior, not PW MAC-IP mobility.

| Lifecycle operation | `/TEST create` validation | `/TEST run` proof |
|---|---|---|
| Add IRB to service A | Add BD and EVPN `router-interface irbX`, commit-check, rollback | Service A owns `irbX`; config/show output reflects attachment and selected option values |
| Remove IRB from service A | Validate no-form for EVPN and BD router-interface, commit-check, rollback | Service A no longer exposes router-interface/default-gateway/MAC-IP evidence; no stale IRB state |
| Move IRB A -> B | Validate remove from A plus add to B in one candidate, commit-check, rollback | Exactly one service owns `irbX`; A is clean and B has expected option behavior |
| Rebind option matrix | Validate `default-gateway`, `host-routes`, and `irb-mac-ip` enabled/disabled | Current IRB owner shows only the enabled option evidence |
| Malformed lifecycle | Validate negative candidates with commit-check and rollback | Duplicate ownership, missing parent, invalid enum, non-existent IRB, and wrong hierarchy placement are rejected cleanly |

### Scenario Families

| Family | Expected TCs |
|---|---|
| No-IRB PW source | ARP/NDP from PW is flooded to ACs only; not learned; not punted; no proxy reply |
| IRB PW source | ARP/NDP from PW is flooded to ACs and punted to Routing; MAC-IP appears with `v>` |
| AC to PW move | Withdraw RT-2 for MAC and MAC-IP, uninstall ARP, send broadcast probe |
| PW to AC move | Uninstall PW ARP, advertise RT-2 for AC MAC-IP, send broadcast probe |
| PW to PW move | Last MAC wins, no BGP RT-2, no suppression count |
| Remote EVPN to PW | Remote entry replaced by PW source without illegal proxy reply |
| DGW anti-scenario | PW update for default-gateway MAC/IP is ignored |
| Proxy-ARP anti-scenario | No proxy-ARP/NDP response is sent toward VPLS PW |

### Bug-Derived Flow Sweep

For SW-228552/SW-241473, `/TP improve` must mine EVPN Proxy-ARP and EVPN VPLS
SI bug evidence before finalizing the plan. Promote a bug-derived pattern only
when it fits the IRB routing component or SW-241473 datapath enabler.

| Bug / catalog pattern | Standalone or multiplier | `/TEST` recipe requirement |
|---|---|---|
| Remote withdraw or `clear evpn mac-table` sequence regression (SW-263553 / local bug evidence) | Standalone Regression TC when the trigger is clear/withdraw | Prove monotonic MAC mobility sequence plus MAC-IP, RT-2, and FIB consistency after fallback |
| DP `is_pw` LIF marking and FibMgr DB selection risk | Standalone Negative/Trace TC | Prove PW-source L2N keeps PW context, uses `v>` MAC-IP, and never advertises RT-2 |
| Proxy-ARP/NDP reply toward PW | Negative invariant, can pack with trace TC only if same event proves both | Use xray/fibmgr/wb_agent evidence; keep cheat-sheet commands `CHEATSHEET_DEBUG` until live-validated |
| File-loaded PW/IRB scale matrix | Standalone Scale/Setup Integrity TC | Import matrix file, validate dedup fingerprints, chunked dry-run commit, smart DNAAS preflight, and modifier/range streams |
| Scale config delta while state exists | Standalone Load + Stress / Scale TC | Scale up/down, toggle IRB options, then prove no stale MAC-IP, RT-2, FIB, dirty candidate, or proxy-ARP state |
| Spirent/BLL EVPN-inject churn degradation | Infrastructure guard, not DNOS verdict TC | Preserve/recreate EVPN/VPLS infra devices after reconnect and mark infra loss separately from DNOS failure |

### MAC/IP Mobility Permutation Model

For SW-228552/SW-241473, the 14 design-doc B.11 rows plus anti-scenarios N1-N7
are the canonical base. Do not generate duplicate TCs for every category. Add
multiplier metadata to each TC and let `/TEST create` expand only the selected
runnable recipe dimensions.

| Axis | Values |
|---|---|
| Service mode | no IRB, IRB attached, IRB removed, IRB moved between services |
| Existing state | none, local AC, VPLS PW, remote EVPN RT-2, local+remote, PW+remote, DGW sticky, AC link down |
| New source | local AC, VPLS PW, remote EVPN RT-2, same-source refresh, AC link down |
| Message type | ARP request, ARP reply, gratuitous ARP, IPv6 NS/NA, refresh probe |
| Mobility direction | AC->PW, PW->AC, PW->PW, remote->PW, remote->AC, AC refresh, PW refresh, AC link down |
| Option state | `default-gateway`, `host-routes`, `irb-mac-ip` enabled/disabled |
| Scale/topology | single EVI, multi-EVI, multi-PW, PE role pair, AC interface variant |

Mandatory assertion surfaces for every mobility recipe:

- MAC table path flags.
- MAC-IP table `v` flag and source.
- BGP RT-2 advertise/withdraw/absence.
- Forwarding-table selected path.
- Mobility-history event order.
- Broadcast probe for AC->PW and PW->AC.
- Proxy-ARP/NDP no-reply-to-PW invariant.
- Counters/traces only when the TC claims those categories.

Dedup fingerprint:
`existing_state + new_event_source + message_type + service_mode + expected DB/BGP/FIB outcome`.

Category packing:

- `Sanity` owns canonical B.11 behavior.
- `Counters` and `Logs/Traces` pack only when captured from the same traffic event.
- `Negative Testing` stays separate for absence/drop/rejection outcomes.
- `HA`, `Scale`, `Load + Stress`, `Upgrade/Downgrade`, and `NETCONF/gNMI` multiply canonical scenarios; they do not redefine expected mobility behavior.

### `/TEST` Recipe Requirements

Every runnable recipe must include:

- `debug_layers.feature_context = "evpn-vpls-si-irb"`
- DNAAS preflight or teach-plan proof before Spirent traffic.
- Source-qualified expected traffic: AC, PW, or remote EVPN.
- Show-command provenance from `show-commands.md`.
- Debug-cheat-sheet commands only under `debug_layers`, not as canonical pass/fail syntax
  unless promoted to `LIVE_VALIDATED`.

### Dedup/Packing Guidance

Pack one TC across categories only when the same traffic event proves all of them.
Example: one AC-to-PW move can cover Sanity, Counters, and Logs/Traces if it has
separate pass criteria for MAC-IP table, counters, and trace signatures.

Do not pack across:

- AC-to-PW vs PW-to-AC
- no-IRB vs IRB
- ARP vs NDP when IPv6-specific NDP behavior is being asserted
- normal behavior vs negative anti-scenario
- traffic sanity vs HA restart
