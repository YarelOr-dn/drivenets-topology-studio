# Flowspec VPN - Complete Configuration with Explanations

## Topology

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
              ge400-0/0/1.100                   ge400-0/0/1.100
              VRF: CUST-A                       VRF: CUST-A
                    │                                 │
              ┌─────┴─────┐                     ┌─────┴─────┐
              │  SPIRENT  │                     │  SPIRENT  │
              │  Port 1   │                     │  Port 2   │
              │ (TX)      │                     │ (RX)      │
              └───────────┘                     └───────────┘
```

---

# 📚 Key Concepts Explained

## 1. Route Distinguisher (RD)

### What is RD?
The **Route Distinguisher (RD)** is an 8-byte value prepended to IPv4/IPv6 prefixes to make them **globally unique** in the BGP VPN table.

### Why do we need RD?
Without RD, if two different customers (VRFs) both have the prefix `10.0.0.0/24`, BGP would see them as the same route. The RD makes them unique:

```
Customer A's 10.0.0.0/24  →  65001:100:10.0.0.0/24
Customer B's 10.0.0.0/24  →  65001:200:10.0.0.0/24
                             ^^^^^^^^^ 
                             RD makes them different!
```

### RD Format
```
<ASN>:<ID>       →  65001:100      (2-byte ASN : 4-byte ID)
<ASN>L:<ID>      →  4200000000L:1  (4-byte ASN : 2-byte ID)
<IP>:<ID>        →  1.1.1.1:100    (4-byte IP : 2-byte ID)
auto             →  System generates from router-id
```

### Critical Rule: RD Must Be UNIQUE Per PE!
```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   PE1 VRF CUST-A:  RD = 65001:100                                   │
│   PE2 VRF CUST-A:  RD = 65001:200    ← DIFFERENT!                   │
│                                                                      │
│   Why? Because RD identifies the ORIGIN of the route.               │
│   If both PEs used the same RD, we couldn't tell which PE           │
│   originated the route in the global BGP table.                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Route Target (RT)

### What is RT?
The **Route Target (RT)** is a BGP Extended Community that controls **which VRFs import which routes**.

### How RT Works
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   export-vpn route-target 65001:100                                         │
│   ─────────────────────────────────                                         │
│   "When I advertise routes from this VRF, tag them with RT 65001:100"       │
│                                                                             │
│   import-vpn route-target 65001:100                                         │
│   ─────────────────────────────────                                         │
│   "Import any VPN routes that have RT 65001:100 into this VRF"             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RT Format (Same as RD)
```
<ASN>:<ID>   →  65001:100
```

### Critical Rule: RT Must MATCH for VPN Peering!
```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   PE1 VRF CUST-A:                                                    │
│     export-vpn route-target 65001:100   ─┐                          │
│     import-vpn route-target 65001:100    │ SAME RT                  │
│                                          │                          │
│   PE2 VRF CUST-A:                        │                          │
│     export-vpn route-target 65001:100   ─┘                          │
│     import-vpn route-target 65001:100                               │
│                                                                      │
│   Result: Routes flow between PE1 and PE2 for the same VPN          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. RD vs RT - The Key Difference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   RD (Route Distinguisher)              RT (Route Target)                   │
│   ────────────────────────              ─────────────────                   │
│                                                                             │
│   • Makes routes UNIQUE                 • Controls IMPORT/EXPORT            │
│   • Different per PE                    • Same for same VPN                 │
│   • Prepended to prefix                 • Carried as Extended Community     │
│   • Used for route identification       • Used for route filtering          │
│                                                                             │
│   Think of it like:                     Think of it like:                   │
│   "Passport number" (unique per person) "Club membership" (shared by group) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Flowspec-VPN vs Flowspec

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ipv4-flowspec (SAFI 133)              ipv4-flowspec-vpn (SAFI 134)        │
│   ────────────────────────              ──────────────────────────          │
│                                                                             │
│   • Used in VRF context                 • Used in global context            │
│   • PE-CE sessions                      • PE-PE / PE-RR sessions            │
│   • No RD in NLRI                       • Includes RD in NLRI               │
│   • Local VRF scope                     • Cross-PE VPN scope                │
│                                                                             │
│   Configured under:                     Configured under:                   │
│   network-services > vrf > instance >   protocols > bgp > address-family    │
│   protocols > bgp > address-family      ipv4-flowspec-vpn                   │
│   ipv4-flowspec                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 🔧 PE1 Configuration (Detailed with Explanations)

```
!
! ════════════════════════════════════════════════════════════════════════════
! PE1 - FLOWSPEC VPN CONFIGURATION
! ════════════════════════════════════════════════════════════════════════════
!

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ SYSTEM - Basic device identity                                           │
! └──────────────────────────────────────────────────────────────────────────┘
system
  name PE1
!

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ INTERFACES                                                               │
! │                                                                          │
! │ lo0          - Loopback for BGP peering (source of RD if using auto)    │
! │ ge400-0/0/0  - Core link to PE2 (MPLS-enabled)                          │
! │ ge400-0/0/2  - Core link to RR (MPLS-enabled)                           │
! │ ge400-0/0/1  - Customer-facing (parent interface)                       │
! │ ge400-0/0/1.100 - Customer sub-interface (will be in VRF CUST-A)        │
! └──────────────────────────────────────────────────────────────────────────┘
interfaces
  !
  ! === LOOPBACK ===
  ! Used for:
  !   1. BGP peering (update-source)
  !   2. MPLS tunnel endpoint
  !   3. Router-ID for protocols
  !
  lo0
    admin-state enabled
    ipv4
      address 1.1.1.1/32
    !
  !
  !
  ! === CORE LINK TO PE2 ===
  ! MPLS-enabled link for VPN traffic
  !
  ge400-0/0/0
    admin-state enabled
    description "To PE2 - MPLS Core"
    mtu 9216
    ipv4
      address 10.0.0.1/30
    !
  !
  !
  ! === CORE LINK TO RR ===
  ! MPLS-enabled link for BGP route reflection
  !
  ge400-0/0/2
    admin-state enabled
    description "To RR - MPLS Core"
    mtu 9216
    ipv4
      address 10.0.1.1/30
    !
  !
  !
  ! === CUSTOMER PARENT INTERFACE ===
  ! Physical port connected to Spirent
  !
  ge400-0/0/1
    admin-state enabled
    description "CUST-A - Spirent Port 1"
    mtu 9000
  !
  !
  ! === CUSTOMER SUB-INTERFACE ===
  ! This will be attached to VRF CUST-A
  ! Note: IP is configured here, VRF attachment is done in network-services
  !
  ge400-0/0/1.100
    admin-state enabled
    description "CUST-A Access - VLAN 100"
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

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ OSPF - Interior Gateway Protocol                                         │
! │                                                                          │
! │ Purpose: Provides reachability to loopbacks (BGP next-hops)             │
! │ Note: Only core-facing interfaces, NOT customer interfaces              │
! └──────────────────────────────────────────────────────────────────────────┘
protocols
  ospf
    instance default
      router-id 1.1.1.1
      area 0.0.0.0
        !
        ! Loopback: advertised but doesn't form adjacency
        interface lo0
          passive
        !
        ! Core links: form OSPF adjacency for MPLS label distribution
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

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ MPLS & LDP - Label Distribution                                          │
! │                                                                          │
! │ Purpose: Provides MPLS labels for VPN traffic forwarding                │
! │ LDP establishes label-switched paths (LSPs) between PE loopbacks        │
! └──────────────────────────────────────────────────────────────────────────┘
protocols
  mpls
    admin-state enabled
  !
  ldp
    admin-state enabled
    router-id 1.1.1.1
    !
    ! Enable LDP on core-facing interfaces only
    interface ge400-0/0/0
    !
    interface ge400-0/0/2
    !
  !
!

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ GLOBAL BGP (Default VRF)                                                 │
! │                                                                          │
! │ This configures BGP in the DEFAULT VRF for PE-PE and PE-RR sessions.    │
! │                                                                          │
! │ Key address-families here:                                               │
! │   - ipv4-vpn        : L3VPN unicast routes                              │
! │   - ipv4-flowspec-vpn: Flowspec rules for VPNs (SAFI 134)               │
! │                                                                          │
! │ These are used for TRANSPORT between PEs, not for customer traffic.     │
! └──────────────────────────────────────────────────────────────────────────┘
protocols
  bgp 65001
    router-id 1.1.1.1
    !
    ! ════════════════════════════════════════════════════════════════════════
    ! GLOBAL ADDRESS FAMILIES
    ! These define what AFI/SAFIs are enabled globally
    ! ════════════════════════════════════════════════════════════════════════
    !
    address-family ipv4-unicast
    !
    !
    ! ipv4-vpn (SAFI 128): Carries L3VPN unicast routes with RD
    address-family ipv4-vpn
    !
    address-family ipv6-vpn
    !
    !
    ! ════════════════════════════════════════════════════════════════════════
    ! FLOWSPEC-VPN (SAFI 134)
    ! ════════════════════════════════════════════════════════════════════════
    ! This is the KEY for Flowspec VPN!
    ! 
    ! ipv4-flowspec-vpn carries Flowspec rules between PEs with:
    !   - Route Distinguisher (identifies source VRF/PE)
    !   - Route Target (controls which VRFs import the rule)
    !   - Flowspec NLRI (the actual match criteria)
    !   - Extended Communities (actions like drop, rate-limit)
    !
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    !
    ! ════════════════════════════════════════════════════════════════════════
    ! NEIGHBOR TO ROUTE REFLECTOR
    ! ════════════════════════════════════════════════════════════════════════
    ! iBGP session to RR using loopback addresses
    !
    neighbor 3.3.3.3
      remote-as 65001
      description "Route Reflector"
      !
      ! Use loopback as source - ensures session survives link failures
      update-source lo0
      !
      ! --- IPv4 Unicast ---
      address-family ipv4-unicast
        admin-state enabled
      !
      !
      ! --- IPv4 VPN (L3VPN) ---
      address-family ipv4-vpn
        admin-state enabled
        !
        ! IMPORTANT: send-community extended
        ! RT is carried as Extended Community - must be sent!
        send-community extended
      !
      !
      address-family ipv6-vpn
        admin-state enabled
        send-community extended
      !
      !
      ! --- IPv4 Flowspec-VPN ---
      ! This enables Flowspec rule exchange with the RR
      !
      address-family ipv4-flowspec-vpn
        admin-state enabled
        !
        ! CRITICAL: Extended communities carry:
        !   - Route Target (for VRF import/export)
        !   - Flowspec actions (traffic-rate, redirect, etc.)
        send-community extended
      !
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ VRF DEFINITION                                                           │
! │                                                                          │
! │ This is where the VRF is created and configured.                        │
! │                                                                          │
! │ Structure:                                                               │
! │   network-services                                                       │
! │     └── vrf                                                              │
! │           └── instance CUST-A                                            │
! │                 ├── interface ge400-0/0/1.100   (attach interface)       │
! │                 └── protocols                                            │
! │                       └── bgp 65001                                      │
! │                             ├── route-distinguisher                      │
! │                             └── address-family ipv4-flowspec             │
! │                                   ├── export-vpn route-target            │
! │                                   └── import-vpn route-target            │
! └──────────────────────────────────────────────────────────────────────────┘
network-services
  vrf
    instance CUST-A
      description "Customer A VPN"
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! INTERFACE ATTACHMENT
      ! ══════════════════════════════════════════════════════════════════════
      ! This moves the interface from default VRF to CUST-A VRF.
      ! The interface keeps its IP configuration.
      ! All routes on this interface are now in VRF CUST-A's routing table.
      !
      interface ge400-0/0/1.100
      !
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! VRF BGP CONFIGURATION
      ! ══════════════════════════════════════════════════════════════════════
      ! This is BGP configuration SPECIFIC to this VRF.
      ! It's separate from the global BGP (protocols > bgp 65001).
      !
      protocols
        bgp 65001
          !
          ! ────────────────────────────────────────────────────────────────────
          ! ROUTE DISTINGUISHER
          ! ────────────────────────────────────────────────────────────────────
          !
          ! RD = 65001:100 for PE1's CUST-A VRF
          !
          ! This makes routes from this VRF unique in the global BGP-VPN table:
          !   192.168.1.0/24 in CUST-A → becomes → 65001:100:192.168.1.0/24
          !
          ! PE2 will use RD 65001:200 for ITS CUST-A VRF (different!)
          !
          route-distinguisher 65001:100
          !
          !
          ! ────────────────────────────────────────────────────────────────────
          ! ADDRESS-FAMILY: IPv4 Unicast (L3VPN)
          ! ────────────────────────────────────────────────────────────────────
          !
          address-family ipv4-unicast
            !
            ! export-vpn route-target 65001:100
            ! ─────────────────────────────────
            ! "Tag all routes exported from this VRF with RT 65001:100"
            !
            ! When a route is advertised to the RR via ipv4-vpn SAFI,
            ! it will carry this RT as an Extended Community.
            !
            export-vpn route-target 65001:100
            !
            ! import-vpn route-target 65001:100
            ! ─────────────────────────────────
            ! "Import any ipv4-vpn routes that have RT 65001:100"
            !
            ! When we receive VPN routes from other PEs via the RR,
            ! we check if RT 65001:100 is in the Extended Communities.
            ! If yes → import into this VRF.
            ! If no  → ignore.
            !
            import-vpn route-target 65001:100
          !
          !
          ! ────────────────────────────────────────────────────────────────────
          ! ADDRESS-FAMILY: IPv4 Flowspec
          ! ────────────────────────────────────────────────────────────────────
          !
          ! This is where Flowspec rules for this VRF are configured.
          !
          ! How it works:
          ! 1. Local Flowspec rules (from routing-policy or BGP neighbors)
          !    are stored in this VRF's Flowspec table
          !
          ! 2. export-vpn route-target tags them with RT 65001:100
          !    and exports them to the global ipv4-flowspec-vpn table
          !
          ! 3. The global BGP sends them to the RR via ipv4-flowspec-vpn SAFI
          !
          ! 4. RR reflects them to PE2
          !
          ! 5. PE2's import-vpn route-target 65001:100 matches, so PE2
          !    imports the rule into its CUST-A VRF's Flowspec table
          !
          ! 6. PE2's datapath programs the rule with VRF-ID as qualifier
          !
          address-family ipv4-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
          ! ────────────────────────────────────────────────────────────────────
          ! ADDRESS-FAMILY: IPv6 Flowspec
          ! ────────────────────────────────────────────────────────────────────
          !
          address-family ipv6-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
        !
      !
    !
  !
!

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ FLOWSPEC LOCAL POLICIES                                                  │
! │                                                                          │
! │ These define Flowspec rules that PE1 will ORIGINATE.                    │
! │                                                                          │
! │ Structure:                                                               │
! │   routing-policy                                                         │
! │     └── flowspec-local-policies                                          │
! │           └── ipv4                                                       │
! │                 ├── mc-defns <name>        (match criteria)              │
! │                 ├── policy <name>          (match + action)              │
! │                 └── apply-policy-to-flowspec <policy> vrf <vrf>          │
! └──────────────────────────────────────────────────────────────────────────┘
routing-policy
  flowspec-local-policies
    ipv4
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! MATCH CLASS DEFINITION: Block DDoS UDP/53 (DNS amplification)
      ! ══════════════════════════════════════════════════════════════════════
      !
      ! This defines WHAT traffic to match:
      !   - Destination IP: 10.1.1.0/24
      !   - Protocol: UDP (17)
      !   - Destination Port: 53 (DNS)
      !
      mc-defns BLOCK-DDOS-UDP53
        dest-ip 10.1.1.0/24
        protocol eq 17
        dest-port eq 53
      !
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! MATCH CLASS DEFINITION: Rate-limit ICMP
      ! ══════════════════════════════════════════════════════════════════════
      !
      mc-defns RATE-LIMIT-ICMP
        dest-ip 10.1.1.0/24
        protocol eq 1
      !
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! POLICY: Drop DDoS traffic
      ! ══════════════════════════════════════════════════════════════════════
      !
      ! Links match-class to an ACTION (discard = drop all packets)
      !
      policy DROP-DDOS
        match-class BLOCK-DDOS-UDP53
          action discard
        !
      !
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! POLICY: Rate limit ICMP to 1 Mbps
      ! ══════════════════════════════════════════════════════════════════════
      !
      ! rate-limit value is in bits per second
      !
      policy LIMIT-ICMP
        match-class RATE-LIMIT-ICMP
          action rate-limit 1000000
        !
      !
      !
      ! ══════════════════════════════════════════════════════════════════════
      ! APPLY POLICY TO VRF
      ! ══════════════════════════════════════════════════════════════════════
      !
      ! This actually ACTIVATES the policy and makes it a Flowspec route.
      !
      ! When applied:
      ! 1. Creates a Flowspec NLRI with the match criteria
      ! 2. Adds Extended Community for the action (traffic-rate:0 for discard)
      ! 3. Exports to ipv4-flowspec-vpn with the VRF's RT
      ! 4. Sent to RR, reflected to other PEs
      !
      ! Uncomment to activate:
      ! apply-policy-to-flowspec DROP-DDOS vrf CUST-A
      !
    !
  !
