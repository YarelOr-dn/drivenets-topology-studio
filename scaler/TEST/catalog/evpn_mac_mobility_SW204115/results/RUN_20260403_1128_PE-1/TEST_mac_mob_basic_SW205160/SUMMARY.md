# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-03T11:31:10+00:00
**Overall:** FAIL
**Elapsed:** 152.6s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 152.6s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC02_learn_remote_evpn | FAIL | trigger=PASS, control_plane=FAIL, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=WARN, timing=PASS | 1.19s | Layer 'control_plane' failed. 2 trace match(es) near 11:28 but no ERROR lines. | Action: Review trace lines for unexpected state transitions. |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | Remote PE traffic via Spirent BGP RT-2 (00:de:ad:00:01:01) | 0.00s |
| control_plane | FAIL | MAC 00:de:ad:00:01:01 expected ['bgp', 'evpn', 'remote'], got local | 0.25s |
| mac_flags | PASS | Flags ['L'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:00:01:01 | 0.00s |
| bgp_session | PASS | 1/2 ESTABLISHED | 0.25s |
| traces | WARN | ERROR lines found near 11:28 | 9.84s |
| timing | PASS | 1.19s <= 30.0s threshold | 0.00s |

**Debug:** Layer 'control_plane' failed. 2 trace match(es) near 11:28 but no ERROR lines. | Action: Review trace lines for unexpected state transitions.


## Observability Summary

- **Commands executed:** 23
- **Anomalies detected:** 0
- **Scenarios:** 1
- **Commands per phase:**
  - snapshot: 1
  - mac_cleanup: 1
  - trigger: 0
  - verify: 14
  - auto_diagnose: 7