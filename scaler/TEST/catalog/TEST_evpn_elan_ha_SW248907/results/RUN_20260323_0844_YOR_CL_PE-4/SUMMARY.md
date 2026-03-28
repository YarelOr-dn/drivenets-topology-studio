# EVPN (ELAN) SI -- EVPN High-Availability

**Test ID:** TEST_evpn_elan_ha_SW248907
**Source:** jira:SW-248907
**Device:** YOR_CL_PE-4
**Run:** 2026-03-23 08:49:38
**Overall:** WARN
**Total elapsed:** 325.3s

## Test Verdict: TEST_evpn_elan_ha_SW248907 on YOR_CL_PE-4
**Overall: WARN** | Elapsed: 325.3s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC06_neighbour_manager_restart | PASS | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 1.70s | -- |
| SC07_mac_recovery | WARN | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, mobility_counter=WARN, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 0.40s | -- |
| SC08_ncc_switchover | WARN | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, mobility_counter=WARN, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 2.20s | -- |
| SC09_mac_move_during_gr | WARN | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, mobility_counter=WARN, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 1.50s | -- |

### SC06_neighbour_manager_restart: Process Restart -- neighbor-manager

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| rt2_recovery | PASS | RT-2 recovered: sessions 1->1, prefixes 2->2 | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:44 | 10.32s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 1.70s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 138627834 frames during test | 0.00s |

### SC07_mac_recovery: MAC Recovery Post-Restart

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| mobility_counter | WARN | Mobility counter 0 -> 0 (delta 0) | 0.20s |
| rt2_recovery | PASS | RT-2 recovered: sessions 1->1, prefixes 2->2 | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.15s |
| traces | PASS | No ERROR lines near 08:45 | 10.82s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 0.40s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 150375926 frames during test | 0.00s |

### SC08_ncc_switchover: NCC / RE Switchover

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| mobility_counter | WARN | Mobility counter 0 -> 0 (delta 0) | 0.20s |
| rt2_recovery | PASS | RT-2 recovered: sessions 1->1, prefixes 2->2 | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:47 | 0.55s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 2.20s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 225563681 frames during test | 0.00s |

### SC09_mac_move_during_gr: MAC Move During Restart Window

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| mobility_counter | WARN | Mobility counter 0 -> 0 (delta 0) | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:48 | 0.45s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 1.50s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 126879040 frames during test | 0.00s |
