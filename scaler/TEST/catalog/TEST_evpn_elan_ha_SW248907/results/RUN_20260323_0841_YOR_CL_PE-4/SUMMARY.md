# EVPN (ELAN) SI -- EVPN High-Availability

**Test ID:** TEST_evpn_elan_ha_SW248907
**Source:** jira:SW-248907
**Device:** YOR_CL_PE-4
**Run:** 2026-03-23 08:42:51
**Overall:** ERROR
**Total elapsed:** 67.5s

## Test Verdict: TEST_evpn_elan_ha_SW248907 on YOR_CL_PE-4
**Overall: ERROR** | Elapsed: 67.5s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC06_neighbour_manager_restart | ERROR | exception=ERROR | -- | -- |

### SC06_neighbour_manager_restart: Process Restart -- neighbor-manager

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| exception | ERROR | Inter-scenario guard FAILED: 0 MACs in EVPN table at start of SC06_neighbour_manager_restart. Prior scenario may not have recovered properly. | 0.00s |
