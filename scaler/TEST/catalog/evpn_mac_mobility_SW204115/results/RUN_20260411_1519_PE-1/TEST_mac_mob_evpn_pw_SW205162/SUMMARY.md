# TEST_mac_mob_evpn_pw_SW205162

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-11T15:21:10+00:00
**Overall:** FAIL
**Elapsed:** 100.4s

## Test Verdict: TEST_mac_mob_evpn_pw_SW205162 on PE-1
**Overall: FAIL** | Elapsed: 100.4s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_evpn_to_pw | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC02_pw_to_evpn | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC03_sticky_evpn_to_pw | FAIL | preflight_smoke_test=FAIL | -- | -- |
| SC04_pw_to_sticky_evpn | FAIL | preflight_smoke_test=FAIL | -- | -- |

### SC01_evpn_to_pw: Non-sticky: remote EVPN -> PW; no RT change; not counted

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC02_pw_to_evpn: PW -> EVPN; accept; static entry

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC03_sticky_evpn_to_pw: Sticky EVPN RT-2 -> PW; IGNORE move (blackholing risk)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |

### SC04_pw_to_sticky_evpn: PW -> Sticky EVPN; accept; datapath static sticky

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in HA_TEST_ELAN mac-table after 10.0s. Check: DNAAS BD, DUT AC state, VLAN tags, Spirent port link. | 0.00s |
