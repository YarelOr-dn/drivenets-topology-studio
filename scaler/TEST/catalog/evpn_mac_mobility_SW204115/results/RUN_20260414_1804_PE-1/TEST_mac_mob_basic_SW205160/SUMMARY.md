# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-14T18:04:46+00:00
**Overall:** FAIL
**Elapsed:** 7.1s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 7.1s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | FAIL | preflight_bgp=FAIL | -- | -- |
| SC02_learn_remote_evpn | FAIL | preflight_bgp=FAIL | -- | -- |
| SC03_learn_vpls_pw | FAIL | preflight_bgp=FAIL | -- | -- |
| SC04_table_counts | FAIL | preflight_bgp=FAIL | -- | -- |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_bgp | FAIL | No EVPN peers ESTABLISHED (3 configured, all down) | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_bgp | FAIL | No EVPN peers ESTABLISHED (3 configured, all down) | 0.00s |

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_bgp | FAIL | No EVPN peers ESTABLISHED (3 configured, all down) | 0.00s |

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_bgp | FAIL | No EVPN peers ESTABLISHED (3 configured, all down) | 0.00s |
