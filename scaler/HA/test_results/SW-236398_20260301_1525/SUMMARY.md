# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Run: 2026-03-01T15:52:29.261887
Route source: preexisting

## Summary

| Test | Name | Verdict | Recovery (s) |
|------|------|---------|--------------|
| test_01 | RIB Manager Process Restart | PASS | 10.148210048675537 |
| test_02 | BGPd Process Restart | PASS | 17.336108207702637 |
| test_03 | wb_agent Process Restart | PASS | 10.147656917572021 |
| test_04 | BGP Container Restart | PASS | 35.169668197631836 |
| test_05 | NCP Container Restart | PASS | 17.396138429641724 |
| test_06 | Cold System Restart | PASS | 10.068960189819336 |
| test_07 | Warm System Restart | PASS | 17.347219705581665 |
| test_08 | NCC Switchover | PASS | 10.151779413223267 |
| test_09 |  | SKIP | - |
| test_10 |  | SKIP | - |
| test_11 | BGP Graceful Restart | PASS | 10.068529844284058 |
| test_12 | Clear BGP Neighbors Multiple Times | PASS | 17.253922939300537 |
| test_13 | NCC Switchover with FlowSpec Admin-Disabled | PASS | 10.073538541793823 |
| test_14 |  | SKIP | - |
| test_15 | Multiple HA Events in Sequence | PASS | 10.067588090896606 |

**Result: 12/12 passed**
