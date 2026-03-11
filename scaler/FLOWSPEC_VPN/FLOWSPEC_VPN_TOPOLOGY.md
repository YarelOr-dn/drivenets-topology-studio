# FlowSpec VPN Topology - Simplified View
# ========================================

## Quick Reference Topology

```
                    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                    ┃           FLOWSPEC VPN TEST TOPOLOGY (Simplified)            ┃
                    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

                                      ┌─────────────┐
                                      │   SPIRENT   │
                                      │   100G TG   │
                                      │  (HW-114)   │
                                      └──────┬──────┘
                                             │
                              ╔══════════════╧══════════════╗
                              ║     Traffic to VRF1/VRF_BLUE ║
                              ╚══════════════╤══════════════╝
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │                                                  │
                    ▼                                                  ▼
         ╔══════════════════════╗                         ╔══════════════════════╗
         ║        DUT           ║                         ║        DN01          ║
         ║     (CL-408D)        ║══════════════════════════║    (NCP-36CD-S)      ║
         ║       PE-1           ║    iBGP + MPLS Core      ║       PE-2           ║
         ╠══════════════════════╣                         ╠══════════════════════╣
         ║ AS: 65000            ║                         ║ AS: 65000            ║
         ║ Loopback: 1.1.1.1    ║                         ║ Loopback: 2.2.2.2    ║
         ║                      ║                         ║                      ║
         ║ VRFs:                ║                         ║ VRFs:                ║
         ║ • VRF1 (RT 65000:100)║                         ║ • VRF1 (RT 65000:100)║
         ║ • VRF_RED (200)      ║                         ║ • VRF_RED (200)      ║
         ║ • VRF_BLUE (300)     ║                         ╠══════════════════════╣
         ║                      ║                         ║ Optional: Can act as ║
         ║ Flowspec-VPN: ✓      ║                         ║ Route Reflector      ║
         ╚══════════╤═══════════╝                         ╚══════════════════════╝
                    │
                    │ eBGP (AS 65001)
                    ▼
         ╔══════════════════════╗
         ║        R2            ║
         ║  cDNOS on Server     ║
         ║     (HW-146)         ║
         ╠══════════════════════╣
         ║ AS: 65001            ║
         ║ External Peer        ║
         ║ Flowspec Source      ║
         ║ (Cisco Interop)      ║
         ╚══════════════════════╝
```

---

## Physical Wiring Diagram

```
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                           PHYSICAL CONNECTIONS                                 ║
    ╠═══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                               ║
    ║   ┌──────────────┐                                                            ║
    ║   │   SPIRENT    │                                                            ║
    ║   │   HW-114     │                                                            ║
    ║   │              │                                                            ║
    ║   │ Port 6:13 ○──┼──────100G──────► ge100-0/0/4 (DUT) ──► VRF1 Traffic        ║
    ║   │ Port 6:14 ○──┼──────100G──────► ge100-0/0/5 (DUT) ──► VRF_BLUE Traffic    ║
    ║   │              │                                                            ║
    ║   └──────────────┘                                                            ║
    ║                                                                               ║
    ║   ┌──────────────┐                              ┌──────────────┐              ║
    ║   │     DUT      │                              │    DN01      │              ║
    ║   │   CL-408D    │                              │  NCP-36CD-S  │              ║
    ║   │              │                              │              │              ║
    ║   │ ge100-0/0/1 ○┼──────100G (MPLS Core)───────○┤ ge100-0/0/1  │              ║
    ║   │ ge100-0/0/2 ○┼──────100G (iBGP to RR)──────○┤ ge100-0/0/2  │              ║
    ║   │              │                              │              │              ║
    ║   └───────┬──────┘                              └──────────────┘              ║
    ║           │                                                                   ║
    ║           │ ge100-0/0/3                                                       ║
    ║           │                                                                   ║
    ║           └────100G (eBGP)────► ge100-0/0/1 (R2)                              ║
    ║                                                                               ║
    ║   ┌──────────────┐                                                            ║
    ║   │      R2      │                                                            ║
    ║   │    cDNOS     │                                                            ║
    ║   │   HW-146     │                                                            ║
    ║   └──────────────┘                                                            ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Hardware Allocation Summary

```
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                         HARDWARE ALLOCATION                                   ║
    ╠════════════╦═══════════════════════╦════════════════╦════════════════════════╣
    ║    ROLE    ║       JIRA HW         ║     TYPE       ║      SERIAL/NAME       ║
    ╠════════════╬═══════════════════════╬════════════════╬════════════════════════╣
    ║            ║ HW-63                 ║ NCP-40C        ║ WDY1A17E00011-P3       ║
    ║            ║ HW-64                 ║ NCP-40C        ║ WDY19C7M00013-P3       ║
    ║    DUT     ║ HW-65                 ║ NCM-48X-6C     ║ AAF1944AAAJ            ║
    ║  (CL-408D) ║ HW-66                 ║ NCC (VM)       ║ kvm108-cl408d-ncc0     ║
    ║            ║ HW-67                 ║ NCC (VM)       ║ kvm108-cl408d-ncc1     ║
    ║            ║ HW-68                 ║ NCF-48CD       ║ WEB19B7G00012-P2       ║
    ╠════════════╬═══════════════════════╬════════════════╬════════════════════════╣
    ║   DN01     ║ HW-136 (primary)      ║ NCP-36CD-S     ║ WK31D7VV00023          ║
    ║   (PE-2)   ║ HW-192 (backup)       ║ NCP-36CD-S     ║ WKY1BC7400002B2        ║
    ╠════════════╬═══════════════════════╬════════════════╬════════════════════════╣
    ║    R2      ║ HW-146                ║ DELL_R740/X86  ║ h263(BMPBZT3) - cDNOS  ║
    ║ (External) ║ (currently Unused)    ║                ║                        ║
    ╠════════════╬═══════════════════════╬════════════════╬════════════════════════╣
    ║  SPIRENT   ║ HW-114                ║ SPIRENT-100G   ║ Spirent01 Port 6:13    ║
    ╚════════════╩═══════════════════════╩════════════════╩════════════════════════╝
```

---

## BGP Logical View

```
                              ┌─────────────────────────────────────┐
                              │            AS 65000                 │
                              │         (iBGP Full Mesh)            │
                              └─────────────────────────────────────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     │                        │                        │
                     ▼                        ▼                        ▼
              ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
              │     PE-1    │◄────────►│     RR      │◄────────►│    PE-2     │
              │    (DUT)    │   iBGP   │ (Optional)  │   iBGP   │   (DN01)    │
              │   1.1.1.1   │          │   3.3.3.3   │          │   2.2.2.2   │
              └──────┬──────┘          └─────────────┘          └─────────────┘
                     │
                     │ eBGP
                     ▼
              ┌─────────────┐
              │     R2      │
              │  AS 65001   │
              │   4.4.4.4   │
              │ (External)  │
              └─────────────┘


    ┌────────────────────────────────────────────────────────────────────────────┐
    │                       BGP Address Families                                  │
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                                            │
    │   PE-PE / PE-RR Sessions (Global BGP):                                     │
    │   ├── ipv4-unicast                                                         │
    │   ├── ipv4-vpn           (VPNv4 routes)                                    │
    │   ├── ipv6-vpn           (VPNv6 routes)                                    │
    │   ├── ipv4-flowspec-vpn  ◄─── THIS IS THE FEATURE UNDER TEST               │
    │   └── ipv6-flowspec-vpn  ◄─── THIS IS THE FEATURE UNDER TEST               │
    │                                                                            │
    │   VRF-level BGP (under network-services vrf):                              │
    │   ├── ipv4-flowspec      (per-VRF flowspec with RT export/import)          │
    │   └── ipv6-flowspec      (per-VRF flowspec with RT export/import)          │
    │                                                                            │
    └────────────────────────────────────────────────────────────────────────────┘
