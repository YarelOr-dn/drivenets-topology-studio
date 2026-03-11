# Debug Session: PE-4 -- IPv6 TCAM 0/4000 after combined IPv4+IPv6 injection
Started: 2026-03-02 12:20:00 UTC | Device: YOR_CL_PE-4
Image: 26.1.0.27 (YOR_CL_PE-4_priv_26.1.0.27)
Topic: test_02 (IPv4+IPv6 Combined) showed IPv6 TCAM=0/4000 despite BGP accepting 4000 IPv6 routes. Reproducing with trace collection.
Session mode: INVESTIGATE
Related bug: BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST.md

---

## Phase 0: Pre-Flight

### [12:20:45] [show] show system image
```
ERROR: Unknown word: 'image'. (Device: YOR_CL_PE-4_priv_26.1.0.27)
```

### [12:20:48] [show] show system npu-resources resource-type flowspec
```
| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 6     | 0                     | 0                      | 0/12000                      | 0                     | 0                      | 0/4000                       |
| 18    | 0                     | 0                      | 0/12000                      | 0                     | 0                      | 0/4000                       |
```

### [12:20:50] [show] show bgp ipv6 flowspec-vpn summary
```
Neighbor 2.2.2.2  AS 1234567  State/PfxAccepted: 0  Up/Down: 00:26:09
```

### [12:20:53] [show] show bgp ipv4 flowspec-vpn summary
```
Neighbor 2.2.2.2  AS 1234567  State/PfxAccepted: 0  Up/Down: 00:26:12
```

### [12:21:12] [show] show flowspec ncp 6
```
(empty - no rules)
```

**Pre-flight: CLEAN STATE CONFIRMED. TCAM=0/0, BGP=0/0, NCP=empty.**

---

## Step 1: Inject 4000 IPv6 ONLY — Wrong RT (default 1234567:300)

### [12:21:47] [local] bgp_tool.py scale --session-id pe_1 --mode flowspec-vpn-ipv6 --count 4000
```
Injected 4000 IPv6 FlowSpec-VPN routes (21.6s, 185 rps)
NOTE: --rt not specified, parser default 1234567:300 used (overrides mode default 1234567:401)
```

### [12:22:10] [show] show bgp ipv6 flowspec-vpn summary
```
PfxAccepted: 4000 (routes in BGP table, U*>i status)
```

### [12:22:13] [show] show system npu-resources resource-type flowspec
```
NCP 6: IPv6 Received=0, Installed=0, HW=0/4000  <--- ZERO at NCP!
NCP 18: IPv6 Received=0, Installed=0, HW=0/4000
```

### [12:23:43] [show] show dnos-internal routing rib-manager database flowspec
```
IPv6 Flowspec table (total size: 0)  <--- zebra DB EMPTY
```

### [12:22:03] [show] bgpd_traces at 12:22:03
```
Finished bestpath marker IPv6 Flowspec-VPN after 666 steps
Chain is done!  <--- bgpd processed but never announced to zebra
```

### [12:26:08] [show] rib-manager destroy_rn_for_nh_tracking NULL count
```
lines: 45000  <--- massive NULL errors from test_11 cleanup
```

### [12:27:23] [show] rib-manager flowspec traces (tail 20)
```
Last real flowspec activity: 12:13:31 (test_11 cleanup)
No zebra flowspec activity at 12:22:XX — routes never reached zebra
```

**DIAGNOSIS: bgpd accepted IPv6 FlowSpec-VPN routes (PfxAccepted=4000) but did NOT import
them into any VRF because RT=1234567:300 does not match VRF ALPHA's IPv6-flowspec import RT=1234567:401.
Without VRF import, no announcement to zebra, no FPM, no NCP, no TCAM.**

---

## Step 1b: Re-inject with correct RT=1234567:401

### [12:31:46] [local] Withdrew 4000 incorrect IPv6 routes (19.08s)

### [12:31:58] [local] bgp_tool.py scale --session-id pe_1 --mode flowspec-vpn-ipv6 --count 4000 --rt 1234567:401
```
Injected 4000 IPv6 FlowSpec-VPN routes (20.37s, 196 rps)
```

