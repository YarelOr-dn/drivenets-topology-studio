# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-16T18:25:09+00:00
**Overall:** FAIL
**Elapsed:** 198.7s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 198.7s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC02_learn_remote_evpn | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC03_learn_vpls_pw | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC04_table_counts | FAIL | preflight_smoke_test=FAIL | -- | -- |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |
