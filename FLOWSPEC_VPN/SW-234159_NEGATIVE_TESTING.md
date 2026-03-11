# SW-234159: FlowSpec VPN | Negative Testing

## Test Category: Negative / Error Handling
**Type:** Mix of 🆕 NEW and DNOS-Specific Tests

---

## Prerequisites

- Topology from SW-234160 is configured and validated
- BGP FlowSpec-VPN sessions Established
- Ability to inject malformed FlowSpec NLRI (via Spirent BGP or IOS-XR)

---

## DNOS-Specific Negative Tests

### NEG-01: Redirect-to-IP Rejection (CRITICAL)
**Type:** 🆕 NEW (DNOS-Specific)

**Objective:** Per SW-182545: Verify DNOS rejects redirect-to-ip (draft-ietf-idr-flowspec-redirect-ip NOT supported)

**Steps:**
1. From RR, advertise FlowSpec with redirect-to-ip extended community:
   - redirect-to-ip 10.0.0.50
2. On PE1 (DUT), verify behavior:
   ```
   show bgp ipv4 flowspec-vpn routes
   show flowspec ncp
   ```

**Expected Result:**
- redirect-to-ip action is NOT applied
- NLRI may be accepted but action ignored
- `show flowspec ncp` shows "action not supported" OR no entry
- No crash

**Pass Criteria:**
- [ ] No crash/error
- [ ] Action not installed in DP
- [ ] Other FlowSpec rules unaffected

---

### NEG-02: Cross-VRF Redirect to Default VRF (CRITICAL)
**Type:** 🆕 NEW (DNOS-Specific)

**Objective:** Per SW-182545: Cannot redirect FlowSpec traffic from non-default VRF to default VRF

**Steps:**
1. Configure FlowSpec in INTERNET-VRF (non-default)
2. Advertise FlowSpec with redirect-to-rt targeting default VRF
3. Verify behavior

**Expected Result:**
- Redirect to default VRF rejected OR ignored
- Traffic stays in INTERNET-VRF
- Warning/error logged

**Pass Criteria:**
- [ ] No redirect to default VRF
- [ ] Traffic stays in source VRF

---

### NEG-03: C=1 Copy Bit Rejection
**Type:** 🆕 NEW (DNOS-Specific)

**Objective:** Per SW-182545: Only C=0 supported for redirect-IP

**Steps:**
1. Advertise FlowSpec with redirect-IP extended community
2. Set Copy bit C=1
3. Verify rejection/ignore

**Expected Result:**
- C=1 redirect-IP rejected or ignored

**Pass Criteria:**
- [ ] C=1 not applied

---

### NEG-04: Mixed Redirect Actions
**Type:** 🆕 NEW (DNOS-Specific)

**Objective:** Per SW-182545: When both redirect-to-ip and redirect-to-rt present, ignore redirect-to-ip

**Steps:**
1. Advertise FlowSpec with BOTH:
   - redirect-to-ip 10.0.0.50
   - redirect-to-rt 65000:999
2. Verify only redirect-to-rt is applied

**Expected Result:**
- redirect-to-rt applied
- redirect-to-ip ignored

**Pass Criteria:**
- [ ] Traffic goes to VRF with RT 65000:999
- [ ] redirect-to-ip not used

---

### NEG-05: VRF Alphabetical Selection
**Type:** 🆕 NEW (DNOS-Specific)

**Objective:** When multiple VRFs import same RT, first alphabetically is chosen

**Steps:**
1. Create VRFs: AAA_VRF, MMM_VRF, ZZZ_VRF - all importing RT 65000:500
2. Advertise FlowSpec with redirect-to-rt 65000:500
3. Send matching traffic
4. Verify traffic goes to AAA_VRF only

**Expected Result:**
- Traffic redirected to AAA_VRF (first alphabetically)
- MMM_VRF and ZZZ_VRF do NOT receive traffic

**Pass Criteria:**
- [ ] Only AAA_VRF receives redirected traffic
- [ ] Deterministic behavior

---

## NLRI Validation Negative Tests

### NEG-06: Invalid Prefix Length (IPv4)
**Type:** 🆕 NEW

**Objective:** Verify NLRI with prefix-length > 32 is rejected

**Steps:**
1. Inject FlowSpec NLRI with destination prefix-length 33
2. Verify rejection

**Expected Result:**
- Invalid NLRI rejected
- Session remains up

