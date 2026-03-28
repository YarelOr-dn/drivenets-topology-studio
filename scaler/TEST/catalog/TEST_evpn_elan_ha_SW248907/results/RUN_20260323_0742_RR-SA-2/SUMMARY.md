# EVPN (ELAN) SI -- EVPN High-Availability

**Test ID:** TEST_evpn_elan_ha_SW248907
**Source:** jira:SW-248907
**Device:** RR-SA-2
**Run:** 2026-03-23 07:48:23
**Overall:** PASS
**Total elapsed:** 335.4s

## Test Verdict: TEST_evpn_elan_ha_SW248907 on RR-SA-2
**Overall: PASS** | Elapsed: 335.4s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_bgp_graceful_restart | PASS | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 4.20s | -- |

### SC01_bgp_graceful_restart: BGP Graceful Restart

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags ['L'] | 2.08s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 3.10s |
| ghost_macs | PASS | No ghost MACs | 2.07s |
| rt2_recovery | PASS | RT-2 recovered: sessions 2->2, prefixes 1->1 | 42.11s |
| bgp_session | PASS | 2/2 ESTABLISHED | 2.08s |
| traces | PASS | No ERROR lines near 07:43 | 19.46s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 4.20s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 538063851 frames during test | 0.00s |
