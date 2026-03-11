# FlowSpec VPN - Complete Test Plan (DNOS Syntax Corrected)

_Version: 2.1 | Generated: 2026-01-13_
_DNOS CLI Syntax Verified against: SW-182545 EPIC, limits.json, DNOS_CLI_Commands_

---

## Test Plan Overview

| Metric | Count |
|--------|-------|
| Total Test Categories | 10 |
| Total Test Cases | 90+ |
| DNOS-Specific Tests | 9 |
| DP Specifics Tests | 7 |
| HA Tests | 4 |
| Scale Tests | 6 |
| Upgrade Tests | 1 |

---

## DNOS CLI SYNTAX REFERENCE

### ✅ CORRECT DNOS FlowSpec CLI Hierarchy

Based on EPIC SW-182545 and DNOS documentation:

#### Default VRF - Neighbor FlowSpec-VPN (SAFI 134):
```
protocols bgp ASN
  neighbor ADDRESS address-family ipv4-flowspec-vpn
  neighbor ADDRESS address-family ipv6-flowspec-vpn
  neighbor-group NAME address-family ipv4-flowspec-vpn
  neighbor-group NAME address-family ipv6-flowspec-vpn
```

#### Non-Default VRF - FlowSpec Import:
```
network-services
  vrf instance NAME
    protocols bgp ASN
      address-family ipv4-flowspec
        import-vpn route-target RT
      !
      address-family ipv6-flowspec
        import-vpn route-target RT
      !
    !
  !
!
```

#### Neighbor AFI-SAFI Features (for flowspec-vpn):
```
policy in
policy out
allow-as-in
as-loop-check
maximum-prefix
nexthop {self | ADDRESS}
```

#### Show Commands:
```
show bgp instance vrf [vrf-name] [address-family] [sub-address-family] statistics
show flowspec ncp [ncp-id]
show flowspec ncp [ncp-id] nlri [nlri]
show flowspec-local-policies counters {address-family [ipv4/ipv6]}
```

---

# 1. BASIC FUNCTIONALITY

## 1.1 IPv4 FlowSpec-VPN - Default VRF

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
- FlowSpec NLRI 10.10.10.0/24 received and visible in routes
- `show flowspec ncp` shows rule as "Installed"
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
   configure
   network-services
     vrf instance VRF1
       protocols
         bgp 65000
           address-family ipv4-flowspec
             import-vpn route-target 65000:100
           !
         !
       !
     !
   !
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
3. R2: Advertise FlowSpec-VPN with RT 65000:100
4. DUT: Verify routes imported to VRF:
   ```
   show bgp instance vrf VRF1 ipv4 flowspec routes
   show flowspec ncp
   ```
5. Verify rule installed in VRF1 datapath

**Pass Criteria:**
- VRF1 exists with import-vpn RT 65000:100
- FlowSpec imported into VRF1 (visible in `show bgp instance vrf VRF1`)
- Default VRF may show RIB-Install-Filtered
- `show flowspec ncp` shows rule "Installed"
- Traffic in VRF1 context is dropped

---

## 1.3 IPv6 FlowSpec-VPN - Default VRF

**Test Name:** Basic | IPv6 FlowSpec-VPN Default VRF

**Description:** Verify IPv6 FlowSpec-VPN (AFI=2, SAFI=134)

**Steps:**
1. DUT: `rollback 0`
2. Configure:
   ```
   configure
   protocols
     bgp 65000
       neighbor 2001:db8::2
         address-family ipv6-flowspec-vpn
       !
     !
   !
   commit confirm 60
   commit
   ```
