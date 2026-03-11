# FlowSpec VPN - Complete Merged Test Plan

_Version: 2.0 | Generated: 2026-01-13_
_Merged from: Original TP + AI-Generated + RFC Analysis + DNOS Specifics_

---

## Test Plan Overview

| Metric | Count |
|--------|-------|
| Total Test Categories | 10 |
| Total Test Cases | 85+ |
| DNOS-Specific Tests | 9 |
| RFC Compliance Tests | 12 |
| HA Tests | 8 |
| Scale Tests | 6 |
| Upgrade Tests | 4 |

---

# 1. BASIC FUNCTIONALITY

## 1.1 IPv4 FlowSpec-VPN - Default VRF

**Test Name:** Basic | IPv4 FlowSpec-VPN Default VRF - Drop Action

**Description:** Verify IPv4 FlowSpec-VPN (AFI=1, SAFI=134) in default VRF with drop action

**Steps:**
1. DUT: `rollback 0`
2. Configure BGP FlowSpec-VPN neighbor:
   ```
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
   !
   commit confirm
   ```
3. R2: Advertise FlowSpec rule `dst 10.10.10.0/24 action drop`
4. DUT: `show protocols bgp 65000 neighbor 1.4.14.2 address-family ipv4-flowspec-vpn`
5. DUT: `show bgp ipv4-flowspec-vpn routes`
6. Generate traffic to 10.10.10.1 from IXIA1

**Pass Criteria:**
- BGP session Established for SAFI 134
- FlowSpec NLRI 10.10.10.0/24 received
- Traffic matching rule is dropped
- Counters increment

**Variants:**
- Rate-limit action instead of drop
- Multiple FlowSpec rules
- Different prefix lengths

---

## 1.2 IPv4 FlowSpec-VPN - Non-Default VRF

**Test Name:** Basic | IPv4 FlowSpec-VPN Non-Default VRF with import-vpn

**Description:** Verify IPv4 FlowSpec-VPN import into non-default VRF via RT

**Steps:**
1. DUT: `rollback 0`
2. Create VRF and configure import-vpn:
   ```
   network-services
     vrf VRF1
       rd 65000:1
       route-target import 65000:100
       protocols
         bgp 65000
           address-family ipv4-flowspec
             import-vpn
   !
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
   !
   commit confirm
   ```
3. R2: Advertise FlowSpec-VPN with RT 65000:100
4. DUT: `show bgp vrf VRF1 ipv4-flowspec routes`
5. Verify rule installed in VRF1 datapath

**Pass Criteria:**
- VRF1 exists with import-vpn RT
- FlowSpec imported into VRF1
- Default VRF shows RIB-Install-Filtered
- Traffic in VRF1 is dropped

---

## 1.3 IPv6 FlowSpec-VPN - Default VRF

**Test Name:** Basic | IPv6 FlowSpec-VPN Default VRF

**Description:** Verify IPv6 FlowSpec-VPN (AFI=2, SAFI=134)

**Steps:**
1. DUT: `rollback 0`
2. Configure:
   ```
   protocols
     bgp 65000
       neighbor 2001:db8::2
         address-family ipv6-flowspec-vpn
   !
   commit confirm
   ```
3. R2: Advertise IPv6 FlowSpec `dst 2001:db8:100::/64 action drop`
4. DUT: `show bgp ipv6-flowspec-vpn routes`
5. Generate IPv6 traffic

**Pass Criteria:**
- IPv6 FlowSpec-VPN session up
- NLRI received and installed
- IPv6 traffic dropped

---

## 1.4 IPv6 FlowSpec-VPN - Non-Default VRF

**Test Name:** Basic | IPv6 FlowSpec-VPN Non-Default VRF

**Description:** Verify IPv6 FlowSpec-VPN import into non-default VRF

**Steps:**
1. Similar to 1.2 but with `address-family ipv6-flowspec-vpn`
2. Use IPv6 prefixes

