# Flowspec VPN - Routing Side Commands Guide

> **Document Purpose**: Complete reference for routing-plane verification commands for Flowspec VPN, including DNOS CLI, vtysh (shell access), and FIB manager commands.
>
> **Last Updated**: January 2026  
> **Verified Against**: Branch `easraf/flowspec_vpn/wbox_side`

---

## Table of Contents

1. [DNOS CLI Commands](#1-dnos-cli-commands)
2. [Shell (vtysh) Commands](#2-shell-vtysh-commands)
3. [FIB Manager Commands](#3-fib-manager-commands)
4. [Debug Commands](#4-debug-commands)
5. [VRF/VPN Specific Commands](#5-vrfvpn-specific-commands)
6. [RT Constraint Commands](#6-rt-constraint-commands)
7. [Verification Scripts](#7-verification-scripts)
8. [Expected Outputs Reference](#8-expected-outputs-reference)

---

## 1. DNOS CLI Commands

### 1.1 BGP Flowspec Table (Global/Default VRF)

```bash
# Show all BGP Flowspec routes (default VRF)
show bgp ipv4 flowspec
show bgp ipv6 flowspec

# Filter by specific NLRI
show bgp ipv4 flowspec nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32"

# Filter by destination prefix
show bgp ipv4 flowspec destination 50.0.0.0/8

# Filter by destination AND source
show bgp ipv4 flowspec destination 50.0.0.0/8 source 50.1.2.3/32

# IPv6 with offset notation
show bgp ipv6 flowspec destination 2001:db8::/32-64
```

### 1.2 BGP Flowspec-VPN Table (VPN SAFI 134)

```bash
# Show all Flowspec-VPN routes
show bgp ipv4 flowspec-vpn
show bgp ipv6 flowspec-vpn

# Filter by Route Distinguisher (RD)
show bgp ipv4 flowspec-vpn rd 65001:100
show bgp ipv4 flowspec-vpn rd 1.1.1.1:100

# Filter by NLRI within specific RD
show bgp ipv4 flowspec-vpn rd 65001:100 nlri "DstPrefix:=50.0.0.0/8"

# Filter by destination/source within RD
show bgp ipv4 flowspec-vpn rd 65001:100 nlri dest-prefix 50.0.0.0/8
```

### 1.3 BGP Flowspec per VRF

```bash
# Show Flowspec routes in specific VRF
show bgp vrf <vrf-name> ipv4 flowspec
show bgp vrf <vrf-name> ipv6 flowspec

# Example with VRF name
show bgp vrf vrf-a ipv4 flowspec
show bgp vrf customer_vrf_1 ipv6 flowspec

# Filter by NLRI in VRF
show bgp vrf vrf-a ipv4 flowspec nlri "DstPrefix:=10.0.0.0/8"
show bgp vrf vrf-a ipv4 flowspec nlri dest-prefix 10.0.0.0/8 src-prefix 192.168.1.0/24
```

### 1.4 Neighbor-Specific Commands

```bash
# Show Flowspec routes advertised to neighbor
show bgp ipv4 flowspec neighbors <neighbor-ip> advertised-routes
show bgp ipv6 flowspec neighbors <neighbor-ip> advertised-routes

# Show Flowspec routes received from neighbor
show bgp ipv4 flowspec neighbors <neighbor-ip> received-routes
show bgp ipv6 flowspec neighbors <neighbor-ip> received-routes

# Show routes from specific neighbor
show bgp ipv4 flowspec neighbors <neighbor-ip> routes

# Flowspec-VPN neighbor commands
show bgp ipv4 flowspec-vpn neighbors <neighbor-ip> advertised-routes
show bgp ipv4 flowspec-vpn neighbors <neighbor-ip> received-routes
show bgp ipv4 flowspec-vpn neighbors <neighbor-ip> routes

# VRF-specific neighbor commands
show bgp vrf <vrf-name> ipv4 flowspec neighbors <neighbor-ip> advertised-routes
show bgp vrf <vrf-name> ipv4 flowspec neighbors <neighbor-ip> received-routes
show bgp vrf <vrf-name> ipv4 flowspec neighbors <neighbor-ip> routes
```

### 1.5 Bestpath Compare (Debugging Route Selection)

```bash
# Compare bestpath for specific NLRI
show bgp ipv4 flowspec bestpath-compare nlri "DstPrefix:=50.0.0.0/8,Protocol:=6"

# Flowspec-VPN bestpath compare
show bgp ipv4 flowspec-vpn bestpath-compare nlri "DstPrefix:=50.0.0.0/8"

# With specific RD
show bgp ipv4 flowspec-vpn rd 65001:100 bestpath-compare nlri "DstPrefix:=50.0.0.0/8"

# VRF-specific bestpath compare
show bgp vrf vrf-a ipv4 flowspec bestpath-compare nlri "DstPrefix:=10.0.0.0/8"
```

---

## 2. Shell (vtysh) Commands

### 2.1 Accessing vtysh from DNOS Shell

```bash
# From DNOS CLI, enter shell mode
run start shell
# Password: dnroot

# Inside shell, access vtysh
vtysh

# Or run single command directly
vtysh -c "show bgp ipv4 flowspec"
```

### 2.2 Zebra Flowspec Database

```bash
# Show all Flowspec routes in Zebra DB (all VRFs)
show flowspec db

# Show Flowspec routes for specific VRF
show flowspec db vrf <vrf-name>
show flowspec db vrf vrf-a
show flowspec db vrf vrf-b
```

**Output Fields:**
- NLRI string (human-readable)
- VRF ID
- BGP AS number
- Actions (Traffic-rate, Redirect, etc.)
- Flags: `[Stale]`, `[Deleted]`

### 2.3 BGP Summary and Neighbor

```bash
# BGP summary (shows Flowspec SAFI state)
show bgp summary

# Neighbor detail (shows Flowspec capability)
show bgp neighbors <neighbor-ip>
show bgp vrf <vrf-name> neighbors <neighbor-ip>
```

### 2.4 Routing Table (VRF-aware)

```bash
# Show IP routes in VRF
show ip route vrf <vrf-name>

# Show IPv6 routes in VRF
show ipv6 route vrf <vrf-name>
```

---

## 3. FIB Manager Commands

### 3.1 Flowspec in FIB Manager

```bash
# Show Flowspec routes in FIB manager
show fib-manager database flowspec

# Show Flowspec for specific VRF/service-instance
show fib-manager database flowspec service-instance <vrf-name>
show fib-manager database flowspec service-instance vrf-a
show fib-manager database flowspec service-instance vrf-b
```

### 3.2 Nexthop OID (for Redirect Actions)

```bash
# Show specific nexthop OID details
show fib-manager database nexthop oid <oid-number>
```

### 3.3 RIB Manager Internal (Deep Debugging)

```bash
# Show internal RIB manager Flowspec database
show dnos-internal routing rib-manager database flowspec
```

---

## 4. Debug Commands

### 4.1 BGP Debug Flags (vtysh)

```bash
# Enable BGP update debugging
debug bgp updates-in
debug bgp updates-out

# Enable BGP filter debugging
debug bgp filters

# Enable BGP-Zebra interaction debugging
debug bgp zebra

# Enable all updates
debug bgp updates

# Disable debug
no debug bgp updates-in
no debug bgp updates-out
no debug bgp zebra
```

### 4.2 Flowspec-Specific Debug

```bash
# Increment counter for specific NLRI (testing)
debug bgp vrf <vrf-name> ipv4 flowspec increment-counter nlri <nlri-string>
debug bgp vrf vrf-a ipv4 flowspec increment-counter nlri "DstPrefix:=50.0.0.0/8"
```

### 4.3 Debug Chain Dump (Advanced)

```bash
# Dump BGP path chain for Flowspec
debug bgp dump-chain PATH ipv4 flowspec <path-info>

# Dump for Flowspec-VPN
debug bgp dump-chain PATH ipv4 flowspec-vpn <path-info>

# VRF-specific dump
debug bgp dump-chain PATH vrf <vrf-name> ipv4 flowspec <path-info>

# Async chain dump
debug bgp dump-chain-async PATH vrf <vrf-name> ipv4 flowspec <path-info>
```

### 4.4 Zebra Debug

```bash
# Enable Zebra RIB debugging
debug zebra rib

# Enable Zebra NHT (Next-Hop Tracking)
debug zebra nht

# Enable Zebra events
debug zebra events
```

### 4.5 Viewing Debug Logs

```bash
# From shell, tail the log
tail -f /var/log/dnos/quagga/bgpd.log
tail -f /var/log/dnos/quagga/zebra.log

# Or use DNOS command
show log bgpd
show log zebra
```

---

## 5. VRF/VPN Specific Commands

### 5.1 VRF Configuration Verification

```bash
# Show VRF list
show vrf

# Show VRF details
show vrf <vrf-name>

# Show BGP VRF configuration
show running-config protocols bgp vrf <vrf-name>
```

### 5.2 Flowspec VRF Address-Family Config

```bash
# Show Flowspec address-family config in VRF
show running-config network-services vrf instance <vrf-name> protocols bgp address-family ipv4-flowspec
show running-config network-services vrf instance <vrf-name> protocols bgp address-family ipv6-flowspec
```

### 5.3 Import/Export Route-Target

```bash
# Show import-vpn route-target config
show running-config | include import-vpn

# Configuration example
network-services
  vrf
    instance customer_vrf_1
      protocols
        bgp 65001
          address-family ipv4-flowspec
            import-vpn route-target 49844:40
          !
        !
      !
    !
  !
!
```

---

## 6. RT Constraint Commands

### 6.1 RT Constraint Table

```bash
# Show RT constraints (Route Target Constraint SAFI)
show bgp ipv4 rt-constrains

# This shows which RTs are being imported by which SAFIs
```

**RT Constraint Behavior:**
- RT constraint table shows ALL RTs imported by ANY SAFI
- When FlowSpec SAFI changes RT, constraint table updates
- When unicast removes RT, FlowSpec may still keep it if needed

---

## 7. Verification Scripts

### 7.1 Complete Flowspec VPN Verification

```bash
#!/bin/bash
# flowspec_vpn_verify.sh - Complete Flowspec VPN verification

VRF_NAME="vrf-a"
PEER_IP="10.0.0.1"
RD="65001:100"

echo "=== 1. BGP Flowspec Table (Default VRF) ==="
vtysh -c "show bgp ipv4 flowspec"

echo "=== 2. BGP Flowspec-VPN Table ==="
vtysh -c "show bgp ipv4 flowspec-vpn"

echo "=== 3. BGP Flowspec in VRF ==="
vtysh -c "show bgp vrf $VRF_NAME ipv4 flowspec"

echo "=== 4. Flowspec-VPN with RD ==="
vtysh -c "show bgp ipv4 flowspec-vpn rd $RD"

echo "=== 5. Zebra Flowspec DB ==="
vtysh -c "show flowspec db vrf $VRF_NAME"

echo "=== 6. FIB Manager Flowspec ==="
vtysh -c "show fib-manager database flowspec service-instance $VRF_NAME"

echo "=== 7. RT Constraint Table ==="
vtysh -c "show bgp ipv4 rt-constrains"

echo "=== 8. Neighbor Received Routes ==="
vtysh -c "show bgp ipv4 flowspec-vpn neighbors $PEER_IP received-routes"
```

### 7.2 Quick Troubleshooting Script

```bash
#!/bin/bash
# flowspec_vpn_troubleshoot.sh

echo "=== Checking BGP Flowspec SAFIs ==="
vtysh -c "show bgp summary" | grep -E "flowspec|Flowspec"

echo "=== Checking Zebra Flowspec DB ==="
vtysh -c "show flowspec db"

echo "=== Checking for Stale Routes ==="
vtysh -c "show flowspec db" | grep -i "stale"

echo "=== Checking FIB Manager ==="
vtysh -c "show fib-manager database flowspec"

echo "=== Checking RIB Manager Internal ==="
vtysh -c "show dnos-internal routing rib-manager database flowspec"
```

---

## 8. Expected Outputs Reference

### 8.1 show bgp ipv4 flowspec-vpn

```
Route Distinguisher: 65001:100
DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6
  1
0.0.0.0 from 10.0.0.1 (1.1.1.1)
Origin IGP, metric 0, localpref 100, valid, internal, best
Extended Community: flowspec-traffic-rate:0
AddPath ID: RX 0, TX 2
Last update: Mon Jan  8 12:00:00 2026
```

### 8.2 show flowspec db vrf vrf-a

```
DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6
vrf_id: 1, bgp_as: 65001
    Traffic-rate: 0 bps (Drop)

DstPrefix:=10.10.0.0/16,Protocol:=17
vrf_id: 1, bgp_as: 65001
    Rate-limit: 1000000 bps
```

### 8.3 show fib-manager database flowspec service-instance vrf-a

```
Flowspec Routes:
  NLRI: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32
  Action: Discard
  Status: Installed
  VRF: vrf-a (ID: 1)

  NLRI: DstPrefix:=10.10.0.0/16
  Action: Rate-limit 1Mbps
  Status: Installed
  VRF: vrf-a (ID: 1)
```

### 8.4 show bgp ipv4 rt-constrains

```
Route Target: 65001:49844:40
  Requested by: ipv4-flowspec (VRF: vrf-a)
  
Route Target: 65001:49844:20
  Requested by: ipv4-unicast (VRF: vrf-a)
  Requested by: ipv4-flowspec (VRF: vrf-a)
```

---

## Command Summary Matrix

| Purpose | DNOS CLI | vtysh | Shell Command |
|---------|----------|-------|---------------|
| BGP Flowspec routes | `show bgp ipv4 flowspec` | Same | `vtysh -c "show bgp ipv4 flowspec"` |
| Flowspec-VPN routes | `show bgp ipv4 flowspec-vpn` | Same | `vtysh -c "show bgp ipv4 flowspec-vpn"` |
| VRF Flowspec | `show bgp vrf X ipv4 flowspec` | Same | `vtysh -c "show bgp vrf X ipv4 flowspec"` |
| Zebra DB | N/A | `show flowspec db` | `vtysh -c "show flowspec db"` |
| FIB Manager | `show fib-manager database flowspec` | Same | `vtysh -c "show fib-manager database flowspec"` |
| RIB Internal | `show dnos-internal routing rib-manager database flowspec` | Same | Via DNOS CLI |
| RT Constraints | `show bgp ipv4 rt-constrains` | Same | `vtysh -c "show bgp ipv4 rt-constrains"` |
| Debug updates | N/A | `debug bgp updates-in` | From vtysh |
| Neighbor routes | `show bgp ipv4 flowspec neighbors X advertised-routes` | Same | Via CLI |

---

## Integration with Datapath

After verifying routing-plane installation, cross-reference with datapath:

```bash
# 1. Verify RIB has the route
show dnos-internal routing rib-manager database flowspec

# 2. Verify FIB manager received it
show fib-manager database flowspec service-instance <vrf>

# 3. Verify datapath installation (from previous doc)
show flowspec ncp 0
xraycli /wb_agent/flowspec/bgp/ipv4/rules
```

---

## References

- Quagga Test Suite: `cheetah_26_1/src/tests/quagga/tests/test_bgp_flowspec_vrf_vpn.py`
- BGP Flowspec VTY: `cheetah_26_1/services/control/quagga/bgpd/bgp_flowspec_vty.c`
- Zebra Flowspec VTY: `cheetah_26_1/services/control/quagga/zebra/flowspec/zebra_flowspec_vty.c`
- VRF Flowspec CLI RST: `prod/dnos_monolith/dnos_cli/Network-services/vrf/instance/protocols/bgp/afi_ipv4-flowspec/`
