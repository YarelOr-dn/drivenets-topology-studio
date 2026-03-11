# FlowSpec VPN Test Plan (SAFI 134)
# ==================================
# Feature: BGP FlowSpec VPN (ipv4-flowspec-vpn / ipv6-flowspec-vpn)
# Epic: FlowSpec VPN
# Author: Yor
# Date: January 2026
# Version: 1.0

---

## 1. Topology Overview

### Simplified Topology Diagram

```
                           ╔═══════════════════════════════════════════════════════════════╗
                           ║                   FLOWSPEC VPN TEST TOPOLOGY                   ║
                           ╚═══════════════════════════════════════════════════════════════╝

                                           ┌─────────────────┐
                                           │    SPIRENT      │
                                           │   (HW-114)      │
                                           │  Port 6:13      │
                                           │  100G Traffic   │
                                           └────────┬────────┘
                                                    │
                                     ┌──────────────┴──────────────┐
                                     │                             │
                                     ▼                             ▼
                        ┌────────────────────────┐    ┌────────────────────────┐
                        │         DUT            │    │         DN01           │
                        │      CL-408D           │    │     NCP-36CD-S         │
                        │      (PE-1)            │    │       (PE-2)           │
                        │                        │    │                        │
                        │  HW: 63/64/65/66/67/68 │    │  HW: 136 or 192        │
                        │                        │    │                        │
                        │  VRFs:                 │    │  VRFs:                 │
                        │  ├─ VRF1 (RT:65000:100)│    │  ├─ VRF1 (RT:65000:100)│
                        │  ├─ VRF_RED (200)      │    │  └─ VRF_RED (200)      │
                        │  └─ VRF_BLUE (300)     │    │                        │
                        │                        │    │                        │
                        │  BGP AS: 65000         │◄══►│  BGP AS: 65000         │
                        │  Flowspec-VPN: ✓       │iBGP│  Flowspec-VPN: ✓       │
                        │  RR-Client: ✓          │    │  RR-Client: ✓          │
                        └────────────────────────┘    └────────────────────────┘
                                     │                             │
                                     │         ┌─────────────────┐ │
                                     └────────►│       RR        │◄┘
                                               │  (Route Refl.)  │
                                               │   DN01 or P     │
                                               │   AS: 65000     │
                                               │ Flowspec-VPN: ✓ │
                                               └─────────────────┘
                                                        ▲
                                                        │ eBGP
                                                        ▼
                                               ┌─────────────────┐
                                               │       R2        │
                                               │  cDNOS (HW-146) │
                                               │   AS: 65001     │
                                               │ External Peer   │
                                               │ Flowspec Source │
                                               └─────────────────┘


═══════════════════════════════════════════════════════════════════════════════════════════════
                                    PHYSICAL CONNECTIONS
═══════════════════════════════════════════════════════════════════════════════════════════════

    [SPIRENT:6:13] ───100G───► [ge100-0/0/4] DUT (VRF1 - Flowspec enabled)
    [SPIRENT:6:14] ───100G───► [ge100-0/0/5] DUT (VRF_BLUE - Flowspec enabled)
    
    [DUT ge100-0/0/1] ───100G───► [ge100-0/0/1] DN01 (iBGP + MPLS Core)
    [DUT ge100-0/0/2] ───100G───► [ge100-0/0/1] RR   (iBGP - RR session)
    [DUT ge100-0/0/3] ───100G───► [ge100-0/0/1] R2   (eBGP - External peer)

═══════════════════════════════════════════════════════════════════════════════════════════════
                                    HARDWARE ALLOCATION
═══════════════════════════════════════════════════════════════════════════════════════════════

    ┌────────────┬──────────────────────┬────────────────┬──────────────────────────────┐
    │    Role    │       HW Key         │     Type       │        Description           │
    ├────────────┼──────────────────────┼────────────────┼──────────────────────────────┤
    │    DUT     │ HW-63/64/65/66/67/68 │   CL-408D      │ Main test device (cluster)   │
    │   DN01     │ HW-136 or HW-192     │  NCP-36CD-S    │ iBGP Peer / RR / PE-2        │
    │    R2      │ HW-146               │ DELL_R740/cDNOS│ External eBGP peer           │
    │  SPIRENT   │ HW-114               │  SPIRENT-100G  │ Traffic generator            │
    └────────────┴──────────────────────┴────────────────┴──────────────────────────────┘
```

