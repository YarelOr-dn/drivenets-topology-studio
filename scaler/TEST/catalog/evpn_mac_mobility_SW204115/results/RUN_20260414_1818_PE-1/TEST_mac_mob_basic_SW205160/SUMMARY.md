# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-14T18:30:19+00:00
**Overall:** FAIL
**Elapsed:** 720.8s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 720.8s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | PASS | trigger=PASS, control_plane=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_advertised=PASS, cross_layer=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 2.02s | -- |
| SC02_learn_remote_evpn | PASS | trigger=PASS, control_plane=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 4.10s | -- |
| SC03_learn_vpls_pw | FAIL | trigger=SKIP, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=FAIL | 330.91s | Layer 'control_plane' failed. 2 trace match(es) near 18:21 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC04_table_counts | FAIL | scale=PASS, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=PASS | 0.65s | Layer 'mac_flags' failed. 1 trace match(es) near 18:28 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Learning 1 MACs on AC1 vlan 1000 (Q-in-Q outer=214) at 1Mbps (polled 0.251s) | 0.00s |
| control_plane | PASS | MAC 00:DE:AD:00:01:01 source=local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| rt2_advertised | PASS | BGP RT-2 for 00:DE:AD:00:01:01: PRESENT | 0.00s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 2.02s <= 90.0s threshold | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent EVPN peer EVPN_RT2_Peer (00:DE:AD:00:02:02) | 0.00s |
| control_plane | PASS | MAC 00:DE:AD:00:02:02 source=bgp | 0.25s |
| mac_flags | PASS | Flags [] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:02:02 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 4.10s <= 90.0s threshold | 0.00s |

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | SKIP | No VPLS PW label found -- PW not installed after convergence wait | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:03:03 expected ['pw', 'pseudo', 'vpls'], got missing | 0.50s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:03:03 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 18:21 | 7.75s |
| timing | FAIL | 330.91s >> 90.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 2 trace match(es) near 18:21 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 1 -> 1 (delta=0) | 0.00s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:01:01 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 18:28 | 13.99s |
| timing | PASS | 0.65s <= 90.0s threshold | 0.00s |

**Debug:** Layer 'mac_flags' failed. 1 trace match(es) near 18:28 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.


## Observability Summary

- **Commands executed:** 141
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 5
  - mac_cleanup: 6
  - trigger: 61
  - verify: 55
  - auto_diagnose: 14