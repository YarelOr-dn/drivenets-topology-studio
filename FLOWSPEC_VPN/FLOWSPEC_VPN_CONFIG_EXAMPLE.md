# Flowspec VPN - DNOS Configuration Example (Accurate Syntax)

## Topology Reference

```
                              ┌─────────────┐
                              │     RR      │
                              │  3.3.3.3    │
                              │  AS 65001   │
                              └──────┬──────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
              ┌─────┴─────┐                     ┌─────┴─────┐
              │    PE1    │                     │    PE2    │
              │  1.1.1.1  │═════════════════════│  2.2.2.2  │
              │  AS 65001 │    MPLS Core        │  AS 65001 │
              └─────┬─────┘                     └─────┬─────┘
                    │                                 │
              ge400-0/0/1                       ge400-0/0/1
              VRF: CUST-A                       VRF: CUST-A
                    │                                 │
              ┌─────┴─────┐                     ┌─────┴─────┐
              │  SPIRENT  │                     │  SPIRENT  │
              │  Port 1   │                     │  Port 2   │
              │ (TX)      │                     │ (RX)      │
              └───────────┘                     └───────────┘

IP Addressing:
- PE1 Loopback: 1.1.1.1/32
- PE2 Loopback: 2.2.2.2/32
- RR Loopback:  3.3.3.3/32
- PE1-PE2 Link: 10.0.0.0/30 (PE1: 10.0.0.1, PE2: 10.0.0.2)
- PE1-RR Link:  10.0.1.0/30 (PE1: 10.0.1.1, RR: 10.0.1.2)
- PE2-RR Link:  10.0.2.0/30 (PE2: 10.0.2.1, RR: 10.0.2.2)
- PE1 Customer: 192.168.1.0/24 (PE1: .1, Spirent: .100)
- PE2 Customer: 192.168.2.0/24 (PE2: .1, Spirent: .100)

VRF:
- Name: CUST-A
- PE1 RD: 65001:100
- PE2 RD: 65001:200
- RT (both): 65001:100
```

---

## DNOS CLI Hierarchy Overview

```
network-services
└── vrf
    └── instance <vrf-name>
        ├── interface <interface-name>       # Attach interface to VRF
        ├── protocols
        │   ├── bgp <asn>
        │   │   ├── route-distinguisher <rd> # RD for VPN routes
        │   │   ├── address-family ipv4-unicast
        │   │   │   ├── export-vpn route-target <rt>
        │   │   │   └── import-vpn route-target <rt>
        │   │   ├── address-family ipv4-flowspec    # ← Flowspec VRF AF
        │   │   │   ├── export-vpn route-target <rt>
        │   │   │   └── import-vpn route-target <rt>
        │   │   ├── address-family ipv6-flowspec
        │   │   │   ├── export-vpn route-target <rt>
        │   │   │   └── import-vpn route-target <rt>
        │   │   └── neighbor <ip>
        │   │       └── address-family ipv4-flowspec # CE neighbor
        │   └── evpn
        │       ├── export-l2vpn-evpn route-target <rt>
        │       └── import-l2vpn-evpn route-target <rt>
        └── description <text>

protocols
└── bgp <asn>                               # Global BGP (default VRF)
    ├── address-family ipv4-flowspec-vpn    # ← Flowspec-VPN SAFI (PE-PE/PE-RR)
    ├── address-family ipv6-flowspec-vpn
    └── neighbor <ip>
        └── address-family ipv4-flowspec-vpn
```

---

## PE1 Configuration