3. R2: Advertise IPv6 FlowSpec `dst 2001:db8:100::/64 action drop`
4. DUT:
   ```
   show bgp ipv6 flowspec-vpn routes
   show flowspec ncp
   ```
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
1. DUT: `rollback 0`
2. Configure:
   ```
   configure
   network-services
     vrf instance VRF1
       protocols
         bgp 65000
           address-family ipv6-flowspec
             import-vpn route-target 65000:100
           !
         !
       !
     !
   !
   protocols
     bgp 65000
       neighbor 2001:db8::2
         address-family ipv6-flowspec-vpn
       !
     !
   !
   commit confirm 60
   commit
   ```
3. R2: Advertise IPv6 FlowSpec-VPN with RT 65000:100
4. DUT:
   ```
   show bgp instance vrf VRF1 ipv6 flowspec routes
   ```

**Pass Criteria:**
- IPv6 FlowSpec imported to VRF1
- Traffic enforcement works

---

## 1.5 Neighbor Group Configuration

**Test Name:** Basic | FlowSpec-VPN via Neighbor-Group

**Description:** Verify FlowSpec-VPN inherited from neighbor-group

**Steps:**
1. DUT: `rollback 0`
2. Configure:
   ```
   configure
   protocols
     bgp 65000
       neighbor-group FS-GROUP
         address-family ipv4-flowspec-vpn
       !
       neighbor 1.4.14.2
         neighbor-group FS-GROUP
       !
       neighbor 1.5.15.2
         neighbor-group FS-GROUP
       !
     !
   !
   commit confirm 60
   commit
   ```
3. Verify both neighbors have FlowSpec-VPN enabled

**Pass Criteria:**
- Both neighbors inherit ipv4-flowspec-vpn from group
- FlowSpec rules received from both peers

---

## 1.6 Neighbor AFI-SAFI Features

### 1.6.1 Maximum-Prefix

**Test Name:** Basic | FlowSpec Maximum-Prefix Limit

**Steps:**
1. Configure:
   ```
   configure
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
           maximum-prefix 100
         !
       !
     !
   !
   commit
   ```
2. Advertise 50 FlowSpec rules - verify accepted
3. Advertise 101 FlowSpec rules - verify behavior

**Pass Criteria:**
- Under limit: all rules accepted
- At/over limit: warning/session action per config

---

### 1.6.2 Policy In/Out

**Test Name:** Basic | FlowSpec with Policy In

**Steps:**
1. Create routing-policy to filter FlowSpec
2. Apply to neighbor:
   ```
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
           policy in FLOWSPEC-FILTER
         !
       !
     !
   ```
3. Verify policy filtering

**Pass Criteria:**
- Policy applied to FlowSpec routes
- Filtered routes not installed

---

### 1.6.3 Allow-as-in

**Test Name:** Basic | FlowSpec with allow-as-in

**Steps:**
1. Configure:
   ```
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
           allow-as-in
         !
       !
     !
   ```
2. Advertise FlowSpec with own ASN in path
3. Verify accepted

**Pass Criteria:**
- FlowSpec with own ASN accepted when allow-as-in enabled

---

### 1.6.4 Nexthop Self

**Test Name:** Basic | FlowSpec with nexthop self

**Steps:**
1. Configure:
   ```
   protocols
     bgp 65000
       neighbor 1.4.14.2
         address-family ipv4-flowspec-vpn
           nexthop self
         !
       !
     !
   ```
2. Verify NH handling on re-advertisement

**Pass Criteria:**
- NH modified correctly

---

# 2. ADVANCED FUNCTIONALITY

## 2.1 RT-C (Route Target Constraint) Integration

**Test Name:** Advanced | RT-C with FlowSpec-VPN

**Description:** Verify RT-C controls FlowSpec-VPN distribution

**Steps:**
1. Configure RT-C on DUT:
   ```
   configure
   protocols
     bgp 65000
       address-family rt-constrain
       !
       neighbor 1.4.14.2
         address-family rt-constrain
       !
     !
   !
   ```
2. Configure VRF with specific RT import
3. Verify only FlowSpec with matching RT is received from RR

**Pass Criteria:**
- RT-C filters FlowSpec distribution
- Only VRFs with import-vpn RT receive matching FlowSpec

---

## 2.2 Route Reflector Topology

**Test Name:** Advanced | FlowSpec-VPN via Route Reflector

**Description:** Verify FlowSpec-VPN works through RR (typical Arbor deployment)

**Steps:**
1. Configure DUT as RR client:
   ```
   protocols
     bgp 65000
       neighbor 1.2.12.2   # RR (R6)
         address-family ipv4-flowspec-vpn
       !
     !
   ```
2. R6 as RR with FlowSpec-VPN enabled
3. R2 advertises FlowSpec-VPN (Arbor simulator)
4. Verify DUT receives via R6

**Pass Criteria:**
- FlowSpec reflected correctly with cluster-id
- Rules installed on DUT

---

## 2.3 eBGP External Peer

**Test Name:** Advanced | FlowSpec-VPN eBGP Peer

**Description:** Verify FlowSpec-VPN over eBGP

**Steps:**
1. Configure eBGP peer for FlowSpec-VPN:
   ```
   protocols
     bgp 65000
       neighbor 1.4.14.2
         peer-as 65001
         address-family ipv4-flowspec-vpn
       !
     !
   ```
2. Verify NLRI exchange
3. Verify next-hop handling (may need nexthop self)

**Pass Criteria:**
- eBGP FlowSpec works
- NH resolved or set to self

---

## 2.4 Multi-VRF Import Same RT

**Test Name:** Advanced | Multiple VRFs Import Same FlowSpec

**Description:** Verify FlowSpec imported to multiple VRFs with same RT

**Steps:**
1. Create two VRFs importing same RT:
   ```
   network-services
     vrf instance VRF1
       protocols
         bgp 65000
           address-family ipv4-flowspec
             import-vpn route-target 65000:100
           !
         !
       !
     !
     vrf instance VRF2
       protocols
         bgp 65000
           address-family ipv4-flowspec
             import-vpn route-target 65000:100
           !
         !
       !
     !
   !
   ```
2. Advertise FlowSpec with RT 65000:100
3. Verify both VRFs receive and install

**Pass Criteria:**
- FlowSpec installed in BOTH VRF1 and VRF2
- Traffic dropped in both VRFs

---

## 2.5 Redirect Actions

### 2.5.1 Redirect-to-RT (Simpson Draft - SUPPORTED)

**Test Name:** Advanced | Redirect-to-RT Action

**Description:** Verify redirect using RT extended community

**Steps:**
1. Create VRF-SINK with RT 65000:999
2. Advertise FlowSpec with redirect-to-rt extended community 65000:999
3. Send matching traffic in source VRF
4. Verify traffic appears in VRF-SINK

**Pass Criteria:**
- Traffic redirected to target VRF based on RT
- Lookup performed in VRF-SINK routing table

---

# 3. DNOS-SPECIFIC BEHAVIOR TESTS

## 3.1 No VPN Label Verification

**Test Name:** DNOS | No VPN Label in FlowSpec-VPN NLRI

**Description:** Per SW-182545: DNOS does NOT expect/use VPN label for FlowSpec-VPN

**Steps:**
1. Establish FlowSpec-VPN session
2. Advertise FlowSpec-VPN NLRI (without VPN label)
3. Verify rule installed:
   ```
   show flowspec ncp
   ```
4. Confirm enforcement works

**Pass Criteria:**
- FlowSpec-VPN works WITHOUT MPLS label
- No label-related errors
- `show flowspec ncp` shows "Installed"

---

## 3.2 No NH Reachability Check

**Test Name:** DNOS | No Next-Hop Reachability Check for FlowSpec-VPN

**Description:** Per SW-182545: FlowSpec-VPN does NOT require NH reachability

**Steps:**
1. Advertise FlowSpec-VPN with unreachable next-hop (e.g., 99.99.99.99)
2. Verify NLRI is still accepted:
   ```
   show bgp ipv4 flowspec-vpn routes
   ```
