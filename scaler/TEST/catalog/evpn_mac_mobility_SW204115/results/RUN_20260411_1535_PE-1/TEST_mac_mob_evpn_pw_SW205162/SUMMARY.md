# TEST_mac_mob_evpn_pw_SW205162

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-11T15:37:20+00:00
**Overall:** FAIL
**Elapsed:** 120.2s

## Test Verdict: TEST_mac_mob_evpn_pw_SW205162 on PE-1
**Overall: FAIL** | Elapsed: 120.2s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_evpn_to_pw | FAIL | trigger=SKIP, mac_flags=FAIL, forwarding=FAIL, mobility_counter=WARN, ghost_macs=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 11.52s | Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic. |
| SC02_pw_to_evpn | FAIL | trigger=SKIP, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 11.52s | Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic. |
| SC03_sticky_evpn_to_pw | FAIL | trigger=SKIP, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 10.92s | Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic. |
| SC04_pw_to_sticky_evpn | FAIL | trigger=SKIP, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 11.02s | Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic. |

### SC01_evpn_to_pw: Non-sticky: remote EVPN -> PW; no RT change; not counted

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.25s |
| mobility_counter | WARN | Mobility counter 0 -> 0 (delta 0) | 0.25s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 11.52s <= 90.0s threshold | 0.00s |

**Debug:** Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic.

### SC02_pw_to_evpn: PW -> EVPN; accept; static entry

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 11.52s <= 90.0s threshold | 0.00s |

**Debug:** Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic.

### SC03_sticky_evpn_to_pw: Sticky EVPN RT-2 -> PW; IGNORE move (blackholing risk)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.20s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 10.92s <= 90.0s threshold | 0.00s |

**Debug:** Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic.

### SC04_pw_to_sticky_evpn: PW -> Sticky EVPN; accept; datapath static sticky

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 11.02s <= 90.0s threshold | 0.00s |

**Debug:** Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic.


## Observability Summary

- **Commands executed:** 25
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 1
  - trigger: 0
  - verify: 24
  - auto_diagnose: 0