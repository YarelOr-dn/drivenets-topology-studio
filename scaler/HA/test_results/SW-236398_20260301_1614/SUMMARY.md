# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Mode: cluster (CL-86,)
Run: 2026-03-01T16:51:23.257822
Route source: preexisting

## Summary

| Test | Name | Verdict | Recovery (s) |
|------|------|---------|--------------|
| test_01 | RIB Manager Process Restart | PASS | 10.160176038742065 |
| test_02 | BGPd Process Restart | PASS | 10.07213282585144 |
| test_03 | wb_agent Process Restart | PASS | 13.167534351348877 |
| test_04 | BGP Container Restart | PASS | 35.16814613342285 |
| test_05 | NCP Container Restart | PASS | 60.19493293762207 |
| test_06 | Cold System Restart | PASS | 14.200271844863892 |
| test_07 | Warm System Restart | PASS | 35.17173933982849 |
| test_08 | NCC Switchover | PASS | 10.149097204208374 |
| test_09 |  | SKIP | - |
| test_10 |  | SKIP | - |
| test_11 | BGP Graceful Restart | PASS | 17.236117362976074 |
| test_12 | Clear BGP Neighbors Multiple Times | PASS | 35.17579388618469 |
| test_13 | NCC Switchover with FlowSpec Admin-Disabled | PASS | 10.151757955551147 |
| test_14 |  | SKIP | - |
| test_15 | Multiple HA Events in Sequence | PASS | 10.151710033416748 |

**Result: 12/12 passed**
