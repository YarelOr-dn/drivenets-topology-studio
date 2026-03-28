# EVPN (ELAN) SI -- EVPN High-Availability

**Test ID:** TEST_evpn_elan_ha_SW248907
**Source:** jira:SW-248907
**Device:** YOR_CL_PE-4
**Run:** 2026-03-23 08:36:29
**Overall:** ERROR
**Total elapsed:** 1188.5s

## Test Verdict: TEST_evpn_elan_ha_SW248907 on YOR_CL_PE-4
**Overall: ERROR** | Elapsed: 1188.5s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_bgp_graceful_restart | PASS | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 2.00s | -- |
| SC02_llgr | PASS | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 1.70s | -- |
| SC03_gr_llgr_failure | PASS | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, rt2_recovery=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 2.00s | -- |
| SC04_fibmgrd_restart | WARN | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, mobility_counter=WARN, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 2.60s | -- |
| SC05_zebra_restart | PASS | mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, bgp_session=PASS, traces=PASS, cross_layer=PASS, timing=PASS, spirent_traffic=PASS | 2.70s | -- |
| SC06_neighbour_manager_restart | ERROR | exception=ERROR | -- | -- |

### SC01_bgp_graceful_restart: BGP Graceful Restart

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| rt2_recovery | PASS | RT-2 recovered: sessions 1->1, prefixes 2->2 | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:16 | 11.07s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 2.00s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 157425184 frames during test | 0.00s |

### SC02_llgr: LLGR (Long-Lived Graceful Restart)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.10s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:18 | 8.26s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 1.70s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 617951195 frames during test | 0.00s |

### SC03_gr_llgr_failure: GR/LLGR Failure (Timer Expiry)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| rt2_recovery | PASS | RT-2 recovered: sessions 1->1, prefixes 2->2 | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:23 | 7.97s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 2.00s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 1372180740 frames during test | 0.00s |

### SC04_fibmgrd_restart: Process Restart -- fib-manager (fibmgrd)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.10s |
| mobility_counter | WARN | Mobility counter 0 -> 0 (delta 0) | 0.20s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:33 | 9.66s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 2.60s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 155075524 frames during test | 0.00s |

### SC05_zebra_restart: Process Restart -- zebra (rib_manager)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| mac_flags | PASS | Flags [] | 0.20s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.10s |
| ghost_macs | PASS | No ghost MACs | 0.05s |
| bgp_session | PASS | 1/1 ESTABLISHED | 0.20s |
| traces | PASS | No ERROR lines near 08:35 | 8.37s |
| cross_layer | PASS | Cross-layer check passed (6 layers, 0 mismatches) | 0.00s |
| timing | PASS | 2.70s <= 120.0s threshold | 0.00s |
| spirent_traffic | PASS | Spirent TX active: 9.6 Gbps, 150375598 frames during test | 0.00s |

### SC06_neighbour_manager_restart: Process Restart -- neighbor-manager

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| exception | ERROR | HA trigger command FAILED: request system process restart ncc 0 management-engine neighbour_manager
YOR_CL_PE-4(23-Mar-2026-10:36:16)# request system process restart ncc 0 management-engine neighbour_manager
------------------------------------------------------------------------------------------^
ERROR: Unknown word: 'neighbour_manager'.
YOR_CL_PE-4# | 0.00s |
