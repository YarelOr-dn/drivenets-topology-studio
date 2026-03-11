# SW-234160: FlowSpec VPN | Topology Creation

## Hardware Used (from HW Project)

| Role | Device | Serial | Type | HW Ticket |
|------|--------|--------|------|-----------|
| **DUT (PE1)** | SA-36CD-S | WK31D7VV00023 | Standalone NCP3 | HW-136 |
| **PE2** | SA-36CD-S | WKY1BC7400002B2 | Standalone NCP3 | HW-192 |
| **RR/P (Cluster)** | CL-408D | kvm108-cl408d | Cluster 2xNCP-40C | HW-66/67/68 |
| **Traffic Gen** | Spirent | Port 6:13 (100G) | Spirent01 | HW-114 |
| **cDNOS (optional)** | h263 | BMPBZT3 | X86 Server | HW-146 |

---

## Physical Topology Diagram

```
                    ┌──────────────────────────────────────────┐
                    │           CL-408D (RR/P Router)          │
                    │  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
                    │  │ NCP-40C │  │ NCP-40C │  │ NCF-48CD│   │
                    │  │  (NCP0) │  │  (NCP1) │  │ (Fabric)│   │
                    │  └────┬────┘  └────┬────┘  └─────────┘   │
                    │       │            │                      │
                    │  ┌────┴────────────┴────┐                │
                    │  │   NCM-48X-6C (NCM)   │                │
                    │  └──────────┬───────────┘                │
                    │             │ ge400-0/0/0 (to PE1)       │
                    │             │ ge400-0/0/1 (to PE2)       │
                    └─────────────┼───────────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
   ┌────────┴────────┐   ┌───────┴────────┐   ┌───────┴────────┐
   │  WK31D7VV00023  │   │ WKY1BC7400002B2│   │   Spirent01    │
   │   (DUT - PE1)   │   │     (PE2)      │   │  Port 6:13     │
   │   SA-36CD-S     │   │   SA-36CD-S    │   │    100G        │
   │                 │   │                │   │                │
   │ ge100-0/0/0 ────┼───┼─── ge100-0/0/0 │   │                │
   │ (to RR)         │   │ (to RR)        │   │                │
   │                 │   │                │   │                │
   │ ge100-0/0/1 ────┼───┤                │   │                │
   │ (PE1-PE2 link)  │   │ ge100-0/0/1    │   │                │
   │                 │   │ (PE1-PE2 link) │   │                │
   │                 │   │                │   │                │
   │ ge100-0/0/2 ────┼───┼────────────────┼───┤ Port 6:13      │
   │ (to Spirent)    │   │                │   │ (to PE1)       │
   └─────────────────┘   └────────────────┘   └────────────────┘
```

---

## Logical Topology (BGP)

```
                    ┌──────────────────────────────────┐
                    │         CL-408D                   │
                    │   Route Reflector (RR)            │
                    │   AS 65000                        │
                    │   Loopback: 10.0.0.100/32         │
                    │                                   │
                    │   BGP Address-Families:           │
                    │   - ipv4-unicast                  │
                    │   - ipv4-vpn                      │
                    │   - ipv4-flowspec-vpn ◀── NEW     │
                    │   - ipv6-flowspec-vpn ◀── NEW     │
                    │   - rt-constrain (optional)       │
                    └───────────────┬───────────────────┘
                                    │ iBGP
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────┴──────────┐       ┌───────────┴──────────┐
         │  PE1 (DUT)          │       │  PE2                 │
         │  WK31D7VV00023      │       │  WKY1BC7400002B2     │
         │  AS 65000           │       │  AS 65000            │
         │  Lo0: 10.0.0.1/32   │       │  Lo0: 10.0.0.2/32    │
         │                     │       │                      │
         │  VRF: INTERNET-VRF  │       │  VRF: INTERNET-VRF   │
         │  RD: 10.0.0.1:100   │       │  RD: 10.0.0.2:100    │
         │  RT: 65000:100      │       │  RT: 65000:100       │
         │                     │       │                      │
         │  address-family:    │       │  address-family:     │
         │  - ipv4-flowspec    │       │  - ipv4-flowspec     │
         │    import-vpn       │       │    import-vpn        │
         │    RT 65000:100     │       │    RT 65000:100      │
         └─────────┬───────────┘       └──────────────────────┘
                   │
         ┌─────────┴───────────┐
         │   Spirent01         │
         │   Port 6:13 (100G)  │
         │                     │
         │   Traffic:          │
         │   - IPv4 10.x.x.x   │
         │   - IPv6 2001:db8:: │
         │   - Match FlowSpec  │
         └─────────────────────┘
```

