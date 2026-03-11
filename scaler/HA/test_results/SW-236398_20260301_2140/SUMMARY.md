# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Mode: cluster (CL-86,)
Run: 2026-03-01T21:51:34.622539
Route source: preexisting
Spirent traffic: Not available

## 4-Layer Summary

| Test | Name | Control-Plane | Datapath (NCP) | Traffic (Spirent) | Packet (XRAY) | Recovery | Verdict |
|------|------|--------------|----------------|-------------------|---------------|----------|---------|
| test_09 | NCC Failover by Cold Restart (Power Reset) | PASS | PASS (0/0) | N/A | PASS (2pkts) | 17.5s | PASS |
| test_14 | LOFD Simulation (NCF Admin-Disable) | PASS | PASS (0/0) | N/A | PASS (2pkts) | 4.7s | PASS |
| test_15 | Multiple HA Events in Sequence | PASS | PASS (0/0) | N/A | PASS (2pkts) | 2.7s | PASS |

**Result: 3 PASS / 0 WARNING / 0 FAIL / 0 SKIP (out of 3 tests)**

Traffic verification: Spirent not available (control-plane + datapath only)
