# FlowSpec VPN - Complete Test Plan v3 (Gap Analysis + Regression Markers)

_Version: 3.0 | Generated: 2026-01-13_
_DNOS CLI Syntax Verified | TP Checklist Gaps Addressed | Regression Tests Marked_

---

## Legend

| Marker | Meaning |
|--------|---------|
| 🆕 **NEW** | New feature test - FlowSpec VPN specific functionality |
| 🔄 **REG** | Regression test - Existing functionality tested with new feature |
| ⚠️ **GAP** | Gap identified from TP checklist - test added |

---

## TP Checklist Gap Analysis Summary

| Checklist Category | Current Coverage | Gaps Identified |
|-------------------|------------------|-----------------|
| CLI | ✅ Partial | ⚠️ Multiple CLI sessions, Rollback, Factory Default, DNOR backup |
| Basic Functionality | ✅ Good | ⚠️ Enable/Disable knobs |
| Data Path | ✅ Good | ⚠️ Different frame sizes, ECMP distribution |
| Variants (IPv4/IPv6) | ✅ Good | - |
| Interface Types | ✅ Good | ⚠️ Breakout interfaces |
| Advanced Functionality | ✅ Partial | ⚠️ VRF create/delete with FlowSpec |
| Scale | ✅ Good | - |
| HA | ✅ Partial | ⚠️ Process restarts (Zebra, BGPd, wb_agent), Warm/Cold restart, LOFD |
| NetConf/SNMP/gNMI | ⚠️ Missing | ⚠️ SNMP, gNMI Subscribe |
| SafeMode/Recovery | ⚠️ Missing | ⚠️ Recovery mode with FlowSpec |
| Interoperability | ✅ Partial | ⚠️ Juniper, Nokia, IXIA/Spirent |
| System Events/Logs | ⚠️ Missing | ⚠️ Syslog, Tech-support |
| Stress | ⚠️ Missing | ⚠️ Network flaps, Config stress |
| Convergence | ⚠️ Missing | ⚠️ IGP/BGP metric changes, Link failure |
| Clear Commands | ⚠️ Partial | ⚠️ Multiple clear operations |

---

## Test Plan Overview

| Metric | Count |
|--------|-------|
| Total Test Cases | 120+ |
| 🆕 New Feature Tests | ~45 |
| 🔄 Regression Tests | ~75 |
| ⚠️ Gap Tests Added | ~30 |

---

# 1. BASIC FUNCTIONALITY

## 1.1 IPv4 FlowSpec-VPN - Default VRF
**Type:** 🆕 **NEW**

**Test Name:** Basic | IPv4 FlowSpec-VPN Default VRF - Drop Action

**Description:** Verify IPv4 FlowSpec-VPN (AFI=1, SAFI=134) in default VRF with drop action

**Steps:**
1. DUT: `rollback 0`
2. Configure BGP FlowSpec-VPN neighbor:
   ```
   configure
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
       !
     !
   !
   commit confirm 60
   commit
   ```
3. R2 (Cisco XR): Advertise FlowSpec rule `dst 10.10.10.0/24 action drop`
4. DUT: Verify session:
   ```
   show bgp ipv4 flowspec-vpn summary
   show bgp ipv4 flowspec-vpn routes
   ```
5. DUT: Verify NCP programming:
   ```
   show flowspec ncp
   ```
6. Generate traffic to 10.10.10.1 from IXIA1

**Pass Criteria:**
- BGP session Established for SAFI 134
- FlowSpec NLRI received
- `show flowspec ncp` shows "Installed"
- Traffic dropped

---

## 1.2 IPv4 FlowSpec-VPN - Non-Default VRF
**Type:** 🆕 **NEW**

**Test Name:** Basic | IPv4 FlowSpec-VPN Non-Default VRF with import-vpn

**Description:** Verify IPv4 FlowSpec-VPN import into non-default VRF via RT

