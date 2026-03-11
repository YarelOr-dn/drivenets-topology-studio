# SW-234158: FlowSpec VPN | Happy Flow

## Test Category: Basic Functionality
**Type:** 🆕 NEW Feature Tests

---

## Prerequisites

- Topology from SW-234160 is configured and validated
- BGP FlowSpec-VPN sessions Established
- VRF INTERNET-VRF with import-vpn configured
- Spirent connected to PE1

---

## Test Cases

### HF-01: IPv4 FlowSpec-VPN Session Establishment
**Type:** 🆕 NEW

**Objective:** Verify IPv4 FlowSpec-VPN (SAFI 134) BGP session comes up

**Steps:**
1. On RR, configure FlowSpec-VPN to PE1:
   ```
   configure
   protocols bgp 65000
     neighbor 10.0.0.1
       address-family ipv4-flowspec-vpn
         admin-state enabled
       !
     !
   !
   commit
   ```
2. On PE1 (DUT), verify session:
   ```
   show bgp ipv4 flowspec-vpn summary
   ```
3. Verify capability negotiated

**Expected Result:**
- Session shows "Established"
- SAFI 134 capability negotiated

**Pass Criteria:**
- [ ] BGP session Established
- [ ] Capability shown in neighbor details

---

### HF-02: IPv4 FlowSpec-VPN Drop Action
**Type:** 🆕 NEW

**Objective:** Verify FlowSpec drop rule is received, imported to VRF, and enforces

**Steps:**
1. On RR, inject FlowSpec-VPN NLRI (simulate Arbor):
   - Destination: 10.10.10.0/24
   - Action: drop (traffic-rate 0)
   - RT: 65000:100
2. On PE1 (DUT), verify route received:
   ```
   show bgp ipv4 flowspec-vpn routes
   ```
3. Verify imported to VRF:
   ```
   show bgp instance vrf INTERNET-VRF ipv4 flowspec routes
   ```
4. Verify installed in NCP:
   ```
   show flowspec ncp
   ```
5. From Spirent, send traffic to 10.10.10.1 at 1Gbps
6. Verify traffic dropped:
   ```
   show flowspec-local-policies counters
   ```

**Expected Result:**
- FlowSpec NLRI received
- Imported to VRF via RT match
- NCP shows "Installed"
- All matching traffic dropped
- Counters increment

**Pass Criteria:**
- [ ] Route in BGP table
- [ ] Route in VRF table
- [ ] `show flowspec ncp` = Installed
- [ ] 0 packets egress
- [ ] Counters > 0

---

### HF-03: IPv4 FlowSpec-VPN Rate-Limit Action
**Type:** 🆕 NEW

**Objective:** Verify traffic-rate action limits bandwidth

**Steps:**
1. Inject FlowSpec with traffic-rate 10000000 (10Mbps)
   - Destination: 10.10.20.0/24
   - RT: 65000:100
2. Verify on PE1:
   ```
   show bgp instance vrf INTERNET-VRF ipv4 flowspec routes
   show flowspec ncp
   ```
3. Send 100Mbps from Spirent to 10.10.20.1
4. Measure egress rate

**Expected Result:**
- Egress rate = ~10Mbps ±10%

**Pass Criteria:**
- [ ] Egress rate between 9-11Mbps
- [ ] Excess traffic dropped

---

### HF-04: IPv6 FlowSpec-VPN Drop Action
**Type:** 🆕 NEW

**Objective:** Verify IPv6 FlowSpec-VPN (AFI=2, SAFI=134)

**Steps:**
1. Inject IPv6 FlowSpec-VPN:
   - Destination: 2001:db8:100::/64
   - Action: drop
   - RT: 65000:100
2. Verify:
   ```
   show bgp ipv6 flowspec-vpn routes
   show bgp instance vrf INTERNET-VRF ipv6 flowspec routes
   show flowspec ncp
   ```
3. Send IPv6 traffic from Spirent
4. Verify dropped

**Pass Criteria:**
- [ ] IPv6 FlowSpec received
- [ ] Imported to VRF
- [ ] Traffic dropped

---

### HF-05: Non-Default VRF FlowSpec Import
**Type:** 🆕 NEW

