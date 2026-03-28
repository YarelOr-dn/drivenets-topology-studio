# EVPN (ELAN) SI -- EVPN High-Availability

**Test ID:** TEST_evpn_elan_ha_SW248907
**Source:** jira:SW-248907
**Device:** YOR_CL_PE-4
**Run:** 2026-03-23 08:15:10
**Overall:** FAIL
**Total elapsed:** 95.7s

## Test Verdict: TEST_evpn_elan_ha_SW248907 on YOR_CL_PE-4
**Overall: FAIL** | Elapsed: 95.7s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_bgp_graceful_restart | FAIL | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, xref_interface_agreement=FAIL, timing=PASS, spirent_traffic=PASS | 1.60s | /debug-dnos verify SW-248907 on YOR_CL_PE-4 --scenario SC01_bgp_graceful_restart |

### SC01_bgp_graceful_restart: BGP Graceful Restart

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.15s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| rt2_recovery | PASS | RT-2 recovered: sessions 1->1, prefixes 2->2 | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:13 | 7.76s |
| xref_interface_agreement | FAIL | Interface mismatch across layers: {'mac_detail': 'label:', 'forwarding_table': 'ge100-18/0/0.24'} | 0.00s |
| timing | PASS | 1.60s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 148025953 frames during test | 0.00s |

**Debug:** /debug-dnos verify SW-248907 on YOR_CL_PE-4 --scenario SC01_bgp_graceful_restart
