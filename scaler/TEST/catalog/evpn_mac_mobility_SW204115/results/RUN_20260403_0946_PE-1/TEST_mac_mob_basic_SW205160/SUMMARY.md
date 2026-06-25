# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-03T10:05:02+00:00
**Overall:** FAIL
**Elapsed:** 1113.2s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 1113.2s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=WARN, rt2_advertised=PASS, cross_layer=PASS, bgp_session=PASS, traces=PASS, timing=PASS | 3.42s | Layer 'control_plane' failed. 1 trace match(es) near 09:46 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC02_learn_remote_evpn | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=WARN, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 1.14s | Layer 'control_plane' failed. 1 trace match(es) near 09:51 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC03_learn_vpls_pw | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=PASS | 18.85s | Layer 'control_plane' failed. 2 trace match(es) near 09:55 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC04_table_counts | FAIL | scale=PASS, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=WARN, timing=PASS | 0.60s | Layer 'mac_flags' failed. 2 error(s) found in traces near 09:59. | Action: /debug-dnos PE-1 -- EVPN MAC mobility mac_flags failure. Timestamp: 09:59. Errors in: bgpd_traces |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Learning 1 MACs on AC1 vlan 1000 (Q-in-Q outer=214) (polled 0.251s) | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['local', 'ac'], got unknown | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | WARN | 1 ghost MAC(s): 00:de:ad:00:01:01 | 0.25s |
| rt2_advertised | PASS | BGP RT-2 for 00:DE:AD:00:01:01: PRESENT | 0.00s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 09:46 | 30.34s |
| timing | PASS | 3.42s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 09:46 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent BGP RT-2 (00:DE:AD:00:01:01) | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['bgp', 'evpn', 'remote'], got unknown | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | WARN | 1 ghost MAC(s): 00:de:ad:00:01:01 | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 09:51 | 15.92s |
| timing | PASS | 1.14s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 09:51 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | PW traffic via Spirent L2 VLAN 1010 | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['pw', 'pseudo', 'vpls'], got missing | 0.50s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 09:55 | 25.08s |
| timing | PASS | 18.85s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 2 trace match(es) near 09:55 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 0 -> 0 (delta=0) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 09:59 | 25.28s |
| timing | PASS | 0.60s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'mac_flags' failed. 2 error(s) found in traces near 09:59. | Action: /debug-dnos PE-1 -- EVPN MAC mobility mac_flags failure. Timestamp: 09:59. Errors in: bgpd_traces


## Observability Summary

- **Commands executed:** 141
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 5
  - trigger: 0
  - verify: 59
  - auto_diagnose: 77