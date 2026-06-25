# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-03T10:24:00+00:00
**Overall:** FAIL
**Elapsed:** 554.0s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 554.0s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | PASS | trigger=PASS, control_plane=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_advertised=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 13.59s | -- |
| SC02_learn_remote_evpn | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 1.14s | Layer 'control_plane' failed. 1 trace match(es) near 10:17 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC03_learn_vpls_pw | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 2.82s | Layer 'control_plane' failed. 1 trace match(es) near 10:19 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC04_table_counts | FAIL | scale=PASS, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=PASS | 0.60s | Layer 'mac_flags' failed. 3 trace match(es) near 10:21 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |

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
| traces | PASS | No ERROR lines near 10:14 | 7.40s |
| timing | PASS | 13.59s <= 30.0s threshold | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent BGP RT-2 (00:DE:AD:00:01:01) | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['bgp', 'evpn', 'remote'], got local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 10:17 | 8.46s |
| timing | PASS | 1.14s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 10:17 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | PW traffic via Spirent L2 VLAN 1010 | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['pw', 'pseudo', 'vpls'], got local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 10:19 | 16.84s |
| timing | PASS | 2.82s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 10:19 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 0 -> 0 (delta=0) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 10:21 | 11.82s |
| timing | PASS | 0.60s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'mac_flags' failed. 3 trace match(es) near 10:21 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.


## Observability Summary

- **Commands executed:** 85
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 5
  - trigger: 0
  - verify: 59
  - auto_diagnose: 21