```
!
! ============================================
! PE1 - FLOWSPEC VPN CONFIGURATION
! ============================================
!

! ----------------
! SYSTEM
! ----------------
system
  name PE1
!

! ----------------
! INTERFACES
! ----------------
interfaces
  !
  ! Loopback
  lo0
    admin-state enabled
    ipv4
      address 1.1.1.1/32
    !
  !
  !
  ! Core link to PE2
  ge400-0/0/0
    admin-state enabled
    description "To PE2"
    mtu 9216
    ipv4
      address 10.0.0.1/30
    !
  !
  !
  ! Core link to RR
  ge400-0/0/2
    admin-state enabled
    description "To RR"
    mtu 9216
    ipv4
      address 10.0.1.1/30
    !
  !
  !
  ! Customer-facing interface (parent)
  ge400-0/0/1
    admin-state enabled
    description "CUST-A - Spirent Port 1"
    mtu 9000
  !
  !
  ! Customer sub-interface (will be attached to VRF)
  ge400-0/0/1.100
    admin-state enabled
    description "CUST-A Access"
    encapsulation
      dot1q
        vlan-id 100
      !
    !
    l3-service enabled
    ipv4
      address 192.168.1.1/24
    !
  !
!

! ----------------
! OSPF (IGP for MPLS Core)
! ----------------
protocols
  ospf
    instance default
      router-id 1.1.1.1
      area 0.0.0.0
        interface lo0
          passive
        !
        interface ge400-0/0/0
          network-type point-to-point
        !
        interface ge400-0/0/2
          network-type point-to-point
        !
      !
    !
  !
!

! ----------------
! MPLS & LDP
! ----------------
protocols
  mpls
    admin-state enabled
  !
  ldp
    admin-state enabled
    router-id 1.1.1.1
    interface ge400-0/0/0
    !
    interface ge400-0/0/2
    !
  !
!

! ----------------
! GLOBAL BGP (Default VRF)
! Flowspec-VPN SAFI for PE-PE/PE-RR sessions
! ----------------
protocols
  bgp 65001
    router-id 1.1.1.1
    !
    ! Global Address Families
    address-family ipv4-unicast
    !
    address-family ipv4-vpn
    !
    address-family ipv6-vpn
    !
    ! FLOWSPEC-VPN (SAFI 134) - Used between PE-PE/PE-RR
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    !
    ! Neighbor to RR
    neighbor 3.3.3.3
      remote-as 65001
      description "Route Reflector"
      update-source lo0
      !
      address-family ipv4-unicast
        admin-state enabled
      !
      address-family ipv4-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv6-vpn
        admin-state enabled
        send-community extended
      !
      ! FLOWSPEC-VPN to RR
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!

! ----------------
! VRF DEFINITION
! ----------------
network-services
  vrf
    instance CUST-A
      description "Customer A VPN"
      !
      ! Attach interface to VRF
      interface ge400-0/0/1.100
      !
      !
      ! VRF BGP Configuration
      protocols
        bgp 65001
          !
          ! Route Distinguisher (unique per PE for same VPN)
          route-distinguisher 65001:100
          !
          ! IPv4 Unicast with VPN export/import
          address-family ipv4-unicast
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
          ! IPv4 Flowspec with VPN export/import
          address-family ipv4-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
          ! IPv6 Flowspec with VPN export/import
          address-family ipv6-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
        !
      !
    !
  !
!

! ----------------
! FLOWSPEC LOCAL POLICIES
! (For locally-originated Flowspec rules)
! ----------------
routing-policy
  flowspec-local-policies
    ipv4
      !
      ! Match Class Definition - Block DDoS UDP/53
      mc-defns BLOCK-DDOS-UDP53
        dest-ip 10.1.1.0/24
        protocol eq 17
        dest-port eq 53
      !
      !
      ! Match Class Definition - Rate-limit ICMP
      mc-defns RATE-LIMIT-ICMP
        dest-ip 10.1.1.0/24
        protocol eq 1
      !
      !
      ! Policy - Drop DDoS traffic
      policy DROP-DDOS
        match-class BLOCK-DDOS-UDP53
          action discard
        !
      !
      !
      ! Policy - Rate limit ICMP to 1Mbps
      policy LIMIT-ICMP
        match-class RATE-LIMIT-ICMP
          action rate-limit 1000000
        !
      !
      !
      ! Apply to VRF CUST-A (uncommment to activate)
      ! apply-policy-to-flowspec DROP-DDOS vrf CUST-A
    !
  !
!
```

---

## PE2 Configuration