3. Verify rule is installed:
   ```
   show flowspec ncp
   ```

**Pass Criteria:**
- FlowSpec accepted despite unreachable NH
- Rule programmed in datapath ("Installed")
- No NH reachability errors

---

## 3.3 Redirect-to-IP Rejection (CRITICAL)

**Test Name:** DNOS-Negative | Reject redirect-to-ip Extended Community

**Description:** Per SW-182545: draft-ietf-idr-flowspec-redirect-ip NOT supported

**Steps:**
1. Establish FlowSpec-VPN session
2. R2: Advertise FlowSpec with redirect-to-ip 10.0.0.1 extended community
3. DUT: Check if NLRI is accepted but action ignored:
   ```
   show bgp ipv4 flowspec-vpn routes
   show flowspec ncp
   ```

**Pass Criteria:**
- redirect-to-ip action is NOT applied (ignored or rejected)
- No crash or error
- Other FlowSpec rules unaffected
- May see "action not supported" in `show flowspec ncp`

---

## 3.4 VRF Alphabetical Selection

**Test Name:** DNOS | VRF Selection by Alphabetical Order

**Description:** Per SW-182545: When multiple VRFs import same RT for redirect, first alphabetically is chosen

**Steps:**
1. Create VRFs: AAA_VRF, MMM_VRF, ZZZ_VRF - all importing RT 65000:500
2. Advertise FlowSpec with redirect-to-rt 65000:500
3. Send matching traffic
4. Verify traffic goes to AAA_VRF only

**Pass Criteria:**
- Traffic redirected to AAA_VRF (first alphabetically)
- MMM_VRF and ZZZ_VRF do NOT receive traffic
- Deterministic behavior

---

## 3.5 Cross-VRF Redirect Rejection (CRITICAL)

**Test Name:** DNOS-Negative | Reject Redirect from Non-Default to Default VRF

**Description:** Per SW-182545: Cannot redirect FlowSpec traffic from non-default VRF to default VRF

**Steps:**
1. Configure FlowSpec in VRF1 (non-default)
2. Attempt redirect to default VRF
3. Verify behavior

**Pass Criteria:**
- Redirect to default VRF rejected OR ignored
- Traffic stays in VRF1
- Error/warning logged

---

## 3.6 C=0 Only for Redirect-IP Copy Bit

**Test Name:** DNOS-Negative | Reject C=1 Copy Bit in redirect-IP

**Description:** Per SW-182545: Only C=0 supported

**Steps:**
1. Advertise FlowSpec with redirect-IP extended community
2. Set Copy bit C=1
3. Verify rejection

**Pass Criteria:**
- C=1 redirect-IP rejected or ignored
- C=0 handled per redirect-IP logic

---

## 3.7 Mixed Redirect Actions

**Test Name:** DNOS | Mixed redirect-to-ip + redirect-to-rt

**Description:** Per SW-182545: When both present, ignore redirect-to-ip, use redirect-to-rt

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

## 3.8 Relaxed Validation (No RFC Section 6 Strict)

**Test Name:** DNOS | Relaxed Validation

**Description:** Per SW-182545: DNOS does not require full RFC 8955 Section 6 validation flow

**Steps:**
1. Advertise FlowSpec that might fail strict RFC validation
2. Verify DNOS accepts if rule is otherwise valid

**Pass Criteria:**
- FlowSpec installed without strict validation errors
- Feature works as expected

---

## 3.9 Simpson Draft Redirect Only

**Test Name:** DNOS | Only draft-simpson-idr-flowspec-redirect Supported

**Description:** Verify redirect uses Simpson draft format only

**Steps:**
1. Advertise redirect action per Simpson draft format
2. Verify correct redirect behavior

**Pass Criteria:**
- Simpson draft redirect works
- IETF draft redirect-to-ip rejected/ignored

---

# 4. NEGATIVE TESTING

