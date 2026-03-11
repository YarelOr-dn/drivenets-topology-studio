# Flowspec VPN - How It Works

## Overview

Flowspec VPN extends BGP Flowspec to work in MPLS VPN environments, allowing traffic filtering rules to be distributed across PE routers for specific customer VRFs.

---

## 1. Topology Example (3 Devices + Spirent)

```
                                    ┌─────────────────────────────────────────────────────────┐
                                    │                    MPLS CORE                             │
                                    │                                                          │
                                    │              ┌─────────────┐                             │
                                    │              │     RR      │                             │
                                    │              │  (AS 65001) │                             │
                                    │              │  3.3.3.3    │                             │
                                    │              └──────┬──────┘                             │
                                    │                     │                                    │
                                    │            iBGP (FlowSpec-VPN)                          │
                                    │                     │                                    │
                                    │     ┌───────────────┴───────────────┐                   │
                                    │     │                               │                   │
                                    │     ▼                               ▼                   │
┌──────────────┐               ┌────┴─────────┐                    ┌─────────────┐            │
│   SPIRENT    │               │     PE1      │                    │     PE2     │            │
│  (Traffic    │───────────────│  (AS 65001)  │════════════════════│  (AS 65001) │            │
│  Generator)  │  ge-0/0/1     │   1.1.1.1    │   MPLS LSP         │   2.2.2.2   │            │
│              │  VRF: CUST-A  │              │                    │             │            │
└──────────────┘               └────┬─────────┘                    └──────┬──────┘            │
                                    │                                     │                   │
                                    └─────────────────────────────────────┘                   │
                                                                                              │
                               ═══════════════════════════════════════════════════════════════┘

PE1 Configuration:
  - VRF: CUST-A (RD: 65001:100)
  - import-vpn route-target: 65001:100
  - export-vpn route-target: 65001:100
  - Interface ge-0/0/1 in VRF CUST-A

PE2 Configuration:
  - VRF: CUST-A (RD: 65001:200)  <- Different RD, same VPN
  - import-vpn route-target: 65001:100
  - export-vpn route-target: 65001:100

RR Configuration:
  - Route Reflector for PE1 and PE2
  - address-family ipv4 flowspec-vpn activated
  - address-family ipv6 flowspec-vpn activated
```

---

## 2. BGP Address Families Involved

| SAFI | Name | Purpose | Where Used |
|------|------|---------|------------|
| **133** | Flowspec | Standard Flowspec in Global/VRF | PE-CE sessions, VRF context |
| **134** | Flowspec-VPN | VPN-aware Flowspec | PE-PE/PE-RR sessions |

---

## 3. How Flowspec VPN Works - Step by Step

### Scenario: Block DDoS Attack Traffic

