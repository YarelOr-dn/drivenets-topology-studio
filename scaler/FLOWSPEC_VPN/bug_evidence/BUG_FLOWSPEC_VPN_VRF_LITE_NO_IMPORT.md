# BUG: FlowSpec redirect-to-rt Cannot Target VRF Without RD (VRF-Lite)

| Field | Value |
|-------|-------|
| **Date** | 2026-02-23 |
| **Device** | PE-1 (YOR_PE-1_priv_26.1.0.24) |
| **Image** | `26.1.0.24_priv.easraf_flowspec_vpn_wbox_side_26` |
| **Branch** | `easraf/flowspec_vpn/wbox_side` |
| **Severity** | Feature gap — architect says this must work |
| **Component** | bgpd — `bgp_service.c` redirect target selection (`match_vrf_from_rt`) |
| **Related SW** | SW-240206 (RT-Redirect dynamic re-evaluation) |

## Retest History

| Date | Image (full path) | Build | Result | Notes |
|------|-------------------|-------|--------|-------|
| 2026-02-23 | 26.1.0.24_priv.easraf_flowspec_vpn_wbox_side_26 | build 26 | BUG PRESENT | Initial discovery and evidence |

## One-Line Summary

FlowSpec `redirect-to-rt` action cannot select a VRF without Route Distinguisher (VRF-Lite) as the redirect target, even when the VRF-Lite has a matching `import-vpn route-target` configured. The redirect target selection logic (`match_vrf_from_rt`) requires `BGP_CONFIG_RD` and excludes VRF-Lite entirely.

## Expected Results

A VRF without RD (VRF-Lite) that has `import-vpn route-target X:Y` configured should be a valid redirect target for FlowSpec rules with `redirect X:Y` — traffic matching the FlowSpec rule should be redirected into the VRF-Lite, verified via `show flowspec instance vrf <name> ipv4` showing `flowspec-redirect-vrf-rt: <vrf-name>`.

## Actual Results

The redirect target selection (`match_vrf_from_rt` at `bgp_service.c:2808`) skips VRF-Lite because `BGP_CONFIG_RD` is not set. The VRF-Lite is never considered as a candidate redirect target. Only VRFs with RD are eligible. As a secondary effect, VPN import (Gate 1) also rejects VRF-Lite, but the primary bug is the redirect target exclusion.

## Steps to Reproduce

1. Configure two VRFs with identical `import-vpn route-target` — one with RD (control), one without RD (VRF-Lite)
2. Inject a FlowSpec-VPN rule with `redirect X:Y` matching the RT via any BGP peer
3. Observe `show flowspec instance vrf <with-rd> ipv4` — redirect target is the with-RD VRF (control passes)
4. Observe `show flowspec instance vrf <no-rd> ipv4` — "No flows found" (bug: VRF-Lite excluded as redirect target)
5. Check traces: `show file traces routing_engine/bgpd_traces | include "Found match VRF"` — only the with-RD VRF appears as a match candidate

## Test Setup

Two VRFs configured identically except for RD:

```
! VRF with RD (control — this WILL import the rule)
network-services
  vrf
    instance TEST_WITH_RD
      protocols
        bgp 1234567
          route-distinguisher 1.1.1.1:888
          router-id 1.1.1.1
          address-family ipv4-flowspec
            import-vpn route-target 888:888
          !
          address-family ipv4-unicast
            import-vpn route-target 888:888
          !
        !
      !
    !
    instance TEST_NO_RD
      protocols
        bgp 1234567
          router-id 1.1.1.1
          address-family ipv4-flowspec
            import-vpn route-target 888:888
          !
          address-family ipv4-unicast
            import-vpn route-target 888:888
          !
        !
      !
    !
  !
!
```

Injected route via ExaBGP:
```
announce flow route rd 1.1.1.1:888 destination 172.16.99.0/24 redirect 888:888 extended-community [ target:888:888 ]
```

## Symptom — Show Command Outputs

### `show bgp instance vrf TEST_WITH_RD` (11:53:36 IST)

```
BGP IPv4 Flowspec, local router ID is 1.1.1.1

 U*>  DstPrefix:=172.16.99.0/24,SrcPrefix:=*
         00:00:19,     AS path: 65200 i, next hop: N/A, from: 100.64.6.134

Displayed 1 out of 1 total prefixes, 1 out of 1 total paths
```

**Result: Rule imported successfully.**

### `show bgp instance vrf TEST_NO_RD` (11:53:39 IST)