## 4.1 NLRI Validation Failures

### 4.1.1 Invalid Prefix Length

**Test Name:** Negative | Reject Prefix Length > 32 (IPv4)

**Steps:**
1. Inject FlowSpec NLRI with prefix-length 33 for IPv4
2. Verify rejection

**Pass Criteria:**
- Invalid prefix rejected
- Session remains up

---

### 4.1.2 Duplicate Component Types

**Test Name:** Negative | Reject Duplicate Components

**Steps:**
1. Advertise NLRI with two Type 1 (Destination) components
2. Verify rejection

**Pass Criteria:**
- Duplicate components rejected

---

## 4.2 Unsupported Actions

### 4.2.1 redirect-to-ip

**Test Name:** Negative | Unsupported redirect-to-ip

**Steps:**
1. Advertise FlowSpec with redirect-to-ip action
2. Verify action ignored or NLRI has no datapath effect

**Pass Criteria:**
- `show flowspec ncp` shows "action not supported" OR action ignored
- No crash

---

# 5. CLI TESTS

## 5.1 Configuration Commands

**Test Name:** CLI | All FlowSpec Configuration Commands

**Correct DNOS Commands to Test:**
```
# Default VRF - Neighbor FlowSpec-VPN SAFI
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv6-flowspec-vpn

# Neighbor-Group
protocols bgp 65000 neighbor-group FS-GROUP address-family ipv4-flowspec-vpn
protocols bgp 65000 neighbor-group FS-GROUP address-family ipv6-flowspec-vpn

# Neighbor in Group
protocols bgp 65000 neighbor-group FS-GROUP neighbor 1.1.1.1 address-family ipv4-flowspec-vpn

# Neighbor AFI-SAFI Features
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn policy in MY_POLICY
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn policy out MY_POLICY
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn allow-as-in
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn as-loop-check
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn maximum-prefix 1000
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn nexthop self
protocols bgp 65000 neighbor 1.1.1.1 address-family ipv4-flowspec-vpn nexthop 2.2.2.2

# Non-Default VRF - FlowSpec Import
network-services vrf instance VRF1 protocols bgp 65000 address-family ipv4-flowspec
network-services vrf instance VRF1 protocols bgp 65000 address-family ipv4-flowspec import-vpn route-target 65000:100
network-services vrf instance VRF1 protocols bgp 65000 address-family ipv6-flowspec
network-services vrf instance VRF1 protocols bgp 65000 address-family ipv6-flowspec import-vpn route-target 65000:100
```

**Pass Criteria:** All commands commit cleanly

---

## 5.2 Show Commands

**Test Name:** CLI | All FlowSpec Show Commands

**Correct DNOS Commands:**
```
# BGP FlowSpec routes
show bgp ipv4 flowspec-vpn summary
show bgp ipv4 flowspec-vpn routes
show bgp ipv6 flowspec-vpn summary
show bgp ipv6 flowspec-vpn routes

# VRF FlowSpec routes
show bgp instance vrf VRF1 ipv4 flowspec routes
show bgp instance vrf VRF1 ipv4 flowspec statistics
show bgp instance vrf VRF1 ipv6 flowspec routes

# NCP FlowSpec status (CRITICAL for DP verification)
show flowspec ncp
show flowspec ncp 0
show flowspec ncp 0 nlri "DstPrefix:=10.0.0.0/8"

# Local policies counters
show flowspec-local-policies counters
show flowspec-local-policies counters address-family ipv4
show flowspec-local-policies counters address-family ipv6
```

**Pass Criteria:** All show commands display correct data

---

## 5.3 Clear Commands

**Test Name:** CLI | FlowSpec Clear Commands

**Commands:**
```
# BGP session refresh
clear bgp neighbor 1.1.1.1 soft in
clear bgp neighbor 1.1.1.1 address-family ipv4-flowspec-vpn soft in
```