**Steps:**
1. Configure VRF with import-vpn
2. Configure BGP neighbor with flowspec-vpn
3. Advertise FlowSpec-VPN with matching RT
4. Verify import and enforcement

**Pass Criteria:**
- FlowSpec imported into VRF1
- Traffic in VRF1 dropped

---

## 1.3 IPv6 FlowSpec-VPN - Default VRF
**Type:** 🆕 **NEW**

**Test Name:** Basic | IPv6 FlowSpec-VPN Default VRF

---

## 1.4 IPv6 FlowSpec-VPN - Non-Default VRF
**Type:** 🆕 **NEW**

**Test Name:** Basic | IPv6 FlowSpec-VPN Non-Default VRF

---

## 1.5 Neighbor Group Configuration
**Type:** 🔄 **REG** (neighbor-group is existing BGP feature)

**Test Name:** Basic | FlowSpec-VPN via Neighbor-Group

**Description:** Verify FlowSpec-VPN inherited from neighbor-group (tests existing neighbor-group mechanism)

---

## 1.6 Neighbor AFI-SAFI Features

### 1.6.1 Maximum-Prefix
**Type:** 🔄 **REG** (maximum-prefix is existing BGP feature)

**Test Name:** Basic | FlowSpec Maximum-Prefix Limit

---

### 1.6.2 Policy In/Out
**Type:** 🔄 **REG** (routing-policy is existing feature)

**Test Name:** Basic | FlowSpec with Policy In

---

### 1.6.3 Allow-as-in
**Type:** 🔄 **REG** (allow-as-in is existing BGP feature)

**Test Name:** Basic | FlowSpec with allow-as-in

---

### 1.6.4 Nexthop Self
**Type:** 🔄 **REG** (nexthop self is existing BGP feature)

**Test Name:** Basic | FlowSpec with nexthop self

---

## 1.7 ⚠️ GAP: Enable/Disable Knobs
**Type:** 🆕 **NEW** + ⚠️ **GAP**

**Test Name:** Basic | FlowSpec Enable/Disable Knobs

**Description:** Per TP Checklist: Test all enable/disable knobs

**Steps:**
1. Configure FlowSpec-VPN neighbor with admin-state enabled
2. Verify FlowSpec working
3. Set admin-state disabled
4. Verify FlowSpec stops
5. Re-enable admin-state
6. Verify FlowSpec resumes

**Pass Criteria:**
- Admin-state controls FlowSpec operation
- No stale rules when disabled

---

## 1.8 ⚠️ GAP: Configure/Delete Feature
**Type:** 🆕 **NEW** + ⚠️ **GAP**

**Test Name:** Basic | FlowSpec Configure/Delete

**Description:** Per TP Checklist: Test configure/delete the feature

**Steps:**
1. Configure FlowSpec-VPN completely
2. Verify working
3. Delete FlowSpec-VPN config entirely
4. Verify clean removal (no stale routes/rules)
5. Re-configure
6. Verify working again

**Pass Criteria:**
- Clean deletion
- No memory leaks
- Re-configuration works

---

# 2. ADVANCED FUNCTIONALITY

## 2.1 RT-C Integration
**Type:** 🔄 **REG** (RT-C is existing BGP feature)

**Test Name:** Advanced | RT-C with FlowSpec-VPN

---

## 2.2 Route Reflector Topology
**Type:** 🔄 **REG** (RR is existing BGP feature)

**Test Name:** Advanced | FlowSpec-VPN via Route Reflector

---

## 2.3 eBGP External Peer
**Type:** 🔄 **REG** (eBGP is existing BGP feature)

**Test Name:** Advanced | FlowSpec-VPN eBGP Peer

---

## 2.4 Multi-VRF Import Same RT
**Type:** 🆕 **NEW**

**Test Name:** Advanced | Multiple VRFs Import Same FlowSpec

---

