# Flowspec VPN - Datapath Debugging Commands Guide

> **Document Purpose**: This guide provides all available xraycli, wboxcli, and DNOS CLI commands for debugging and verifying Flowspec VPN installation and behavior on Drivenets devices.
>
> **Last Updated**: January 2026  
> **Verified Against**: Branch `easraf/flowspec_vpn/wbox_side`

---

## Table of Contents

1. [XRAYCLI Commands (Datapath Level)](#1-xraycli-commands-datapath-level)
2. [DNOS CLI Show Commands](#2-dnos-cli-show-commands)
3. [DNOS CLI Clear Commands](#3-dnos-cli-clear-commands)
4. [DNOS CLI Request Commands](#4-dnos-cli-request-commands)
5. [WBOX API Commands (Python Interface)](#5-wbox-api-commands-python-interface)
6. [Flowspec VPN Scale Limits](#6-flowspec-vpn-scale-limits)
7. [Verification Checklist](#7-verification-checklist)
8. [Debugging Flowcharts](#8-debugging-flowcharts)
9. [Expected Behavior Reference](#9-expected-behavior-reference)

---

## 1. XRAYCLI Commands (Datapath Level)

The xraycli commands are accessed via the `wb_agent` process and show **real-time datapath state**. These are the most reliable commands for verifying actual hardware installation.

### 1.1 BGP Flowspec Rules (Received from BGP Peers)

```bash
# IPv4 BGP Flowspec rules - shows all installed BGP-learned rules
xraycli /wb_agent/flowspec/bgp/ipv4/rules

# IPv6 BGP Flowspec rules
xraycli /wb_agent/flowspec/bgp/ipv6/rules

# IPv4 BGP Flowspec table info (summary: entries, unsupported, tcam errors)
xraycli /wb_agent/flowspec/bgp/ipv4/info

# IPv6 BGP Flowspec table info
xraycli /wb_agent/flowspec/bgp/ipv6/info
```

#### Output Fields for `/flowspec/bgp/*/rules`:

| Field | Description | VPN Relevance |
|-------|-------------|---------------|
| `index` | Rule index (1-based) | - |
| `vrf_id` | VRF ID for the rule | **Key for VPN!** 0=default VRF (valid), >0=specific VRF |
| `nlri` | NLRI in hex format | Raw NLRI bytes |
| `nlri_readable` | Human-readable NLRI | Parsed format (if available) |
| `nlri_length` | Length of NLRI in bytes | - |
| `priority` | Rule priority | Higher = more specific |
| `support` | Support state | 0=supported, 1=unsupported |
| `rate_limit_policer_enabled` | Whether rate-limit policer attached | `true`/`false` |
| `rate_limit_policer_id` | Policer ID | Valid if policer enabled |
| `rate_limit_policer_meter_id` | Meter ID in HW | BCM meter reference |
| `rate_limit_policer_rate_bytes` | Rate limit in bytes/sec | Configured rate |
| `rate_limit_policer_bucket_size` | Bucket size for policer | Token bucket size |

#### Output Fields for `/flowspec/bgp/*/info`:

| Field | Description | What to Check |
|-------|-------------|---------------|
| `number_of_entries` | Total rules in table | Should match expected |
| `num_unsupported` | Rules with unsupported NLRI/action | Should be 0 |
| `num_tcam_errors` | Rules that failed TCAM write | **Must be 0** |

---

### 1.2 Local Policies Rules (Locally Configured)

```bash
# IPv4 Local Policy rules
xraycli /wb_agent/flowspec/local_policies/ipv4/rules

# IPv6 Local Policy rules
xraycli /wb_agent/flowspec/local_policies/ipv6/rules

# IPv4 Local Policy table info
xraycli /wb_agent/flowspec/local_policies/ipv4/info

# IPv6 Local Policy table info
xraycli /wb_agent/flowspec/local_policies/ipv6/info
```

> **Note**: Local policy rules can have `vrf_id = "any"` meaning they apply to all VRFs.

---

### 1.3 General Flowspec Info

```bash
# Total number of flowspec entries (all tables combined)
xraycli /wb_agent/flowspec/info

# HW operation counters (writes, deletes, failures)
xraycli /wb_agent/flowspec/hw_counters
```

#### HW Counters Output Fields:

| Counter | Description | Expected Value |
|---------|-------------|----------------|
| `hw_policers_write_ok` | Policers successfully created | Increments on config |
| `hw_policers_write_fail` | Policers failed to create | **Must be 0** |
| `hw_policers_delete_ok` | Policers successfully deleted | Increments on delete |
| `hw_policers_delete_fail` | Policers failed to delete | **Must be 0** |
| `hw_policers_configurations_count` | Unique policer configurations | ≤ 100 |
| `hw_rules_write_ok` | Rules successfully written to TCAM | Should increment |
| `hw_rules_write_fail` | Rules failed to write to TCAM | **Must be 0** |
| `hw_rules_delete_ok` | Rules successfully deleted | Increments on delete |
| `hw_rules_delete_fail` | Rules failed to delete | **Must be 0** |

---

## 2. DNOS CLI Show Commands

### 2.1 Control Plane (RIB/BGP Level)

```bash
# BGP Flowspec NLRI from BGP peers (global routing table)
show bgp ipv4 flowspec
show bgp ipv6 flowspec

# BGP Flowspec for specific VRF (VPN!)
show bgp instance vrf <vrf-name> ipv4 flowspec
show bgp instance vrf <vrf-name> ipv6 flowspec

# Filter by specific NLRI
show bgp ipv4 flowspec nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32"

# Filter by destination prefix
show bgp ipv4 flowspec destination 50.0.0.0/8

# Filter by destination and source
show bgp ipv4 flowspec destination 50.0.0.0/8 source 50.1.2.3/32

# IPv6 with offset
show bgp ipv6 flowspec destination 2001:db8::/32-64
```

#### Output Example:
```
DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6
  1
0.0.0.0 from 192.168.1.2 (9.9.9.2)
Origin IGP, metric 0, localpref 100, valid, external, best
Extended Community: flowspec-redirect-ip-nh:0 flowspec-traffic-rate:1:500
AddPath ID: RX 0, TX 2
Last update: Thu Nov  7 14:38:37 2019
```

---

### 2.2 BGP Flowspec Neighbors

```bash
# Show flowspec-capable neighbors
show bgp flowspec neighbors

# Show routes advertised to neighbor
show bgp flowspec neighbors advertised-routes

# Show routes received from neighbor
show bgp flowspec neighbors received-routes
```

---

### 2.3 Datapath Installation Status (NCP Level)

```bash
# Flowspec rules on specific NCP (shows INSTALLED/NOT INSTALLED status)
show flowspec ncp 0
show flowspec ncp 1

# Filter by specific NLRI
show flowspec ncp 0 nlri "DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32"
```

#### Output Example:
```
Address-family: IPv4
    Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6
        Actions: Traffic-rate: 0 bps
        Status: Installed
    Flow: DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17
        Actions: Traffic-rate: 5000 bps
        Status: Not installed, nlri and/or action not supported
```

---

### 2.4 Installed Rules with Counters

```bash
# All installed flowspec rules with match counters
show flowspec
show flowspec ipv4
show flowspec ipv6

# Filter by NLRI
show flowspec ipv4 nlri "DstPrefix:=50.0.0.0/8"

# Filter by destination/source
show flowspec ipv4 destination 50.0.0.0/8
show flowspec ipv4 destination 50.0.0.0/8 source 50.1.2.3/32

# VPN-specific (VRF instance)
show flowspec instance vrf <vrf-name>
show flowspec instance vrf <vrf-name> ipv4
```

#### Output Example:
```
Address-family: IPv4
    Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6
        Actions: Traffic-rate: 0 bps
        Match packet counter: 1523
        Match octets counter: 564234
```

---

### 2.5 Local Policies Commands

```bash
# NCP installation status for local policies
show flowspec-local-policies ncp 0

# Configured match-classes
show flowspec-local-policies match-classes
show flowspec-local-policies match-classes address-family ipv4
show flowspec-local-policies match-classes match-class <mc-name>

# Configured policies
show flowspec-local-policies policies
show flowspec-local-policies policies policy <policy-name>
show flowspec-local-policies policies address-family ipv4

# Counters per match-class (traffic statistics)
show flowspec-local-policies counters
show flowspec-local-policies counters address-family ipv4
```

---

### 2.6 Internal Debugging (RIB Manager)

```bash
# RIB Manager internal database - shows flowspec NLRIs in RIB
show dnos-internal routing rib-manager database flowspec
```

#### Output Example:
```
IPv4 Flowspec table (total size: 1):
-------------------------------
DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5
    flowspec-traffic-rate:0

IPv6 Flowspec table (total size: 1):
-------------------------------
DstPrefix:=aaaa::11:11:0:0/96,SrcPrefix:=bbbb::11:22:33:44/128
    flowspec-traffic-rate:0
```

---

## 3. DNOS CLI Clear Commands

```bash
# Clear all flowspec counters
clear flowspec counters

# Clear for specific address family
clear flowspec counters ipv4
clear flowspec counters ipv6

# Clear for specific NLRI
clear flowspec counters ipv4 nlri "DstPrefix:=50.0.0.0/8"

# Clear by destination/source prefix
clear flowspec counters ipv4 destination 50.0.0.0/8
clear flowspec counters ipv4 destination 50.0.0.0/8 source 50.1.2.3/24

# Clear for specific VRF
clear flowspec counters instance vrf <vrf-name>

# Clear local policies counters
clear flowspec-local-policies counters
clear flowspec-local-policies counters address-family ipv4
```

---

## 4. DNOS CLI Request Commands

```bash
# Retry installing any failed local policy rules (TCAM errors recovery)
request retry-install flowspec-local-policy-rules

# Retry for specific address family
request retry-install flowspec-local-policy-rules ipv4
request retry-install flowspec-local-policy-rules ipv6
```

> **Use Case**: After TCAM space is freed up, use this to retry installing previously failed rules.

---

## 5. WBOX API Commands (Python Interface)

These commands are used in automated testing via the wbox handler:

### 5.1 Get BGP Flowspec Rules

```python
import qpb.qpb_pb2 as qpb

# Get IPv4 BGP Flowspec rules from datapath
resp = handler.wb_api.flowspec.get_rules(
    ncp_id=0, 
    address_family=qpb.AddressFamily.IPV4,
    start_idx=0
)

# Iterate through paginated results
while resp.flowspec.get_rules.next_idx != -1:
    for rule in resp.flowspec.get_rules.rule_data:
        print(f"NLRI: {rule.nlri_str}")
        print(f"Installed: {rule.installed}")
        print(f"Supported: {rule.supported}")
        print(f"VRF ID: {rule.vrf_id}")
        print(f"Actions: {rule.actions}")
    resp = handler.wb_api.flowspec.get_rules(
        ncp_id=0, 
        address_family=qpb.AddressFamily.IPV4,
        start_idx=resp.flowspec.get_rules.next_idx
    )
```

### 5.2 Get Local Policy Rules

```python
import cheetah_api.flowspec_local_policies_pb2 as flowspec_local_policies_pb

# Get IPv4 Local Policy rules
resp = handler.api.flowspec_local_policies.get_rules(
    ncp_id=0,
    address_type=flowspec_local_policies_pb.RULE_TYPE_IPV4,
    start_idx=0
)

# Process results
for rule in resp.flowspec_local_policies.get_rules.rule_data:
    print(f"NLRI: {rule.nlri_str}")
    print(f"Installed: {rule.installed}")
```

### 5.3 Retry Failed Rules

```python
# Retry installing failed local policy rules
handler.api.flowspec_local_policies.retry_install_rules(
    address_type=flowspec_local_policies_pb.RULE_TYPE_IPV4
)
```

### 5.4 Get XRAY Stats Programmatically

```python
# Get flowspec info
info = handler.get_xray_stats('/flowspec/info')

# Get HW counters
hw_counters = handler.get_xray_stats('/flowspec/hw_counters')

# Get BGP IPv4 rules
rules = handler.get_xray_stats('/flowspec/bgp/ipv4/rules')

# Get table info
table_info = handler.get_xray_stats('/flowspec/bgp/ipv4/info')
```

---

## 6. Flowspec VPN Scale Limits

### 6.1 TCAM/KBP Capacity

| Metric | Value | Source |
|--------|-------|--------|
| **IPv4 External Capacity** | 12,000 rules | `FlowspecCapacity.EXTERNAL_FLOWSPEC_IPV4_MINIMUM_CAPACITY` |
| **IPv6 External Capacity** | 4,000 rules | `FlowspecCapacity.EXTERNAL_FLOWSPEC_IPV6_MINIMUM_CAPACITY` |
| **Unique Policer Configurations** | 100 | `MAX_POLICERS_CONFIGURATIONS` |
| **Meter ID Capacity** | 16,384 | `FLOWSPEC_METER_ID_CAPACITY` (BCM per database) |

### 6.2 VRF Field Impact on Capacity

| Rule Type | `field_exists` | Capacity Impact |
|-----------|----------------|-----------------|
| With VRF (VPN) | 1 | Uses standard capacity |
| Without VRF (global) | 0 | Uses standard capacity |
| Mixed VRF/non-VRF | both | May reduce effective capacity |

> **Note**: When mixing rules with and without VRF specification, KBP capacity may be affected due to different lookup patterns.

---

## 7. Verification Checklist

### 7.1 Quick Verification Matrix

| What to Verify | Command | Expected Result |
|----------------|---------|-----------------|
| VRF ID present in rule | `xraycli /wb_agent/flowspec/bgp/ipv4/rules` | 0=default VRF (valid), >0=specific VRF |
| Rule installed in TCAM | `show flowspec ncp 0` | Status = "Installed" |
| Rule received from BGP | `show bgp ipv4 flowspec` | Rule visible with Extended Community |
| Counters incrementing | `show flowspec` | "Match packet counter" > 0 |
| No TCAM errors | `xraycli /wb_agent/flowspec/bgp/ipv4/info` | `num_tcam_errors = 0` |
| HW write success | `xraycli /wb_agent/flowspec/hw_counters` | `hw_rules_write_fail = 0` |
| Policer configured | `xraycli /wb_agent/flowspec/bgp/ipv4/rules` | `rate_limit_policer_enabled = true` |
| Supported NLRI | `xraycli /wb_agent/flowspec/bgp/ipv4/info` | `num_unsupported = 0` |

### 7.2 Complete Verification Procedure

```bash
# Step 1: Verify BGP session and route reception
show bgp flowspec neighbors
show bgp instance vrf MY_VRF ipv4 flowspec

# Step 2: Verify RIB installation
show dnos-internal routing rib-manager database flowspec

# Step 3: Verify NCP datapath installation
show flowspec ncp 0

# Step 4: Check xray for VRF ID and support state
xraycli /wb_agent/flowspec/bgp/ipv4/rules
# Look for: vrf_id (0=default VRF, >0=specific VRF), support = 0 (supported)

# Step 5: Check HW operation counters
xraycli /wb_agent/flowspec/hw_counters
# Verify: hw_rules_write_fail = 0

# Step 6: Check table capacity and errors
xraycli /wb_agent/flowspec/bgp/ipv4/info
# Verify: num_tcam_errors = 0

# Step 7: Verify traffic matching (after traffic flow)
show flowspec
# Check: Match packet counter > 0

# Step 8: If issues found, retry installation
request retry-install flowspec-local-policy-rules ipv4
```

---

## 8. Debugging Flowcharts

### 8.1 Rule Not Installed

```
Rule shows "Not installed" in 'show flowspec ncp 0'
    │
    ├── Check: xraycli /wb_agent/flowspec/bgp/ipv4/info
    │   │
    │   ├── num_unsupported > 0?
    │   │   └── NLRI or action not supported by hardware
    │   │
    │   └── num_tcam_errors > 0?
    │       └── TCAM full - check capacity
    │
    ├── Check: xraycli /wb_agent/flowspec/hw_counters
    │   │
    │   └── hw_rules_write_fail > 0?
    │       └── HW programming issue - check BCM logs
    │
    └── Check: show bgp ipv4 flowspec
        │
        └── Rule not visible?
            └── BGP session issue or route filtering
```

### 8.2 Traffic Not Matching

```
Counters not incrementing in 'show flowspec'
    │
    ├── Verify rule is installed
    │   └── show flowspec ncp 0 → Status: Installed
    │
    ├── Verify traffic is flowing
    │   └── Interface counters increasing?
    │
    ├── Verify NLRI matches traffic
    │   └── Check DstPrefix, SrcPrefix, Protocol, Ports
    │
    ├── Verify interfaces have flowspec enabled
    │   └── show running-config | include "flowspec"
    │
    └── Clear counters and retest
        └── clear flowspec counters
```

---

## 9. Expected Behavior Reference

### 9.1 Flowspec VPN SAFI Behavior

| SAFI | Description | VRF Handling |
|------|-------------|--------------|
| Flowspec (133) | Standard Flowspec | Global VRF only |
| FlowSpec-VPN (134) | VPN Flowspec | VRF-aware, uses RT for import |

### 9.2 VPN Flowspec Route Import

- Uses `import-vpn route-target` configuration
- RT matching imports rules into specific VRF
- Imported rules have VRF ID set in datapath

### 9.3 Actions Behavior

| Action | Hardware Support | Notes |
|--------|------------------|-------|
| Traffic-rate: 0 | ✅ Supported | Discard |
| Traffic-rate: N | ✅ Supported | Rate limit (bps) |
| Redirect-to-VRF | ✅ Supported | VRF redirect |
| Redirect-to-IP | ✅ Supported | NH redirect |
| Traffic-marking | ⚠️ Partial | DSCP marking |

### 9.4 NLRI Component Support

| Component | IPv4 | IPv6 | Notes |
|-----------|------|------|-------|
| Destination Prefix | ✅ | ✅ | Primary filter |
| Source Prefix | ✅ | ✅ | Primary filter |
| Protocol/Next-Header | ✅ | ✅ | L3 protocol |
| Port (Dst/Src) | ✅ | ✅ | L4 port |
| DSCP | ✅ | ✅ | Traffic class |
| Packet Length | ✅ | ✅ | Total length |
| TCP Flags | ✅ | ✅ | TCP only |
| ICMP Type/Code | ✅ | ✅ | ICMP only |
| Fragment | ✅ | ✅ | Fragment flags |

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| Jan 2026 | AI Assistant | Initial creation from code analysis |

---

## References

- DNOS CLI Documentation: `/home/dn/SCALER/dnos_cheetah_docs/`
- Flowspec Test Suite: `cheetah_26_1/src/tests/wbox/tests/test_flowspec.py`
- Flowspec Manager: `cheetah_26_1/src/wbox/src/flowspec/FlowspecManager.hpp`
- XRAY Registration: `cheetah_26_1/src/wbox/src/flowspec/flowspec_xray.cpp`
- WBOX API Proto: `cheetah_26_1/src/jag_msgs/proto/wb_api/wb_flowspec.proto`