```
No BGP IPv4 Unicast prefixes displayed, 0 exist
No BGP IPv4 Flowspec prefixes displayed, 0 exist
No BGP IPv6 Unicast prefixes displayed, 0 exist
No BGP IPv6 Flowspec prefixes displayed, 0 exist
No BGP EVI prefixes displayed, 0 exist
```

**Result: No FlowSpec rule imported. 0 prefixes.**

### `show flowspec instance vrf TEST_WITH_RD ipv4` (11:53:42 IST)

```
Address-family: IPv4

    Flow: DstPrefix:=172.16.99.0/24,SrcPrefix:=*
        Actions: flowspec-redirect-vrf-rt: TEST_WITH_RD  888:888
        Match packet counter: 0
```

**Result: Rule installed in datapath, redirect target = TEST_WITH_RD.**

### `show flowspec instance vrf TEST_NO_RD ipv4` (11:53:45 IST)

```
Address-family: IPv4

    No flows found.
```

**Result: No flows. VRF-Lite completely excluded.**

### `show bgp ipv4 flowspec-vpn rd 1.1.1.1:888` (11:53:53 IST)

```
Route Distinguisher: 1.1.1.1:888

 U*>  DstPrefix:=172.16.99.0/24,SrcPrefix:=*
         00:00:35,     AS path: 65200 i, next hop: N/A, from: 100.64.6.134

Displayed 1 out of 1 total prefixes, 1 out of 1 total paths
```

**Result: Route exists in global VPN table.**

## Topology

```
  ExaBGP ──────── eBGP FlowSpec-VPN ──────── PE-1
  (100.64.6.134)   AS 65200 → 1234567       (1.1.1.1)
      redirect 888:888                              │
                         ┌──────────────────────────┴──────────────────────────┐
                         │  TEST_WITH_RD (RD 1.1.1.1:888)  │  TEST_NO_RD (VRF-Lite)  │
                         │  RT 888:888 → redirect target ✓ │  RT 888:888 → BUG: not a│
                         │  traffic redirected here        │  redirect target candidate│
                         └───────────────────────────────────────────────────┘
```

<details>
<summary>Topology JSON (load via Topologies → Load Debug-DNOS... or File → Load)</summary>

See `BUG_FLOWSPEC_VPN_VRF_LITE_NO_IMPORT.topology.json` in this directory.

</details>

## Raw Trace Evidence (debug bgp import/export enabled)

### Full timeline at `11:53:17.948` — route injection processing

```
11:53:17.948528  [DEBUG] bgp_service.c:1331  Import re-evaluate RN 1.1.1.1:888:DstPrefix:=172.16.99.0/24,SrcPrefix:=*
11:53:17.948540  [DEBUG] bgp_service.c:1337  Checking route: key 1.1.1.1:888:DstPrefix:=172.16.99.0/24,SrcPrefix:=* ri 0x7f9087c06838
11:53:17.948546  [DEBUG] bgp_service.c:933   Found rt_node 0x7f909b603af0 for 888:888
11:53:17.948562  [DEBUG] bgp_service.c:1431  Checking bgp_inst_id 4 policy          ← TEST_WITH_RD (inst_id 4)
11:53:17.948567  [DEBUG] bgp_service.c:846   Import policy for route ... vrf TEST_WITH_RD returned PERMIT
11:53:17.948573  [DEBUG] bgp_vrf.c:1409      About to remove previously imported if exist. Source RI ... on vrf 19(TEST_WITH_RD)
11:53:17.948580  [DEBUG] bgp_service.c:1416  *** Cancel import due to invalid service state ***   ← TEST_NO_RD REJECTED HERE
11:53:17.948582  [DEBUG] bgp_vrf.c:1409      About to remove previously imported if exist. Source RI ... on vrf 20(TEST_NO_RD)
11:53:17.948599  [INFO]  bgp_chain.c:373     Finished bestpath marker IPv4 Flowspec-VPN after 1 steps
11:53:17.948730  [NOTICE] bgp_chain.c:3777   default IPv4 Flowspec-VPN: Chain is done!
11:53:17.948773  [DEBUG] bgp_service.c:2840  Found match VRF TEST_WITH_RD (inst_id:19), for rt:888:888   ← redirect target selection
11:53:17.948802  [DEBUG] bgp_service.c:3944  Consider prefix ... on IPv4 Flowspec bgp id 4 instance-id 19(TEST_WITH_RD)
11:53:17.948816  [INFO]  bgp_chain.c:373     Finished bestpath marker IPv4 Flowspec after 1 steps
11:53:17.948818  [NOTICE] bgp_chain.c:3777   TEST_WITH_RD IPv4 Flowspec: Chain is done!
```

### Key observations from traces:

1. **Line .948546**: RT `888:888` matched — `Found rt_node` for both VRFs (both have the RT configured)
2. **Line .948562**: `bgp_inst_id 4` (TEST_WITH_RD) is checked first → **PERMIT** (import gate passes)
3. **Line .948580**: `bgp_inst_id 5` (TEST_NO_RD) hits "Cancel import due to invalid service state" — VPN import gate (Gate 1) rejects VRF-Lite (secondary effect)
4. **Line .948773 — PRIMARY BUG**: Redirect target `match_vrf_from_rt()` only finds TEST_WITH_RD — **TEST_NO_RD is excluded as a redirect target** because `bgp_service.c:2808` requires `BGP_CONFIG_RD`. This is the core bug: VRF-Lite cannot be the destination VRF for `redirect-to-rt` traffic

## Code-Level Root Cause

### PRIMARY — Redirect Target Selection (`bgp_service.c:2807-2811`)

```c
// A "VRF Light" (RD is not configured) can not be a candidate to have traffic redirected to it.
if(!tmp_matched_vrf || !bgp_config_check (tmp_matched_vrf, BGP_CONFIG_RD))
{
    continue;   // ← VRF-Lite excluded from redirect targets
}
```

This is the core bug. `match_vrf_from_rt()` iterates over VRFs with matching RT but **skips any VRF without `BGP_CONFIG_RD`**. A VRF-Lite with `import-vpn route-target 888:888` is never considered as a candidate for `redirect 888:888`, even though the RT matches.

**What needs to change:** `match_vrf_from_rt()` should consider VRF-Lite as a valid redirect target when it has a matching `import-vpn route-target`. The RD is only needed for VPN export — not for being a redirect destination.

### SECONDARY — VPN Import Gate (`bgp_service.c:1133-1136`)

```c
bool bgp_service_import_export_invalid_vrf(struct bgp *dst_bgp)
{
    return (((dst_bgp->vrf_id == VRF_UNKNOWN)) || (!bgp_config_check (dst_bgp, BGP_CONFIG_RD)));
}
```

This gate also rejects VRF-Lite during VPN route import (prevents the FlowSpec-VPN route from being imported into the VRF-Lite's BGP RIB). This is a secondary effect — even if redirect target selection were fixed, the route still wouldn't be imported into VRF-Lite's RIB. Both gates need to be relaxed for the full fix.

Note: The RD is still needed for VPN export (you can't export a route without an RD). But for **redirect target** and **import-only** use cases, the RD requirement should be relaxed.

## Condition for Bug to Trigger

1. FlowSpec-VPN rule with `redirect X:Y` (redirect-to-rt action) is received
2. A VRF-Lite (no `route-distinguisher`) has `import-vpn route-target X:Y` configured — matching the redirect RT
3. The redirect target selection (`match_vrf_from_rt`) skips VRF-Lite because `BGP_CONFIG_RD` is not set

## Reproduction Steps

1. Configure two VRFs with identical `import-vpn route-target X:Y` — one with RD (control), one without RD (VRF-Lite)
2. Inject a FlowSpec-VPN rule with `redirect X:Y` matching the RT
3. Verify: `show flowspec instance vrf <with-rd> ipv4` — shows `flowspec-redirect-vrf-rt: <with-rd>` (control: VRF with RD selected as redirect target)
4. Verify: `show flowspec instance vrf <no-rd> ipv4` — "No flows found" (bug: VRF-Lite excluded from redirect targets)
5. Check traces: `show file traces routing_engine/bgpd_traces | include "Found match VRF"` — only the with-RD VRF appears as a match candidate

## Comparison Table

| Aspect | TEST_WITH_RD | TEST_NO_RD |
|--------|-------------|------------|
| RD | `1.1.1.1:888` | none |
| ipv4-flowspec import-vpn RT | `888:888` | `888:888` |
| ipv4-unicast import-vpn RT | `888:888` | `888:888` |
| BGP_CONFIG_RD set | yes | **no** |
| **Redirect target candidate** | **yes** (`match_vrf_from_rt` found it) | **NO — excluded by RD check (PRIMARY BUG)** |
| Import gate result | pass (PERMIT) | rejected ("Cancel import due to invalid service state") |
| `show flowspec instance vrf ... ipv4` | `redirect-vrf-rt: TEST_WITH_RD` | **"No flows found"** |
| FlowSpec rule in BGP RIB | 1 prefix | 0 prefixes |

## Related Bugs

- **SW-240206**: FlowSpec RT redirect dynamic re-evaluation — Ilana's fix addresses trigger mechanism but does NOT relax the RD requirement
- **SW-206889**: Redirect to default VRF from non-default VRF — not supported (by design)