## 2.5 Redirect-to-RT
**Type:** 🆕 **NEW**

**Test Name:** Advanced | Redirect-to-RT Action

---

## 2.6 ⚠️ GAP: VRF Create/Delete with FlowSpec
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Advanced | VRF Create/Delete with Active FlowSpec

**Description:** Per TP Checklist: Test creating/deleting VRFs with feature

**Steps:**
1. Configure FlowSpec imported to VRF1
2. Verify rules installed
3. Delete VRF1
4. Verify FlowSpec rules removed cleanly
5. Re-create VRF1 with same config
6. Verify FlowSpec re-imported

**Pass Criteria:**
- VRF deletion cleans FlowSpec state
- No orphan rules
- Re-creation works

---

## 2.7 ⚠️ GAP: ECMP with FlowSpec
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Advanced | FlowSpec with ECMP Paths

**Description:** Per TP Checklist: Test with ECMP

**Steps:**
1. Configure 4x ECMP paths to FlowSpec peer
2. Advertise FlowSpec rules
3. Verify FlowSpec received
4. Generate traffic - verify distribution across ECMP
5. Remove one ECMP path
6. Verify FlowSpec still works

**Pass Criteria:**
- FlowSpec works with ECMP to peer
- Traffic distribution correct

---

# 3. DNOS-SPECIFIC BEHAVIOR TESTS

## 3.1 No VPN Label Verification
**Type:** 🆕 **NEW**

---

## 3.2 No NH Reachability Check
**Type:** 🆕 **NEW**

---

## 3.3 Redirect-to-IP Rejection
**Type:** 🆕 **NEW**

---

## 3.4 VRF Alphabetical Selection
**Type:** 🆕 **NEW**

---

## 3.5 Cross-VRF Redirect Rejection
**Type:** 🆕 **NEW**

---

## 3.6 C=0 Only for Redirect-IP
**Type:** 🆕 **NEW**

---

## 3.7 Mixed Redirect Actions
**Type:** 🆕 **NEW**

---

## 3.8 Relaxed Validation
**Type:** 🆕 **NEW**

---

## 3.9 Simpson Draft Redirect Only
**Type:** 🆕 **NEW**

---

# 4. NEGATIVE TESTING

## 4.1 Invalid Prefix Length
**Type:** 🆕 **NEW**

---

## 4.2 Duplicate Component Types
**Type:** 🆕 **NEW**

---

## 4.3 Unsupported Actions
**Type:** 🆕 **NEW**

---

## 4.4 ⚠️ GAP: Invalid RT Format
**Type:** 🆕 **NEW** + ⚠️ **GAP**

**Test Name:** Negative | Invalid Route-Target Format

**Steps:**
1. Try to configure import-vpn with invalid RT format
2. Verify rejection

---

## 4.5 ⚠️ GAP: FlowSpec Without VRF
**Type:** 🆕 **NEW** + ⚠️ **GAP**

**Test Name:** Negative | FlowSpec VRF Not Exist

**Steps:**
1. Configure import-vpn to VRF that doesn't exist
2. Verify behavior

---

# 5. CLI TESTS

## 5.1 Configuration Commands
**Type:** 🆕 **NEW**

---

## 5.2 Show Commands
**Type:** 🆕 **NEW**

---

## 5.3 Clear Commands
**Type:** 🔄 **REG** (clear commands are existing)

---

## 5.4 ⚠️ GAP: Multiple CLI Sessions
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** CLI | Multiple CLI Sessions

**Description:** Per TP Checklist: Test multiple CLI sessions

**Steps:**
1. Open 2 SSH sessions to DUT
2. Session 1: Start FlowSpec configuration
3. Session 2: Try to modify same config
4. Verify proper locking/handling

**Pass Criteria:**
- Concurrent access handled properly
- No corruption

---

## 5.5 ⚠️ GAP: Multiple Actions Same Commit
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** CLI | Multiple Actions Same Commit

