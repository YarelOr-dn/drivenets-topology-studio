# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Mode: cluster (CL-86,)
Run: 2026-03-01T16:12:54.198203
Route source: preexisting

## Summary

| Test | Name | Verdict | Recovery (s) |
|------|------|---------|--------------|
| test_01 | RIB Manager Process Restart | PASS | 10.071927785873413 |
| test_02 | BGPd Process Restart | PASS | 10.076081037521362 |
| test_03 | wb_agent Process Restart | PASS | 10.140079975128174 |
| test_04 | BGP Container Restart | PASS | 10.076105117797852 |
| test_05 | NCP Container Restart | PASS | 10.081157445907593 |
| test_06 | Cold System Restart | PASS | 10.06794285774231 |
| test_07 | Warm System Restart | PASS | 10.19578218460083 |
| test_08 | NCC Switchover | PASS | 10.149928331375122 |
| test_09 |  | SKIP | - |
| test_10 |  | SKIP | - |
| test_11 | BGP Graceful Restart | PASS | 10.07962417602539 |
| test_12 | Clear BGP Neighbors Multiple Times | PASS | 10.147833585739136 |
| test_13 | NCC Switchover with FlowSpec Admin-Disabled | PASS | 10.163723230361938 |
| test_14 |  | SKIP | - |
| test_15 | Multiple HA Events in Sequence | PASS | 10.07571029663086 |

**Result: 12/12 passed**