---

## 2. Test Categories

### Category Legend
| Symbol | Meaning |
|--------|---------|
| ✅ | Covered |
| ⚠️ | Partially Covered |
| ❌ | Missing - ADDED |

---

## 3. Test Cases

### Category 1: SANITY ✅
*Basic enable/disable, ON/OFF tests of the FlowSpec VPN feature*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 1.1 | Basic Enable/Disable | Enable ipv4-flowspec-vpn AF on BGP neighbor, verify session establishment | AF advertised in BGP OPEN, session UP |
| 1.2 | VRF Flowspec AF Enable | Enable ipv4-flowspec under VRF BGP config | Config accepted, `show config` displays correctly |
| 1.3 | Local Flowspec Rule Inject | Configure local flowspec-policy in VRF, verify VPN export | Rule appears in `show bgp ipv4 flowspec-vpn` with correct RT |
| 1.4 | Remote Rule Import | Import flowspec rule from remote PE via RT match | Rule appears in local VRF flowspec table |
| 1.5 | Traffic Drop Action | Configure discard action, send matching traffic | Traffic dropped, counters increment |
| 1.6 | Traffic Rate-Limit Action | Configure rate-limit action, send traffic | Traffic rate-limited to configured value |
| 1.7 | Redirect VRF Action | Configure redirect-vrf action, send traffic | Traffic redirected to target VRF |
| 1.8 | Traffic Marking (DSCP) | Configure dscp marking action | Traffic DSCP value modified |

---

### Category 2: CLI ✅
*All CLI operations, rollback, load commands*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 2.1 | Rollback with Candidate Config | Make flowspec changes, rollback, verify candidate = active | Config reverted, no traffic impact |
| 2.2 | Load Override Flowspec Config | Load flowspec config from file using `load override` | Config applied correctly |
| 2.3 | Load Merge Flowspec Config | Load flowspec config using `load merge` | Config merged, existing preserved |
| 2.4 | No Command All Hierarchies | Test `no` command for all flowspec config hierarchies | Config removed cleanly |
| 2.5 | Rollback 1-49 | Test rollback to previous commits (1-49) | Correct historic config restored |
| 2.6 | Commit Check/Confirm | Use `commit check`, `commit confirm` with flowspec config | Commands work as expected |
| 2.7 | Show Config Flatten | Verify `show config | flatten` works for flowspec | Flatten output correct |
| 2.8 | CLI Auto-complete | Test TAB completion for all flowspec commands | All commands complete correctly |
| 2.9 | Help Lines | Verify `?` shows correct help for all flowspec knobs | Help text accurate |
| 2.10 | Monitor Interval | Run `show flowspec | monitor interval 5` for 256+ rotations | No errors, display updates |

---

### Category 3: INTERFACE TYPES ✅
*Testing across different interface types*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 3.1 | Physical Interface | Enable flowspec on physical interface in VRF | Flowspec rules applied |
| 3.2 | Sub-Interface | Enable flowspec on sub-interface (dot1q) | Flowspec rules applied |
| 3.3 | Bundle Interface | Enable flowspec on bundle interface | Flowspec rules applied |
| 3.4 | Bundle Sub-Interface | Enable flowspec on bundle sub-interface | Flowspec rules applied |
| 3.5 | Breakout Interface | Enable flowspec on breakout port | Flowspec rules applied |
| 3.6 | Cross-NCP Bundle | Enable flowspec on cross-NCP bundle (CL-408D) | Rules applied on all NCPs |
| 3.7 | Interface Type Change | Change interface from physical to bundle with flowspec | Flowspec preserved/reapplied |

