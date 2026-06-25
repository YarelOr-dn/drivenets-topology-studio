# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-03T09:43:00+00:00
**Overall:** FAIL
**Elapsed:** 1146.6s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 1146.6s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=WARN, rt2_advertised=PASS, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 13.29s | Layer 'control_plane' failed. 4 trace match(es) near 09:23 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC02_learn_remote_evpn | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=WARN, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 8.64s | Layer 'control_plane' failed. 4 trace match(es) near 09:27 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC03_learn_vpls_pw | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=WARN, timing=PASS | 19.88s | Layer 'control_plane' failed. 1 trace match(es) near 09:31 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC04_table_counts | FAIL | scale=PASS, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=WARN, timing=PASS | 7.76s | Layer 'mac_flags' failed. 2 error(s) found in traces near 09:35. | Action: /debug-dnos PE-1 -- EVPN MAC mobility mac_flags failure. Timestamp: 09:35. Errors in: bgpd_traces |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Learning 1 MACs on AC1 vlan 1000 (Q-in-Q outer=214) | 0.00s |
| control_plane | FAIL | MAC 00:de:ad:00:01:01 expected ['local', 'ac'], got unknown | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | WARN | 1 ghost MAC(s): 00:de:ad:00:01:01 | 0.25s |
| rt2_advertised | PASS | BGP RT-2 for 00:de:ad:00:01:01: PRESENT | 0.00s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 09:23 | 22.58s |
| timing | PASS | 13.29s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 4 trace match(es) near 09:23 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent BGP RT-2 (00:de:ad:00:01:01) | 0.00s |
| control_plane | FAIL | MAC 00:de:ad:00:01:01 expected ['bgp', 'evpn', 'remote'], got unknown | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | WARN | 1 ghost MAC(s): 00:de:ad:00:01:01 | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 09:27 | 21.48s |
| timing | PASS | 8.64s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 4 trace match(es) near 09:27 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | PW traffic via Spirent L2 VLAN 1010 | 0.00s |
| control_plane | FAIL | MAC 00:de:ad:00:01:01 expected ['pw', 'pseudo', 'vpls'], got missing | 0.50s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 09:31 | 24.93s |
| timing | PASS | 19.88s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 09:31 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 0 -> 0 (delta=0) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 09:35 | 17.02s |
| timing | PASS | 7.76s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'mac_flags' failed. 2 error(s) found in traces near 09:35. | Action: /debug-dnos PE-1 -- EVPN MAC mobility mac_flags failure. Timestamp: 09:35. Errors in: bgpd_traces


## Observability Summary

- **Commands executed:** 149
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 5
  - trigger: 0
  - verify: 67
  - auto_diagnose: 77