```

---

## VRF and Route Target Design

```
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                         VRF CONFIGURATION                                      ║
    ╠═══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                               ║
    ║   DUT (PE-1)                              DN01 (PE-2)                         ║
    ║   ━━━━━━━━━━                              ━━━━━━━━━━━━                         ║
    ║                                                                               ║
    ║   VRF: VRF1                               VRF: VRF1                           ║
    ║   ├── RD: 65000:1001                      ├── RD: 65000:2001                  ║
    ║   ├── RT Import: 65000:100                ├── RT Import: 65000:100            ║
    ║   ├── RT Export: 65000:100                ├── RT Export: 65000:100            ║
    ║   └── Interface: ge100-0/0/4.100          └── Interface: ge100-0/0/4.100      ║
    ║                                                                               ║
    ║   VRF: VRF_RED                            VRF: VRF_RED                        ║
    ║   ├── RD: 65000:1002                      ├── RD: 65000:2002                  ║
    ║   ├── RT Import: 65000:200                ├── RT Import: 65000:200            ║
    ║   ├── RT Export: 65000:200                ├── RT Export: 65000:200            ║
    ║   └── Interface: ge100-0/0/4.200          └── Interface: ge100-0/0/4.200      ║
    ║                                                                               ║
    ║   VRF: VRF_BLUE                                                               ║
    ║   ├── RD: 65000:1003                                                          ║
    ║   ├── RT Import: 65000:300                                                    ║
    ║   ├── RT Export: 65000:300                                                    ║
    ║   └── Interface: ge100-0/0/5.300                                              ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Test Flow Summary

```
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                           TEST EXECUTION FLOW                                │
    └─────────────────────────────────────────────────────────────────────────────┘

    STEP 1: Setup Base Topology
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [Configure DUT] ──► [Configure DN01] ──► [Configure R2] ──► [Connect Spirent]


    STEP 2: Establish BGP Sessions
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ┌──────────┐
                              │    RR    │
                              └────┬─────┘
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
              ┌────────┐                      ┌────────┐
              │  DUT   │◄────────────────────►│  DN01  │
              └────┬───┘     iBGP              └────────┘
                   │
                   ▼
              ┌────────┐
              │   R2   │ eBGP
              └────────┘


    STEP 3: Configure VRFs + Flowspec
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [Enable flowspec-vpn AF] ──► [Configure VRF BGP] ──► [Add RT] ──► [Verify]


    STEP 4: Inject Flowspec Rules
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [Local Policy on DUT] ──► [Exported via VPN] ──► [Received on DN01]
                                     │
                                     ▼
                        [Or from R2 via eBGP]


    STEP 5: Verify Datapath
    ━━━━━━━━━━━━━━━━━━━━━━━
    [Send Traffic from Spirent] ──► [Match Flowspec Rule] ──► [Action Applied]
                                                                    │
                                            ┌───────────────────────┴──────────┐
                                            ▼                                  ▼
                                      [Drop Traffic]                [Rate-Limit/Mark]


    STEP 6: Execute Test Categories
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    CLI ──► HA ──► Scale ──► Interop ──► Negative ──► SNMP ──► Longevity ──► Done
```

---

## Quick Commands Reference

```bash
# Verify Flowspec-VPN session
show bgp neighbor X.X.X.X address-family ipv4-flowspec-vpn

# Check VRF Flowspec table
show bgp vrf VRF1 ipv4 flowspec

# Check global Flowspec-VPN table
show bgp ipv4 flowspec-vpn

# Check datapath rules on NCP
show flowspec ncp 0

# Check counters
show flowspec counters

# Debug
debug bgp flowspec
```

---

*Topology Document - January 2026*
