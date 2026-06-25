# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-03T11:31:13+00:00
**Overall:** FAIL
**Elapsed:** 551.8s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 551.8s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | WARN | trigger=PASS, control_plane=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_advertised=PASS, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 3.44s | -- |
| SC02_learn_remote_evpn | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 1.14s | Layer 'control_plane' failed. 2 trace match(es) near 11:24 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC03_learn_vpls_pw | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 4.65s | Layer 'control_plane' failed. 2 trace match(es) near 11:26 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC04_table_counts | WARN | scale=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 0.40s | -- |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Learning 1 MACs on AC1 vlan 1000 (Q-in-Q outer=214) (polled 0.251s) | 0.00s |
| control_plane | PASS | MAC 00:DE:AD:00:01:01 source=local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| rt2_advertised | PASS | BGP RT-2 for 00:DE:AD:00:01:01: PRESENT | 0.00s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 11:22 | 9.31s |
| timing | PASS | 3.44s <= 30.0s threshold | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent BGP RT-2 (00:DE:AD:00:01:01) | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['bgp', 'evpn', 'remote'], got local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 11:24 | 9.97s |
| timing | PASS | 1.14s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 2 trace match(es) near 11:24 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | PW traffic via Spirent L2 VLAN 1010 | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['pw', 'pseudo', 'vpls'], got local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 11:26 | 12.67s |
| timing | PASS | 4.65s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 2 trace match(es) near 11:26 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 1 -> 1 (delta=0) | 0.00s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 11:28 | 8.34s |
| timing | PASS | 0.40s <= 30.0s threshold | 0.00s |


## Observability Summary

- **Commands executed:** 81
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 5
  - mac_cleanup: 3
  - trigger: 0
  - verify: 59
  - auto_diagnose: 14