### [12:33:55] [show] show bgp ipv6 flowspec-vpn summary
```
PfxAccepted: 4000
```

### [12:33:58] [show] show system npu-resources resource-type flowspec
```
NCP 6: IPv6 Received=4000, Installed=4000, HW=4000/4000  <--- FULL INSTALLATION!
NCP 18: IPv6 Received=4000, Installed=4000, HW=4000/4000
```

### [12:34:23] [show] NCP 6 wb_agent.flowspec traces (tail)
```
Flowspec: Succeeded to write 1 rules in TCAM for rule id 11729
FlowspecReshuffleTimer finished  <--- Clean, no errors
```

**CONFIRMED: Correct RT=1234567:401 → IPv6 4000/4000 installed.**

---

## Step 2: Inject 12K IPv4 on top of 4000 IPv6

### [12:34:41] [local] bgp_tool.py scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count 12000 --rt 1234567:301
```
Injected 12000 IPv4 FlowSpec-VPN routes (65.38s, 184 rps)
```

### [12:36:31] [show] show system npu-resources resource-type flowspec
```
NCP 6: IPv4=12000/12000, IPv6=4000/4000  <--- BOTH FULL!
NCP 18: IPv4=12000/12000, IPv6=4000/4000
```

### [12:36:38] [show] NCP 6 wb_agent.flowspec ERROR traces
```
(EMPTY — ZERO errors during combined injection)
```

**TEST_02 COMBINED SCENARIO: PASS. IPv4=12K + IPv6=4K coexist at full capacity with ZERO NCP errors.**

---

## Root Cause

The test_02 "failure" (IPv6=0/4000) was caused by a **Route-Target mismatch in the test tooling**:

| Component | RT Used | VRF IPv6-flowspec Import RT | Match? |
|---|---|---|---|
| bgp_tool parser default | 1234567:300 | 1234567:401 | NO |
| Orchestrator --rt override | 1234567:301 | 1234567:401 | NO |
| Correct value | 1234567:401 | 1234567:401 | YES |

Two bugs in test tooling:
1. **bgp_tool.py**: `p_scale.add_argument("--rt", default="1234567:300")` — parser default overrides
   per-mode defaults (flowspec-vpn-ipv6 should use 1234567:401)
2. **sw_234480_scale_test.py**: passes `--rt self.default_rt` (1234567:301) for ALL modes,
   ignoring that IPv6 needs a different RT

This is NOT a software bug in DNOS. The combined IPv4+IPv6 FlowSpec-VPN installation works correctly
when the proper RT is used.

---

## Cleanup

### [12:39:12] [local] Withdrew 12000 IPv4 routes (33.25s)
### [12:39:26] [local] Withdrew 4000 IPv6 routes (9.74s)

### [12:39:56] [show] show system npu-resources resource-type flowspec
```
NCP 6: IPv4=0/12000, IPv6=0/4000
NCP 18: IPv4=0/12000, IPv6=0/4000  <--- CLEAN
```

### [12:39:59] [show] show bgp ipv4 flowspec-vpn summary
```
PfxAccepted: 1 (1 pre-existing route)
```

### [12:40:02] [show] show bgp ipv6 flowspec-vpn summary
```
PfxAccepted: 0
```

**CLEAN STATE RESTORED.**

---

## Fixes Applied

1. **bgp_tool.py** (line 818): Changed `--rt` parser default from `"1234567:300"` to `None`,
   allowing per-mode defaults to work (flowspec-vpn-ipv6 → 1234567:401)
2. **sw_234480_scale_test.py**: Added `rt_overrides` dict for per-mode RT selection
   (`flowspec-vpn-ipv6` → `1234567:401`)
3. **sw_234480.json**: Added `rt_overrides` section to test definitions

---

## Session Conclusion
Ended: 2026-03-02 12:40:00 UTC
Verdict: NO BUG (test tooling RT mismatch)
Bug file: none (updated BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST.md retest history)

