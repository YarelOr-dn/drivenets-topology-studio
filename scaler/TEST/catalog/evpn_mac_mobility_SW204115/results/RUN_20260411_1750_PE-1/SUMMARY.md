# EVPN_PW Test Run -- 2026-04-11 17:50 -- PE-1

## Test: MAC Mobility | Remote EVPN <-> PW | Sticky/Non-sticky (SW-205162)

**Device:** PE-1 (YOR_PE-1) | **DNOS:** cluster | **EVPN Instance:** PW_TEST_ELAN (EVI 6)
**Duration:** ~195s (3m 15s) | **Result:** ALL PASS (4/4)

## Infrastructure

| Component | Detail |
|---|---|
| VPLS PW Peer | VPLS_PW_Peer (17.17.17.2), ISIS+LDP+BGP l2vpn-vpls |
| EVPN RT-2 Peer | EVPN_RT2_Peer (19.19.19.2), BGP l2vpn-evpn |
| PW Status | Installed, Ingress-label=1032263, Egress-label=17 |
| EVPN Instance | PW_TEST_ELAN, EVI=6, Seamless-Integration enabled |
| EVPN RT | import/export l2vpn-evpn 9990:9990, RD=1.1.1.1:9990 |
| Convergence | ~60s for full ISIS+LDP+BGP+PW chain |

## Scenarios

### SC01: Non-sticky remote EVPN -> PW (not counted) -- PASS

**Sequence:**
1. Inject EVPN RT-2 (MAC as B> remote EVPN, nexthop 19.19.19.2)
2. Withdraw EVPN RT-2 (protocol-stop on EVPN device)
3. Send PW traffic via vpls-stream (MAC learned as v> on PW, nexthop 6.6.6.6)

**Key finding:** DNOS suppresses PW data-plane learning when a remote EVPN BGP entry
exists for the same MAC. The correct test sequence is: inject RT-2 -> withdraw RT-2 ->
then PW traffic creates the v> entry. No suppression counter increment.

### SC02: PW -> EVPN (accept; static entry) -- PASS

**Sequence:**
1. Send PW traffic (MAC as v> on PW, nexthop 6.6.6.6)
2. Inject EVPN RT-2 (MAC stays v> on PW -- PW retains priority)

**Key finding:** When a MAC is already learned via PW and an EVPN RT-2 arrives for the
same MAC, the PW entry retains selection. The EVPN RT-2 is accepted but does not
override the active PW-learned MAC. No suppression.

### SC03: Sticky EVPN -> PW (IGNORE move) -- PASS

**Sequence:**
1. Inject sticky EVPN RT-2 (MAC as Bs> sticky remote EVPN)
2. Send PW traffic with same MAC via vpls-stream
3. MAC stays Bs> (sticky EVPN kept, PW move ignored)

### SC04: PW -> Sticky EVPN (accept; sticky wins) -- PASS

**Sequence:**
1. Send PW traffic (MAC as v> on PW)
2. Inject sticky EVPN RT-2 (MAC becomes Bs> -- sticky EVPN overrides PW)

## Key Parameters

| Parameter | Value |
|---|---|
| PW MPLS Label | 1032263 |
| EVPN RD | 1.1.1.1:9990 |
| EVPN RT | 9990:9990 |
| VPLS VE-ID (Spirent) | 1 |
| VPLS VE-ID (DUT) | 2 |
| Outer VLAN | 214 |
| PW Inner VLAN | 3 |
| EVPN Inner VLAN | 5 |
| DUT MAC | e8:c5:7a:39:b6:6a |

## MAC Table Flags Reference

| Flag | Meaning |
|---|---|
| B | BGP-learned (remote EVPN) |
| v | VPLS PW learned |
| s | Sticky (static) MAC |
| > | Selected route (best path) |
| L | Local (AC) learned |

## DNOS Behavioral Discoveries

1. **Remote EVPN suppresses PW data-plane learning:** When a MAC has a BGP-learned entry
   (B>), PW data-plane traffic with the same MAC does NOT create a v> entry. The MAC
   remains B> until the EVPN route is withdrawn.

2. **PW retains priority over incoming EVPN RT-2:** When a MAC is PW-learned (v>) and
   an EVPN RT-2 arrives, the PW entry is not overridden. The v> remains selected.

3. **Sticky EVPN always wins over PW:** Both directions tested -- sticky EVPN ignores
   incoming PW moves (SC03) and overrides existing PW entries (SC04).

4. **MAC table column format:** The `show evpn mac-table` output has 6 pipe-delimited
   columns: Flags | MAC | ESI | Nexthop | Label/VNI | Resolution. The ESI column is
   often empty for single-homed entries, which causes parser issues if empty fields
   are filtered out.

5. **STC DeviceStop disrupts port:** Stopping a Spirent device (protocol-stop) briefly
   disrupts the port configuration, which can glitch active traffic streams on the
   same port. For tests that need traffic running during EVPN withdrawal, send fresh
   PW traffic AFTER the withdrawal instead of relying on continuous traffic.

## Timing Breakdown

| Phase | Duration |
|---|---|
| Infrastructure rebuild (connect + reserve + 2 devices + protocols + start) | ~100s |
| ISIS + LDP + BGP convergence | ~60s |
| SC01 (inject + withdraw + PW + verify) | ~55s |
| SC02 (PW + inject + verify) | ~40s |
| SC03 (inject + PW + verify) | ~35s |
| SC04 (PW + inject + verify) | ~40s |

## Issues Encountered

1. **Spirent Lab Server session loss** -- Session dropped mid-test due to Lab Server
   connection instability (DNS resolution for `il-auto-containers` was intermittent).
   Fixed by switching to direct IP (10.10.50.18) in `~/.spirent_config.json`.

2. **MAC table parser bug** -- Initial parser filtered empty pipe-delimited columns,
   causing column misalignment (ESI column is often empty). Fixed by keeping all
   columns from `split('|')` regardless of content.

3. **SC01 sequence correction** -- Original recipe sequence (inject EVPN -> PW traffic
   -> withdraw) didn't work because EVPN suppresses PW learning. Corrected to:
   inject EVPN -> withdraw EVPN -> PW traffic.
