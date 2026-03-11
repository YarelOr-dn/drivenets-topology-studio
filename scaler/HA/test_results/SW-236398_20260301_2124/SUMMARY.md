# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Mode: cluster (CL-86,)
Run: 2026-03-01T21:34:25.930699
Route source: preexisting
Spirent traffic: Not available

## 4-Layer Summary

| Test | Name | Control-Plane | Datapath (NCP) | Traffic (Spirent) | Packet (XRAY) | Recovery | Verdict |
|------|------|--------------|----------------|-------------------|---------------|----------|---------|
| test_09 | NCC Failover by Cold Restart (Power Reset) | ERROR | ? (?/?) | N/A | SKIP | - | ERROR |
| test_12 | Clear BGP Neighbors Multiple Times | PASS | PASS (0/0) | N/A | PASS (2pkts) | 1.7s | PASS |
| test_13 | NCC Switchover with FlowSpec Admin-Disabled | PASS | PASS (0/0) | N/A | PASS (2pkts) | 16.2s | PASS |
| test_14 | LOFD Simulation (NCF Admin-Disable) | FAIL | ? (?/?) | N/A | SKIP | - | FAIL |
| test_15 | Multiple HA Events in Sequence | FAIL | PASS (0/0) | N/A | SKIP | 90.0s | FAIL |

**Result: 2 PASS / 0 WARNING / 2 FAIL / 0 SKIP (out of 5 tests)**

Traffic verification: Spirent not available (control-plane + datapath only)
