# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-16T16:55:36+00:00
**Overall:** FAIL
**Elapsed:** 313.1s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 313.1s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | PASS | trigger=PASS, control_plane=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_advertised=PASS, cross_layer=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 3.30s | -- |
| SC02_learn_remote_evpn | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=FAIL, forwarding=FAIL, ghost_macs=PASS, cross_layer_mac_existence=FAIL, bgp_session=PASS, traces=PASS, timing=PASS | 44.80s | Layer 'control_plane' failed. 1 trace match(es) near 16:52 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |
| SC03_learn_vpls_pw | FAIL | trigger=FAIL | -- | -- |
| SC04_table_counts | WARN | scale=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=WARN, traces=SKIP, timing=PASS | 0.40s | -- |

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
| timing | PASS | 3.30s <= 90.0s threshold | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent EVPN peer EVPN_RT2_Peer (00:DE:AD:00:02:02) | 0.00s |
| control_plane | FAIL | MAC 00:DE:AD:00:02:02 expected ['bgp', 'evpn', 'remote'], got missing | 0.50s |
| mac_flags | FAIL | MAC not found in detail output | 0.25s |
| forwarding | FAIL | MAC not found in forwarding table | 0.15s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer_mac_existence | FAIL | MAC 00:de:ad:00:02:02 not found in mac-table | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 16:52 | 7.43s |
| timing | PASS | 44.80s <= 90.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 1 trace match(es) near 16:52 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | FAIL | VPLS PW not Installed after 60s recovery. Run: spirent_tool.py protocol-start --device-name VPLS_PW_Peer | 0.00s |

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| scale | PASS | Count: 2 -> 2 (delta=0) | 0.00s |
| mac_flags | PASS | Flags ['L'] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 0.40s <= 90.0s threshold | 0.00s |


## Observability Summary

- **Commands executed:** 57
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 4
  - mac_cleanup: 4
  - trigger: 1
  - verify: 41
  - auto_diagnose: 7