**Pass Criteria:**
- [ ] NLRI rejected
- [ ] Session stable

---

### NEG-07: Invalid Prefix Length (IPv6)
**Type:** 🆕 NEW

**Objective:** Verify NLRI with prefix-length > 128 is rejected

**Steps:**
1. Inject IPv6 FlowSpec NLRI with prefix-length 129
2. Verify rejection

**Pass Criteria:**
- [ ] NLRI rejected

---

### NEG-08: Duplicate Component Types
**Type:** 🆕 NEW

**Objective:** Verify NLRI with duplicate component types rejected

**Steps:**
1. Inject FlowSpec NLRI with two Type 1 (Destination Prefix) components
2. Verify rejection

**Expected Result:**
- Duplicate components detected
- NLRI rejected

**Pass Criteria:**
- [ ] NLRI rejected

---

### NEG-09: Out-of-Order Components
**Type:** 🆕 NEW

**Objective:** Verify components must be in increasing Type order

**Steps:**
1. Inject NLRI with components in wrong order (e.g., Type 3 before Type 1)
2. Verify rejection

**Pass Criteria:**
- [ ] Order violation rejected

---

### NEG-10: NLRI Length Mismatch
**Type:** 🆕 NEW

**Objective:** Verify NLRI length byte matches actual content

**Steps:**
1. Inject malformed NLRI with wrong length field
2. Verify handling (reject/withdraw)

**Pass Criteria:**
- [ ] Malformed NLRI handled gracefully
- [ ] No crash

---

### NEG-11: Non-Zero Padding in Prefix
**Type:** 🆕 NEW

**Objective:** Verify prefix has zero bits in unused octets

**Steps:**
1. Inject prefix 10.0.0.0/8 with non-zero bits in octets 2-4
2. Verify rejection

**Pass Criteria:**
- [ ] Non-zero padding rejected

---

## Configuration Negative Tests

### NEG-12: FlowSpec Without BGP Neighbor
**Type:** 🆕 NEW

**Objective:** Verify behavior when FlowSpec AFI enabled but no neighbor

**Steps:**
1. Configure address-family ipv4-flowspec in VRF
2. Do NOT configure any neighbor with ipv4-flowspec-vpn
3. Verify commit succeeds but no routes

**Expected Result:**
- Config accepted
- No FlowSpec routes (no source)

**Pass Criteria:**
- [ ] Commit succeeds
- [ ] No operational issues

---

### NEG-13: Import-VPN Without VRF Existence
**Type:** 🆕 NEW

**Objective:** Verify behavior when VRF doesn't exist

**Steps:**
1. Try to configure:
   ```
   network-services vrf instance NON-EXISTENT-VRF protocols bgp 65000 address-family ipv4-flowspec
   ```
2. Verify behavior (creates VRF or errors)

**Pass Criteria:**
- [ ] VRF created OR clear error

---

### NEG-14: Invalid Route-Target Format
**Type:** 🆕 NEW

**Objective:** Verify invalid RT format rejected

**Steps:**
1. Try to configure invalid RT:
   ```
   import-vpn route-target INVALID
   ```
2. Verify rejection

**Pass Criteria:**
- [ ] Invalid RT rejected at commit

---

### NEG-15: Conflicting RT Import
**Type:** 🆕 NEW

**Objective:** Verify behavior with conflicting RTs

**Steps:**
1. Configure VRF1 with import RT 65000:100
2. Configure VRF2 with same import RT 65000:100
3. Advertise FlowSpec with RT 65000:100
4. Verify both VRFs receive (not conflict)

**Expected Result:**
- Both VRFs receive FlowSpec (designed behavior)
- This is actually valid per SW-182545

**Pass Criteria:**
- [ ] Both VRFs get FlowSpec

---

## Action Negative Tests

### NEG-16: Unknown Action Extended Community
**Type:** 🆕 NEW

**Objective:** Verify unknown action type handled gracefully

**Steps:**
1. Advertise FlowSpec with unknown/proprietary action extended community
2. Verify handling

**Expected Result:**
- Unknown action ignored
- FlowSpec may still be installed with known actions

**Pass Criteria:**
- [ ] No crash
- [ ] Known actions still work

---

### NEG-17: Unsupported Rate Value
**Type:** 🆕 NEW

**Objective:** Verify behavior with extreme rate values