**Goal**: Spirent simulates a DDoS attack. We need to drop traffic matching `DstIP=10.1.1.0/24, Protocol=UDP, DstPort=53` in customer VRF `CUST-A` across all PEs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 1: Flowspec Rule is Created (at PE1 or via Controller)                          │
│   ═══════════════════════════════════════════════════════════════                      │
│                                                                                         │
│   Configuration on PE1 (VRF CUST-A):                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │ router bgp 65001 vrf CUST-A                                         │              │
│   │   address-family ipv4 flowspec                                      │              │
│   │     export-vpn route-target 65001:100                               │              │
│   │     import-vpn route-target 65001:100                               │              │
│   │                                                                     │              │
│   │ routing-policy                                                      │              │
│   │   flowspec-local-policies                                           │              │
│   │     ipv4                                                            │              │
│   │       mc-defns BLOCK-DDOS                                           │              │
│   │         dest-ip 10.1.1.0/24                                         │              │
│   │         protocol 17                                                 │              │
│   │         dest-port eq 53                                             │              │
│   │       policy DROP-DDOS                                              │              │
│   │         match-class BLOCK-DDOS action discard                       │              │
│   │       apply-policy-to-flowspec DROP-DDOS                            │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
│   OR received via BGP from CE/Controller:                                              │
│   NLRI: "DstPrefix:=10.1.1.0/24,Protocol:=17,DstPort:=53"                             │
│   Extended Community: flowspec-traffic-rate:0 (drop)                                   │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 2: VRF Flowspec → Flowspec-VPN Conversion (Export)                              │
│   ═══════════════════════════════════════════════════════════                          │
│                                                                                         │
│   PE1 BGP Process:                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │                                                                     │              │
│   │   VRF CUST-A Flowspec Table:                                        │              │
│   │   ┌───────────────────────────────────────────────────────────┐     │              │
│   │   │ NLRI: DstPrefix:=10.1.1.0/24,Protocol:=17,DstPort:=53    │     │              │
│   │   │ Action: traffic-rate:0 (drop)                             │     │              │
│   │   │ VRF-ID: 1 (CUST-A)                                        │     │              │
│   │   └───────────────────────────────────────────────────────────┘     │              │
│   │                            │                                        │              │
│   │                            │ export-vpn route-target 65001:100      │              │
│   │                            ▼                                        │              │
│   │   Global Flowspec-VPN Table (SAFI 134):                            │              │
│   │   ┌───────────────────────────────────────────────────────────┐     │              │
│   │   │ RD: 65001:100 (from VRF config)                           │     │              │
│   │   │ NLRI: DstPrefix:=10.1.1.0/24,Protocol:=17,DstPort:=53    │     │              │
│   │   │ RT: 65001:100 (from export-vpn route-target)              │     │              │
│   │   │ Action: traffic-rate:0                                    │     │              │
│   │   └───────────────────────────────────────────────────────────┘     │              │
│   │                                                                     │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 3: BGP UPDATE to RR (Flowspec-VPN SAFI)                                         │
│   ════════════════════════════════════════════                                         │
│                                                                                         │
│   BGP UPDATE Message from PE1 → RR:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │                                                                     │              │
│   │   NLRI (Type 2 - Flowspec-VPN):                                     │              │
│   │   ├── Route Distinguisher: 65001:100                                │              │
│   │   └── Flowspec NLRI: DstPrefix:=10.1.1.0/24,Protocol:=17,DstPort=53│              │
│   │                                                                     │              │
│   │   Path Attributes:                                                  │              │
│   │   ├── ORIGIN: IGP                                                   │              │
│   │   ├── AS_PATH: (empty - iBGP)                                       │              │
│   │   ├── LOCAL_PREF: 100                                               │              │
│   │   ├── NEXT_HOP: 1.1.1.1 (PE1 loopback)                             │              │
│   │   └── EXTENDED_COMMUNITIES:                                         │              │
│   │       ├── Route-Target: 65001:100                                   │              │
│   │       └── Flowspec-Traffic-Rate: 0 (drop)                           │              │
│   │                                                                     │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
│   PE1 ─────────────BGP UPDATE─────────────▶ RR (3.3.3.3)                              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 4: RR Reflects to PE2                                                           │
│   ══════════════════════════                                                           │
│                                                                                         │
│   RR keeps the route and reflects it to PE2:                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │                                                                     │              │
│   │   RR adds:                                                          │              │
│   │   ├── CLUSTER_LIST: 3.3.3.3                                         │              │
│   │   └── ORIGINATOR_ID: 1.1.1.1                                        │              │
│   │                                                                     │              │
│   │   NEXT_HOP remains: 1.1.1.1 (unchanged by RR)                       │              │
│   │                                                                     │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
│   RR ─────────────BGP UPDATE─────────────▶ PE2 (2.2.2.2)                              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 5: PE2 Receives and Imports into VRF (RT Matching)                              │
│   ═══════════════════════════════════════════════════════                              │
│                                                                                         │
│   PE2 BGP Process:                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │                                                                     │              │
│   │   1. Receive Flowspec-VPN route                                     │              │
│   │                                                                     │              │
│   │   2. Check RT: 65001:100                                            │              │
│   │      Does any VRF have "import-vpn route-target 65001:100"?         │              │
│   │                                                                     │              │
│   │   3. Match found: VRF CUST-A has import-vpn RT 65001:100           │              │
│   │                                                                     │              │
│   │   4. Import into VRF CUST-A Flowspec table:                        │              │
│   │   ┌───────────────────────────────────────────────────────────┐     │              │
│   │   │ VRF: CUST-A                                               │     │              │
│   │   │ NLRI: DstPrefix:=10.1.1.0/24,Protocol:=17,DstPort:=53    │     │              │
│   │   │ Action: traffic-rate:0 (drop)                             │     │              │
│   │   │ VRF-ID: 2 (PE2's CUST-A VRF ID)                          │     │              │
│   │   └───────────────────────────────────────────────────────────┘     │              │
│   │                                                                     │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 6: Programming to Datapath (wb_agent)                                           │
│   ══════════════════════════════════════════                                           │
│                                                                                         │
│   On PE2:                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │                                                                     │              │
│   │   Zebra receives route from BGP:                                    │              │
│   │   ┌───────────────────────────────────────────┐                     │              │
│   │   │ FLOWSPEC_RULE_ADD                         │                     │              │
│   │   │   vrf_id: 2                               │                     │              │
│   │   │   nlri: (binary encoding)                 │                     │              │
│   │   │   action: DISCARD                         │                     │              │
│   │   └───────────────────────────────────────────┘                     │              │
│   │                            │                                        │              │
│   │                            ▼ FPM (Forwarding Plane Manager)         │              │
│   │                                                                     │              │
│   │   wb_agent (Whitebox Agent) receives via FPM:                       │              │
│   │   ┌───────────────────────────────────────────┐                     │              │
│   │   │ FlowspecManager::AddBGPRule()             │                     │              │
│   │   │   vrf_id: 2                               │                     │              │
│   │   │   is_ipv4: true                           │                     │              │
│   │   │   nlri: DstIP=10.1.1.0/24, Proto=17...   │                     │              │
│   │   │   action: DROP                            │                     │              │
│   │   └───────────────────────────────────────────┘                     │              │
│   │                            │                                        │              │
│   │                            ▼                                        │              │
│   │   FlowspecTcamManager::WriteRule():                                │              │
│   │   ┌───────────────────────────────────────────┐                     │              │
│   │   │ PMF (Packet Match Filter) Entry:          │                     │              │
│   │   │   VRF-ID qualifier: 2                     │  ← KEY POINT!       │              │
│   │   │   DstIP qualifier: 10.1.1.0/24           │                     │              │
│   │   │   Protocol qualifier: 17 (UDP)           │                     │              │
│   │   │   DstPort qualifier: 53                  │                     │              │
│   │   │   Action: DROP                           │                     │              │
│   │   └───────────────────────────────────────────┘                     │              │
│   │                            │                                        │              │
│   │                            ▼                                        │              │
│   │   BCM SDK - Write to External TCAM (KBP):                          │              │
│   │   ┌───────────────────────────────────────────┐                     │              │
│   │   │ TCAM Entry Written!                       │                     │              │
│   │   │ Rule installed in hardware                │                     │              │
│   │   └───────────────────────────────────────────┘                     │              │
│   │                                                                     │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   STEP 7: Traffic Filtering (Spirent Test)                                             │
│   ════════════════════════════════════════                                             │
│                                                                                         │
│   Spirent sends traffic:                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐              │
│   │                                                                     │              │
│   │   Stream 1 (Should be DROPPED):                                     │              │
│   │   ├── Src IP: 192.168.1.100                                         │              │
│   │   ├── Dst IP: 10.1.1.50       ← Matches 10.1.1.0/24                │              │
│   │   ├── Protocol: UDP (17)      ← Matches Protocol=17                 │              │
│   │   └── Dst Port: 53            ← Matches DstPort=53                  │              │
│   │                                                                     │              │
│   │   Result: DROPPED by Flowspec rule (rate=0)                        │              │
│   │                                                                     │              │
│   │   Stream 2 (Should PASS):                                           │              │
│   │   ├── Src IP: 192.168.1.100                                         │              │
│   │   ├── Dst IP: 10.1.1.50       ← Matches 10.1.1.0/24                │              │
│   │   ├── Protocol: TCP (6)       ← Does NOT match Protocol=17         │              │
│   │   └── Dst Port: 80                                                  │              │
│   │                                                                     │              │
│   │   Result: PASSED (no Flowspec match)                               │              │
│   │                                                                     │              │
│   └─────────────────────────────────────────────────────────────────────┘              │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           CONTROL PLANE (Routing)                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐                       │
│  │   BGP Peer     │     │    bgpd        │     │    zebra       │                       │
│  │  (CE/RR/PE)    │     │                │     │                │                       │
│  └───────┬────────┘     └───────┬────────┘     └───────┬────────┘                       │
│          │                      │                      │                                 │
│          │ BGP UPDATE           │                      │                                 │
│          │ (Flowspec-VPN)       │                      │                                 │
│          ▼                      │                      │                                 │
│  ┌───────────────────┐          │                      │                                 │
│  │ bgp_flowspec.c    │          │                      │                                 │
│  │ ───────────────── │          │                      │                                 │
│  │ - Parse NLRI      │          │                      │                                 │
│  │ - Validate action │          │                      │                                 │
│  │ - RT matching     │◄─────────┘                      │                                 │
│  │ - VRF import      │                                 │                                 │
│  └───────┬───────────┘                                 │                                 │
│          │                                              │                                 │
│          │ if RT matches VRF import-vpn:               │                                 │
│          │   Import to VRF Flowspec table              │                                 │
│          │                                              │                                 │
│          ▼                                              │                                 │
│  ┌───────────────────┐                                 │                                 │
│  │ bgp_zebra.c       │                                 │                                 │
│  │ ───────────────── │                                 │                                 │
│  │ bgp_zebra_       │                                 │                                 │
│  │ announce_flowspec │─────────────────────────────────▶                                │
│  └───────────────────┘                                 │                                 │
│                                                        │                                 │
│                                              ┌─────────▼─────────┐                       │
│                                              │ zebra_flowspec.c  │                       │
│                                              │ ────────────────── │                       │
│                                              │ - Store in        │                       │
│                                              │   flowspec_db     │                       │
│                                              │ - vrf_id attached │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        │ ZAPI_FLOWSPEC_RULE              │
│                                                        │ (to FPM)                        │
│                                                        ▼                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                           FPM (Forwarding Plane Manager)                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                        │                                 │
│                                              ┌─────────▼─────────┐                       │
│                                              │ fib_manager       │                       │
│                                              │ ────────────────── │                       │
│                                              │ - Receives route  │                       │
│                                              │ - Queues for NCP  │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        │ FPM_FLOWSPEC message            │
│                                                        │ (contains vrf_id!)              │
│                                                        ▼                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                           DATA PLANE (wb_agent)                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                        │                                 │
│                                              ┌─────────▼─────────┐                       │
│                                              │ wbox_flowspec.c   │                       │
│                                              │ ────────────────── │                       │
│                                              │ - Receive from FPM│                       │
│                                              │ - Parse NLRI      │                       │
│                                              │ - Extract vrf_id  │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        ▼                                 │
│                                              ┌───────────────────┐                       │
│                                              │ FlowspecManager   │                       │
│                                              │ (FlowspecManager. │                       │
│                                              │  hpp/cpp)         │                       │
│                                              │ ────────────────── │                       │
│                                              │ AddBGPRule():     │                       │
│                                              │ - vrf_id          │   ◄── VRF-aware!     │
│                                              │ - bgp_as          │                       │
│                                              │ - afi (v4/v6)     │                       │
│                                              │ - nlri            │                       │
│                                              │ - actions         │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        ▼                                 │
│                                              ┌───────────────────┐                       │
│                                              │ FlowspecTable     │                       │
│                                              │ (IPv4/IPv6)       │                       │
│                                              │ ────────────────── │                       │
│                                              │ - Store rule      │                       │
│                                              │ - Priority calc   │                       │
│                                              │ - Dedup check     │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        ▼                                 │
│                                              ┌───────────────────┐                       │
│                                              │FlowspecTcamManager│                       │
│                                              │ ────────────────── │                       │
│                                              │ WriteRule():      │                       │
│                                              │ - Build qualifiers│                       │
│                                              │ - VRF-ID as key!  │   ◄── CRITICAL       │
│                                              │ - Build action    │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        ▼                                 │
│                                              ┌───────────────────┐                       │
│                                              │ PMF Manager       │                       │
│                                              │ (bcm_wrap_acl.c)  │                       │
│                                              │ ────────────────── │                       │
│                                              │ bcm_wrap_         │                       │
│                                              │ flowspec_add_     │                       │
│                                              │ entry()           │                       │
│                                              └─────────┬─────────┘                       │
│                                                        │                                 │
│                                                        ▼                                 │
│                                              ┌───────────────────┐                       │
│                                              │ BCM SDK (KBP)     │                       │
│                                              │ ────────────────── │                       │
│                                              │ External TCAM     │                       │
│                                              │ Entry Written!    │                       │
│                                              └───────────────────┘                       │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Key Components Explained

### 5.1 Route Distinguisher (RD)
- **Purpose**: Makes VPN routes unique in the global BGP table
- **Format**: `ASN:NN` or `IP:NN` (e.g., `65001:100`)
- **Key Point**: Each PE has a **different RD** for the same VPN
  - PE1 VRF CUST-A: RD `65001:100`
  - PE2 VRF CUST-A: RD `65001:200`

### 5.2 Route Target (RT)
- **Purpose**: Controls which VRFs import which routes
- **export-vpn route-target**: "Tag this route with RT X"
- **import-vpn route-target**: "Import routes tagged with RT X"
- **Key Point**: Same RT on both PEs for same VPN
  - PE1: export-vpn RT `65001:100`, import-vpn RT `65001:100`
  - PE2: export-vpn RT `65001:100`, import-vpn RT `65001:100`

### 5.3 VRF-ID in Datapath

> **From DP Team (Ehud) - Confirmed in code (`bcm_wrap.c`)**

| VRF-ID Value | Meaning | Behavior |
|--------------|---------|----------|
| **VRF-ID = 0** | Default VRF | ✅ Valid - Rule applies to default routing table |
| **No VRF field** | ALL VRFs | Rule applies globally to all VRFs |
| **VRF-ID > 0** | Specific VRF | Rule applies only to that VRF |

**Code Evidence:**
```c
// From src/wbox/src/sdk_wrap/bcm_wrap/jericho2/bcm_wrap.c
if (vrf_id == 0)
{
    ingress_l3_interface.flags |= BCM_L3_INGRESS_GLOBAL_ROUTE;
}
```

- **VRF-ID is used as a qualifier in TCAM** to ensure VPN isolation
- **For FlowSpec-VPN**: VRF-ID is set based on which VRF imported the route via RT

---

## 6. Spirent Test Scenario

### Setup
```
┌─────────────────────────────────────────────────────────────────────┐
│                          SPIRENT                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Port 1 (TX) ──────────────────────────────────▶ PE1 ge-0/0/1       │
│  (VRF CUST-A)                                    (VRF CUST-A)        │
│                                                                      │
│  Port 2 (RX) ◀────────────────────────────────── PE2 ge-0/0/2       │
│  (VRF CUST-A)                                    (VRF CUST-A)        │
│                                                                      │
│  Stream Configuration:                                               │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Stream 1: Attack Traffic (Should be DROPPED)                    │ │
│  │   Src IP: 192.168.1.100                                         │ │
│  │   Dst IP: 10.1.1.50                                             │ │
│  │   Protocol: UDP                                                  │ │
│  │   Dst Port: 53                                                   │ │
│  │   Rate: 10,000 pps                                               │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Stream 2: Normal Traffic (Should PASS)                          │ │
│  │   Src IP: 192.168.1.100                                         │ │
│  │   Dst IP: 10.1.1.50                                             │ │
│  │   Protocol: TCP                                                  │ │
│  │   Dst Port: 80                                                   │ │
│  │   Rate: 10,000 pps                                               │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Test Steps

1. **Configure Flowspec Rule on PE1 (VRF CUST-A)**
   ```
   NLRI: DstPrefix:=10.1.1.0/24,Protocol:=17,DstPort:=53
   Action: traffic-rate:0 (drop)
   ```

2. **Verify Rule Propagation**
   ```bash
   # On PE1 - Check VRF Flowspec table
   show bgp vrf CUST-A ipv4 flowspec
   
   # On PE1 - Check Flowspec-VPN export
   show bgp ipv4 flowspec-vpn
   
   # On RR - Check route reflection
   show bgp ipv4 flowspec-vpn
   
   # On PE2 - Check VRF import
   show bgp vrf CUST-A ipv4 flowspec
   
   # On PE2 - Check datapath installation
   show flowspec ncp 0
   xraycli /wb_agent/flowspec/bgp/ipv4/rules
   ```

3. **Start Spirent Traffic**
   - Stream 1 (Attack): Should see 0 packets received at Port 2
   - Stream 2 (Normal): Should see ~10,000 pps at Port 2

4. **Verify Counters**
   ```bash
   # Check Flowspec match counters
   show flowspec
   # Should show "Match packet counter: 10000" for the drop rule
   
   # Check xray counters
   xraycli /wb_agent/flowspec/hw_counters
   # hw_rules_write_ok should be > 0
   # hw_rules_write_fail should be 0
   ```

---

## 7. What Makes Flowspec-VPN Different from Regular Flowspec

| Aspect | Regular Flowspec (SAFI 133) | Flowspec-VPN (SAFI 134) |
|--------|----------------------------|-------------------------|
| **Scope** | Single VRF or global | Cross-VRF via MPLS VPN |
| **RD** | Not used | Required (identifies VRF) |
| **RT** | Not used | Required (controls import/export) |
| **VRF-ID in TCAM** | May be 0 (default) or no VRF (all) | 0=default, >0=specific, no field=all |
| **Priority** | Local: 0-2M (WINS!) | BGP: 2M-4M (lower # = higher precedence) |
| **TCAM Capacity** | Shared 12K IPv4, 4K IPv6 | BGP + Local Policies combined |
| **Use Case** | ISP edge filtering | Multi-tenant VPN filtering |
| **Distribution** | PE-CE only | PE-PE via RR |

---

## 8. Verification Commands Summary

```bash
# === ROUTING PLANE ===

# 1. Check BGP Flowspec-VPN table (PE-PE)
show bgp ipv4 flowspec-vpn
show bgp ipv4 flowspec-vpn rd 65001:100

# 2. Check VRF Flowspec table
show bgp vrf CUST-A ipv4 flowspec

# 3. Check Zebra Flowspec DB
show flowspec db vrf CUST-A

# 4. Check FIB Manager
show fib-manager database flowspec service-instance CUST-A

# === DATAPATH ===

# 5. Check NCP installation
show flowspec ncp 0

# 6. Check xray rules (verify VRF-ID is present!)
xraycli /wb_agent/flowspec/bgp/ipv4/rules
# VRF-ID semantics: 0 = default VRF (valid!), >0 = specific VRF

# 7. Check HW counters
xraycli /wb_agent/flowspec/hw_counters

# 8. Check match counters
show flowspec
```

---

## 9. Common Issues to Watch For

| Issue | Symptom | How to Debug |
|-------|---------|--------------|
| RT mismatch | Route not imported to VRF | Check `import-vpn route-target` matches `export-vpn` |
| No VRF field | Rule may apply to all VRFs | Check if rule was imported via RT into VRF |
| TCAM error | Rule "Not installed" | Check `xraycli /wb_agent/flowspec/bgp/ipv4/info` for `num_tcam_errors` |
| No RD in update | Route not in Flowspec-VPN table | Check `bgp rd` is configured in VRF |
| Session down | No routes received | Check `show bgp flowspec-vpn neighbors` |

---

This document should give you a solid understanding of how Flowspec VPN works end-to-end!