---

### Category 4: VRF TESTING ✅
*VRF variations (default/non-default)*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 4.1 | Single VRF | Configure flowspec-vpn in single VRF | Import/Export works |
| 4.2 | Multiple VRFs | Configure flowspec-vpn in 3+ VRFs with different RTs | Isolation maintained |
| 4.3 | VRF with Same RT | Two VRFs with same RT, flowspec shared | Rules propagated correctly |
| 4.4 | VRF with Overlapping Prefixes | Same dest-prefix match in different VRFs | Correct VRF isolation |
| 4.5 | Move Interface Between VRFs | Move interface from VRF1 to VRF2, verify flowspec | Rules follow interface |
| 4.6 | Delete VRF with Flowspec | Delete VRF containing flowspec config | Clean removal, no crash |

---

### Category 5: BGP OPERATIONS ✅
*BGP session handling and route propagation*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 5.1 | iBGP Session Establishment | Establish iBGP with flowspec-vpn AF | Capability advertised, session UP |
| 5.2 | eBGP Session Establishment | Establish eBGP with flowspec-vpn AF | Capability advertised, session UP |
| 5.3 | Route Reflector | Configure RR, verify flowspec-vpn reflection | Rules reflected to clients |
| 5.4 | Clear BGP Neighbor | Clear flowspec-vpn neighbor, verify reconvergence | Session re-establishes, rules re-learned |
| 5.5 | BGP Soft Reconfiguration | Perform soft reconfig inbound for flowspec-vpn | Rules refreshed without session reset |
| 5.6 | Extended Community | Verify RT extended community in flowspec-vpn routes | Correct RT attached |
| 5.7 | Multiple Neighbors | Configure 3+ flowspec-vpn neighbors | All sessions UP, rules propagated |
| 5.8 | Neighbor Shutdown/Enable | Shutdown/enable flowspec-vpn neighbor | Rules withdrawn/re-advertised |

---

### Category 6: SCALE ✅
*Scale testing for flowspec rules and sessions*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 6.1 | 100 Flowspec Rules | Configure 100 local flowspec rules | All installed in datapath |
| 6.2 | 500 Flowspec Rules | Configure 500 local flowspec rules | All installed in datapath |
| 6.3 | 1000 Flowspec Rules | Configure 1000 local flowspec rules | All installed in datapath |
| 6.4 | Multiple VRFs Scale | 50 VRFs with 20 rules each (1000 total) | All rules installed correctly |
| 6.5 | Max Neighbors Scale | Configure max flowspec-vpn neighbors | All sessions UP |
| 6.6 | Rapid Rule Add/Remove | Add/remove 100 rules in rapid succession | System stable, rules consistent |

---

### Category 7: HA (High Availability) ✅
*HA scenarios including restarts, failovers*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 7.1 | NCC Switchover | Trigger NCC switchover with active flowspec sessions | Sessions recover, rules preserved |
| 7.2 | NCC Failover | Kill active NCC process, verify failover | Traffic < 3s impact |
| 7.3 | Routing Container Restart | Restart RE container with flowspec config | Rules re-installed, sessions recover |
| 7.4 | DP Container Restart | Restart DP container with flowspec rules | Rules re-programmed |
| 7.5 | Process Restart (wb_agent) | Kill wb_agent on master NCP | Rules re-synced from RE |
| 7.6 | Process Restart (bgpd) | Kill bgpd process | BGP sessions recover, rules re-learned |
| 7.7 | Cold System Restart | Cold restart entire system | Config restored, sessions recover |
| 7.8 | Warm System Restart | Warm restart system | Minimal traffic impact, rules preserved |
| 7.9 | NCP Power Cycle | Power cycle single NCP in cluster | Traffic continues on remaining NCPs |
| 7.10 | NCF Restart | Restart NCF in cluster | Fabric recovers, flowspec intact |
| 7.11 | GR/NSR | Test Graceful Restart with flowspec-vpn neighbor | Rules preserved during restart |