```
!
! ============================================
! PE2 - FLOWSPEC VPN CONFIGURATION
! ============================================
!

! ----------------
! SYSTEM
! ----------------
system
  name PE2
!

! ----------------
! INTERFACES
! ----------------
interfaces
  !
  ! Loopback
  lo0
    admin-state enabled
    ipv4
      address 2.2.2.2/32
    !
  !
  !
  ! Core link to PE1
  ge400-0/0/0
    admin-state enabled
    description "To PE1"
    mtu 9216
    ipv4
      address 10.0.0.2/30
    !
  !
  !
  ! Core link to RR
  ge400-0/0/2
    admin-state enabled
    description "To RR"
    mtu 9216
    ipv4
      address 10.0.2.1/30
    !
  !
  !
  ! Customer-facing interface (parent)
  ge400-0/0/1
    admin-state enabled
    description "CUST-A - Spirent Port 2"
    mtu 9000
  !
  !
  ! Customer sub-interface
  ge400-0/0/1.100
    admin-state enabled
    description "CUST-A Access"
    encapsulation
      dot1q
        vlan-id 100
      !
    !
    l3-service enabled
    ipv4
      address 192.168.2.1/24
    !
  !
!

! ----------------
! OSPF
! ----------------
protocols
  ospf
    instance default
      router-id 2.2.2.2
      area 0.0.0.0
        interface lo0
          passive
        !
        interface ge400-0/0/0
          network-type point-to-point
        !
        interface ge400-0/0/2
          network-type point-to-point
        !
      !
    !
  !
!

! ----------------
! MPLS & LDP
! ----------------
protocols
  mpls
    admin-state enabled
  !
  ldp
    admin-state enabled
    router-id 2.2.2.2
    interface ge400-0/0/0
    !
    interface ge400-0/0/2
    !
  !
!

! ----------------
! GLOBAL BGP
! ----------------
protocols
  bgp 65001
    router-id 2.2.2.2
    !
    address-family ipv4-unicast
    !
    address-family ipv4-vpn
    !
    address-family ipv6-vpn
    !
    ! FLOWSPEC-VPN
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    !
    ! Neighbor to RR
    neighbor 3.3.3.3
      remote-as 65001
      description "Route Reflector"
      update-source lo0
      !
      address-family ipv4-unicast
        admin-state enabled
      !
      address-family ipv4-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv6-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!

! ----------------
! VRF DEFINITION
! ----------------
network-services
  vrf
    instance CUST-A
      description "Customer A VPN"
      !
      ! Attach interface to VRF
      interface ge400-0/0/1.100
      !
      !
      ! VRF BGP Configuration
      protocols
        bgp 65001
          !
          ! Different RD than PE1!
          route-distinguisher 65001:200
          !
          ! IPv4 Unicast
          address-family ipv4-unicast
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
          ! IPv4 Flowspec
          address-family ipv4-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
          ! IPv6 Flowspec
          address-family ipv6-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
        !
      !
    !
  !
!
```

---

## RR (Route Reflector) Configuration