**Objective:** Verify FlowSpec imported to VRF via RT match

**Steps:**
1. On PE1, verify VRF config:
   ```
   show network-services vrf INTERNET-VRF protocols bgp address-family ipv4-flowspec
   ```
   - import-vpn route-target 65000:100
2. Advertise FlowSpec with RT 65000:100
3. Verify imported:
   ```
   show bgp instance vrf INTERNET-VRF ipv4 flowspec routes
   ```
4. Advertise FlowSpec with different RT 65000:999 (no match)
5. Verify NOT imported to INTERNET-VRF

**Pass Criteria:**
- [ ] Matching RT → imported
- [ ] Non-matching RT → NOT imported

---

### HF-06: Neighbor-Group FlowSpec-VPN
**Type:** 🔄 REG (neighbor-group is existing feature)

**Objective:** Verify FlowSpec-VPN config via neighbor-group

**Steps:**
1. Configure neighbor-group with flowspec-vpn:
   ```
   protocols bgp 65000
     neighbor-group FLOWSPEC-PEERS
       address-family ipv4-flowspec-vpn
         admin-state enabled
       !
     !
     neighbor 10.0.0.100
       neighbor-group FLOWSPEC-PEERS
     !
   !
   ```
2. Verify neighbor inherits config:
   ```
   show bgp neighbors 10.0.0.100
   ```
3. Verify FlowSpec works

**Pass Criteria:**
- [ ] Config inherited from group
- [ ] FlowSpec operational

---

### HF-07: Maximum-Prefix Limit
**Type:** 🔄 REG (maximum-prefix is existing feature)

**Objective:** Verify maximum-prefix limit for FlowSpec

**Steps:**
1. Configure maximum-prefix:
   ```
   protocols bgp 65000
     neighbor 10.0.0.100
       address-family ipv4-flowspec-vpn
         maximum-prefix 10
       !
     !
   !
   ```
2. Advertise 5 FlowSpec rules → accepted
3. Advertise 11 FlowSpec rules → verify behavior (warning/teardown per config)

**Pass Criteria:**
- [ ] Under limit: all accepted
- [ ] Over limit: configured action

---

### HF-08: Policy In Filtering
**Type:** 🔄 REG (routing-policy is existing feature)

**Objective:** Verify routing-policy filters FlowSpec

**Steps:**
1. Create policy to reject specific FlowSpec:
   ```
   routing-policy
     policy REJECT-FLOWSPEC
       rule 10
         match destination-prefix 10.99.0.0/16
         action reject
       !
     !
   !
   ```
2. Apply to neighbor:
   ```
   protocols bgp 65000
     neighbor 10.0.0.100
       address-family ipv4-flowspec-vpn
         policy in REJECT-FLOWSPEC
       !
     !
   !
   ```
3. Advertise FlowSpec for 10.99.1.0/24 → rejected
4. Advertise FlowSpec for 10.10.1.0/24 → accepted

**Pass Criteria:**
- [ ] Matching policy → rejected
- [ ] Non-matching → accepted

---

### HF-09: Allow-as-in
**Type:** 🔄 REG (allow-as-in is existing feature)

**Objective:** Verify FlowSpec with own ASN accepted

**Steps:**
1. Configure allow-as-in:
   ```
   protocols bgp 65000
     neighbor 10.0.0.100
       address-family ipv4-flowspec-vpn
         allow-as-in
       !
     !
   !
   ```
2. Advertise FlowSpec with AS-PATH containing 65000
3. Verify accepted

**Pass Criteria:**
- [ ] FlowSpec with own ASN accepted

---

### HF-10: Nexthop Self
**Type:** 🔄 REG (nexthop self is existing feature)

**Objective:** Verify nexthop modification for FlowSpec

**Steps:**
1. Configure nexthop self:
   ```
   protocols bgp 65000
     neighbor 10.0.0.100
       address-family ipv4-flowspec-vpn
         nexthop self
       !
     !
   !
   ```
2. Verify NH handling on re-advertisement

**Pass Criteria:**
- [ ] NH modified correctly

---

### HF-11: RT-C Integration
**Type:** 🔄 REG (RT-C is existing feature)

**Objective:** Verify RT-C controls FlowSpec distribution

**Steps:**
1. Enable RT-C on PE1:
   ```
   protocols bgp 65000
     address-family rt-constrain
     !
     neighbor 10.0.0.100
       address-family rt-constrain
     !
   !
   ```
2. Configure VRF with RT 65000:100
3. Verify RT-C advertises RT
4. Verify only FlowSpec with RT 65000:100 received

**Pass Criteria:**
- [ ] RT-C filters FlowSpec distribution

---

### HF-12: Route Reflector Path
**Type:** 🔄 REG (RR is existing feature)

**Objective:** Verify FlowSpec-VPN works via RR

**Steps:**
1. On RR (CL-408D), receive FlowSpec from simulated Arbor
2. Verify reflected to PE1:
   ```
   show bgp ipv4 flowspec-vpn neighbors 10.0.0.1 advertised-routes
   ```
3. Verify PE1 receives with cluster-id

**Pass Criteria:**
- [ ] FlowSpec reflected correctly
- [ ] Cluster-id present

---

### HF-13: Redirect-to-RT Action
**Type:** 🆕 NEW (DNOS Simpson draft)

**Objective:** Verify redirect-to-rt extended community

**Steps:**
1. Create sink VRF:
   ```
   network-services
     vrf instance SINK-VRF
       route-target import 65000:999
     !
   !
   ```
2. Advertise FlowSpec with redirect-to-rt 65000:999
3. Send matching traffic in INTERNET-VRF
4. Verify traffic redirected to SINK-VRF

**Pass Criteria:**
- [ ] Traffic redirected to SINK-VRF

---

### HF-14: Enable/Disable FlowSpec
**Type:** 🆕 NEW + ⚠️ GAP

**Objective:** Verify admin-state controls FlowSpec

**Steps:**
1. Configure FlowSpec, verify working
2. Disable:
   ```
   protocols bgp 65000
     neighbor 10.0.0.100
       address-family ipv4-flowspec-vpn
         admin-state disabled
       !
     !
   !
   commit
   ```
3. Verify FlowSpec session down
4. Verify rules removed from NCP:
   ```
   show flowspec ncp
   ```
5. Re-enable, verify recovered

**Pass Criteria:**
- [ ] Disabled → session down, rules removed
- [ ] Re-enabled → session up, rules restored

---

### HF-15: Configure/Delete FlowSpec
**Type:** 🆕 NEW + ⚠️ GAP

**Objective:** Verify clean removal and re-configuration

**Steps:**
1. Configure FlowSpec completely, receive rules
2. Delete entire FlowSpec config:
   ```
   no protocols bgp 65000 neighbor 10.0.0.100 address-family ipv4-flowspec-vpn
   commit
   ```
3. Verify no stale rules:
   ```
   show flowspec ncp
   show bgp ipv4 flowspec-vpn summary
   ```
4. Re-configure FlowSpec
5. Verify works again

**Pass Criteria:**
- [ ] Clean deletion
- [ ] No stale state
- [ ] Re-configuration works

---

## Summary Matrix

| Test | Type | Description | Priority |
|------|------|-------------|----------|
| HF-01 | 🆕 NEW | Session establishment | HIGH |
| HF-02 | 🆕 NEW | Drop action | HIGH |
| HF-03 | 🆕 NEW | Rate-limit action | HIGH |
| HF-04 | 🆕 NEW | IPv6 FlowSpec | HIGH |
| HF-05 | 🆕 NEW | VRF import | HIGH |
| HF-06 | 🔄 REG | Neighbor-group | MED |
| HF-07 | 🔄 REG | Maximum-prefix | MED |
| HF-08 | 🔄 REG | Policy In | MED |
| HF-09 | 🔄 REG | Allow-as-in | MED |
| HF-10 | 🔄 REG | Nexthop self | MED |
| HF-11 | 🔄 REG | RT-C | MED |
| HF-12 | 🔄 REG | Route Reflector | HIGH |
| HF-13 | 🆕 NEW | Redirect-to-RT | HIGH |
| HF-14 | 🆕 NEW | Enable/Disable | HIGH |
| HF-15 | 🆕 NEW | Configure/Delete | HIGH |

---