---

### Category 8: UPGRADE/DOWNGRADE ✅
*Version migration testing*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 8.1 | Upgrade with Flowspec Config | Upgrade from V25 to V26 with flowspec VPN config | Config preserved, rules functional |
| 8.2 | Downgrade with Flowspec Config | Downgrade from V26 to V25 | Config compatible or graceful error |
| 8.3 | Config Default Changes | Check flowspec defaults after upgrade | Documented changes applied |
| 8.4 | Rolling Upgrade | Rolling upgrade cluster with flowspec traffic | Minimal traffic impact |

---

### Category 9: ROUTING POLICY ✅
*Routing policy interaction with flowspec*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 9.1 | Import Policy | Apply route-policy on flowspec-vpn import | Policy filters rules correctly |
| 9.2 | Export Policy | Apply route-policy on flowspec-vpn export | Policy modifies/filters exports |
| 9.3 | Policy with RT Match | Policy matching on RT extended community | Correct rules filtered |
| 9.4 | Policy Update | Update policy, verify flowspec behavior changes | New policy applied immediately |
| 9.5 | Policy Delete | Delete policy from flowspec-vpn session | Rules pass unfiltered |

---

### Category 10: DATAPATH ✅
*Traffic verification and counters*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 10.1 | IPv4 Drop Traffic | Send matching IPv4 traffic with drop action | Traffic dropped at ingress |
| 10.2 | IPv6 Drop Traffic | Send matching IPv6 traffic with drop action | Traffic dropped at ingress |
| 10.3 | Rate Limit Verification | Send 10Gbps, verify 1Gbps rate-limit | Throughput limited correctly |
| 10.4 | DSCP Marking Verification | Send traffic, capture at egress | DSCP value modified |
| 10.5 | Counter Accuracy | Send known packet count, verify counters | Counters match sent packets |
| 10.6 | ECMP Traffic | Send traffic with multiple ECMP paths | Flowspec applied on all paths |
| 10.7 | Multicast Traffic | Test flowspec with multicast streams | Rules applied if supported |

---

### Category 11: DNOR ✅
*DNOR backup/restore testing*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 11.1 | Save Config to DNOR | Save flowspec VPN config to DNOR | Config saved successfully |
| 11.2 | Restore Config from DNOR | Restore flowspec config from DNOR | Config restored, rules functional |
| 11.3 | Config Compare | Compare DNOR saved vs running config | No unexpected differences |

---

### Category 12: INTEROPERABILITY ✅
*Testing with other vendors*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 12.1 | DN to DN Flowspec-VPN | DNOS PE to DNOS PE via RR | Rules propagated correctly |
| 12.2 | DN to Cisco Flowspec-VPN | DNOS PE to Cisco IOS-XR | Rules propagated correctly |
| 12.3 | DN to Juniper Flowspec-VPN | DNOS PE to Juniper MX | Rules propagated correctly |
| 12.4 | Spirent BGP Peer | Spirent as flowspec-vpn peer | Rules received/advertised |

---

### Category 13: NEGATIVE TESTING ⚠️
*Error handling and boundary conditions*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 13.1 | Invalid RT Format | Configure invalid RT format | Commit rejected with error |
| 13.2 | Overlapping Rules | Configure overlapping flowspec rules | Most specific wins |
| 13.3 | Unsupported Match Field | Configure unsupported match field | Validation error or graceful ignore |
| 13.4 | Invalid NLRI from Peer | Peer sends malformed flowspec NLRI | Session stable, NLRI rejected |
| 13.5 | Over-scale Rules | Configure rules beyond max scale | Graceful rejection |
| 13.6 | Memory Pressure | Configure flowspec during memory pressure | System remains stable |

---

## ❌ MISSING CATEGORIES - ADDED BELOW

---

### Category 14: SNMP ❌ (ADDED)
*SNMP monitoring and MIB verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 14.1 | SNMP Walk Flowspec MIB | Perform SNMP walk on flowspec OIDs | MIB values returned correctly |
| 14.2 | SNMP Get Flowspec Counters | SNMP get for flowspec rule counters | Values match CLI counters |
| 14.3 | SNMP Poll During Scale | SNMP poll during 1000 rule scale | No timeout, values accurate |
| 14.4 | SNMPv2c/v3 Verification | Test both SNMP versions with flowspec | Both versions work |

---

### Category 15: TRAPS ❌ (ADDED)
*SNMP trap verification for flowspec events*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 15.1 | Flowspec Rule Install Trap | Configure trap-server, install flowspec rule | Trap received on install |
| 15.2 | Flowspec Rule Remove Trap | Remove flowspec rule | Trap received on removal |
| 15.3 | Flowspec Session Down Trap | Bring down flowspec-vpn BGP session | Session down trap received |
| 15.4 | Trap with IPv4/IPv6 Server | Configure trap-server with both IPv4/IPv6 | Traps received on both |

---

### Category 16: SYSTEM EVENTS ❌ (ADDED)
*Syslog and system event verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 16.1 | Flowspec Install Event | Enable debug logging, install flowspec rule | Event logged in system-events.log |
| 16.2 | Flowspec Remove Event | Remove flowspec rule | Removal event logged |
| 16.3 | BGP Session Event | Flowspec-VPN session UP/DOWN | Session events logged |
| 16.4 | Rule Conflict Event | Configure conflicting flowspec rules | Conflict event logged |
| 16.5 | Scale Event | Install 1000 rules, verify events | Events for all rules (batched OK) |

---

### Category 17: LOGS/TRACES ❌ (ADDED)
*Log file verification and trace debugging*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 17.1 | BGP Flowspec Traces | Enable `debug bgp flowspec`, verify traces | Traces appear in bgpd_traces |
| 17.2 | WB Agent Logs | Check wb_agent.log for flowspec programming | DP programming logged |
| 17.3 | Log Rotation | Generate large flowspec log, verify rotation | Logs rotate correctly |
| 17.4 | Debug Enable/Disable | Toggle debug levels for flowspec | Debug output controlled |

---

### Category 18: COUNTERS ❌ (ADDED)
*Counter verification across all interfaces*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 18.1 | CLI Counters | Check `show flowspec counters` | Counters increment correctly |
| 18.2 | Clear Counters | Use `clear flowspec counters`, verify reset | Counters reset to 0 |
| 18.3 | Per-Rule Counters | Verify per-rule packet/byte counters | Accurate per rule |
| 18.4 | GNMI Counters | Get flowspec counters via gNMI | Match CLI values |
| 18.5 | Netconf Counters | Get flowspec counters via Netconf | Match CLI values |
| 18.6 | Counter Persistence | Restart process, verify counter behavior | Counters reset/preserved per spec |

---

### Category 19: NETCONF ✅ (Enhanced)
*Netconf operations for flowspec*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 19.1 | Get Running Config | Netconf get-config for flowspec | XML matches CLI config |
| 19.2 | Edit Config | Netconf edit-config for flowspec | Config applied successfully |
| 19.3 | Delete Config | Netconf delete operation | Config removed |
| 19.4 | Get Oper Data | Netconf get for flowspec oper | Oper data retrieved |
| 19.5 | Subscribe | Netconf notification subscription | Events received |

---

### Category 20: GNMI ✅ (Enhanced)
*gNMI operations for flowspec*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 20.1 | gNMI Get Config | Get flowspec config via gNMI | Data matches CLI |
| 20.2 | gNMI Subscribe Sample | Subscribe with sample interval | Updates received |
| 20.3 | gNMI Subscribe On-Change | Subscribe on-change for flowspec oper | Changes reported |
| 20.4 | gNMI Set | Configure flowspec via gNMI set | Config applied |

