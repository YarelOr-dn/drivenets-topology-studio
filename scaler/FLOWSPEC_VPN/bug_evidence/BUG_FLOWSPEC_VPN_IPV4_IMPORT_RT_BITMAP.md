# BUG: IPv4 FlowSpec-VPN Routes Not Imported into VRF — RT Bitmap Not Populated

| Field | Value |
|-------|-------|
| **Date** | 2026-02-25 |
| **Devices** | RR-SA-2 (receiving PE-1 routes) |
| **Image (discovered)** | 26.1.0.24_priv (build on `easraf/flowspec_vpn/wbox_side` branch) |
| **Branch** | `easraf/flowspec_vpn/wbox_side` |
| **Severity** | Critical — complete feature failure for IPv4 FlowSpec-VPN import |
| **Component** | bgpd — VPN import path (`bgp_service.c`) |
| **Jira** | TBD |

## Retest History

| Date | Image (full path) | Build | Result | Notes |
|------|-------------------|-------|--------|-------|
| 2026-02-25 | 26.1.0.24_priv.easraf_flowspec_vpn_wbox_side | 24 | BUG PRESENT | Initial discovery with `debug bgp import` |

## One-Line Summary

`bgp_service_fill_import_vpn_bitmap_per_type` never finds a matching RT for IPv4 FlowSpec-VPN routes during VRF import evaluation, despite the VRF having the correct `import-vpn route-target` configured for `ipv4-flowspec`. IPv6 FlowSpec-VPN import works correctly with the same code path.

## Expected Results

When a VRF is configured with `import-vpn route-target` for `ipv4-flowspec` and received FlowSpec-VPN routes carry a matching RT, the routes should be imported into the VRF, installed in the zebra FlowSpec DB, programmed into TCAM, and reflected to iBGP peers.

## Actual Results

IPv4 FlowSpec-VPN routes are received into the global VPN table (12,000 routes accepted) but never imported into any VRF. The import handler evaluates each route but the RT bitmap lookup silently returns no match. Zero routes reach zebra, zero are installed in TCAM, and zero are reflected (AdjOut=0).

## Steps to Reproduce

1. Configure any non-default VRF with `import-vpn route-target <RT>` under `address-family ipv4-flowspec`
2. Receive IPv4 FlowSpec-VPN (SAFI 134) routes from a BGP peer carrying the matching RT as an extended community
3. Observe `show bgp ipv4 flowspec-vpn summary` — routes are accepted (PfxAccepted > 0)
4. Observe `show dnos-internal routing rib-manager database flowspec` — IPv4 table size is 0
5. Observe `show system npu-resources resource-type flowspec` — IPv4 Rules installed is 0
6. Compare with IPv6 FlowSpec-VPN using the same setup — IPv6 imports and installs correctly

## Test Setup — VRF ZULU on RR-SA-2

```
network-services
  vrf
    instance ZULU
      interface bundle-100.216
      protocols
        bgp 123
          route-distinguisher 2.2.2.2:112
          router-id 2.2.2.2
          address-family ipv4-flowspec
            export-vpn route-target 1234567:301
            import-vpn route-target 300:300,1234567:301       ← RT 300:300 should match
          !
          address-family ipv6-flowspec
            export-vpn route-target 1234567:401
            import-vpn route-target 1234567:401                ← RT 1234567:401 matches ✓
          !
```

Injected routes from PE-1 (ExaBGP → PE-1 → RR-SA-2):
- **IPv4 FlowSpec-VPN:** 12,000 routes, RD `1.1.1.1:200`, RT `300:300`, action `rate-limit 0`
- **IPv6 FlowSpec-VPN:** 4,000 routes, RD `1.1.1.1:200`, RT `1234567:401`, action `rate-limit 0`

## Symptom — Raw Show Command Outputs

### `show bgp ipv4 flowspec-vpn summary` (25-Feb-2026 21:07:57)

```
  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  1.1.1.1         4    1234567      58223      53891    0     0       0 00:00:25               12000
  4.4.4.4         4    1234567       9238       9433    0     0       0 00:17:10                   0
```

