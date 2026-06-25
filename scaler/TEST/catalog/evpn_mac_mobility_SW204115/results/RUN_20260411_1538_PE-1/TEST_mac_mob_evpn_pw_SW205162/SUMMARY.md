# TEST_mac_mob_evpn_pw_SW205162

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-11T15:46:47+00:00
**Overall:** WARN
**Elapsed:** 498.1s

## Test Verdict: TEST_mac_mob_evpn_pw_SW205162 on PE-1
**Overall: WARN** | Elapsed: 498.1s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_evpn_to_pw | WARN | trigger=SKIP, mac_flags=PASS, forwarding=PASS, mobility_counter=WARN, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 1.00s | -- |
| SC02_pw_to_evpn | PASS | trigger=SKIP, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 1.00s | -- |
| SC03_sticky_evpn_to_pw | PASS | trigger=SKIP, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 0.45s | -- |
| SC04_pw_to_sticky_evpn | PASS | trigger=SKIP, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 0.50s | -- |

### SC01_evpn_to_pw: Non-sticky: remote EVPN -> PW; no RT change; not counted

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| mobility_counter | WARN | Mobility counter 0 -> 0 (delta 0) | 0.25s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 15:38 | 12.26s |
| timing | PASS | 1.00s <= 90.0s threshold | 0.00s |

### SC02_pw_to_evpn: PW -> EVPN; accept; static entry

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 15:40 | 8.69s |
| timing | PASS | 1.00s <= 90.0s threshold | 0.00s |

### SC03_sticky_evpn_to_pw: Sticky EVPN RT-2 -> PW; IGNORE move (blackholing risk)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 15:42 | 9.30s |
| timing | PASS | 0.45s <= 90.0s threshold | 0.00s |

### SC04_pw_to_sticky_evpn: PW -> Sticky EVPN; accept; datapath static sticky

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | Unknown trigger:  (mapped=unknown) | 0.00s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 15:44 | 9.77s |
| timing | PASS | 0.50s <= 90.0s threshold | 0.00s |


## Observability Summary

- **Commands executed:** 57
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 1
  - trigger: 0
  - verify: 56