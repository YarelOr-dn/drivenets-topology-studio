# FlowSpec VPN HA Test Report (SW-236398)

Device: YOR_CL_PE-4
Mode: cluster (CL-86,)
Run: 2026-03-01T22:40:52.340539
Route source: preexisting
Spirent traffic: Not available

## 4-Layer Summary

| Test | Name | Control-Plane | Datapath (NCP) | Traffic (Spirent) | Packet (XRAY) | Recovery | Verdict |
|------|------|--------------|----------------|-------------------|---------------|----------|---------|
| test_01 | RIB Manager Process Restart | PASS | PASS (0/0) | N/A | SKIP | 1.2s | PASS |

**Result: 1 PASS / 0 WARNING / 0 FAIL / 0 SKIP (out of 1 tests)**

Traffic verification: Spirent not available (control-plane + datapath only)