**12,000 routes received from PE-1 (1.1.1.1), AdjOut=0 toward PE-4 (4.4.4.4).**

### `show system npu-resources resource-type flowspec` (25-Feb-2026 21:08:02)

```
| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 0     | 0                     | 0                      | 0/12000                      | 4001                  | 4000                   | 4000/4000                    |
```

**IPv4: 0 received by NCP, 0 installed. IPv6: 4000 installed (full capacity).**

### `show dnos-internal routing rib-manager database flowspec` (25-Feb-2026 21:08:05)

```
VRF: default
IPv4 Flowspec table (total size: 0):
IPv6 Flowspec table (total size: 4000):
```

**IPv4 FlowSpec never reached zebra. IPv6 FlowSpec is fully present.**

## Raw Trace Evidence

### Bestpath Chain — `bgpd_traces` (25-Feb-2026 21:07)

```
2026-02-25T21:07:28.967078 [INFO] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb]
  On vrf 0, bgpid 1(default): Finished bestpath marker IPv4 Flowspec-VPN after 12000 steps

2026-02-25T21:07:29.023014 [INFO] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb]
  On vrf 0, bgpid 1(default): Finished bestpath marker IPv6 Flowspec-VPN after 4000 steps

2026-02-25T21:07:29.036029 [INFO] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb]
  On vrf 4, bgpid 3(ZULU): Finished bestpath marker IPv6 Flowspec after 4000 steps   ← IPv6 IMPORTED ✓

                            *** NO "vrf 4 (ZULU) IPv4 Flowspec" bestpath marker ***   ← IPv4 NEVER IMPORTED ✗
```

After VPN table bestpath, IPv6 immediately triggers VRF ZULU import (4000 steps). IPv4 never does.

Additional IPv4 FlowSpec-VPN bestpath batches on vrf 0 (post-import re-evaluation):
```
21:07:31.479 vrf 0: Finished bestpath marker IPv4 Flowspec-VPN after 3168 steps
21:07:31.516 vrf 0: Finished bestpath marker IPv4 Flowspec-VPN after 2636 steps
21:07:31.553 vrf 0: Finished bestpath marker IPv4 Flowspec-VPN after 2196 steps
21:07:31.586 vrf 0: Finished bestpath marker IPv4 Flowspec-VPN after 2304 steps
21:07:31.629 vrf 0: Finished bestpath marker IPv4 Flowspec-VPN after 1696 steps
```

All on vrf 0 (global VPN table). None on vrf 4 (ZULU). The routes stay in the VPN table and are never imported.

### Import Debug Traces — `debug bgp import` enabled (25-Feb-2026 21:07)

#### IPv6 FlowSpec-VPN — Full Import Sequence Per Route (WORKING)

```
2026-02-25T21:07:31.751435 [DEBUG] [bgp_service.c:1331:bgp_service_import_handler_common]
  Import re-evaluate RN 1.1.1.1:200:DstPrefix:=2001:db8:1a::/48,SrcPrefix:=*

2026-02-25T21:07:31.751435 [DEBUG] [bgp_service.c:1337:bgp_service_import_handler_common]
  Checking route: key 1.1.1.1:200:DstPrefix:=2001:db8:1a::/48,SrcPrefix:=* ri 0x7f1191de2e20

2026-02-25T21:07:31.751435 [DEBUG] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type]
  Found rt_node 0x7f11c4e03670 for 1234567L:401                              ← RT MATCH FOUND ✓

2026-02-25T21:07:31.751435 [DEBUG] [bgp_service.c:1431:bgp_service_import_handler_common]
  Checking bgp_inst_id 3 policy                                               ← VRF ZULU selected ✓

2026-02-25T21:07:31.751437 [DEBUG] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy]
  Import policy for route DstPrefix:=2001:db8:1a::/48 peer 1.1.1.1 vrf ZULU returned PERMIT  ← Policy PERMIT ✓

2026-02-25T21:07:31.751438 [DEBUG] [bgp_vrf.c:1409:bgp_service_mark_for_remove_import_vpn_route_default_vrf]
  About to remove previously imported if exist. Source RI 0x7f1191de2e20 on vrf 4(ZULU)  ← Import proceeds ✓
```

