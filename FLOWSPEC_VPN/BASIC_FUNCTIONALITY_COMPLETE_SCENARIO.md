# FlowSpec VPN - Basic Functionality Complete Scenario

## Sources Used for DNOS Syntax Validation
- ✅ **Jira EPIC SW-182545** - FlowSpec VPN syntax reference
- ✅ **DNOS CLI PDF** (pages 574-575, 604) - `mpls enabled`, `flowspec enabled`
- ✅ **Network Mapper CLI Docs** - Interface and BGP commands
- ✅ **Cursor Rules** - 2-space indent, flat interface model

---

## Basic Functionality Topology

```
                    ┌─────────────────┐
                    │  Spirent        │
                    │  Port 6:13      │
                    │  HW-114 (100G)  │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ ARBOR_SIM   │ │
                    │ │ VLAN 10     │ │
                    │ │ AS 65001    │ │
                    │ │ eBGP FS-VPN │ │
                    │ └──────┬──────┘ │
                    │        │        │
                    │ ┌──────┴──────┐ │
                    │ │ ATTACKER    │ │
                    │ │ VLAN 100    │ │
                    │ │ Sends:      │ │
                    │ │ →10.10.10.1 │ │
                    │ └─────────────┘ │
                    └────────┬────────┘
                             │
                             │ Single 100G Port (2 VLANs)
                             │
┌────────────────────────────┴───────────────────────────────────┐
│                         PE1 (DUT)                              │
│                    WK31D7VV00023 | HW-136                      │
│                         AS 65000                               │
│                                                                │
│   lo0: 10.0.0.1/32                                            │
│                                                                │
│   ge100-0/0/0.10  ◄── Arbor (eBGP FlowSpec-VPN)               │
│       IP: 10.1.1.1/30                                          │
│                                                                │
│   ge100-0/0/0.100 ◄── Attack traffic enters here              │
│       IP: 192.168.1.1/24                                       │
│       VRF: INTERNET-VRF                                        │
│       flowspec enabled  ◄── Rules applied here                │
│                                                                │
│   ge100-0/0/1 ─────────────────────────────────────────────┐  │
│       IP: 10.1.2.1/30                                      │  │
│       mpls enabled                                         │  │
│       (iBGP to PE2)                                        │  │
└────────────────────────────────────────────────────────────┼──┘
                                                             │
                                                             │
┌────────────────────────────────────────────────────────────┼──┐
│                         PE2                                │  │
│                   WKY1BC7400002B2 | HW-192                 │  │
│                         AS 65000                           │  │
│                                                            │  │
│   lo0: 10.0.0.2/32                                        │  │
│                                                            │  │
│   ge100-0/0/1 ◄────────────────────────────────────────────┘  │
│       IP: 10.1.2.2/30                                         │
│       mpls enabled                                            │
│       (iBGP to PE1)                                           │
│                                                                │
│   VRF: INTERNET-VRF                                           │
│   (Imports same FlowSpec rules via iBGP)                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## What We're Testing

| # | Test Case | Verification |
|---|-----------|--------------|
| 1 | eBGP FlowSpec-VPN session UP | `show bgp ipv4 flowspec-vpn summary` |
| 2 | FlowSpec rule received | `show bgp ipv4 flowspec-vpn routes` |
| 3 | Rule imported to VRF via RT | `show bgp instance vrf INTERNET-VRF ipv4 flowspec routes` |
| 4 | Rule installed in datapath | `show flowspec ncp` |
| 5 | Traffic DROPPED (counter) | `show flowspec-local-policies counters` |
| 6 | Rule propagated to PE2 via iBGP | PE2: `show bgp ipv4 flowspec-vpn routes` |

**"Server" = Just a destination IP (10.10.10.1) - verified by counters, no physical device**

---

## Connection 1: PE1 ↔ Spirent (Single Port, Dual VLAN)

### Purpose
- **VLAN 10**: Arbor simulation - sends FlowSpec-VPN rules via eBGP
- **VLAN 100**: Attacker simulation - sends traffic to be dropped

### Physical
| Device | Interface | Speed |
|--------|-----------|-------|
| PE1 | ge100-0/0/0 | 100G |
| Spirent | Port 6:13 | 100G |

### PE1 Interface Configuration
```
interfaces
  ge100-0/0/0
    admin-state enabled
  !
  ge100-0/0/0.10
    admin-state enabled
    vlan-id 10
    ipv4-address 10.1.1.1/30
  !
  ge100-0/0/0.100
    admin-state enabled
    vlan-id 100
    ipv4-address 192.168.1.1/24
    flowspec enabled
  !
!
```

---

## Connection 2: PE1 ↔ PE2 (iBGP FlowSpec-VPN Distribution)

### Purpose
- iBGP session for FlowSpec-VPN route distribution
- MPLS enabled for VPN traffic forwarding
- Verifies FlowSpec rules propagate to second PE

### Physical
| Device | Interface | Speed |
|--------|-----------|-------|
| PE1 | ge100-0/0/1 | 100G |
| PE2 | ge100-0/0/1 | 100G |

### PE1 Interface Configuration
```
interfaces
  ge100-0/0/1
    admin-state enabled
    ipv4-address 10.1.2.1/30
    mpls enabled
  !
!
```

### PE2 Interface Configuration
```
interfaces
  ge100-0/0/1
    admin-state enabled
    ipv4-address 10.1.2.2/30
    mpls enabled
  !
!
```

---

## Loopback Interfaces

### PE1
```
interfaces
  lo0
    admin-state enabled
    ipv4-address 10.0.0.1/32
  !
!
```

### PE2
```
interfaces
  lo0
    admin-state enabled
    ipv4-address 10.0.0.2/32
  !
!
```

---

## IGP Configuration (ISIS) - For Loopback Reachability

### PE1
```
protocols
  isis 1
    net 49.0001.0100.0000.0001.00
    is-type level-2-only
    interface lo0
      passive
    !
    interface ge100-0/0/1
      circuit-type level-2
    !
  !
!
```

### PE2
```
protocols
  isis 1
    net 49.0001.0100.0000.0002.00
    is-type level-2-only
    interface lo0
      passive
    !
    interface ge100-0/0/1
      circuit-type level-2
    !
  !
!
```

---

## BGP Configuration

### PE1 (DUT)
```
protocols
  bgp 65000
    router-id 10.0.0.1
    !
    neighbor 10.1.1.2
      description SPIRENT-ARBOR
      remote-as 65001
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
    neighbor 10.0.0.2
      description PE2
      remote-as 65000
      update-source lo0
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!
```

### PE2
```
protocols
  bgp 65000
    router-id 10.0.0.2
    !
    neighbor 10.0.0.1
      description PE1
      remote-as 65000
      update-source lo0
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!
```

---

## VRF Configuration

### PE1
```
network-services
  vrf instance INTERNET-VRF
    interface ge100-0/0/0.100
    !
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    !
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

### PE2
```
network-services
  vrf instance INTERNET-VRF
    route-distinguisher 10.0.0.2:100
    route-target import 65000:100
    route-target export 65000:100
    !
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

---

## Spirent Configuration (Port 6:13)

### Emulated Device 1: ARBOR_SIM

| Parameter | Value |
|-----------|-------|
| **Name** | ARBOR_SIM |
| **VLAN** | 10 |
| **MAC** | 00:10:94:01:00:01 |
| **IPv4** | 10.1.1.2/30 |
| **Gateway** | 10.1.1.1 |
| **BGP AS** | 65001 (eBGP) |
| **BGP Neighbor** | 10.1.1.1 |
| **BGP AFI/SAFI** | IPv4-FlowSpec-VPN (SAFI 134) |

#### FlowSpec Routes Advertised

| Name | Match | Action | RT |
|------|-------|--------|-----|
| DROP-HTTP | dst 10.10.10.1/32, tcp/80 | traffic-rate 0 (DROP) | 65000:100 |
| DROP-ICMP | dst 10.10.10.1/32, icmp | traffic-rate 0 (DROP) | 65000:100 |
| RATE-DNS | dst 10.10.10.2/32, udp/53 | traffic-rate 1000000 (1Mbps) | 65000:100 |

### Emulated Device 2: ATTACKER

| Parameter | Value |
|-----------|-------|
| **Name** | ATTACKER |
| **VLAN** | 100 |
| **MAC** | 00:10:94:02:00:02 |
| **IPv4** | 192.168.1.100/24 |
| **Gateway** | 192.168.1.1 |

#### Traffic Streams

| Stream | Src IP | Dst IP | Protocol | Port | Expected |
|--------|--------|--------|----------|------|----------|
| HTTP-ATTACK | 192.168.1.100 | 10.10.10.1 | TCP | 80 | **DROPPED** |
| ICMP-ATTACK | 192.168.1.100 | 10.10.10.1 | ICMP | - | **DROPPED** |
| DNS-ATTACK | 192.168.1.100 | 10.10.10.2 | UDP | 53 | **RATE-LIMITED** |
| CLEAN-HTTPS | 192.168.1.100 | 10.10.10.99 | TCP | 443 | **PASSED** (no rule) |

---

## Complete PE1 (DUT) Configuration

```
interfaces
  lo0
    admin-state enabled
    ipv4-address 10.0.0.1/32
  !
  ge100-0/0/0
    admin-state enabled
  !
  ge100-0/0/0.10
    admin-state enabled
    vlan-id 10
    ipv4-address 10.1.1.1/30
  !
  ge100-0/0/0.100
    admin-state enabled
    vlan-id 100
    ipv4-address 192.168.1.1/24
    flowspec enabled
  !
  ge100-0/0/1
    admin-state enabled
    ipv4-address 10.1.2.1/30
    mpls enabled
  !
!

network-services
  vrf instance INTERNET-VRF
    interface ge100-0/0/0.100
    !
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    !
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
  isis 1
    net 49.0001.0100.0000.0001.00
    is-type level-2-only
    interface lo0
      passive
    !
    interface ge100-0/0/1
      circuit-type level-2
    !
  !
!

protocols
  bgp 65000
    router-id 10.0.0.1
    !
    neighbor 10.1.1.2
      description SPIRENT-ARBOR
      remote-as 65001
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
    neighbor 10.0.0.2
      description PE2
      remote-as 65000
      update-source lo0
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!
```

---

## Complete PE2 Configuration

```
interfaces
  lo0
    admin-state enabled
    ipv4-address 10.0.0.2/32
  !
  ge100-0/0/1
    admin-state enabled
    ipv4-address 10.1.2.2/30
    mpls enabled
  !
!

network-services
  vrf instance INTERNET-VRF
    route-distinguisher 10.0.0.2:100
    route-target import 65000:100
    route-target export 65000:100
    !
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
  isis 1
    net 49.0001.0100.0000.0002.00
    is-type level-2-only
    interface lo0
      passive
    !
    interface ge100-0/0/1
      circuit-type level-2
    !
  !
!

protocols
  bgp 65000
    router-id 10.0.0.2
    !
    neighbor 10.0.0.1
      description PE1
      remote-as 65000
      update-source lo0
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!
```

---

## Traffic Flow Diagram

```
STEP 1: Arbor sends FlowSpec rule "DROP dst 10.10.10.1 tcp/80"

    Spirent (ARBOR_SIM) ──► PE1 ──► (iBGP) ──► PE2
    VLAN 10                  │                  │
    eBGP FS-VPN         Rule imported     Rule imported
                        to VRF            to VRF


STEP 2: Attacker sends HTTP traffic to "server" 10.10.10.1

    Spirent (ATTACKER) ──► PE1 (ge100-0/0/0.100)
    VLAN 100                    │
    Src: 192.168.1.100          │ flowspec enabled
    Dst: 10.10.10.1:80          │
                                ▼
                          FlowSpec DROPS traffic ✗
                          Counter increments


STEP 3: Clean traffic (no matching rule) would pass

    Spirent (ATTACKER) ──► PE1 ──► (would forward if destination existed)
    Dst: 10.10.10.99:443        │
    (No FlowSpec match)         ▼
                          Traffic PASSES ✓
```

---

## Verification Commands

### PE1 (DUT)

```bash
# 1. Check interfaces
show interfaces ge100-0/0/0*
show interfaces ge100-0/0/1

# 2. Check ISIS adjacency to PE2
show protocols isis neighbors

# 3. Check BGP sessions
show bgp summary
show bgp ipv4 flowspec-vpn summary

# 4. Check FlowSpec routes received from Spirent
show bgp ipv4 flowspec-vpn routes

# 5. Check FlowSpec imported to VRF
show bgp instance vrf INTERNET-VRF ipv4 flowspec routes

# 6. Check datapath installation
show flowspec ncp

# 7. Check counters (BEFORE traffic)
show flowspec-local-policies counters

# 8. Send traffic from Spirent, then check counters again
show flowspec-local-policies counters
# Match count should increase for dropped traffic
```

### PE2

```bash
# Verify FlowSpec route propagated via iBGP
show bgp ipv4 flowspec-vpn summary
show bgp ipv4 flowspec-vpn routes

# Verify imported to VRF
show bgp instance vrf INTERNET-VRF ipv4 flowspec routes
```

---

## Test Execution Steps

### Step 1: Configure Devices
1. Apply PE1 configuration
2. Apply PE2 configuration
3. Commit both: `commit confirm 300`

### Step 2: Verify Underlay
1. ISIS adjacency UP: `show protocols isis neighbors`
2. Loopbacks reachable: `ping 10.0.0.2 source 10.0.0.1`

### Step 3: Configure Spirent
1. Create ARBOR_SIM on VLAN 10
2. Create ATTACKER on VLAN 100
3. Start ARP resolution

### Step 4: Establish BGP Sessions
1. Start BGP on ARBOR_SIM
2. Verify on PE1: `show bgp ipv4 flowspec-vpn summary`
3. Expected: 10.1.1.2 (Spirent) and 10.0.0.2 (PE2) both **Established**

### Step 5: Inject FlowSpec Rules
1. Advertise FlowSpec NLRI from ARBOR_SIM with RT 65000:100
2. Verify on PE1: `show bgp ipv4 flowspec-vpn routes`
3. Verify imported: `show bgp instance vrf INTERNET-VRF ipv4 flowspec routes`
4. Verify on PE2: Same commands - rules should be present

### Step 6: Verify Datapath
1. `show flowspec ncp` - Rules installed
2. `show flowspec-local-policies counters` - Zero initially

### Step 7: Send Attack Traffic
1. Start HTTP-ATTACK stream (TCP/80 to 10.10.10.1)
2. Start ICMP-ATTACK stream
3. Start CLEAN-HTTPS stream (TCP/443 to 10.10.10.99)

### Step 8: Validate Results
1. `show flowspec-local-policies counters`
   - DROP counters increased for HTTP/ICMP attacks
   - No counter for clean traffic (passed through)
2. Document PASS/FAIL

---

## Summary Table

| Connection | Devices | Interface | VLAN | IP | Config |
|------------|---------|-----------|------|-----|--------|
| 1a | PE1 ↔ Spirent (Arbor) | ge100-0/0/0.10 | 10 | 10.1.1.1/30 | eBGP FS-VPN |
| 1b | PE1 ↔ Spirent (Attacker) | ge100-0/0/0.100 | 100 | 192.168.1.1/24 | `flowspec enabled`, VRF |
| 2 | PE1 ↔ PE2 | ge100-0/0/1 | - | 10.1.2.x/30 | `mpls enabled`, iBGP FS-VPN, ISIS |

**Total:** 2 PEs + 1 Spirent port (2 VLANs)

---

## IP Addressing Summary

| Device | Interface | IP Address | Purpose |
|--------|-----------|------------|---------|
| PE1 | lo0 | 10.0.0.1/32 | Router-ID, iBGP source |
| PE1 | ge100-0/0/0.10 | 10.1.1.1/30 | eBGP to Spirent |
| PE1 | ge100-0/0/0.100 | 192.168.1.1/24 | VRF customer interface |
| PE1 | ge100-0/0/1 | 10.1.2.1/30 | PE-PE link |
| PE2 | lo0 | 10.0.0.2/32 | Router-ID, iBGP source |
| PE2 | ge100-0/0/1 | 10.1.2.2/30 | PE-PE link |
| Spirent | ARBOR_SIM | 10.1.1.2/30 | eBGP FlowSpec source |
| Spirent | ATTACKER | 192.168.1.100/24 | Attack traffic source |

---
