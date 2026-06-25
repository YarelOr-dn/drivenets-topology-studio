# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-03T06:07:44+00:00
**Overall:** FAIL
**Elapsed:** 1046.1s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 1046.1s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, rt2_advertised=FAIL, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=WARN, timing=FAIL | 22.19s | Layer 'control_plane' failed. 1 trace match(es) near 05:50 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC02_learn_remote_evpn | FAIL | trigger=SKIP, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=FAIL | 11.71s | Layer 'control_plane' failed. 2 trace match(es) near 05:54 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC03_learn_vpls_pw | FAIL | trigger=SKIP, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=FAIL | 11.76s | Layer 'control_plane' failed. No trace hits near 05:57. Trace buffer may have rotated or timestamp mismatch. | Action: Reproduce the failure for fresh traces. Check trace buffer size: show file traces routing_engine/bgpd_traces | tail 5 |
| SC04_table_counts | FAIL | scale=PASS, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=WARN, timing=FAIL | 7.91s | Layer 'mac_flags' failed. 2 error(s) found in traces near 06:01. | Action: /debug-dnos PE-1 -- EVPN MAC mobility mac_flags failure. Timestamp: 06:01. Errors in: bgpd_traces |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Learning 1 MACs on AC1 vlan 1010 (Q-in-Q outer=214) | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['local', 'ac'], got missing | 0.50s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| rt2_advertised | FAIL | BGP RT-2 for 00:DE:AD:00:01:01: NOT FOUND | 0.00s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 05:50 | 19.13s |
| timing | FAIL | 22.19s >> 2.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 05:50 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | No spirent_bgp_device configured for remote PE | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['bgp', 'evpn', 'remote'], got missing | 0.45s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 05:54 | 23.98s |
| timing | FAIL | 11.71s >> 2.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 2 trace match(es) near 05:54 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | No pw_vlan for PW traffic | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:01:01 expected ['pw', 'pseudo', 'vpls'], got missing | 0.50s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 05:57 | 28.49s |
| timing | FAIL | 11.76s >> 2.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. No trace hits near 05:57. Trace buffer may have rotated or timestamp mismatch. | Action: Reproduce the failure for fresh traces. Check trace buffer size: show file traces routing_engine/bgpd_traces | tail 5

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 0 -> 0 (delta=0) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.50s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 06:01 | 16.92s |
| timing | FAIL | 7.91s >> 2.0s threshold | 0.00s |

**Debug:** Layer 'mac_flags' failed. 2 error(s) found in traces near 06:01. | Action: /debug-dnos PE-1 -- EVPN MAC mobility mac_flags failure. Timestamp: 06:01. Errors in: bgpd_traces


## Observability Summary

- **Commands executed:** 156
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 5
  - trigger: 0
  - verify: 74
  - auto_diagnose: 77