**Description:** Per TP Checklist: Swap, change, add, remove in same commit

**Steps:**
1. Configure FlowSpec with 3 VRFs importing
2. In single commit:
   - Delete VRF1 flowspec
   - Modify VRF2 RT
   - Add VRF3 flowspec
3. Verify all changes applied correctly

**Pass Criteria:**
- All changes in single commit work
- No partial state

---

## 5.6 ⚠️ GAP: Rollback Tests
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** CLI | FlowSpec Rollback

**Description:** Per TP Checklist: Test rollback

**Steps:**
1. Save config with FlowSpec
2. Modify FlowSpec config
3. Commit
4. Rollback to previous config
5. Verify FlowSpec restored

**Pass Criteria:**
- Rollback restores FlowSpec config
- Rules updated correctly

---

## 5.7 ⚠️ GAP: Factory Default
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** CLI | Factory Default with FlowSpec

**Description:** Per TP Checklist: Test factory default

**Steps:**
1. Configure FlowSpec
2. Load factory-default
3. Verify FlowSpec removed
4. Re-configure FlowSpec
5. Verify works

**Pass Criteria:**
- Factory default cleans FlowSpec
- No stale state

---

## 5.8 ⚠️ GAP: DNOR Backup/Restore
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** CLI | DNOR Backup FlowSpec Config

**Description:** Per TP Checklist: Check if feature CLI possible to backup with DNOR

**Steps:**
1. Configure FlowSpec
2. Backup config via DNOR
3. Factory default device
4. Restore from DNOR backup
5. Verify FlowSpec config restored

**Pass Criteria:**
- DNOR backup includes FlowSpec config
- Restore works

---

# 6. DATAPATH (DP) SPECIFICS

## 6.1 NCP Rule Installation
**Type:** 🆕 **NEW**

---

## 6.2 Action Not Supported Handling
**Type:** 🆕 **NEW**

---

## 6.3 Counters Verification
**Type:** 🆕 **NEW**

---

## 6.4 Line-Rate Enforcement
**Type:** 🆕 **NEW**

---

## 6.5 Rate-Limit Accuracy
**Type:** 🆕 **NEW**

---

## 6.6 Per-VRF Rule Isolation
**Type:** 🆕 **NEW**

---

## 6.7 Interface Type Coverage
**Type:** 🔄 **REG** (interface types are existing)

---

## 6.8 ⚠️ GAP: Different Frame Sizes
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** DP | FlowSpec with Different Frame Sizes

**Description:** Per TP Checklist: Use different frame sizes

**Steps:**
1. Configure FlowSpec drop rule
2. Send traffic with frame sizes: 64, 128, 256, 512, 1024, 1518, 9000 (jumbo)
3. Verify all dropped

**Pass Criteria:**
- All frame sizes matched and dropped
- No frame size dependency

---

## 6.9 ⚠️ GAP: ECMP Traffic Distribution
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** DP | FlowSpec with ECMP Distribution

**Description:** Per TP Checklist: Use different TCP/UDP ports for ECMP

**Steps:**
1. Configure 4x ECMP paths
2. Enable FlowSpec on ingress
3. Send traffic with varied src-port/dst-port
4. Verify FlowSpec enforcement across all ECMP members

**Pass Criteria:**
- FlowSpec works on all ECMP paths
- Traffic distribution even

---

## 6.10 ⚠️ GAP: Breakout Interfaces
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** DP | FlowSpec on Breakout Interfaces

**Description:** Per TP Checklist: Test on breakout interfaces

**Steps:**
1. Configure 4x10G breakout from 1x40G port
2. Enable FlowSpec on breakout interfaces
3. Verify FlowSpec enforcement on each

**Pass Criteria:**
- FlowSpec works on breakout interfaces

---

# 7. HA TESTS

## 7.1 BGP Container Restart
**Type:** 🔄 **REG** (container restart is existing HA mechanism)