**Pass Criteria:**
- IPv6 FlowSpec imported to VRF
- Traffic enforcement works

---

## 1.5 NLRI Parsing (RFC 8955 Compliance)

### 1.5.1 Length Field Correctness

**Test Name:** Basic | NLRI Length Field Validation

**Description:** Verify NLRI length field equals sum of all component TLVs

**Steps:**
1. Establish FlowSpec session
2. Advertise properly formatted NLRI
3. Verify acceptance

**Pass Criteria:** Valid NLRI accepted and installed

---

### 1.5.2 Component TLV Parsing

**Test Name:** Basic | Component Type-Length-Value Parsing

**Description:** Verify correct parsing of all 12 FlowSpec component types

**Steps:**
1. Advertise FlowSpec with each component type:
   - Type 1: Destination Prefix
   - Type 2: Source Prefix
   - Type 3: IP Protocol
   - Type 4: Port
   - Type 5: Destination Port
   - Type 6: Source Port
   - Type 7: ICMP Type
   - Type 8: ICMP Code
   - Type 9: TCP Flags
   - Type 10: Packet Length
   - Type 11: DSCP
   - Type 12: Fragment
2. Verify each is parsed correctly

**Pass Criteria:** All component types parsed and enforced

---

### 1.5.3 Component Ordering

**Test Name:** Basic | Component Type Ordering Enforcement

**Description:** Verify components must be in increasing Type order

**Steps:**
1. Advertise NLRI with components in correct order (1,2,3,4...)
2. Verify acceptance

**Pass Criteria:** Ordered components accepted

---

### 1.5.4 Port-Range Validation

**Test Name:** Basic | Port Range Component

**Description:** Verify destination-port ranges (low ≤ high)

**Steps:**
1. Advertise FlowSpec with port range 80-443
2. Verify traffic to ports in range is matched

**Pass Criteria:** Port ranges correctly enforced

---

### 1.5.5 IP Protocol Validation

**Test Name:** Basic | IP Protocol Component

**Description:** Verify ip-protocol component matching

**Steps:**
1. Advertise FlowSpec matching protocol TCP (6)
2. Send TCP and UDP traffic
3. Verify only TCP matched

**Pass Criteria:** Protocol matching works correctly

---

## 1.6 Basic Actions

### 1.6.1 Drop Action

**Test Name:** Basic | FlowSpec Drop Action

**Steps:** Covered in 1.1

---

### 1.6.2 Rate-Limit Action

**Test Name:** Basic | FlowSpec Rate-Limit Action

**Description:** Verify traffic-rate action

**Steps:**
1. Advertise FlowSpec with `traffic-rate 10000` (10kbps)
2. Send 100Mbps traffic
3. Measure egress rate

**Pass Criteria:** Traffic limited to ~10kbps ±10%

---

### 1.6.3 DSCP Marking Action

**Test Name:** Basic | FlowSpec DSCP Marking

**Description:** Verify traffic-marking action

**Steps:**
1. Advertise FlowSpec with `set dscp 46`
2. Send traffic with dscp 0
3. Capture egress, verify DSCP=46

**Pass Criteria:** DSCP marked correctly

---

# 2. ADVANCED FUNCTIONALITY

## 2.1 RT-C (Route Target Constraint) Integration

**Test Name:** Advanced | RT-C with FlowSpec-VPN

**Description:** Verify RT-C controls FlowSpec-VPN distribution

**Steps:**
1. Configure RT-C on DUT
2. Advertise RT-C for RT 65000:100
3. Verify only FlowSpec with matching RT is received

**Pass Criteria:** RT-C filters FlowSpec distribution

---

## 2.2 Route Reflector Topology

**Test Name:** Advanced | FlowSpec-VPN via Route Reflector

**Description:** Verify FlowSpec-VPN works through RR

**Steps:**
1. Configure DUT as RR client
2. R6 as RR
3. R2 advertises FlowSpec-VPN
4. Verify DUT receives via R6

**Pass Criteria:** FlowSpec reflected correctly with cluster-id

---

## 2.3 eBGP External Peer

**Test Name:** Advanced | FlowSpec-VPN eBGP Peer

**Description:** Verify FlowSpec-VPN over eBGP

**Steps:**
1. Configure eBGP peer (AS 65001) for FlowSpec-VPN
2. Verify NLRI exchange
3. Verify next-hop handling

**Pass Criteria:** eBGP FlowSpec works with proper NH

---

## 2.4 Multi-VRF Import

**Test Name:** Advanced | Multiple VRFs Import Same FlowSpec

**Description:** Verify FlowSpec imported to multiple VRFs with same RT

**Steps:**
1. Create VRF1 and VRF2 both importing RT 65000:100
2. Advertise FlowSpec with RT 65000:100
3. Verify both VRFs receive

**Pass Criteria:** FlowSpec installed in both VRFs

---

## 2.5 Redirect Actions

### 2.5.1 Redirect-to-RT (Simpson Draft)

**Test Name:** Advanced | Redirect-to-RT Action

**Description:** Verify redirect using RT extended community (SUPPORTED)

**Steps:**
1. Create VRF-SINK
2. Advertise FlowSpec with redirect-to-rt VRF-SINK
3. Send matching traffic
4. Verify traffic appears in VRF-SINK

**Pass Criteria:** Traffic redirected to target VRF

---

### 2.5.2 Redirect-to-VRF

**Test Name:** Advanced | Redirect-to-VRF Action

**Description:** Verify redirect to named VRF

**Steps:**
1. Configure VRF-SINK
2. Advertise FlowSpec with redirect-to-vrf VRF-SINK
3. Verify traffic forwarding

**Pass Criteria:** Traffic uses VRF-SINK routing table

---

## 2.6 BGP Neighbor Groups

**Test Name:** Advanced | FlowSpec via Neighbor Group

**Description:** Verify FlowSpec-VPN config via neighbor-group

**Steps:**
1. Configure neighbor-group FS-PEERS with ipv4-flowspec-vpn
2. Assign multiple neighbors to group
3. Verify all peers enabled for FlowSpec

**Pass Criteria:** Group config applied to all members

---

## 2.7 Multi-Neighbor FlowSpec

**Test Name:** Advanced | Multiple Peers Advertising FlowSpec

**Description:** Verify FlowSpec from multiple peers

**Steps:**
1. Configure FlowSpec-VPN with R2, R4, R6
2. Each advertises different FlowSpec rule
3. Verify all rules installed

**Pass Criteria:** All peer rules coexist and enforce

---

# 3. DNOS-SPECIFIC BEHAVIOR TESTS

## 3.1 No VPN Label Verification

**Test Name:** DNOS | No VPN Label in FlowSpec-VPN NLRI

**Description:** Verify DNOS does NOT expect/use VPN label for FlowSpec-VPN

**Steps:**
1. Establish FlowSpec-VPN session
2. Advertise FlowSpec-VPN NLRI
3. Verify no MPLS label in path attributes
4. Confirm enforcement works without label

**Pass Criteria:**
- FlowSpec-VPN works without MPLS label
- No label-related errors
- Datapath enforcement succeeds

---

## 3.2 No NH Reachability Check

**Test Name:** DNOS | No Next-Hop Reachability Check for FlowSpec-VPN

**Description:** Verify FlowSpec-VPN path does NOT require NH reachability

**Steps:**
1. Advertise FlowSpec-VPN with unreachable next-hop (e.g., 99.99.99.99)
2. Verify NLRI is still accepted
3. Verify rule is installed

**Pass Criteria:**
- FlowSpec accepted despite unreachable NH
- Rule programmed in datapath
- No NH reachability errors

---

## 3.3 Redirect-to-IP Rejection (CRITICAL)

**Test Name:** DNOS-Negative | Reject redirect-to-ip Extended Community

**Description:** Verify DNOS rejects redirect-to-ip (draft-ietf-idr-flowspec-redirect-ip NOT supported)

**Steps:**
1. Establish FlowSpec-VPN session
2. R2: Advertise FlowSpec with redirect-to-ip 10.0.0.1 extended community
3. DUT: Check if NLRI is rejected or action ignored

**Pass Criteria:**
- redirect-to-ip action is NOT installed
- No crash or error
- Other FlowSpec rules unaffected
- Log message indicates unsupported action

---

## 3.4 VRF Alphabetical Selection

**Test Name:** DNOS | VRF Selection by Alphabetical Order

**Description:** When multiple VRFs import same RT for redirect, first alphabetically is chosen

**Steps:**
1. Create VRFs: AAA_VRF, MMM_VRF, ZZZ_VRF - all importing RT 65000:500
2. Advertise FlowSpec with redirect-to-rt 65000:500
3. Send matching traffic
4. Verify traffic goes to AAA_VRF (first alphabetically)

**Pass Criteria:**
- Traffic redirected to AAA_VRF only
- MMM_VRF and ZZZ_VRF do not receive traffic
- Deterministic behavior

---

## 3.5 Cross-VRF Redirect Rejection (CRITICAL)

**Test Name:** DNOS-Negative | Reject Redirect from Non-Default to Default VRF

**Description:** Verify cannot redirect FlowSpec traffic from non-default VRF to default VRF

**Steps:**
1. Configure FlowSpec in VRF1 (non-default)
2. Attempt to configure redirect-to-vrf default
3. Or advertise FlowSpec with RT that would redirect to default

**Pass Criteria:**
- Configuration rejected OR
- Redirect action ignored
- Traffic stays in VRF1
- Error/warning logged

---

## 3.6 C=0 Only for Redirect-IP Copy Bit

**Test Name:** DNOS-Negative | Reject C=1 Copy Bit in redirect-IP

**Description:** Only C=0 supported; C=1 must be rejected

**Steps:**
1. Advertise FlowSpec with redirect-IP extended community
2. Set Copy bit C=1
3. Verify rejection

**Pass Criteria:**
- C=1 redirect-IP rejected
- C=0 redirect-IP accepted (if redirect-IP were supported)

---

## 3.7 Mixed Redirect Actions - Ignore redirect-to-ip

**Test Name:** DNOS | Mixed redirect-to-ip + redirect-to-rt

**Description:** When both redirect actions present, ignore redirect-to-ip

**Steps:**
1. Advertise FlowSpec with BOTH:
   - redirect-to-ip 10.0.0.1
   - redirect-to-rt 65000:200
2. Verify only redirect-to-rt is applied

**Pass Criteria:**
- redirect-to-rt action applied
- redirect-to-ip ignored
- Traffic goes to VRF with RT 65000:200

---

## 3.8 No RFC Validation Flow Required

**Test Name:** DNOS | Relaxed Validation (No RFC Section 6 Strict)

**Description:** DNOS does not require full RFC 8955 Section 6 validation

**Steps:**
1. Advertise FlowSpec that might fail strict RFC validation
2. Verify DNOS accepts

**Pass Criteria:**
- FlowSpec installed without strict validation
- Feature works as expected

---

## 3.9 Simpson Draft Redirect Only

**Test Name:** DNOS | Only draft-simpson-idr-flowspec-redirect Supported

**Description:** Verify redirect uses Simpson draft format

**Steps:**
1. Advertise redirect action per Simpson draft format
2. Verify correct redirect behavior

**Pass Criteria:**
- Simpson draft redirect works
- IETF draft redirect-to-ip rejected

---

# 4. NEGATIVE TESTING

## 4.1 NLRI Validation Failures (RFC 8955)

### 4.1.1 Length Mismatch

**Test Name:** Negative | Reject NLRI with Length Mismatch

**Description:** NLRI length byte doesn't match actual content

**Steps:**
1. Inject malformed NLRI with wrong length
2. Verify rejection/withdrawal

**Pass Criteria:** Malformed NLRI rejected

---

### 4.1.2 Oversized Prefix Length

**Test Name:** Negative | Reject Prefix Length > 32 (IPv4) or > 128 (IPv6)

**Steps:**
1. Advertise FlowSpec with prefix-length 33 for IPv4
2. Verify rejection

**Pass Criteria:** Invalid prefix rejected

---

### 4.1.3 Non-Zero Padding

**Test Name:** Negative | Reject Non-Zero Padding in Prefix

**Steps:**
1. Advertise prefix 10.0.0.0/8 but with non-zero bits in unused octets
2. Verify rejection

**Pass Criteria:** Padding violation rejected

---

### 4.1.4 Duplicate Component Types

**Test Name:** Negative | Reject Duplicate Components

**Steps:**
1. Advertise NLRI with two Type 1 (Destination) components
2. Verify rejection

**Pass Criteria:** Duplicate components rejected

---

### 4.1.5 Out-of-Order Components

**Test Name:** Negative | Reject Out-of-Order Components

**Steps:**
1. Advertise NLRI with components in wrong order (Type 3 before Type 1)
2. Verify rejection

**Pass Criteria:** Order violation rejected

---

### 4.1.6 Withdrawal on Validation Failure

**Test Name:** Negative | Automatic Withdrawal on Failure

**Steps:**
1. Inject invalid NLRI
2. Verify DUT withdraws rather than installs

**Pass Criteria:** Invalid routes withdrawn, not installed

---

## 4.2 Invalid Configuration

### 4.2.1 FlowSpec Without BGP Session

**Test Name:** Negative | FlowSpec Without BGP Neighbor

**Steps:**
1. Configure FlowSpec address-family without any neighbor
2. Verify commit behavior

**Pass Criteria:** Config accepted but no routes received

---

### 4.2.2 Import-VPN Without VRF

**Test Name:** Negative | import-vpn in Default VRF

**Steps:**
1. Try to configure import-vpn under default VRF FlowSpec
2. Verify behavior

**Pass Criteria:** Either rejected or ignored

---

## 4.3 Unsupported Actions

### 4.3.1 Unknown Action Community

**Test Name:** Negative | Unknown Extended Community

**Steps:**
1. Advertise FlowSpec with unknown action type
2. Verify handling

**Pass Criteria:** Unknown action ignored, rule still works

---

# 5. CLI TESTS

## 5.1 Configuration Commands

### 5.1.1 Basic FlowSpec Config

**Test Name:** CLI | Configure FlowSpec-VPN Address Family

**Commands to Test:**
```
protocols bgp 65000 neighbor X.X.X.X address-family ipv4-flowspec-vpn
protocols bgp 65000 neighbor X.X.X.X address-family ipv6-flowspec-vpn
network-services vrf VRF1 protocols bgp 65000 address-family ipv4-flowspec import-vpn
```

**Pass Criteria:** All configs commit cleanly

---

### 5.1.2 Maximum-Prefix

**Test Name:** CLI | FlowSpec Maximum-Prefix Limit

**Commands:**
```
address-family ipv4-flowspec-vpn
  maximum-prefix 1000
```

**Pass Criteria:** Limit enforced when exceeded

---

## 5.2 Show Commands

**Test Name:** CLI | All FlowSpec Show Commands

**Commands to Verify:**
```
show protocols bgp 65000 neighbor X.X.X.X address-family ipv4-flowspec-vpn
show bgp ipv4-flowspec-vpn summary
show bgp ipv4-flowspec-vpn routes
show bgp ipv4-flowspec-vpn routes detail
show bgp vrf VRF1 ipv4-flowspec routes
show network-services vrf VRF1 flowspec rules
show network-services vrf VRF1 flowspec counters
show flowspec instance
```

**Pass Criteria:** All show commands work and display correct data

---

## 5.3 Clear Commands

**Test Name:** CLI | FlowSpec Clear Commands

**Commands to Test:**
```
clear bgp ipv4-flowspec-vpn neighbor X.X.X.X
clear flowspec counters
clear flowspec counters vrf VRF1
```

**Pass Criteria:** Counters reset, sessions cleared as expected

---

## 5.4 Rollback/Commit

**Test Name:** CLI | FlowSpec Config Rollback

**Steps:**
1. Configure FlowSpec
2. `commit confirm 60`
3. `rollback 0`
4. Verify FlowSpec removed

**Pass Criteria:** Rollback works correctly

---

# 6. HA (HIGH AVAILABILITY) TESTS

## 6.1 Container Restart - BGP

**Test Name:** HA | BGP Container Restart with Active FlowSpec

**Description:** Restart bgp_rpd container during active FlowSpec session

**Steps:**
1. Establish FlowSpec-VPN session, verify rules installed
2. DUT: `docker restart bgp_rpd`
3. Wait for container recovery
4. Verify FlowSpec session re-established
5. Verify all rules re-installed
6. Verify traffic enforcement resumes

**Pass Criteria:**
- Container restarts within 60s
- BGP session re-established
- FlowSpec rules recovered
- Traffic enforcement works post-recovery
- No manual intervention needed

---

## 6.2 Process Restart - BGP

**Test Name:** HA | Kill BGP Process with Active FlowSpec

**Steps:**
1. Establish FlowSpec session with 100 rules
2. DUT: `kill -9 $(pgrep bgp_rpd)`
3. Monitor recovery
4. Verify rules restored

**Pass Criteria:**
- Process restarts automatically
- FlowSpec recovered
- Counters may reset but rules intact

---

## 6.3 NCC/NCM Switchover

**Test Name:** HA | NCM Switchover with FlowSpec

**Description:** Active NCM failure, standby takes over

**Steps:**
1. Configure FlowSpec on active NCM
2. Verify rules installed on NCPs
3. Trigger NCM switchover
4. Verify standby becomes active
5. Verify FlowSpec state preserved

**Pass Criteria:**
- Switchover completes < 30s
- FlowSpec rules persist
- No traffic black hole > 3s

---

## 6.4 NCP Restart

**Test Name:** HA | NCP Restart with FlowSpec Rules

**Steps:**
1. Configure FlowSpec rules
2. Restart NCP hosting FlowSpec interface
3. Verify rules re-programmed

**Pass Criteria:**
- NCP recovers
- FlowSpec rules re-installed
- Traffic enforcement resumes

---

## 6.5 Graceful Restart - Sender

**Test Name:** HA | FlowSpec Graceful Restart (DUT as Sender)

**Steps:**
1. Enable GR on DUT
2. Establish FlowSpec session
3. Restart BGP on DUT
4. Verify peer maintains routes during GR

**Pass Criteria:**
- Peer keeps FlowSpec during GR period
- Session re-established
- No rule flap

---

## 6.6 Graceful Restart - Receiver

**Test Name:** HA | FlowSpec Graceful Restart (DUT as Receiver)

**Steps:**
1. Enable GR on DUT
2. Establish FlowSpec from peer
3. Peer restarts BGP
4. DUT maintains FlowSpec during GR

**Pass Criteria:**
- DUT keeps FlowSpec rules during peer GR
- Rules maintained for GR-time
- Normal operation after peer recovers

---

## 6.7 Dual NCM HA

**Test Name:** HA | Dual NCM FlowSpec Sync

**Steps:**
1. Configure FlowSpec on active NCM
2. Verify standby NCM synced
3. Switchover
4. Verify no rule loss

**Pass Criteria:** State synced between NCMs

---

## 6.8 Session Flap Recovery

**Test Name:** HA | FlowSpec Session Flap

**Steps:**
1. Establish FlowSpec session with 500 rules
2. Flap BGP session (shut/no shut) 10 times
3. Verify rules restored each time

**Pass Criteria:**
- All rules recovered after each flap
- No memory leak
- No stale rules

---

# 7. SCALE TESTS

## 7.1 Maximum FlowSpec Rules Per VRF

**Test Name:** Scale | Max FlowSpec Rules Per VRF

**Steps:**
1. Configure VRF with FlowSpec
2. Advertise increasing number of rules: 100, 500, 1000, 2000, 5000, 10000
3. Measure installation time
4. Verify all rules installed
5. Test traffic enforcement at scale

**Pass Criteria:**
- All rules installed (up to platform limit)
- Installation time linear
- Memory stable
- Enforcement works for all rules

**Expected Limits:**
- Per VRF: ~10,000 rules (verify)
- Total system: ~50,000 rules (verify)

---

## 7.2 Maximum FlowSpec Rules Total

**Test Name:** Scale | Max FlowSpec Rules System-Wide

**Steps:**
1. Create 10 VRFs
2. Add 5000 rules per VRF
3. Verify total 50,000 rules
4. Test random enforcement

**Pass Criteria:** System handles max rules

---

## 7.3 Memory Under Load

**Test Name:** Scale | FlowSpec Memory Utilization

**Steps:**
1. Record baseline memory
2. Add 10,000 FlowSpec rules
3. Measure memory increase
4. Remove rules
5. Verify memory returns to baseline

**Pass Criteria:**
- Memory increase proportional to rules
- No memory leak on removal
- < 1GB for 10K rules (verify)

---

## 7.4 Churn - Rapid Add/Remove

**Test Name:** Scale | FlowSpec Churn Test

**Steps:**
1. Add 1000 rules
2. Remove 500 rules
3. Add 500 different rules
4. Repeat 100 times
5. Monitor stability

**Pass Criteria:**
- No crashes
- Correct rule count maintained
- No stale entries

---

## 7.5 High-Volume Install (RFC)

**Test Name:** Scale | Rapid FlowSpec Install

**Steps:**
1. Advertise 1000 FlowSpec rules in 1 second burst
2. Measure installation latency
3. Verify all installed correctly

**Pass Criteria:**
- All 1000 rules installed < 10s
- No dropped updates

---

## 7.6 Convergence Time

**Test Name:** Scale | FlowSpec Convergence

**Steps:**
1. Measure time from BGP update to datapath enforcement
2. Test with 1, 10, 100, 1000 rules

**Pass Criteria:**
- Single rule: < 100ms
- 1000 rules: < 5s

---

# 8. UPGRADE TESTS

## 8.1 In-Service Software Upgrade (ISSU)

**Test Name:** Upgrade | ISSU with Active FlowSpec

**Steps:**
1. Configure FlowSpec with 1000 rules
2. Start ISSU to new version
3. Monitor FlowSpec state during upgrade
4. Verify rules maintained after upgrade

**Pass Criteria:**
- FlowSpec rules survive upgrade
- Traffic disruption < 50ms
- No manual re-configuration needed

---

## 8.2 Version Rollback

**Test Name:** Upgrade | Rollback with FlowSpec

**Steps:**
1. Upgrade with FlowSpec active
2. Rollback to previous version
3. Verify FlowSpec state

**Pass Criteria:**
- FlowSpec works after rollback
- Rules may need re-advertisement

---

## 8.3 Hitless Upgrade (NCM)

**Test Name:** Upgrade | NCM Hitless Upgrade

**Steps:**
1. Configure FlowSpec
2. Upgrade standby NCM
3. Switchover
4. Upgrade other NCM
5. Verify FlowSpec throughout

