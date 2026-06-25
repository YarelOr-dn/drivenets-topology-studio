# TEST_mac_mob_basic_SW205160

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-14T18:05:37+00:00
**Overall:** FAIL
**Elapsed:** 6.8s

## Test Verdict: TEST_mac_mob_basic_SW205160 on PE-1
**Overall: FAIL** | Elapsed: 6.8s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_learn_local_ac | FAIL | preflight=FAIL | -- | -- |
| SC02_learn_remote_evpn | FAIL | preflight=FAIL | -- | -- |
| SC03_learn_vpls_pw | FAIL | preflight=FAIL | -- | -- |
| SC04_table_counts | FAIL | preflight=FAIL | -- | -- |

### SC01_learn_local_ac: Learn MAC from local AC; expect Type-2 advertised

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight | FAIL | [FAIL] Zero EVPN peers ESTABLISHED (3 configured): 2.2.2.2=Connect, 5.5.5.5=Connect, 19.19.19.2=Connect -- test BLOCKED | 0.00s |

### SC02_learn_remote_evpn: Learn MAC from remote EVPN RT-2

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight | FAIL | [FAIL] Zero EVPN peers ESTABLISHED (3 configured): 2.2.2.2=Connect, 5.5.5.5=Connect, 19.19.19.2=Connect -- test BLOCKED | 0.00s |

### SC03_learn_vpls_pw: Learn MAC from VPLS PW (dynamic)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight | FAIL | [FAIL] Zero EVPN peers ESTABLISHED (3 configured): 2.2.2.2=Connect, 5.5.5.5=Connect, 19.19.19.2=Connect -- test BLOCKED | 0.00s |

### SC04_table_counts: Verify MAC table counts and forwarding continuity

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight | FAIL | [FAIL] Zero EVPN peers ESTABLISHED (3 configured): 2.2.2.2=Connect, 5.5.5.5=Connect, 19.19.19.2=Connect -- test BLOCKED | 0.00s |