---

## 7.2 NCM Switchover
**Type:** 🔄 **REG** (NCM switchover is existing HA mechanism)

---

## 7.3 NCP Restart
**Type:** 🔄 **REG** (NCP restart is existing HA mechanism)

---

## 7.4 Graceful Restart
**Type:** 🔄 **REG** (GR is existing BGP feature)

---

## 7.5 ⚠️ GAP: Process Restart - Zebra
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | Zebra Process Restart with FlowSpec

**Description:** Per TP Checklist: Test process restarts (zebra)

**Steps:**
1. Configure FlowSpec, verify rules installed
2. Kill zebra process: `kill -9 $(pgrep zebra)`
3. Wait for recovery
4. Verify FlowSpec rules maintained

**Pass Criteria:**
- Zebra restarts
- FlowSpec state recovered

---

## 7.6 ⚠️ GAP: Process Restart - BGPd
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | BGPd Process Restart with FlowSpec

**Steps:**
1. Configure FlowSpec
2. Kill bgpd: `kill -9 $(pgrep bgpd)`
3. Verify recovery

---

## 7.7 ⚠️ GAP: Process Restart - wb_agent
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | wb_agent Restart with FlowSpec

**Steps:**
1. Configure FlowSpec
2. Kill wb_agent on master NCP
3. Verify FlowSpec rules maintained in DP

---

## 7.8 ⚠️ GAP: System Restart Cold
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | Cold System Restart with FlowSpec

**Description:** Per TP Checklist: Test system restart cold/warm

**Steps:**
1. Configure FlowSpec, save config
2. Request system restart cold
3. Wait for boot
4. Verify FlowSpec config restored and working

**Pass Criteria:**
- Config survives cold restart
- FlowSpec operational after boot

---

## 7.9 ⚠️ GAP: System Restart Warm
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | Warm System Restart with FlowSpec

**Steps:**
1. Configure FlowSpec
2. Request system restart warm
3. Verify minimal disruption
4. Verify FlowSpec maintained

---

## 7.10 ⚠️ GAP: NCE Power Cycle
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | NCE Power Cycle with FlowSpec

**Description:** Per TP Checklist: Power cycle NCE

**Steps:**
1. Configure FlowSpec
2. Power cycle one NCE (NCP)
3. Verify FlowSpec rules on other NCEs maintained
4. Verify NCE recovers and gets rules

---

## 7.11 ⚠️ GAP: LOFD
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | LOFD with FlowSpec

**Description:** Per TP Checklist: Test LOFD

**Steps:**
1. Configure FlowSpec
2. Trigger LOFD condition
3. Verify system recovers
4. Verify FlowSpec state

---

## 7.12 ⚠️ GAP: NCC Failover by Power Cycle
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | NCC Failover by Power Cycle

**Description:** Per TP Checklist: By power cycle active NCC

**Steps:**
1. Configure FlowSpec
2. Power cycle active NCC
3. Verify standby takes over
4. Verify FlowSpec maintained

---

## 7.13 ⚠️ GAP: Clear Neighbors Multiple Times
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | Clear BGP Neighbors Multiple Times

**Description:** Per TP Checklist: Clear neighbors single/scale/multiple-times

**Steps:**
1. Configure FlowSpec from peer
2. Clear BGP neighbor 10 times in succession
3. Verify FlowSpec recovers each time
4. Verify no memory leak

---

## 7.14 ⚠️ GAP: Admin-Disabled During Switchover
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** HA | NCM Switchover with FlowSpec Disabled

**Description:** Per TP Checklist: NCC switchover when feature admin-state disabled

**Steps:**
1. Configure FlowSpec but set admin-state disabled
2. Trigger NCM switchover
3. Verify disabled state preserved
4. Re-enable, verify works

---

# 8. SCALE TESTS

## 8.1 Max FlowSpec-VPN Peers
**Type:** 🆕 **NEW**