**Pass Criteria:** Sessions refreshed, routes re-advertised

---

# 6. DATAPATH (DP) SPECIFICS

## 6.1 NCP Rule Installation

**Test Name:** DP | Verify FlowSpec NCP Installation

**Description:** Verify FlowSpec rules programmed to all NCPs

**Steps:**
1. Configure FlowSpec and receive rules
2. Verify on ALL NCPs:
   ```
   show flowspec ncp 0
   show flowspec ncp 1
   show flowspec ncp 2
   # ... for all NCPs
   ```
3. Verify Status = "Installed" on all NCPs

**Pass Criteria:**
- All NCPs show same FlowSpec rules
- Status = "Installed" on all NCPs
- If any shows "Not installed", indicates NCP issue

---

## 6.2 Action Not Supported Handling

**Test Name:** DP | Unsupported Action Handling

**Description:** Verify behavior when action not supported in hardware

**Steps:**
1. Advertise FlowSpec with unsupported action (e.g., redirect-to-ip)
2. Check NCP status:
   ```
   show flowspec ncp 0 nlri "<nlri-string>"
   ```

**Pass Criteria:**
- `show flowspec ncp` shows "Not installed, nlri and/or action not supported"
- No crash
- Other rules unaffected

---

## 6.3 Counters Verification

**Test Name:** DP | FlowSpec Counter Accuracy

**Description:** Verify match counters reflect actual traffic

**Steps:**
1. Install FlowSpec drop rule
2. Send 1000 packets matching rule
3. Check counters:
   ```
   show flowspec-local-policies counters
   ```

**Pass Criteria:**
- Counter shows ~1000 matches (±5% for timing)
- Counter increments in real-time

---

## 6.4 Line-Rate Enforcement

**Test Name:** DP | FlowSpec Line-Rate Drop

**Description:** Verify drop action works at line rate

**Steps:**
1. Configure FlowSpec drop rule
2. Send 100Gbps traffic matching rule
3. Verify zero egress

**Pass Criteria:**
- All matching traffic dropped
- No egress traffic
- NCP CPU not impacted

---

## 6.5 Rate-Limit Accuracy

**Test Name:** DP | FlowSpec Rate-Limit Accuracy

**Description:** Verify rate-limit action enforces correct rate

**Steps:**
1. Advertise FlowSpec with `traffic-rate 10000000` (10Mbps)
2. Send 100Mbps traffic
3. Measure egress rate

**Pass Criteria:**
- Egress rate = 10Mbps ±10%
- Excess traffic dropped

---

## 6.6 Per-VRF Rule Isolation

**Test Name:** DP | VRF Rule Isolation

**Description:** Verify FlowSpec rules are VRF-scoped

**Steps:**
1. Install rule in VRF1 only (via import-vpn RT)
2. Send matching traffic in VRF1 → dropped
3. Send matching traffic in VRF2 (no rule) → forwarded
4. Send matching traffic in default VRF → forwarded

**Pass Criteria:**
- Rules only affect VRF where imported
- No cross-VRF rule leakage

---

## 6.7 Interface Type Coverage

**Test Name:** DP | FlowSpec on All Interface Types

**Description:** Verify FlowSpec works on all interface types

**Interface Types to Test:**
- Physical (ge400-0/0/x)
- Physical VLAN sub-interface (ge400-0/0/x.100)
- Bundle (bundle-x)
- Bundle VLAN sub-interface (bundle-x.100)
- IRB (irb100)

**Steps:**
1. Enable flowspec on each interface type
2. Verify FlowSpec rules enforced on each

**Pass Criteria:**
- All interface types support FlowSpec enforcement

---

# 7. HA TESTS

## 7.1 Container Restart - BGP

**Test Name:** HA | BGP Container Restart with Active FlowSpec

