# DNOS CLI Configuration Documentation

This document contains the correct DNOS CLI syntax for configuring network services,
interfaces, and system profiles. All examples are extracted from the official DriveNets
CLI documentation.

---

## Table of Contents

1. [Interfaces](#interfaces)
   - [Physical/Bundle Sub-interfaces](#physicalbundle-sub-interfaces)
   - [VLAN Configuration](#vlan-configuration)
   - [L2-Service](#l2-service)
2. [Network Services](#network-services)
   - [EVPN-VPWS-FXC](#evpn-vpws-fxc)
   - [VRF (L3VPN)](#vrf-l3vpn)
   - [EVPN (MAC-VRF)](#evpn-mac-vrf)
   - [Multihoming](#multihoming)
3. [System Profile](#system-profile)

---

## Interfaces

### Interface Naming Convention

| Interface Type | Syntax | Example |
|----------------|--------|---------|
| Physical | `geX-f/n/p` | `ge100-1/0/39` |
| Sub-interface | `geX-f/n/p.Y` | `ge100-1/0/39.100` |
| Bundle | `bundle-X` | `bundle-2` |
| Bundle Sub-interface | `bundle-X.Y` | `bundle-2.102` |
| Loopback | `loX` | `lo0` |
| IRB | `irbX` | `irb1` |

Where:
- X = Interface speed (10, 25, 40, 50, 100)
- f = NCP ID (0-255)
- n = Slot ID (0-255)
- p = Port ID (0-255)
- Y = Sub-interface ID (1-65535)

### Physical/Bundle Sub-interfaces

#### Creating a Sub-interface

```
dnRouter# configure
dnRouter(cfg)# interfaces
dnRouter(cfg-if)# ge100-1/1/1.100
dnRouter(cfg-if-ge100-1/1/1.100)# vlan-id 301
```

### VLAN Configuration

#### Single VLAN (vlan-id)

Command: `vlan-id [vlan-id] tpid [tpid]`

- vlan-id: 1-4094
- tpid: 0x8100 (default), 0x9100, 0x9200

```
dnRouter(cfg)# interfaces
dnRouter(cfg-if)# bundle-1.1
dnRouter(cfg-if-bundle-1.1)# vlan-id 20

dnRouter(cfg-if)# ge10-1/1/1.100
dnRouter(cfg-if-ge10-1/1/1.100)# vlan-id 301 tpid 0x9100
```

#### QinQ (vlan-tags)

Command: `vlan-tags outer-tag [outer-vlan-id] inner-tag [inner-vlan-id] outer-tpid [tpid]`

```
dnRouter(cfg)# interfaces
dnRouter(cfg-if)# bundle-1.2
dnRouter(cfg-if-bundle-1.2)# vlan-tags outer-tag 20 inner-tag 20

dnRouter(cfg-if)# ge10-1/1/2.100
dnRouter(cfg-if-ge10-1/1/2.100)# vlan-tags outer-tag 20 inner-tag 301 outer-tpid 0x8100
```

### L2-Service

To enable L2 service on an interface (required for EVPN/FXC):

Command: `l2-service [enabled|disabled]`

```
dnRouter(cfg)# interfaces
dnRouter(cfg-if)# bundle-100.2
dnRouter(cfg-if-bundle-100.2)# l2-service enabled

dnRouter(cfg-if)# ge100-1/0/1.22
dnRouter(cfg-if-ge100-1/0/1.22)# l2-service enabled
```

---

## Network Services

### EVPN-VPWS-FXC

EVPN-VPWS Flexible Cross-Connect Service for L2VPN.

#### Hierarchy

```
network-services
  evpn-vpws-fxc
    instance <name>
      admin-state enabled|disabled
      fxc-mode vlan-aware
      description <text>
      l2-mtu <value>
      interface <interface-name>
      transport-protocol
        mpls
      protocols
        bgp <as-number>
          route-distinguisher <rd-value>
          export-l2vpn-evpn route-target <rt-value>
          import-l2vpn-evpn route-target <rt-value>
```

#### Creating FXC Instance

```
dnRouter# configure
dnRouter(cfg)# network-services
dnRouter(cfg-netsrv)# evpn-vpws-fxc
dnRouter(cfg-netsrv-fxc)# instance evpn-vpws-fxc1
dnRouter(cfg-netsrv-fxc-evpn-vpws-fxc1)#
```

#### Admin State

```
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# admin-state enabled
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# admin-state disabled
```

#### FXC Mode

```
dnRouter(cfg-evpn-vpws-fxc-inst)# fxc-mode vlan-aware
```

#### Attaching Interface

Interface must be L2-service enabled sub-interface (geX-X/X/X.Y or bundle-X.Y):

```
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# interface ge100-0/0/0.10
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# interface bundle-1.120
```

#### Transport Protocol (MPLS)

```
dnRouter(cfg-netsrv-evpn-vpws-inst)# transport-protocol
dnRouter(cfg-evpn-vpws-inst-tp)# mpls
```

#### BGP Protocol Configuration

```
dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn1
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
dnRouter(cfg-inst-protocols-bgp)# route-distinguisher 56335:1
dnRouter(cfg-inst-protocols-bgp)# export-l2vpn-evpn route-target 49844:20
dnRouter(cfg-inst-protocols-bgp)# import-l2vpn-evpn route-target 49844:20
```

Multiple route-targets can be specified:
```
dnRouter(cfg-inst-protocols-bgp)# export-l2vpn-evpn route-target 49844:20, 49844:30
```

#### Complete FXC Example

```
dnRouter# configure
dnRouter(cfg)# network-services
dnRouter(cfg-netsrv)# evpn-vpws-fxc
dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance FXC_SERVICE_1
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# admin-state enabled
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# fxc-mode vlan-aware
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# interface ge100-0/0/0.100
dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
dnRouter(cfg-inst-protocols-bgp)# route-distinguisher 10.0.0.1:1
dnRouter(cfg-inst-protocols-bgp)# export-l2vpn-evpn route-target 65000:1
dnRouter(cfg-inst-protocols-bgp)# import-l2vpn-evpn route-target 65000:1
```

---

### VRF (L3VPN)

Virtual Routing and Forwarding for L3VPN services.

#### Hierarchy

```
network-services
  vrf
    instance <name>
      description <text>
      interface <interface-name>
      protocols
        bgp <as-number>
          route-distinguisher <rd-value>
          router-id <ipv4-address>
          afi ipv4-unicast
            export-vpnv4-policy <policy>
            import-vpnv4-policy <policy>
            export-vpnv4 route-target <rt-value>
            import-vpnv4 route-target <rt-value>
```

#### Creating VRF Instance

```
dnRouter# configure
dnRouter(cfg)# network-services
dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
dnRouter(cfg-netsrv-vrf-inst)#
```

#### Attaching Interface to VRF

```
dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
dnRouter(cfg-netsrv-vrf-inst)# interface bundle-1
dnRouter(cfg-netsrv-vrf-inst)# interface ge100-1/1/1.10
```

#### BGP Configuration for VRF

```
dnRouter(cfg-network-services)# vrf
dnRouter(cfg-network-services-vrf)# instance customer_vrf_1
dnRouter(cfg-network-services-vrf-inst)# protocols
dnRouter(cfg-vrf-inst-protocols)# bgp 65000
dnRouter(cfg-inst-protocols-bgp)# route-distinguisher 56335:1
```

---

### EVPN (MAC-VRF)

EVPN service for bridging with MAC learning.

#### Hierarchy

```
network-services
  evpn
    instance <name>
      description <text>
      interface <interface-name>
      router-interface <irb-interface>
      evpn-protocols
        bgp
          route-distinguisher <rd-value>
          export-l2vpn-evpn route-target <rt-value>
          import-l2vpn-evpn route-target <rt-value>
```

#### Creating EVPN Instance

```
dnRouter# configure
dnRouter(cfg)# network-services
dnRouter(cfg-netsrv)# evpn
dnRouter(cfg-netsrv-evpn)# instance evpn1
dnRouter(cfg-netsrv-evpn-inst)#
```

---

### Multihoming

EVPN Multihoming for redundant connections.

#### Hierarchy

```
network-services
  multihoming
    interface <interface-name>
      esi arbitrary value <esi-value>
      redundancy-mode single-active|all-active|port-active
```

#### Creating Multihomed Interface

```
dnRouter# configure
dnRouter(cfg)# network-services
dnRouter(cfg-netsrv)# multihoming
dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
dnRouter(cfg-netsrv-mh-int)#

dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0.10
dnRouter(cfg-evpn-mh-int)#
```

#### ESI Configuration

ESI types: arbitrary (requires value), lacp

```
dnRouter(cfg-netsrv-mh-int)# esi arbitrary value 00:11:22:33:44:55:66:77:88:99
```

#### Redundancy Mode

Options: single-active, all-active, port-active

```
dnRouter(cfg-netsrv-mh-int)# redundancy-mode single-active
dnRouter(cfg-netsrv-mh-int)# redundancy-mode all-active
```

---

## System Profile

System profile dictates the feature set available in the system.

#### Command

```
dnRouter# configure
dnRouter(cfg)# system
dnRouter(cfg-system)# profile <profile-name>
```

**Warning**: Profile reconfiguration is traffic affecting and causes WB Agent restart on all NCPs.

#### Available Profiles

- `default` - Default profile
- `l3_pe` - L3 PE profile (for PWHE scale)
- Custom profiles as defined by the system

```
dnRouter(cfg-system)# profile l3_pe
Notice: Continuing with the commit will cause the following:
The following commit will change the system profile. WB Agent process on all NCPs shall restart, traffic loss will occur and some features may not be available after this change takes effect.
Enter yes to continue with commit, no to abort commit (yes/no) [no]
```

---

## Route Distinguisher Format

Route Distinguisher (RD) format: `<ip-address>:<number>` or `<asn>:<number>`

Examples:
- `10.0.0.1:1`
- `56335:1`
- `auto` (system generates using router-id)

## Route Target Format

Route Target (RT) format: `<asn>:<number>`

Examples:
- `65000:1`
- `49844:20`

Multiple RTs can be comma-separated:
- `49844:20, 49844:30`

---

## Quick Reference Examples

### Complete FXC Service with Interface

```
! Create sub-interface with VLAN
interfaces
  ge100-0/0/0.100
    vlan-id 100
    l2-service enabled
!
! Create FXC service
network-services
  evpn-vpws-fxc
    instance FXC-1
      admin-state enabled
      fxc-mode vlan-aware
      interface ge100-0/0/0.100
      protocols
        bgp 65000
          route-distinguisher 10.0.0.1:1
          export-l2vpn-evpn route-target 65000:1
          import-l2vpn-evpn route-target 65000:1
```

### Complete VRF with Interface

```
! Create sub-interface
interfaces
  ge100-1/0/0.200
    vlan-id 200
    ipv4-address 192.168.1.1/24
!
! Create VRF
network-services
  vrf
    instance CUSTOMER_VRF
      interface ge100-1/0/0.200
      protocols
        bgp 65000
          route-distinguisher 10.0.0.1:100
```

### Multihomed Interface with FXC

```
! Configure multihoming on interface
network-services
  multihoming
    interface ge100-0/0/0.100
      esi arbitrary value 00:01:02:03:04:05:06:07:08:09
      redundancy-mode all-active
!
! Associate with FXC service
  evpn-vpws-fxc
    instance FXC-MH
      interface ge100-0/0/0.100
```

---

*Documentation generated from DriveNets DNOS CLI RST files*