---

### Category 21: BGP NEIGHBOR GROUPS ❌ (ADDED)
*Flowspec-VPN with neighbor-group configuration*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 21.1 | Neighbor Group Basic | Configure flowspec-vpn AF under neighbor-group | All group members receive AF |
| 21.2 | Move Neighbor In/Out Group | Move neighbor between groups | Flowspec AF follows correctly |
| 21.3 | Override in Neighbor | Override group setting in specific neighbor | Neighbor-level takes precedence |
| 21.4 | Delete Neighbor Group | Delete group with flowspec-vpn | Graceful handling |

---

### Category 22: TECHSUPPORT ❌ (ADDED)
*Techsupport file verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 22.1 | Generate TS with Flowspec | Generate techsupport with flowspec configured | TS generated successfully |
| 22.2 | Verify Flowspec in TS | Check flowspec commands in TS | All show commands present |
| 22.3 | Verify Traces in TS | Check flowspec traces in TS | Traces included |
| 22.4 | TS During Scale | Generate TS during 1000 rule scale | TS completes successfully |

---

### Category 23: LONGEVITY ❌ (ADDED)
*Long-running stability tests*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 23.1 | 24-Hour Stability | Run flowspec VPN with traffic for 24 hours | No memory leak, sessions stable |
| 23.2 | 72-Hour Stability | Run flowspec VPN for 72 hours with HA events | System stable |
| 23.3 | Memory Monitoring | Monitor memory during 24-hour test | No growth beyond baseline |
| 23.4 | CPU Monitoring | Monitor CPU during 24-hour test | No unexpected spikes |

---

### Category 24: MEMORY & CPU FOOTPRINT ❌ (ADDED)
*Resource consumption verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 24.1 | Baseline Memory | Record memory before flowspec config | Baseline established |
| 24.2 | Memory with 1000 Rules | Record memory with 1000 flowspec rules | Within expected bounds |
| 24.3 | Memory After Delete | Delete all rules, verify memory release | Memory returns to baseline |
| 24.4 | CPU During Install | Monitor CPU during 1000 rule install | No sustained >80% CPU |
| 24.5 | Process Memory | Monitor bgpd/wb_agent memory | No leaks |

---

### Category 25: ALARMS ❌ (ADDED)
*DNOS alarm verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 25.1 | Flowspec Session Alarm | Bring down flowspec-vpn session | Alarm raised |
| 25.2 | Alarm Clear | Restore session | Alarm cleared |
| 25.3 | Scale Limit Alarm | Approach flowspec scale limit | Warning alarm if applicable |
| 25.4 | Resource Alarm | Deplete flowspec resources | Resource alarm raised |

---

### Category 26: SANITIZER ❌ (ADDED)
*Testing with sanitizer builds*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 26.1 | Sanitizer Basic | Run sanity tests on sanitizer build | No sanitizer errors |
| 26.2 | Sanitizer HA | Run HA tests on sanitizer build | No memory errors |
| 26.3 | Sanitizer Scale | Run scale tests on sanitizer build | No errors detected |

---

### Category 27: DOCUMENTATION ✅
*RST documentation verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 27.1 | CLI vs RST | Compare CLI commands to RST docs | All commands documented |
| 27.2 | Default Values | Verify documented defaults match CLI | Defaults accurate |
| 27.3 | Value Ranges | Verify documented ranges match CLI | Ranges accurate |

---

### Category 28: SHOW COMMANDS ❌ (ADDED)
*Comprehensive show command verification*