---

## 8.2 Max FlowSpec-VPN Routes
**Type:** 🆕 **NEW**

---

## 8.3 DP IPv4 Rules Limit
**Type:** 🆕 **NEW**

---

## 8.4 DP IPv6 Rules Limit
**Type:** 🆕 **NEW**

---

## 8.5 Max Rules Per VRF
**Type:** 🆕 **NEW**

---

## 8.6 Max VRFs with FlowSpec
**Type:** 🆕 **NEW**

---

## 8.7 ⚠️ GAP: Multi-Dimensional Scale
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Scale | Multi-Dimensional Scale

**Description:** Per TP Checklist: Multi-dimensional scale

**Steps:**
1. Configure max peers (8) + max rules per peer + multiple VRFs
2. Verify all dimensions at scale simultaneously
3. Monitor CPU/memory

**Pass Criteria:**
- All dimensions work at scale
- No degradation

---

# 9. UPGRADE TESTS

## 9.1 ISSU with FlowSpec
**Type:** 🔄 **REG** (ISSU is existing mechanism)

---

## 9.2 ⚠️ GAP: Downgrade with FlowSpec
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Upgrade | Downgrade with FlowSpec

**Description:** Per TP Checklist: System upgrade/downgrade

**Steps:**
1. Configure FlowSpec on new version
2. Downgrade to previous version
3. Verify FlowSpec behavior (may be unsupported)

**Pass Criteria:**
- Downgrade handles FlowSpec gracefully
- No crash if feature didn't exist

---

## 9.3 ⚠️ GAP: GI Upgrade
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Upgrade | GI Mode Upgrade with FlowSpec

**Description:** Per TP Checklist: GI/DNOR upgrade

**Steps:**
1. Configure FlowSpec
2. Perform GI upgrade
3. Verify FlowSpec survives

---

# 10. OPENCONFIG / NETCONF / GNMI

## 10.1 OpenConfig Model
**Type:** 🆕 **NEW**

---

## 10.2 ⚠️ GAP: NETCONF Get/Edit
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** NETCONF | FlowSpec Get/Edit-config

**Description:** Per TP Checklist: Netconf Get/Edit-config/Get-config/Request

**Steps:**
1. Configure FlowSpec via NETCONF edit-config
2. Verify with NETCONF get-config
3. Verify operational state with NETCONF get

**Pass Criteria:**
- NETCONF CRUD operations work

---

## 10.3 ⚠️ GAP: gNMI Subscribe
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** gNMI | FlowSpec Subscribe

**Description:** Per TP Checklist: GNMI Get/Subscribe/On-change

**Steps:**
1. Subscribe to FlowSpec paths via gNMI
2. Change FlowSpec config
3. Verify on-change notifications

**Pass Criteria:**
- gNMI streaming works

---

## 10.4 ⚠️ GAP: SNMP
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** SNMP | FlowSpec MIBs

**Description:** Per TP Checklist: SNMP Poll/Get

**Steps:**
1. Configure FlowSpec
2. Query relevant SNMP OIDs
3. Verify correct values

**Pass Criteria:**
- SNMP MIBs reflect FlowSpec state

---

# 11. ⚠️ GAP: SYSTEM EVENTS / LOGS / TRACES

## 11.1 Syslog Events
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Logs | FlowSpec Syslog Events

**Description:** Per TP Checklist: Syslog

**Steps:**
1. Configure FlowSpec
2. Verify syslog messages for:
   - Session establishment
   - Rule installation
   - Rule removal
   - Errors

**Pass Criteria:**
- Appropriate syslog events generated

---

## 11.2 Traces
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Logs | FlowSpec Traces

**Description:** Per TP Checklist: Traces

**Steps:**
1. Enable BGP traces
2. Configure FlowSpec
3. Verify trace output

**Pass Criteria:**
- Traces capture FlowSpec activity

---