!
```

---

# 🔧 PE2 Configuration

```
!
! ════════════════════════════════════════════════════════════════════════════
! PE2 - FLOWSPEC VPN CONFIGURATION
! ════════════════════════════════════════════════════════════════════════════
!

system
  name PE2
!

interfaces
  lo0
    admin-state enabled
    ipv4
      address 2.2.2.2/32
    !
  !
  ge400-0/0/0
    admin-state enabled
    description "To PE1 - MPLS Core"
    mtu 9216
    ipv4
      address 10.0.0.2/30
    !
  !
  ge400-0/0/2
    admin-state enabled
    description "To RR - MPLS Core"
    mtu 9216
    ipv4
      address 10.0.2.1/30
    !
  !
  ge400-0/0/1
    admin-state enabled
    description "CUST-A - Spirent Port 2"
    mtu 9000
  !
  ge400-0/0/1.100
    admin-state enabled
    description "CUST-A Access - VLAN 100"
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
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    !
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

! ┌──────────────────────────────────────────────────────────────────────────┐
! │ PE2's VRF CUST-A - Note the DIFFERENT RD!                               │
! │                                                                          │
! │ PE1 uses RD 65001:100                                                    │
! │ PE2 uses RD 65001:200  ← DIFFERENT per PE                               │
! │                                                                          │
! │ But RT is the SAME (65001:100) for both PEs                             │
! │ This is what makes them part of the same VPN!                           │
! └──────────────────────────────────────────────────────────────────────────┘
network-services
  vrf
    instance CUST-A
      description "Customer A VPN"
      !
      interface ge400-0/0/1.100
      !
      protocols
        bgp 65001
          !
          ! ════════════════════════════════════════════════════════════════════
          ! DIFFERENT RD than PE1!
          ! ════════════════════════════════════════════════════════════════════
          !
          ! PE1: 65001:100
          ! PE2: 65001:200  ← This one
          !
          ! Why different?
          ! In the global BGP-VPN table, we need to distinguish:
          !   - 65001:100:192.168.1.0/24 (from PE1)
          !   - 65001:200:192.168.2.0/24 (from PE2)
          !
          route-distinguisher 65001:200
          !
          !
          ! ════════════════════════════════════════════════════════════════════
          ! SAME RT as PE1!
          ! ════════════════════════════════════════════════════════════════════
          !
          ! Both PE1 and PE2 use RT 65001:100 for CUST-A VPN.
          ! This is how routes flow between them:
          !
          !   PE1 exports with RT 65001:100
          !         ↓
          !   RR reflects to PE2
          !         ↓
          !   PE2's import-vpn RT 65001:100 matches → imported!
          !
          address-family ipv4-unicast
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
          address-family ipv4-flowspec
            export-vpn route-target 65001:100
            import-vpn route-target 65001:100
          !
          !
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

# 🔧 RR (Route Reflector) Configuration

