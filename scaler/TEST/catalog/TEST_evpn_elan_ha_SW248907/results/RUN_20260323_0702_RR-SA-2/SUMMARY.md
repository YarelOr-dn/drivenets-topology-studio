# EVPN (ELAN) SI -- EVPN High-Availability

**Test ID:** TEST_evpn_elan_ha_SW248907
**Source:** jira:SW-248907
**Device:** RR-SA-2
**Run:** 2026-03-23 07:07:18
**Overall:** FAIL
**Total elapsed:** 285.6s

## Test Verdict: TEST_evpn_elan_ha_SW248907 on RR-SA-2
**Overall: FAIL** | Elapsed: 285.6s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_bgp_graceful_restart | FAIL | mac_flags=PASS, forwarding=FAIL, ghost_macs=PASS, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, xref_interface_agreement=FAIL, xref_fib_ncp_interface=FAIL, timing=PASS, spirent_traffic=PASS | 4.20s | /debug-dnos verify SW-248907 on RR-SA-2 --scenario SC01_bgp_graceful_restart |

### SC01_bgp_graceful_restart: BGP Graceful Restart

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags ['L'] | 2.22s |
| forwarding | FAIL | NCP state: unknown (expected forwarding) | 9.38s |
| ghost_macs | PASS | No ghost MACs | 2.07s |
| rt2_recovery | PASS | RT-2 recovered: sessions 2->2, prefixes 1->1 | 35.14s |
| bgp_session | PASS | 2/2 ESTABLISHED | 2.09s |
| traces | PASS | No ERROR lines near 07:03 | 32.38s |
| xref_interface_agreement | FAIL | Interface mismatch across layers: {'mac_detail': 'bundle-100.2150', 'forwarding_table': 'bundle-100.2150', 'fib_database': 'eth_tag=0,'} | 0.00s |
| xref_fib_ncp_interface | FAIL | FIB interface=eth_tag=0, vs NCP forwarding interface=bundle-100.2150 | 0.00s |
| timing | PASS | 4.20s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 502819447 frames during test | 0.00s |

**Debug:** /debug-dnos verify SW-248907 on RR-SA-2 --scenario SC01_bgp_graceful_restart
