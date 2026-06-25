# AC_PW Test Run -- 2026-04-11 17:20 -- PE-1

## Test: MAC Mobility | AC <-> PW | Sticky/Non-sticky (SW-205198)

**Device:** PE-1 (YOR_PE-1) | **DNOS:** cluster | **EVPN Instance:** PW_TEST_ELAN (EVI 6)
**Duration:** 131s (2m 11s) | **Result:** ALL PASS (4/4)

## Infrastructure

| Component | Value | Time to converge |
|-----------|-------|-------------------|
| Spirent Session | dn_spirent_main | 0s (already active) |
| VPLS_PW_Peer device | 17.17.17.2 (VLAN 214/inner 3) | 2s |
| ISIS adjacency | L2 Up (area 49.0001) | ~40s |
| ISIS route 6.6.6.6 | via ge400-0/0/5.3, metric 11 | ~42s |
| LDP session | via BGP (label 17) | ~50s |
| BGP l2vpn-vpls | Established, 1 prefix | ~55s |
| VPLS PW | Installed, ingress=1032263, egress=17 | ~60s |
| AC .1010 | forwarding-all on PW_TEST_ELAN | pre-existing |

## Scenarios

### SC01: Non-sticky AC -> PW MAC move -- PASS
- **MAC:** 00:DE:AD:00:01:01
- **AC phase:** Flags=`L>` Interface=`ge400-0/0/5.1010` (Local, selected)
- **PW phase:** Flags=`v>` Interface=`6.6.6.6` (VPLS PW, selected)
- **Verdict:** MAC correctly moved from local AC to VPLS PW

### SC02: Non-sticky PW -> AC MAC move -- PASS
- **MAC:** 00:DE:AD:00:02:02
- **PW phase:** Flags=`v>` Interface=`6.6.6.6` (VPLS PW, selected)
- **AC phase:** Flags=`L>` Interface=`ge400-0/0/5.1010` (Local, selected)
- **Verdict:** MAC correctly moved from VPLS PW to local AC

### SC03: Sticky AC -> PW (move IGNORED) -- PASS
- **MAC:** 00:DE:AD:00:03:03
- **Sticky AC phase:** Flags=`Lsi>` Interface=`ge400-0/0/5.1010` (Local+Sticky-Interface)
- **After PW attempt:** Flags=`Lsi>` Interface=`ge400-0/0/5.1010` (unchanged)
- **Verdict:** MAC stayed on sticky AC; PW move correctly ignored

### SC04: PW -> Sticky AC (sticky wins) -- PASS
- **MAC:** 00:DE:AD:00:04:04
- **PW phase:** Flags=`v>` Interface=`6.6.6.6` (VPLS PW)
- **Sticky AC phase:** Flags=`Lsi>` Interface=`ge400-0/0/5.1010` (Local+Sticky-Interface)
- **Verdict:** Sticky AC correctly took over from PW

## Key Parameters

| Parameter | Value |
|-----------|-------|
| PW ingress label | 1032263 |
| PW egress label | 17 |
| DUT site-id | 2 |
| Spirent VE-ID | 1 |
| VPLS RT | 9990:9990 |
| VPLS RD | 1.1.1.1:9990 (DUT) / 6.6.6.6:9990 (Spirent) |
| AC interface | ge400-0/0/5.1010 (outer-tag 214, inner-tag 1010) |
| DUT MAC | e8:c5:7a:39:b6:6a |
| Spirent VPLS nexthop | 6.6.6.6 |

## Timing Breakdown

| Phase | Duration |
|-------|----------|
| VPLS infra rebuild (device+ISIS+LDP+BGP) | ~12s |
| Protocol convergence | ~60s |
| SC01 (AC->PW) | ~20s |
| SC02 (PW->AC) | ~20s |
| SC03 (Sticky AC, PW ignored) | ~22s |
| SC04 (PW -> Sticky AC) | ~22s |
| Total test execution (4 scenarios) | 131s |

## Issues Encountered

None -- clean run. All prerequisites were met after VPLS infrastructure rebuild.

## Learnings for Future Runs

1. **VPLS PW convergence is fast (~60s)** when DUT config is already in place (label pool, BGP neighbor, EVPN SI instance). Only need Spirent device + protocol-start.
2. **L2 streams work for AC-side MAC learning** -- no need for full emulated device with ARP. A simple L2 broadcast stream with the test MAC as source is sufficient.
3. **vpls-stream works immediately** -- MPLS-labeled frames with the correct ingress label cause immediate PW MAC learning.
4. **Sticky behavior is consistent** across AC-to-PW and PW-to-AC directions: sticky always wins.
5. **MAC address format matters** -- use valid hex only (0-9, A-F). Invalid chars like P, W cause silent failures.