**Steps:**
1. Advertise FlowSpec with traffic-rate = 0 (drop)
2. Verify works
3. Advertise FlowSpec with traffic-rate = max uint (very high)
4. Verify handling

**Pass Criteria:**
- [ ] Rate 0 = drop works
- [ ] Very high rate = no limit or capped

---

### NEG-18: Rate-Limit Negative Value
**Type:** 🆕 NEW

**Objective:** Verify negative rate handled

**Steps:**
1. Try to inject FlowSpec with negative traffic-rate
2. Verify rejection/handling

**Pass Criteria:**
- [ ] Handled gracefully

---

## Session/Protocol Negative Tests

### NEG-19: Peer Disconnect During Rule Install
**Type:** 🔄 REG

**Objective:** Verify graceful handling when peer disconnects mid-update

**Steps:**
1. Start advertising 1000 FlowSpec rules
2. Mid-update, disconnect peer
3. Verify DUT handles gracefully
4. Reconnect, verify recovery

**Pass Criteria:**
- [ ] No crash/hang
- [ ] State cleaned up
- [ ] Recovery works

---

### NEG-20: FlowSpec from Non-VPN Neighbor
**Type:** 🆕 NEW

**Objective:** Verify FlowSpec-VPN requires VPN attributes

**Steps:**
1. Configure neighbor with ipv4-flowspec (not flowspec-vpn)
2. Advertise FlowSpec without RT extended community
3. Verify it doesn't import to VRF

**Expected Result:**
- FlowSpec without RT doesn't match VRF import

**Pass Criteria:**
- [ ] No VRF import without matching RT

---

### NEG-21: Session with Wrong SAFI
**Type:** 🆕 NEW

**Objective:** Verify SAFI 134 vs SAFI 133 handling

**Steps:**
1. Configure ipv4-flowspec-vpn (SAFI 134)
2. Peer tries to establish SAFI 133 (regular flowspec)
3. Verify capability mismatch handling

**Pass Criteria:**
- [ ] Mismatch handled
- [ ] No incorrect routes

---

## Summary Matrix

| Test | Type | Description | Severity |
|------|------|-------------|----------|
| NEG-01 | 🆕 NEW | redirect-to-ip rejection | CRITICAL |
| NEG-02 | 🆕 NEW | Cross-VRF to default rejection | CRITICAL |
| NEG-03 | 🆕 NEW | C=1 copy bit rejection | HIGH |
| NEG-04 | 🆕 NEW | Mixed redirect actions | HIGH |
| NEG-05 | 🆕 NEW | VRF alphabetical selection | MED |
| NEG-06 | 🆕 NEW | Invalid prefix length IPv4 | HIGH |
| NEG-07 | 🆕 NEW | Invalid prefix length IPv6 | HIGH |
| NEG-08 | 🆕 NEW | Duplicate components | HIGH |
| NEG-09 | 🆕 NEW | Out-of-order components | MED |
| NEG-10 | 🆕 NEW | Length mismatch | HIGH |
| NEG-11 | 🆕 NEW | Non-zero padding | MED |
| NEG-12 | 🆕 NEW | No neighbor | LOW |
| NEG-13 | 🆕 NEW | VRF doesn't exist | MED |
| NEG-14 | 🆕 NEW | Invalid RT format | HIGH |
| NEG-15 | 🆕 NEW | Conflicting RT (valid) | MED |
| NEG-16 | 🆕 NEW | Unknown action | HIGH |
| NEG-17 | 🆕 NEW | Extreme rate values | MED |
| NEG-18 | 🆕 NEW | Negative rate | MED |
| NEG-19 | 🔄 REG | Peer disconnect mid-update | HIGH |
| NEG-20 | 🆕 NEW | No RT extended community | HIGH |
| NEG-21 | 🆕 NEW | Wrong SAFI | HIGH |

---

## DNOS-Specific Quick Reference

| Behavior | Expected | Test |
|----------|----------|------|
| redirect-to-ip | NOT supported (ignore) | NEG-01 |
| Redirect to default VRF | NOT allowed | NEG-02 |
| C=1 copy bit | NOT supported | NEG-03 |
| Mixed redirects | Use redirect-to-rt only | NEG-04 |
| Multiple VRF same RT | First alphabetically | NEG-05 |
| No VPN label | OK (not required) | See HF tests |
| No NH reachability | OK (not checked) | See HF tests |

---