**Steps:**
1. Establish FlowSpec-VPN session, verify rules via `show flowspec ncp`
2. DUT: `docker restart bgp_rpd`
3. Wait for container recovery
4. Verify:
   ```
   show bgp ipv4 flowspec-vpn summary
   show flowspec ncp
   ```

**Pass Criteria:**
- Container restarts within 60s
- BGP session re-established
- FlowSpec rules recovered (via BGP re-advertisement)
- `show flowspec ncp` shows "Installed"

---

## 7.2 NCC/NCM Switchover

**Test Name:** HA | NCM Switchover with FlowSpec

**Steps:**
1. Configure FlowSpec, verify `show flowspec ncp` on all NCPs
2. Trigger NCM switchover
3. Verify:
   ```
   show flowspec ncp
   ```

**Pass Criteria:**
- Switchover completes < 30s
- FlowSpec rules persist on NCPs
- No traffic black hole > 3s

---

## 7.3 NCP Restart

**Test Name:** HA | NCP Restart with FlowSpec Rules

**Steps:**
1. Configure FlowSpec rules
2. Verify `show flowspec ncp 0` shows "Installed"
3. Restart NCP 0
4. Verify `show flowspec ncp 0` shows "Installed" after recovery

**Pass Criteria:**
- NCP recovers
- FlowSpec rules re-installed from NCM
- Traffic enforcement resumes

---

## 7.4 Graceful Restart

**Test Name:** HA | FlowSpec Graceful Restart

**Steps:**
1. Enable GR on DUT
2. Establish FlowSpec from peer
3. Peer restarts BGP (with GR)
4. DUT maintains FlowSpec during GR-stale-time

**Pass Criteria:**
- DUT keeps FlowSpec rules during peer GR
- Rules maintained for GR-time
- No datapath disruption

---

# 8. SCALE TESTS

**Reference:** SW-206883 (Scale User Story under SW-182545)

## 8.1 Maximum FlowSpec VPN Peers

**Test Name:** Scale | Max FlowSpec-VPN Peers

**Expected Limit:** ~8 peers (like scale of VPN RR)

**Steps:**
1. Configure 8 BGP neighbors with ipv4-flowspec-vpn
2. Verify all sessions established
3. Verify FlowSpec routes from all peers

**Pass Criteria:**
- 8 FlowSpec-VPN peers supported
- All sessions Established

---

## 8.2 Maximum FlowSpec VPN Routes

**Test Name:** Scale | Max FlowSpec-VPN Routes System-Wide

**Expected Limit:** ~20,000 routes across all VRFs (per SW-206883)

**Steps:**
1. Advertise 20,000 FlowSpec-VPN routes across multiple VRFs
2. Verify all routes received:
   ```
   show bgp ipv4 flowspec-vpn statistics
   ```
3. Monitor memory/CPU

**Pass Criteria:**
- 20,000 FlowSpec-VPN routes installed
- System stable

---

## 8.3 DP IPv4 Rules Limit

**Test Name:** Scale | DP IPv4 FlowSpec Rules

**Expected Limit:** 12,000 IPv4 rules (DP hardware limit)

**Steps:**
1. Advertise 12,000 IPv4 FlowSpec rules
2. Verify all installed in NCP:
   ```
   show flowspec ncp
   ```
3. Try 12,001 rules - verify behavior

**Pass Criteria:**
- 12,000 IPv4 rules installed in DP
- Beyond limit: new rules rejected with "Not installed, resources"

**Note:** DP resources shared among ALL FlowSpec entries regardless of VRF

---

## 8.4 DP IPv6 Rules Limit

**Test Name:** Scale | DP IPv6 FlowSpec Rules

**Expected Limit:** 4,000 IPv6 rules (DP hardware limit)

**Steps:**
1. Advertise 4,000 IPv6 FlowSpec rules
2. Verify all installed in NCP
3. Try 4,001 rules - verify behavior

**Pass Criteria:**
- 4,000 IPv6 rules installed in DP
- Beyond limit: new rules rejected

---