```
!
! ════════════════════════════════════════════════════════════════════════════
! RR - ROUTE REFLECTOR CONFIGURATION
! ════════════════════════════════════════════════════════════════════════════
!
! The RR doesn't need VRF configuration - it just reflects VPN routes.
! But it MUST support the ipv4-flowspec-vpn address-family!
!

system
  name RR
!

interfaces
  lo0
    admin-state enabled
    ipv4
      address 3.3.3.3/32
    !
  !
  ge400-0/0/0
    admin-state enabled
    description "To PE1"
    mtu 9216
    ipv4
      address 10.0.1.2/30
    !
  !
  ge400-0/0/1
    admin-state enabled
    description "To PE2"
    mtu 9216
    ipv4
      address 10.0.2.2/30
    !
  !
!

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
    !
    ! ════════════════════════════════════════════════════════════════════════
    ! FLOWSPEC-VPN on RR
    ! ════════════════════════════════════════════════════════════════════════
    ! The RR MUST enable these to reflect Flowspec-VPN routes!
    !
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    !
    ! ════════════════════════════════════════════════════════════════════════
    ! PE1 as RR Client
    ! ════════════════════════════════════════════════════════════════════════
    !
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
      !
      ! Flowspec-VPN: Mark PE1 as RR client
      ! This allows routes from PE1 to be reflected to PE2
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
    ! ════════════════════════════════════════════════════════════════════════
    ! PE2 as RR Client
    ! ════════════════════════════════════════════════════════════════════════
    !
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

# 📊 Summary Table

| Parameter | PE1 | PE2 | RR | Notes |
|-----------|-----|-----|-----|-------|
| **AS Number** | 65001 | 65001 | 65001 | Same (iBGP) |
| **Loopback** | 1.1.1.1 | 2.2.2.2 | 3.3.3.3 | Used for BGP peering |
| **VRF Name** | CUST-A | CUST-A | N/A | Same customer |
| **RD** | 65001:100 | 65001:200 | N/A | **DIFFERENT per PE** |
| **RT Export** | 65001:100 | 65001:100 | N/A | **SAME for VPN peering** |
| **RT Import** | 65001:100 | 65001:100 | N/A | **SAME for VPN peering** |
| **Flowspec-VPN** | ✅ | ✅ | ✅ | Required on all |
| **RR Client** | N/A | N/A | PE1, PE2 | RR reflects routes |

---

# 🔄 Data Flow Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  1. PE1 creates Flowspec rule (via local policy or BGP from CE)            │
│     NLRI: DstIP=10.1.1.0/24, Proto=UDP, DstPort=53                         │
│     Action: Discard (traffic-rate:0)                                        │
│                                                                             │
│  2. PE1 exports to ipv4-flowspec-vpn:                                       │
│     RD: 65001:100 (from VRF config)                                         │
│     RT: 65001:100 (from export-vpn route-target)                            │
│     NLRI: 65001:100:DstIP=10.1.1.0/24,Proto=UDP,DstPort=53                 │
│     Communities: RT 65001:100, traffic-rate:0                               │
│                                                                             │
│  3. PE1 sends BGP UPDATE to RR (3.3.3.3) via ipv4-flowspec-vpn SAFI        │
│                                                                             │
│  4. RR receives, stores, and REFLECTS to PE2 (2.2.2.2)                     │
│     (RR adds ORIGINATOR_ID and CLUSTER_LIST)                               │
│                                                                             │
│  5. PE2 receives BGP UPDATE via ipv4-flowspec-vpn SAFI                     │
│     Checks RT: 65001:100                                                    │
│     VRF CUST-A has import-vpn RT 65001:100 → MATCH!                        │
│                                                                             │
│  6. PE2 imports rule into VRF CUST-A's ipv4-flowspec table                 │
│                                                                             │
│  7. PE2 programs datapath:                                                  │
│     TCAM entry with VRF-ID qualifier = CUST-A's internal ID                │
│     Match: DstIP=10.1.1.0/24, Proto=UDP, DstPort=53                        │
│     Action: DROP                                                            │
│                                                                             │
│  8. Traffic from Spirent Port 1 → PE1 → MPLS → PE2 → Spirent Port 2        │
│     If matches rule: DROPPED at PE2 ingress                                │
│     If doesn't match: FORWARDED normally                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
