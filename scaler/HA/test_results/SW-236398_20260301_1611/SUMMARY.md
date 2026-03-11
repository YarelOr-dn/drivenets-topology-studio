# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Mode: cluster (CL-86,)
Run: 2026-03-01T16:46:40.513825
Route source: preexisting

## Summary

| Test | Name | Verdict | Recovery (s) |
|------|------|---------|--------------|
| test_01 | RIB Manager Process Restart | PASS | 10.148194313049316 |
| test_02 | BGPd Process Restart | PASS | 10.078785419464111 |
| test_03 | wb_agent Process Restart | PASS | 35.17204713821411 |
| test_04 | BGP Container Restart | PASS | 35.17210578918457 |
| test_05 | NCP Container Restart | PASS | 10.072102546691895 |
| test_06 | Cold System Restart | PASS | 10.15179705619812 |
| test_07 | Warm System Restart | PASS | 10.147721767425537 |
| test_08 | NCC Switchover | PASS | 14.180146932601929 |
| test_09 |  | SKIP | - |
| test_10 |  | SKIP | - |
| test_11 | BGP Graceful Restart | PASS | 35.16761326789856 |
| test_12 | Clear BGP Neighbors Multiple Times | PASS | 35.16164207458496 |
| test_13 | NCC Switchover with FlowSpec Admin-Disabled | PASS | 10.071938753128052 |
| test_14 |  | SKIP | - |
| test_15 | Multiple HA Events in Sequence | PASS | 13.187741041183472 |

**Result: 12/12 passed**