## 11.3 Tech-Support
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Logs | FlowSpec in Tech-Support

**Description:** Per TP Checklist: Tech-support parsing

**Steps:**
1. Configure FlowSpec with rules
2. Generate tech-support
3. Verify FlowSpec info included

**Pass Criteria:**
- Tech-support contains FlowSpec config and state

---

## 11.4 Counters Northbound
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Logs | FlowSpec Counters via Northbound

**Description:** Per TP Checklist: Counters via northbound interfaces

**Steps:**
1. Configure FlowSpec rules
2. Query counters via NETCONF/gNMI
3. Verify counter values

**Pass Criteria:**
- Counters exposed via northbound

---

# 12. ⚠️ GAP: INTEROPERABILITY

## 12.1 Cisco IOS-XR
**Type:** 🔄 **REG** (interop is existing test type)

**Test Name:** Interop | FlowSpec-VPN with Cisco IOS-XR

---

## 12.2 ⚠️ GAP: Juniper
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Interop | FlowSpec-VPN with Juniper

**Description:** Per TP Checklist: Juniper

---

## 12.3 ⚠️ GAP: Nokia
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Interop | FlowSpec-VPN with Nokia

---

## 12.4 ⚠️ GAP: IXIA/Spirent Traffic Gen
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Interop | FlowSpec with IXIA/Spirent

**Description:** Per TP Checklist: IXIA/Spirent

**Steps:**
1. Configure FlowSpec rules
2. Generate traffic from IXIA
3. Verify enforcement
4. Generate traffic from Spirent
5. Verify enforcement

---

## 12.5 ⚠️ GAP: DN2DN
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Interop | FlowSpec DN to DN

**Description:** Per TP Checklist: DN2DN interop

**Steps:**
1. Two DNOS devices with FlowSpec-VPN
2. Advertise FlowSpec between them
3. Verify mutual enforcement

---

## 12.6 ⚠️ GAP: Version Interop
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Interop | FlowSpec Between DNOS Versions

**Description:** Per TP Checklist: Version interoperability

**Steps:**
1. DUT on version X, peer on version Y
2. Advertise FlowSpec between versions

---

# 13. ⚠️ GAP: STRESS TESTS

## 13.1 Interface Flaps
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Stress | Interface Flaps with FlowSpec

**Description:** Per TP Checklist: Network flaps - interface flaps

**Steps:**
1. Configure FlowSpec on interface
2. Flap interface 100 times rapidly
3. Verify FlowSpec recovers each time
4. Verify no stale rules

---

## 13.2 BGP Withdrawal Storm
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Stress | BGP Withdrawal Storm

**Description:** Per TP Checklist: BGP withdrawal

**Steps:**
1. Configure 1000 FlowSpec rules
2. Rapidly withdraw all 1000
3. Re-advertise all 1000
4. Repeat 10 times
5. Verify final state correct

---

## 13.3 Config Stress
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Stress | Config Stress

**Description:** Per TP Checklist: Config stress

**Steps:**
1. Rapidly add/delete FlowSpec VRF config
2. 100 iterations
3. Verify no config corruption

---

## 13.4 Process Restart Storm
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Stress | Process Restart Storm

**Description:** Per TP Checklist: Process restarts stress

**Steps:**
1. Configure FlowSpec
2. Restart BGP container 10 times rapidly
3. Verify FlowSpec stable after storm

---

## 13.5 DP Stress
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Stress | DP Stress with FlowSpec

**Description:** Per TP Checklist: DP stress

**Steps:**
1. Configure max FlowSpec rules
2. Send line-rate traffic to all rules simultaneously
3. Monitor NCP CPU

---

# 14. ⚠️ GAP: CONVERGENCE TESTS

## 14.1 IGP Metric Change
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Convergence | IGP Metric Change with FlowSpec

**Description:** Per TP Checklist: IGP level metric changes