| Test# | Test Name | Description | Pass Criteria |
|-------|-----------|-------------|---------------|
| 28.1 | show bgp ipv4 flowspec-vpn | Verify output format and content | All fields present and accurate |
| 28.2 | show bgp vrf X ipv4 flowspec | Verify VRF-specific flowspec | Correct VRF rules shown |
| 28.3 | show flowspec | Verify flowspec summary | Accurate summary |
| 28.4 | show flowspec ncp X | Verify per-NCP flowspec | NCP-specific data correct |
| 28.5 | show bgp neighbor X flowspec-vpn | Verify neighbor-specific | Accurate neighbor data |
| 28.6 | Show with Pipelines | Test `| include`, `| count`, `| no-more` | All pipelines work |

---

## 4. Test Execution Variants

For each test case above, consider these variants:

| Variant | Description |
|---------|-------------|
| IPv4 vs IPv6 | Test both ipv4-flowspec-vpn and ipv6-flowspec-vpn |
| Single vs Multi-VRF | Test with 1 VRF and with 3+ VRFs |
| Physical vs Bundle | Test on physical interface and bundle interface |
| Cluster vs Standalone | Test on CL-408D (cluster) and NCP-36CD-S (standalone) |
| iBGP vs eBGP | Test with internal and external BGP peers |
| With/Without RR | Test direct PE-PE and via Route Reflector |

---

## 5. Test Environment Setup

### Prerequisites
1. DUT (CL-408D) with DNOS V25.2+
2. DN01 (NCP-36CD-S) with DNOS V25.2+
3. R2 (cDNOS on h263 server) for external peer
4. Spirent with BGP Flowspec and traffic capability
5. Management connectivity (SSH, SNMP, Netconf, gNMI)

### Configuration Templates
See: `/home/dn/SCALER/FLOWSPEC_VPN/FLOWSPEC_VPN_CONFIG_EXAMPLE.md`

### Debugging Commands
See: `/home/dn/SCALER/FLOWSPEC_VPN/FLOWSPEC_VPN_DEBUGGING.md`

---

## 6. Coverage Summary

| Category | Status | Test Count |
|----------|--------|------------|
| Sanity | ✅ | 8 |
| CLI | ✅ | 10 |
| Interface Types | ✅ | 7 |
| VRF Testing | ✅ | 6 |
| BGP Operations | ✅ | 8 |
| Scale | ✅ | 6 |
| HA | ✅ | 11 |
| Upgrade/Downgrade | ✅ | 4 |
| Routing Policy | ✅ | 5 |
| Datapath | ✅ | 7 |
| DNOR | ✅ | 3 |
| Interoperability | ✅ | 4 |
| Negative Testing | ⚠️ | 6 |
| **SNMP** | ❌ ADDED | 4 |
| **Traps** | ❌ ADDED | 4 |
| **System Events** | ❌ ADDED | 5 |
| **Logs/Traces** | ❌ ADDED | 4 |
| **Counters** | ❌ ADDED | 6 |
| Netconf | ✅ | 5 |
| GNMI | ✅ | 4 |
| **BGP Neighbor Groups** | ❌ ADDED | 4 |
| **Techsupport** | ❌ ADDED | 4 |
| **Longevity** | ❌ ADDED | 4 |
| **Memory & CPU** | ❌ ADDED | 5 |
| **Alarms** | ❌ ADDED | 4 |
| **Sanitizer** | ❌ ADDED | 3 |
| Documentation | ✅ | 3 |
| **Show Commands** | ❌ ADDED | 6 |
| **TOTAL** | | **150** |

---

## 7. References

- [Checklist for TP (Confluence)](https://drivenets.atlassian.net/wiki/spaces/UP/pages/4959536319)
- [DAP Scrum Testing Methodology](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5305827392)
- [SIT Test Plan Checklist](https://drivenets.atlassian.net/wiki/spaces/QA/pages/4121919492)
- [DNOS FlowSpec VPN Config Examples](/home/dn/SCALER/FLOWSPEC_VPN/)

---

*Document Generated: January 2026*
*Last Updated: January 2026*