**Pass Criteria:** Zero traffic loss during upgrade

---

## 8.4 NCP Upgrade

**Test Name:** Upgrade | NCP Upgrade with FlowSpec

**Steps:**
1. FlowSpec rules on NCP
2. Upgrade NCP image
3. Verify rules re-programmed

**Pass Criteria:** Rules restored after NCP upgrade

---

# 9. OPENCONFIG / NETCONF TESTS

## 9.1 OpenConfig Model

**Test Name:** OC | FlowSpec via OpenConfig

**Description:** (From US SW-221388)

**Steps:**
1. Configure FlowSpec via OpenConfig model
2. Verify configuration applied
3. Read back via OpenConfig
4. Verify operational state

**Pass Criteria:**
- OpenConfig config works
- State readable via OC

---

## 9.2 NETCONF Operations

**Test Name:** NETCONF | FlowSpec CRUD

**Steps:**
1. Create FlowSpec config via NETCONF
2. Read via NETCONF get
3. Update FlowSpec config
4. Delete FlowSpec config

**Pass Criteria:** All CRUD operations work

---

## 9.3 gNMI Subscribe

**Test Name:** gNMI | FlowSpec State Subscription

**Steps:**
1. Subscribe to FlowSpec oper state via gNMI
2. Add/remove FlowSpec rules
3. Verify streaming updates received

**Pass Criteria:** State changes streamed correctly

---

# 10. INTEROP TESTS

## 10.1 Cisco IOS-XR Peer

**Test Name:** Interop | FlowSpec-VPN with Cisco IOS-XR

**Steps:**
1. Configure FlowSpec-VPN between DNOS and IOS-XR
2. Verify bidirectional rule exchange
3. Verify enforcement on both sides

**Pass Criteria:**
- Session established
- Rules exchanged correctly
- Actions enforced

---

## 10.2 Wire-Format Encoding (RFC 4.3)

**Test Name:** Interop | RFC 4.3 Encoding Examples

**Steps:**
1. Capture FlowSpec UPDATE from DUT
2. Compare wire-format against RFC 8955 Section 4.3 examples
3. Verify exact octet sequences

**Pass Criteria:** Wire format matches RFC

---

## 10.3 Multi-Vendor Topology

**Test Name:** Interop | Full Multi-Vendor FlowSpec

**Steps:**
1. DNOS DUT, Cisco R2, Juniper R4 (if available)
2. FlowSpec rules from all vendors
3. Verify mutual enforcement

**Pass Criteria:** All vendors interoperate

---

# APPENDIX A: Test Summary Matrix

| Category | Test Count | Priority |
|----------|:----------:|:--------:|
| Basic Functionality | 12 | 🔴 HIGH |
| Advanced Functionality | 8 | 🟡 MED |
| DNOS-Specific | 9 | 🔴 HIGH |
| Negative Testing | 10 | 🔴 HIGH |
| CLI Tests | 8 | 🟡 MED |
| HA Tests | 8 | 🔴 HIGH |
| Scale Tests | 6 | 🔴 HIGH |
| Upgrade Tests | 4 | 🔴 HIGH |
| OpenConfig/NETCONF | 3 | 🟡 MED |
| Interop Tests | 3 | 🟡 MED |
| **TOTAL** | **71** | |

---

# APPENDIX B: DNOS-Specific Quick Reference

| DNOS Behavior | Test Section |
|---------------|--------------|
| No VPN label | 3.1 |
| No NH reachability check | 3.2 |
| redirect-to-ip NOT supported | 3.3 |
| VRF alphabetical order | 3.4 |
| No cross-VRF redirect to default | 3.5 |
| C=0 only for redirect-IP | 3.6 |
| Mixed redirect: ignore redirect-to-ip | 3.7 |
| Relaxed validation | 3.8 |
| Simpson draft only | 3.9 |

---

_End of Complete Test Plan_