**Steps:**
1. Configure FlowSpec via path A (primary)
2. Change IGP metric to prefer path B
3. Verify FlowSpec session follows new path
4. Verify rules maintained

---

## 14.2 BGP Metric Change
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Convergence | BGP Metric Change

**Description:** Per TP Checklist: BGP level metric change

---

## 14.3 Link Failure
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Convergence | Link Failure with FlowSpec

**Description:** Per TP Checklist: Link failure/recover

**Steps:**
1. Configure FlowSpec via primary link
2. Fail primary link (admin down)
3. Verify convergence to backup
4. Verify FlowSpec maintained
5. Recover link
6. Verify re-convergence

---

## 14.4 BFD Failure
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Convergence | BFD Failure with FlowSpec

**Description:** Per TP Checklist: BFD failure/recover

---

## 14.5 FRR with FlowSpec
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Convergence | FRR Protection with FlowSpec

**Description:** Per TP Checklist: LFA/rLFA/TI-LFA

**Steps:**
1. Configure TI-LFA on path to FlowSpec peer
2. Fail primary link
3. Measure FRR switchover time
4. Verify FlowSpec maintained during FRR

---

# 15. ⚠️ GAP: SAFEMODE / RECOVERY

## 15.1 Enter Recovery Mode
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Recovery | Enter Recovery Mode with FlowSpec

**Description:** Per TP Checklist: SafeMode/Recovery

**Steps:**
1. Configure FlowSpec
2. Enter recovery mode
3. Verify FlowSpec not active (expected)
4. Exit recovery mode
5. Verify FlowSpec restored

---

## 15.2 SafeMode
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** Recovery | SafeMode with FlowSpec

**Steps:**
1. Configure FlowSpec
2. Enter SafeMode
3. Verify FlowSpec handling

---

# 16. ⚠️ GAP: AAA

## 16.1 RADIUS
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** AAA | FlowSpec Config with RADIUS Auth

**Description:** Per TP Checklist: AAA Radius/Tacacs

**Steps:**
1. Configure RADIUS authentication
2. Login via RADIUS user
3. Configure FlowSpec
4. Verify authorization works

---

## 16.2 TACACS+
**Type:** 🔄 **REG** + ⚠️ **GAP**

**Test Name:** AAA | FlowSpec Config with TACACS+

---

---

# APPENDIX: Test Summary by Type

## 🆕 NEW FEATURE TESTS (~45 tests)

All tests for:
- FlowSpec-VPN SAFI 134 specific functionality
- import-vpn route-target mechanism
- DNOS-specific behaviors (no VPN label, no NH check, etc.)
- Redirect actions (Simpson draft)
- DP rule installation via `show flowspec ncp`

## 🔄 REGRESSION TESTS (~75 tests)

All tests that verify existing features work with FlowSpec:
- BGP neighbor-group inheritance
- BGP maximum-prefix
- BGP routing-policy
- BGP allow-as-in, nexthop self
- RT-C, Route Reflector, eBGP
- VRF create/delete
- ECMP
- All HA mechanisms (container restart, switchover, GR, etc.)
- All process restarts
- All interface types
- All convergence scenarios
- ISSU/Upgrade
- NETCONF/gNMI/SNMP
- Interoperability
- All stress scenarios
- AAA

---

# APPENDIX: Scale Limits (SW-206883)

| Resource | Limit | Notes |
|----------|-------|-------|
| FlowSpec-VPN peers | ~8 | Like scale of VPN RR |
| FlowSpec-VPN routes total | ~20,000 | Across all VRFs |
| DP IPv4 rules | 12,000 | Hardware limit |
| DP IPv6 rules | 4,000 | Hardware limit |
| DP resources | Shared | Among ALL FlowSpec entries regardless of VRF |
| Flowspec rules per VRF | 3,000 | |
| VRFs with flowspec AFI | 512 | |

---

_End of Complete Test Plan v3_
