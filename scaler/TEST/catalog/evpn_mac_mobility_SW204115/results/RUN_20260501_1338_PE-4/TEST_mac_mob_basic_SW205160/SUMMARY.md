# TEST_mac_mob_basic_SW205160

**Device:** PE-4
**Mode:** execute
**Time:** 2026-05-01T13:39:29+00:00
**Overall:** FAIL
**Elapsed:** 31.2s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-4
**Overall: FAIL** | Elapsed: 31.2s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_L_local_ac | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC02_B_remote_evpn | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC03_v_pw_via_rrsa2_ac | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC04_counts_and_stability | FAIL | preflight_smoke_test=FAIL | -- | -- |

### SC01_L_local_ac: SC01: L> Local AC -- PE-4 learns MAC from its own untagged AC and advertises RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC02_B_remote_evpn: SC02: B> Remote EVPN -- PE-1 learns MAC locally; PE-4 receives via RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC03_v_pw_via_rrsa2_ac: SC03: v> VPLS PW -- RR-SA-2 learns MAC locally on its AC; PE-4 sees it via VPLS PW (label 1032269)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC04_counts_and_stability: SC04: Counts + stability -- all three sources coexist (L+B+v), no suppression, no ghosts, BGP stable

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |
