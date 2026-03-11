# FlowSpec VPN Test Plan - Comprehensive Comparison Analysis

_Generated: 2026-01-13_
_Comparison of: Original TP File | AI-Generated TP | EPIC Requirements | TP Checklist_

---

## 1. DNOS Implementation Differences from RFC 8955

Based on EPIC SW-182545 description, **DNOS implements FlowSpec VPN differently from the RFC in these critical ways:**

| # | RFC 8955 Standard | DNOS Implementation | Testing Impact |
|---|-------------------|---------------------|----------------|
| 1 | VPN label associated with FlowSpec-VPN NLRI | **No VPN label** for flowspec-vpn NLRI | Test should NOT expect MPLS labels |
| 2 | NH reachability check required | **No NH reachability check** needed | Don't test MPLS-reachability validation |
| 3 | Validation flow per RFC 8955 Section 6 | **Validation NOT required** | Skip strict RFC validation tests |
| 4 | redirect-to-ip (draft-ietf-idr-flowspec-redirect-ip) | **NOT supported** | Negative test: reject redirect-to-ip |
| 5 | draft-simpson-idr-flowspec-redirect | **Supported** | Test only Simpson draft for redirect |
| 6 | Both redirect-to-ip + redirect-to-rt in NLRI | **Ignore redirect-to-ip**, use redirect-to-rt only | Test mixed action handling |
| 7 | Multiple VRFs import same RT for redirect | **First alphabetically** wins | Test VRF selection order (e.g., AAA_VRF before ZZZ_VRF) |
| 8 | Redirect from non-default VRF to default | **NOT supported** | Negative test: verify rejection |
| 9 | redirect-IP Copy bit (C=0/C=1) | **Only C=0 supported** | Test C=0 only; negative for C=1 |

### 🔴 Critical Missing Tests Based on DNOS Differences:
1. **Redirect-to-IP Rejection** - Verify DNOS rejects redirect-to-ip extended community
2. **VRF Alphabetical Selection** - When multiple VRFs import same RT, first alphabetically is used
3. **Cross-VRF Redirect Rejection** - Cannot redirect from non-default to default VRF
4. **C=1 Copy Bit Rejection** - Only C=0 supported for redirect-IP

---

## 2. TP Checklist Categories Comparison

### Categories PRESENT in Both Plans:

| Category | Original TP | AI-Generated | Status |
|----------|-------------|--------------|--------|
| Basic Functionality | ✅ | ✅ | Covered |
| CLI Config | ✅ | ✅ | Covered |
| CLI Show | ✅ | ✅ | Covered |
| IPv4 FlowSpec-VPN | ✅ | ✅ | Covered |
| IPv6 FlowSpec-VPN | ✅ | ✅ | Covered |
| Non-Default VRF | ✅ | ✅ | Covered |
| Default VRF | ✅ | ✅ | Covered |
| Actions (Drop, Rate-limit) | ✅ | ✅ | Covered |
| RT/RD Handling | ✅ | ✅ | Covered |
| BGP Session/Neighbor | ✅ | ✅ | Covered |
| Traffic Enforcement | ✅ | ✅ | Covered |

### Categories MISSING from Both Plans:

| Category | TP Checklist Requirement | Priority | Notes |
|----------|--------------------------|----------|-------|
| **HA - Container Restart** | Mandatory | 🔴 HIGH | Restart BGP container during FlowSpec session |
| **HA - Process Restart** | Mandatory | 🔴 HIGH | Kill bgp_rpd process, verify recovery |
| **HA - NCC Switchover** | Mandatory | 🔴 HIGH | NCM switchover with active FlowSpec |
| **HA - Graceful Restart** | Mandatory | 🔴 HIGH | GR during FlowSpec session |
| **Upgrade Testing** | Mandatory | 🔴 HIGH | In-service upgrade with FlowSpec |
| **Scale - Max Entries** | Mandatory | 🔴 HIGH | Max FlowSpec rules per VRF |
| **Scale - Memory Utilization** | Mandatory | 🔴 HIGH | Memory under FlowSpec load |
| **Scale - Churn** | Mandatory | 🔴 HIGH | Add/remove FlowSpec rapidly |
| **NETCONF/Openconfig** | Covered in US | 🟡 MED | SW-221388 OpenConfig support |
| **Stress Testing** | Recommended | 🟡 MED | High message rate, convergence |
| **Negative - Malformed NLRI** | Covered in RFC | 🟡 MED | Bad length, padding, ordering |
| **Negative - Invalid Config** | Partial | 🟡 MED | Invalid CLI combinations |
| **Counters/Statistics** | Partial | 🟡 MED | FlowSpec match counters |
| **Clear Commands** | Missing | 🟡 MED | clear flowspec, clear bgp |
| **Traps/SNMP** | Missing | 🟢 LOW | FlowSpec traps |
| **Alarms** | Missing | 🟢 LOW | FlowSpec-related alarms |
| **Tech Support** | Missing | 🟢 LOW | FlowSpec in techsupport bundle |
| **Longevity** | Missing | 🟢 LOW | 24-72 hour soak test |