---

## IGP Configuration (ISIS)

```
protocols
  isis 1
    net 49.0001.0100.0000.0001.00   # PE1
    interface lo0
    !
    interface ge100-0/0/0           # to RR
    !
    interface ge100-0/0/1           # to PE2
    !
  !
!
```

---

## BGP Configuration (FlowSpec VPN)

### PE1 (DUT) - WK31D7VV00023

```
protocols
  bgp 65000
    router-id 10.0.0.1
    !
    neighbor 10.0.0.100              # RR
      remote-as 65000
      update-source lo0
      address-family ipv4-unicast
      !
      address-family ipv4-vpn
      !
      address-family ipv4-flowspec-vpn    # ◀── NEW SAFI 134
        admin-state enabled
        send-community extended
      !
      address-family ipv6-flowspec-vpn    # ◀── NEW SAFI 134
        admin-state enabled
        send-community extended
      !
    !
  !
!

network-services
  vrf instance INTERNET-VRF
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    !
    protocols
      bgp 65000
        address-family ipv4-flowspec       # ◀── Import FlowSpec
          import-vpn route-target 65000:100
        !
        address-family ipv6-flowspec
          import-vpn route-target 65000:100
        !
      !
    !
  !
!

interfaces
  ge100-0/0/2
    admin-state enabled
    flowspec enabled                        # ◀── Enable FlowSpec on interface
  !
!
```

### RR (CL-408D)

```
protocols
  bgp 65000
    router-id 10.0.0.100
    !
    cluster-id 10.0.0.100
    !
    neighbor 10.0.0.1                        # PE1
      remote-as 65000
      update-source lo0
      route-reflector-client
      address-family ipv4-flowspec-vpn       # ◀── FlowSpec VPN
      !
      address-family ipv6-flowspec-vpn
      !
    !
    neighbor 10.0.0.2                        # PE2
      remote-as 65000
      update-source lo0
      route-reflector-client
      address-family ipv4-flowspec-vpn
      !
      address-family ipv6-flowspec-vpn
      !
    !
  !
!
```

---

## IP Addressing Plan

| Device | Interface | IP Address | Purpose |
|--------|-----------|------------|---------|
| PE1 | lo0 | 10.0.0.1/32 | BGP Router-ID |
| PE1 | ge100-0/0/0 | 10.1.1.1/30 | to RR |
| PE1 | ge100-0/0/1 | 10.1.2.1/30 | to PE2 |
| PE1 | ge100-0/0/2 | VRF INTERNET | to Spirent |
| PE2 | lo0 | 10.0.0.2/32 | BGP Router-ID |
| PE2 | ge100-0/0/0 | 10.1.1.5/30 | to RR |
| PE2 | ge100-0/0/1 | 10.1.2.2/30 | to PE1 |
| RR | lo0 | 10.0.0.100/32 | BGP Router-ID |
| RR | ge400-0/0/0 | 10.1.1.2/30 | to PE1 |
| RR | ge400-0/0/1 | 10.1.1.6/30 | to PE2 |

---

## VRF Configuration

| VRF | RD | RT Import | RT Export | Purpose |
|-----|----|-----------|-----------|---------| 
| INTERNET-VRF | 10.0.0.X:100 | 65000:100 | 65000:100 | FlowSpec rules installed here |

---

## Spirent Traffic Profile

| Stream | Source | Destination | Protocol | Match FlowSpec |
|--------|--------|-------------|----------|----------------|
| Stream1 | 192.168.1.100 | 10.10.10.1 | TCP/80 | Drop rule |
| Stream2 | 192.168.1.100 | 10.10.10.2 | UDP/53 | Rate-limit |
| Stream3 | 2001:db8::100 | 2001:db8:100::1 | ICMPv6 | Drop rule |

---

## Tasks to Complete

- [ ] Cable physical connections per diagram
- [ ] Configure management IPs
- [ ] Configure ISIS underlay
- [ ] Configure BGP with FlowSpec-VPN SAFI
- [ ] Configure VRF with import-vpn
- [ ] Verify BGP sessions established
- [ ] Verify FlowSpec-VPN capability advertised
- [ ] Configure Spirent streams
- [ ] Document final topology in Confluence

---

## Test Environment Validation

Before testing FlowSpec VPN:

1. `show protocols isis neighbors` - All ISIS adjacencies UP
2. `show bgp summary` - All BGP sessions Established
3. `show bgp ipv4 flowspec-vpn summary` - SAFI 134 sessions UP
4. `show network-services vrf INTERNET-VRF` - VRF exists
5. `show interfaces ge100-0/0/2` - Admin UP, has IP in VRF

---
