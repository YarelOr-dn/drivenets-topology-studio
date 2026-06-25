# TEST_mac_mob_ac_pw_SW205198

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-18T20:14:42+00:00
**Overall:** PASS
**Elapsed:** 270.4s

## Test Verdict: TEST_mac_mob_ac_pw_SW205198 on PE-1
**Overall: PASS** | Elapsed: 270.4s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_ac_to_pw | PASS | trigger=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=WARN, traces=SKIP, timing=PASS | 4.39s | -- |
| SC02_pw_to_ac | PASS | trigger=PASS, control_plane=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=WARN, traces=SKIP, timing=PASS | 4.27s | -- |
| SC03_sticky_ac_to_pw | PASS | trigger=PASS, sticky=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=WARN, traces=SKIP, timing=PASS | 17.40s | -- |
| SC04_pw_to_sticky_ac | SKIP | spirent_health=SKIP | -- | -- |

### SC01_ac_to_pw: Non-sticky: Local AC -> PW; withdraw RT-2; suppression counted

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | AC->PW: learned on AC (inner 1010), then sent via MPLS label 1032265 | 0.00s |
| mac_flags | PASS | Flags ['L', 'K', 'M', 'P'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 4.39s <= 90.0s threshold | 0.00s |

### SC02_pw_to_ac: PW -> Local AC (non-sticky); advertise RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | PW learn (MPLS label 1032265) then AC learn (inner 1010) | 0.00s |
| control_plane | PASS | AC attachment: local | 0.00s |
| mac_flags | PASS | Flags ['L', 'K', 'M', 'P'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) | 0.20s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 4.27s <= 90.0s threshold | 0.00s |

### SC03_sticky_ac_to_pw: Sticky AC -> PW: IGNORE move (SW-194578)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | AC->PW: learned on AC (inner 1010), then sent via MPLS label 1032265 | 0.00s |
| sticky | PASS | Sticky MAC enforced | 0.00s |
| mac_flags | PASS | Flags ['L', 'K'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.20s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) | 0.20s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 17.40s <= 90.0s threshold | 0.00s |

### SC04_pw_to_sticky_ac: PW -> Sticky AC: prefer sticky AC; advertise RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| spirent_health | SKIP | Spirent session unhealthy and auto-reconnect failed; skipping scenario | 0.00s |


## Observability Summary

- **Commands executed:** 52
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 1
  - mac_cleanup: 6
  - trigger: 3
  - verify: 33