### Categories ONLY in Original TP (FlowSpec-VPN-TP.txt):

| Category | Description | Recommendation |
|----------|-------------|----------------|
| Session Flap Recovery | BGP session flap and rule recovery | Keep - Important stability |
| Multi-Neighbor | Multiple peers advertising FlowSpec | Keep - Production scenario |
| Redirect Actions | Various redirect scenarios | Keep - Core functionality |
| Inter-VRF | Between VRFs (where supported) | Keep with DNOS caveats |

### Categories ONLY in AI-Generated TP:

| Category | Description | Recommendation |
|----------|-------------|----------------|
| RFC 8955 NLRI Parsing | Component ordering, length validation | Add - RFC compliance |
| RFC 8955 Encoding | Wire-format encoding verification | Add - Interop |
| Implementation Basis Detection | Cisco IOS-XR compatibility notes | Informational |

---

## 3. User Story Coverage Analysis

### From EPIC SW-182545 User Stories:

| US Key | Summary | In Original | In Generated | Notes |
|--------|---------|-------------|--------------|-------|
| SW-223008 | Clear counters CLI + BGP | ⚠️ Partial | ✅ Test 1 | Generated covers CLI aspects |
| SW-223000 | Missing CLI show cmds | ⚠️ Partial | ✅ Test 2 | Generated includes show verification |
| SW-221388 | OpenConfig support | ❌ Missing | ✅ Test 3 | Need to add NETCONF tests |
| SW-211343 | Non-Default VRF IPv4/6 | ✅ Covered | ✅ Test 4 | Both cover well |
| SW-206889 | RT Redirect action | ⚠️ Partial | ✅ Test 5 | Generated more detailed |
| SW-206883 | Scale | ❌ Missing | ✅ Test 6 | Need dedicated scale section |
| SW-206882 | RT-C Integration | ❌ Missing | ✅ Test 7 | RT-Constrain interaction |
| SW-206881 | show bgp flowspec-vpn | ✅ Covered | ✅ Test 8 | Both cover |
| SW-206880 | VRF address-family config | ✅ Covered | ✅ Test 9 | Both cover |
| SW-206879 | peer flowspec-vpn safi | ✅ Covered | ✅ Test 10 | Both cover |
| SW-206877 | Non-Default VRF support | ✅ Covered | ✅ Test 11 | Core feature |
| SW-206876 | Default VRF support | ✅ Covered | ✅ Test 12 | Core feature |

---

## 4. RFC Tests Split into Categories

The 12 RFC-derived tests should be distributed as follows:

### Basic Functionality Tests (5):

| RFC Test | New Category | Justification |
|----------|--------------|---------------|
| NLRI Length Field Correctness | Basic Functionality | Fundamental parsing |
| Parse Component Type-Length-Value | Basic Functionality | Core NLRI handling |
| Enforce Component Ordering | Basic Functionality | Standard compliance |
| Port-Range Component Validation | Basic Functionality | Common match field |
| Validate IP Protocol Component | Basic Functionality | Common match field |

### Negative/Error Handling Tests (5):

| RFC Test | New Category | Justification |
|----------|--------------|---------------|
| Reject NLRI When Length Mismatch | Negative Testing | Error handling |
| Reject Oversized Prefix Length | Negative Testing | Boundary validation |
| Reject Non-Zero Padding in Prefix | Negative Testing | RFC compliance |
| Reject Duplicate Component Types | Negative Testing | Malformed NLRI |
| Withdraw on Validation Failure | Negative Testing | Error recovery |

### Advanced Functionality Tests (1):

| RFC Test | New Category | Justification |
|----------|--------------|---------------|
| Round-Trip Encoding of Section 4.3 Examples | Interop/Advanced | Wire-format compatibility |

### Scale Tests (1):

| RFC Test | New Category | Justification |
|----------|--------------|---------------|
| High-Volume Flow Spec Install | Scale Testing | Performance under load |

---

## 5. Recommended Test Plan Structure

Based on the comprehensive analysis, here is the recommended structure:

```
FlowSpec VPN Test Plan
├── 1. Basic Functionality
│   ├── 1.1 IPv4 FlowSpec-VPN Default VRF
│   ├── 1.2 IPv4 FlowSpec-VPN Non-Default VRF
│   ├── 1.3 IPv6 FlowSpec-VPN Default VRF
│   ├── 1.4 IPv6 FlowSpec-VPN Non-Default VRF
│   ├── 1.5 NLRI Parsing (from RFC)
│   │   ├── Length Field Correctness
│   │   ├── Component TLV Parsing
│   │   ├── Component Ordering
│   │   ├── Port-Range Validation
│   │   └── IP Protocol Validation
│   └── 1.6 Basic Actions (drop, rate-limit)
│
├── 2. Advanced Functionality
│   ├── 2.1 RT-C Integration
│   ├── 2.2 Route Reflector Topology
│   ├── 2.3 eBGP External Peer
│   ├── 2.4 Multi-VRF Import
│   ├── 2.5 Redirect Actions
│   │   ├── redirect-to-rt (Simpson draft - SUPPORTED)
│   │   └── redirect-to-vrf
│   └── 2.6 Neighbor Groups
│
├── 3. DNOS-Specific Behavior (NEW SECTION)
│   ├── 3.1 No VPN Label Verification
│   ├── 3.2 No NH Reachability Check
│   ├── 3.3 redirect-to-ip Rejection
│   ├── 3.4 VRF Alphabetical Selection (multi-VRF same RT)
│   ├── 3.5 Cross-VRF Redirect Rejection
│   └── 3.6 C=0 Only for redirect-IP
│
├── 4. Negative Testing
│   ├── 4.1 NLRI Validation Failures (from RFC)
│   │   ├── Length Mismatch
│   │   ├── Oversized Prefix
│   │   ├── Non-Zero Padding
│   │   ├── Duplicate Components
│   │   └── Withdrawal on Failure
│   ├── 4.2 Invalid Configuration
│   ├── 4.3 Unsupported Actions (redirect-to-ip)
│   └── 4.4 C=1 Copy Bit Rejection
│
├── 5. CLI Tests
│   ├── 5.1 Configuration Commands
│   ├── 5.2 Show Commands
│   ├── 5.3 Clear Commands
│   └── 5.4 Rollback/Commit Behavior
│
├── 6. HA Tests (MISSING - ADD)
│   ├── 6.1 Container Restart (bgp_rpd)
│   ├── 6.2 Process Restart
│   ├── 6.3 NCC/NCM Switchover
│   └── 6.4 Graceful Restart
│
├── 7. Scale Tests (MISSING - ADD)
│   ├── 7.1 Max FlowSpec Rules per VRF
│   ├── 7.2 Max FlowSpec Rules Total
│   ├── 7.3 Memory Under Load
│   ├── 7.4 Churn (Add/Remove Rapid)
│   └── 7.5 High-Volume Install (from RFC)
│
├── 8. Upgrade Tests (MISSING - ADD)
│   ├── 8.1 In-Service Upgrade
│   └── 8.2 Version Rollback
│
├── 9. OpenConfig/NETCONF (from US SW-221388)
│   ├── 9.1 OpenConfig Model Compliance
│   └── 9.2 NETCONF Operations
│
└── 10. Interop Tests
    ├── 10.1 Cisco IOS-XR Peer
    ├── 10.2 Juniper Peer (if applicable)
    └── 10.3 Wire-Format Encoding (RFC 4.3)
```

---

## 6. Summary: What's Missing from Each

### Missing from Original TP (FlowSpec-VPN-TP.txt):

| Item | Priority | Action |
|------|----------|--------|
| RFC 8955 NLRI validation tests | 🔴 HIGH | Add NLRI parsing/validation section |
| DNOS-specific behavior tests | 🔴 HIGH | Add new section for DNOS differences |
| HA testing | 🔴 HIGH | Add container/process/NCC tests |
| Scale testing | 🔴 HIGH | Add max rules, memory, churn |
| Upgrade testing | 🔴 HIGH | Add ISSU tests |
| OpenConfig support | 🟡 MED | Add from US SW-221388 |
| RT-C integration | 🟡 MED | Add from US SW-206882 |

### Missing from AI-Generated TP:

| Item | Priority | Action |
|------|----------|--------|
| HA testing (all types) | 🔴 HIGH | Add HA section |
| Scale testing (dedicated) | 🔴 HIGH | Add scale section |
| Upgrade testing | 🔴 HIGH | Add upgrade section |
| Clear commands tests | 🟡 MED | Add clear CLI tests |
| DNOS-specific negative tests | 🟡 MED | Add redirect-to-ip rejection, C=1 rejection |
| Multi-neighbor scenarios | 🟡 MED | Test multiple peers |
| Session flap recovery | 🟡 MED | Add session stability tests |
| Longevity testing | 🟢 LOW | Add soak tests |

### Missing from BOTH Plans:

| Item | Priority | Notes |
|------|----------|-------|
| SNMP/Traps for FlowSpec | 🟢 LOW | May not be implemented yet |
| Alarms for FlowSpec | 🟢 LOW | May not be implemented yet |
| Tech Support bundle | 🟢 LOW | Verify FlowSpec in bundle |
| Documentation review | 🟢 LOW | Verify user docs match |

---

## 7. Recommended Immediate Actions

1. **Add DNOS-Specific Tests** - Create tests for all 9 DNOS implementation differences
2. **Add HA Section** - Container restart, process restart, NCC switchover, GR
3. **Add Scale Section** - Max rules, memory, churn
4. **Add Upgrade Section** - ISSU with active FlowSpec
5. **Split RFC Tests** - Distribute into Basic/Negative/Advanced/Scale categories
6. **Merge Best of Both** - Combine original TP's multi-neighbor/redirect with generated RFC compliance

---

_This analysis ensures comprehensive FlowSpec VPN testing coverage with DNOS-specific considerations._