```
!
! ============================================
! RR - ROUTE REFLECTOR CONFIGURATION
! ============================================
!

! ----------------
! SYSTEM
! ----------------
system
  name RR
!

! ----------------
! INTERFACES
! ----------------
interfaces
  !
  ! Loopback
  lo0
    admin-state enabled
    ipv4
      address 3.3.3.3/32
    !
  !
  !
  ! Link to PE1
  ge400-0/0/0
    admin-state enabled
    description "To PE1"
    mtu 9216
    ipv4
      address 10.0.1.2/30
    !
  !
  !
  ! Link to PE2
  ge400-0/0/1
    admin-state enabled
    description "To PE2"
    mtu 9216
    ipv4
      address 10.0.2.2/30
    !
  !
!

! ----------------
! OSPF
! ----------------
protocols
  ospf
    instance default
      router-id 3.3.3.3
      area 0.0.0.0
        interface lo0
          passive
        !
        interface ge400-0/0/0
          network-type point-to-point
        !
        interface ge400-0/0/1
          network-type point-to-point
        !
      !
    !
  !
!

! ----------------
! MPLS & LDP
! ----------------
protocols
  mpls
    admin-state enabled
  !
  ldp
    admin-state enabled
    router-id 3.3.3.3
    interface ge400-0/0/0
    !
    interface ge400-0/0/1
    !
  !
!

! ----------------
! BGP - ROUTE REFLECTOR
! ----------------
protocols
  bgp 65001
    router-id 3.3.3.3
    !
    address-family ipv4-unicast
    !
    address-family ipv4-vpn
    !
    address-family ipv6-vpn
    !
    ! FLOWSPEC-VPN - RR must support this!
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    !
    ! Neighbor PE1 (RR Client)
    neighbor 1.1.1.1
      remote-as 65001
      description "PE1 - RR Client"
      update-source lo0
      !
      address-family ipv4-unicast
        admin-state enabled
        route-reflector-client
      !
      address-family ipv4-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
      address-family ipv6-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
      ! FLOWSPEC-VPN - Mark as RR client
      address-family ipv4-flowspec-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
    !
    !
    ! Neighbor PE2 (RR Client)
    neighbor 2.2.2.2
      remote-as 65001
      description "PE2 - RR Client"
      update-source lo0
      !
      address-family ipv4-unicast
        admin-state enabled
        route-reflector-client
      !
      address-family ipv4-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
      address-family ipv6-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
      address-family ipv4-flowspec-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        route-reflector-client
        send-community extended
      !
    !
  !
!
```

---

## Key DNOS Syntax Differences

### ❌ WRONG (Generic/Other Vendors)
```
service-instance CUST-A
  type l3vpn
  route-distinguisher 65001:100
  address-family ipv4-flowspec
    route-target import 65001:100
    route-target export 65001:100
```

### ✅ CORRECT (DNOS)
```
network-services
  vrf
    instance CUST-A
      interface ge400-0/0/1.100
      protocols
        bgp 65001
          route-distinguisher 65001:100
          address-family ipv4-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
```

---

## Verification Commands

### On PE1 (Rule Origin)

```bash
# Check VRF exists
show network-services vrf

# Check VRF BGP config
show network-services vrf instance CUST-A protocols bgp

# Check VRF Flowspec table
show bgp vrf CUST-A ipv4 flowspec

# Check Flowspec-VPN export (global table)
show bgp ipv4 flowspec-vpn

# Check neighbor status
show bgp neighbor 3.3.3.3 address-family ipv4-flowspec-vpn

# Check datapath
show flowspec ncp 0
```

### On RR

```bash
# Check Flowspec-VPN table
show bgp ipv4 flowspec-vpn

# Check routes advertised to PE2
show bgp neighbor 2.2.2.2 address-family ipv4-flowspec-vpn advertised-routes
```

### On PE2 (Rule Import)

```bash
# Check Flowspec-VPN received
show bgp ipv4 flowspec-vpn

# Check VRF import (RT match)
show bgp vrf CUST-A ipv4 flowspec

# Check datapath (critical!)
show flowspec ncp 0

# Check xray rules (vrf_id should NOT be 0)
# From shell:
xraycli /wb_agent/flowspec/bgp/ipv4/rules
```

---

## Quick Reference: DNOS CLI Paths

| Configuration | DNOS CLI Path |
|--------------|---------------|
| VRF Instance | `network-services > vrf > instance <name>` |
| VRF Interface | `network-services > vrf > instance <name> > interface <if>` |
| VRF BGP | `network-services > vrf > instance <name> > protocols > bgp <asn>` |
| VRF RD | `... > bgp <asn> > route-distinguisher <rd>` |
| VRF Flowspec AF | `... > bgp <asn> > address-family ipv4-flowspec` |
| VRF RT Export | `... > address-family ipv4-flowspec > export-vpn route-target <rt>` |
| VRF RT Import | `... > address-family ipv4-flowspec > import-vpn route-target <rt>` |
| Global Flowspec-VPN | `protocols > bgp <asn> > address-family ipv4-flowspec-vpn` |
| Neighbor Flowspec-VPN | `protocols > bgp <asn> > neighbor <ip> > address-family ipv4-flowspec-vpn` |