This 6-step sequence repeats for all 4,000 IPv6 FlowSpec-VPN routes.

#### IPv4 FlowSpec-VPN — Truncated Import Sequence (BROKEN)

```
2026-02-25T21:07:28.847687 [DEBUG] [bgp_service.c:1331:bgp_service_import_handler_common]
  Import re-evaluate RN 1.1.1.1:200:DstPrefix:=10.13.168.0/24,SrcPrefix:=*

2026-02-25T21:07:28.848071 [DEBUG] [bgp_service.c:1337:bgp_service_import_handler_common]
  Checking route: key 1.1.1.1:200:DstPrefix:=10.13.139.0/24,SrcPrefix:=* ri 0x...

                   *** NO "Found rt_node" ***     ← RT lookup returns EMPTY
                   *** NO "Checking bgp_inst_id" *** ← No VRF selected
                   *** NO "Import policy" ***      ← No policy check
                   *** NO "About to remove" ***    ← No import

2026-02-25T21:07:28.850300 [DEBUG] [bgp_service.c:1331:bgp_service_import_handler_common]
  Import re-evaluate RN 1.1.1.1:200:DstPrefix:=10.12.139.0/24,SrcPrefix:=*   ← Skips to next route
```

This 2-step truncated sequence (evaluate + skip) repeats for all 12,000 IPv4 FlowSpec-VPN routes.

### RT Bitmap Lookup Proof

```
# IPv6 RT found in bitmap (many matches):
show file traces routing_engine/bgpd_traces | include rt_node | include 1234567
  → Found rt_node 0x7f11c4e03670 for 1234567L:401   (appears for every IPv6 route)

# IPv4 RT NEVER found in bitmap:
show file traces routing_engine/bgpd_traces | include 21:07 | include regex "rt_node.*300"
  → EMPTY (zero results)
```

The function `bgp_service_fill_import_vpn_bitmap_per_type` (bgp_service.c:933) finds RT `1234567:401` for every IPv6 route but NEVER finds RT `300:300` (or `1234567:301`) for any IPv4 route.

### rib-manager Errors (earlier in session)

```
2026-02-25T19:10:22 [ERROR] [zebra_flowspec_db.c:181:destroy_rn_for_nh_tracking]
  Got NULL parameter!
```

Occurred during cleanup of old FlowSpec entries, before the BGP re-establishment.

## Comparison Table

| Aspect | IPv4 FlowSpec-VPN | IPv6 FlowSpec-VPN |
|--------|-------------------|-------------------|
| Routes received (PfxAccepted) | 12,000 | 4,000 |
| VPN bestpath (vrf 0) | 12,000 steps ✓ | 4,000 steps ✓ |
| Import handler called | Yes (12K evaluations) | Yes (4K evaluations) |
| `Found rt_node` in bitmap | **NEVER** | Always (`1234567L:401`) |
| VRF ZULU bestpath (vrf 4) | **Never runs** | 4,000 steps ✓ |
| Zebra FlowSpec DB | 0 | 4,000 |
| TCAM installed | 0/12,000 | 4,000/4,000 |
| AdjOut to PE-4 | 0 | 4,000 |
| VRF import-vpn RT config | `300:300,1234567:301` | `1234567:401` |
| Route carries RT | `300:300` | `1234567:401` |

## Code-Level Root Cause

### Phase 5 Code Analysis (branch: `easraf/flowspec_vpn/wbox_side`)

**All import pipeline code is symmetric between IPv4 and IPv6 FlowSpec.** No AFI-specific branching or missing code paths.

#### Key files and functions analyzed:

| Function | File:Line | Purpose |
|----------|-----------|---------|
| `bgp_service_fill_import_vpn_bitmap_per_type` | `bgp_service.c:923-939` | RT lookup in hash, indexes `import_candidate[dst_afi_safi]` |
| `bgp_service_import_handler_common` | `bgp_service.c:1312-1402` | Per-route import evaluation, calls bitmap fill |
| `bgp_service_fill_candidate_import_vpn_bitmap` | `bgp_service.c:987-1048` | Iterates route's ecommunities, calls AF_OPS fill |
| `bgp_service_handle_import_rt_add` | `bgp_service.c:2195-2242` | RT registration into hash (called at config time) |
| `import_export_rt` | `bgp_vty.c:26023-26092` | VTY handler for `import-vpn route-target` |
| `bgp_vrf_rt_node_alloc` | `bgp_vrf.c:36-56` | RT node creation, inits `import_candidate[V4_FLOWSPEC]` |
| `bgp_init_specific_non_default_vrf` | `bgpd.c:7238-7257` | VRF init, creates `import_vpn.rt_ecom` for V4/V6 FlowSpec |

#### Symmetry verification:

| Component | V4_FLOWSPEC | V6_FLOWSPEC |
|-----------|:-:|:-:|
| AF_OPS `fill_import_bitmap_per_rt` | `_vpn` (bgpd.c:1168) | `_vpn` (bgpd.c:1689) |
| VTY `import-vpn route-target` installed | `BGP_IPV4_FLOWSPEC_NODE` (bgp_vty.c:31084) | `BGP_IPV6_FLOWSPEC_NODE` (bgp_vty.c:31093) |
| VRF `import_vpn.rt_ecom` init | `ecommunity_new()` (bgpd.c:7244) | `ecommunity_new()` (bgpd.c:7245) |
| RT node `import_candidate[]` | initialized (bgp_vrf.c:50) | initialized (bgp_vrf.c:51) |

**Conclusion:** The code is designed to work identically for both. The asymmetric failure is NOT due to missing code paths.

#### Bug in `import_export_rt()` — no rollback on failure:

```c
// bgp_vty.c:26023-26092
static int import_export_rt(...)
{
    // Step 1: Add RT to rt_list FIRST (this is what "show config" reads)
    listnode_add_unique_str(rt_list, rt_str);

    // Step 2: Register RT in internal hash
    ret = bgp_service_add_rt(bgp, afi, safi, rt_type, ecom_val);
    // If bgp_service_add_rt FAILS → rt_list still has the RT
    // → "show config" shows it, but bgpd's hash does not
}
```

`bgp_service_handle_import_rt_add` has three failure paths, ALL of which silently leave the RT in `rt_list` without registering it in the hash:
1. `bgp_rt_node_get()` returns NULL
2. `afi_safi_data[afi_safi]` is NULL
3. `ecommunity_add_val()` fails

**Root cause:** During initial config application at boot, `import-vpn route-target 300:300` under `ipv4-flowspec` gets added to `rt_list` (visible in `show config`), but `bgp_service_add_rt()` fails silently for IPv4 FlowSpec. The RT is never registered in the VPN import RT hash. IPv6 FlowSpec registration succeeds (different timing or RT encoding).

**Confirmation test:** Remove and re-add `import-vpn route-target 300:300` under `ipv4-flowspec` at runtime on the device. If routes then get imported, it proves the initial config application failed.

## Related Bugs

- **BUG_FLOWSPEC_REDIRECT_IP_UNREACHABLE_VRF** — Different issue (redirect-IP NH resolution), but same VRF FlowSpec-VPN pipeline
- **BUG_CONFIG_DESYNC_BGP_NETWORK_SERVICES** — Likely related. Code analysis proves `import_export_rt()` adds RT to `rt_list` (show config) BEFORE `bgp_service_add_rt()` registers it in the hash, and does NOT rollback on failure. This is the same class of bug: config shows settings that bgpd hasn't internally registered

## Topology

See `BUG_FLOWSPEC_VPN_IPV4_IMPORT_RT_BITMAP.topology.json` in this directory.
Load in topology app: Topologies → Load Debug-DNOS... or File → Load from File.