## 8.5 Maximum FlowSpec Rules Per VRF

**Test Name:** Scale | Max FlowSpec Rules Per VRF

**Expected Limit:** 3,000 rules per VRF

**Steps:**
1. Configure VRF with FlowSpec
2. Advertise 3,000 FlowSpec rules to single VRF
3. Verify all installed:
   ```
   show bgp instance vrf VRF1 ipv4 flowspec statistics
   show flowspec ncp
   ```
4. Try 3,001 rules to same VRF - verify behavior

**Pass Criteria:**
- 3,000 rules installed per VRF
- Beyond limit: warning/rejection or max-prefix action

---

## 8.6 Maximum VRFs with FlowSpec

**Test Name:** Scale | Max VRFs with FlowSpec AFI

**Expected Limit:** 512 VRFs with flowspec address-family

**Steps:**
1. Create 512 VRFs with ipv4-flowspec address-family and import-vpn
2. Verify all VRFs operational

**Pass Criteria:**
- 512 VRFs with FlowSpec supported

---

# 9. UPGRADE TESTS

## 9.1 In-Service Upgrade

**Test Name:** Upgrade | ISSU with Active FlowSpec

**Steps:**
1. Configure FlowSpec with 1000 rules
2. Verify `show flowspec ncp` shows all "Installed"
3. Start ISSU to new version
4. Monitor `show flowspec ncp` during upgrade
5. Verify rules maintained after upgrade

**Pass Criteria:**
- FlowSpec rules survive upgrade
- Minimal traffic disruption
- No manual re-configuration needed

---

# 10. OPENCONFIG / NETCONF

## 10.1 OpenConfig Model (US SW-221388)

**Test Name:** OC | FlowSpec via OpenConfig

**Steps:**
1. Configure FlowSpec via OpenConfig/NETCONF
2. Verify configuration applied
3. Read back via OpenConfig
4. Verify operational state

**Pass Criteria:**
- OpenConfig config works
- State readable via OC

---

# APPENDIX A: Syntax Corrections Made

| Original (Incorrect) | Corrected (DNOS) |
|---------------------|------------------|
| `show protocols bgp 65000 neighbor X address-family ipv4-flowspec-vpn` | `show bgp ipv4 flowspec-vpn summary/routes` |
| `show bgp vrf VRF1 ipv4-flowspec routes` | `show bgp instance vrf VRF1 ipv4 flowspec routes` |
| `show network-services vrf VRF1 flowspec rules` | `show flowspec ncp` |
| `show network-services vrf VRF1 flowspec counters` | `show flowspec-local-policies counters` |
| `network-services vrf VRF1 protocols bgp 65000 address-family ipv4-flowspec import-vpn` | `network-services vrf instance VRF1 protocols bgp 65000 address-family ipv4-flowspec import-vpn route-target RT` |
| `clear flowspec counters vrf VRF1` | `clear bgp neighbor X soft in` (for route refresh) |

---

# APPENDIX B: Limits Reference (from SW-206883 + limits.json)

## FlowSpec VPN Scale Targets (per SW-206883)

| Resource | Limit | Notes |
|----------|-------|-------|
| FlowSpec-VPN peers | ~8 | Like scale of VPN RR |
| FlowSpec-VPN routes total | ~20,000 | Across all VRFs |
| DP IPv4 rules | 12,000 | Hardware limit |
| DP IPv6 rules | 4,000 | Hardware limit |
| DP resources | Shared | Among ALL FlowSpec entries regardless of VRF |

## General FlowSpec Limits

| Resource | Limit |
|----------|-------|
| Flowspec rules per VRF | 3,000 |
| Total flowspec rules | 20,000 |
| Flowspec-enabled interfaces | 1,000 |
| VRFs with flowspec AFI | 512 |
| Local policies | 256 |
| Match-classes per policy | 1,024 |

---

_End of Complete Test Plan (DNOS Syntax Corrected)_
