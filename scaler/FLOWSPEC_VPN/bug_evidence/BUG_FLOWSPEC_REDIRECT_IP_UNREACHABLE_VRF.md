# BUG: FlowSpec Redirect-IP Next-Hop Always "Unreachable" in Non-Default VRF

**Date discovered**: 2026-02-18
**Devices tested**: YOR_PE-1, YOR_CL_PE-4
**Image**: `26.1.0.24_priv.easraf_flowspec_vpn_wbox_side_26` (build 26)
**Branch**: easraf/flowspec_vpn/wbox_side
**Severity**: Critical — redirect-ip action is completely non-functional in any non-default VRF
**Component**: rib-manager (zebra) → fib-manager protobuf interface

---

## Summary

When a FlowSpec rule with a **redirect-ip** action is installed in any **non-default VRF**, the redirect next-hop is always marked `(unreachable)` in NCP — even though the target IP is fully reachable in the VRF routing table.

The root cause: `rib-manager` internally resolves the redirect NH correctly (right VRF, right interface, right gateway), but the `ADD_NEXTHOP` protobuf message sent to `fib-manager` contains **no VRF context and no resolved forwarding information**. `fib-manager` receives only a bare IP address with `is_flowspec: true` and cannot resolve it.

The bug is **SAFI-independent** — it reproduces identically with SAFI 134 (FlowSpec-VPN) and SAFI 133 (plain FlowSpec), and regardless of how the target IP resolves (eBGP, static, connected, or MPLS/VPN).

---

## Expected Results

FlowSpec redirect-ip next-hop is marked `(reachable)` when the target IP exists as `best, fib` in the VRF routing table — verified via `show flowspec ncp <id>`.

## Actual Results

FlowSpec redirect-ip next-hop is always marked `(unreachable)` in any non-default VRF, regardless of SAFI, NH resolution method, or whether the target IP is reachable.

## Steps to Reproduce

1. Configure any non-default VRF with a reachable route to a target IP (via eBGP, static, connected, or L3VPN)
2. Inject a FlowSpec rule with `redirect-ip` action targeting that IP into the VRF
3. Verify `show route vrf <name> <redirect-ip>` returns `best, fib`
4. Observe `show flowspec ncp <id>` shows `(unreachable)` next to the redirect NH
5. Check `show file traces routing_engine/fibmgrd_traces | include is_flowspec` — the `ADD_NEXTHOP` protobuf has no `vrf_id` and no `nexthops` array

---

## Topology

```
ExaBGP (100.64.6.134, AS 65200)
  │
  │ eBGP: FlowSpec-VPN (SAFI 134) + plain FlowSpec (SAFI 133)
  │       Rule: match dst 100.100.100.1/32 src 16.16.16.0/30
  │       Action: redirect-ip 10.0.0.230
  │
PE-1 (1.1.1.1, AS 1234567) ─── iBGP ─── RR-SA-2 (2.2.2.2) ─── iBGP ─── PE-4 (4.4.4.4)
  │                                                                          │
  │ VRF ALPHA (vrf_id 16)                                     VRF ALPHA (vrf_id 104)
  │ ge400-0/0/5.1 (16.16.16.1/30)                   ge100-18/0/0.219 (49.49.49.4/28)
  │                                                                          │
CE (16.16.16.2, AS 65100)                                    CE (49.49.49.9, AS 65100)
  advertises 10.0.0.230/32 via eBGP                      imports 10.0.0.230/32 via L3VPN
```

<details>
<summary>Topology JSON (load via Topologies → Load Debug-DNOS... or File → Load)</summary>

See `BUG_FLOWSPEC_REDIRECT_IP_UNREACHABLE_VRF.topology.json` in this directory.

</details>

---

## 1. VRF Identity

VRF ALPHA's internal `vrf_id` (referenced in traces and protobuf messages):

```
YOR_PE-1(22-Feb-2026-11:17:17)# show network-services vrf ALPHA

VRF: ALPHA
    VRF ID: 16, Type: VRF
    Route Distinguisher: 1.1.1.1:100
    Description: L3VPN customer 1
    Associated interfaces:
            ge400-0/0/5.1
            ge400-0/0/5.999
```

PE-4 allocates `vrf_id 104` for the same VRF name (each PE allocates independently).

---

## 2. The FlowSpec Rule in NCP — Symptom

The rule is installed in NCP on both PEs, but the redirect next-hop is `(unreachable)`:

```
YOR_PE-1(22-Feb-2026-11:16:42)# show flowspec ncp 0

Address-Family IPv4
    Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
        Vrf: ALPHA
        Actions: Redirect-ip-nh: 10.0.0.230 (unreachable)
        Status: Installed
```

```
YOR_CL_PE-4(22-Feb-2026-10:10:35)# show flowspec ncp 6

Address-Family IPv4
    Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
        Vrf: ALPHA
        Actions: Redirect-ip-nh: 10.0.0.230 (unreachable)
        Status: Installed
```

---

## 3. What the Rule Does

- **Match:** Any IPv4 packet in VRF ALPHA with destination `100.100.100.1/32` and source from `16.16.16.0/30`
- **Action:** Redirect matching traffic to next-hop `10.0.0.230` (instead of normal forwarding)
- **Intent:** `10.0.0.230` is a host behind the CE — could be a scrubbing appliance, DPI tap, or DDoS mitigation device

---

## 4. How the Redirect Target Reached VRF ALPHA

The redirect target `10.0.0.230/32` is a valid route in VRF ALPHA, learned via eBGP from the CE:

```
YOR_PE-1(22-Feb-2026-11:18:04)# show bgp instance vrf ALPHA ipv4 unicast

     |       Network      |                Next hop                |Metric|  LocPref | Weight |   Path   |
----------------------------------------------------------------------------------------------------------
 U*> |10.0.0.230/32       | 16.16.16.2                             |      |          |       0|   65100 i|
```

```
YOR_PE-1(22-Feb-2026-11:16:39)# show route vrf ALPHA 10.0.0.230

VRF: ALPHA
Routing entry for 10.0.0.230/32
  Known via "bgp", priority low, distance 20, metric 0, vrf ALPHA, best, fib
  * 16.16.16.2, via ge400-0/0/5.1
```

On PE-4, the same prefix arrives via L3VPN import and resolves through MPLS:

```
YOR_CL_PE-4(22-Feb-2026-10:18:08)# show route vrf ALPHA 10.0.0.230

VRF: ALPHA
Routing entry for 10.0.0.230/32
  Known via "bgp", priority low, distance 200, metric 0, vrf ALPHA, best, fib
    1.1.1.1 [vrf default] (recursive) label 1040400
  *   14.14.14.1, via ge100-18/0/0.14 [vrf default] label 3
```

Both routes are `best, fib` — fully resolved and programmed. The redirect target is reachable on both PEs.

---

## 5. FlowSpec BGP Table — The Rule Exists

```
YOR_PE-1(22-Feb-2026-09:34:04)# show bgp ipv4 flowspec-vpn

Route Distinguisher: 1.1.1.1:100

 U*>  DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
         2d17h14m,     AS path: 65200 i, next hop: 10.0.0.230, from: 100.64.6.134
```

```
YOR_PE-1(22-Feb-2026-11:16:36)# show bgp instance vrf ALPHA ipv4 flowspec

 U*>  DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
         00:32:56,     AS path: 65200 i, next hop: 10.0.0.230, from: 100.64.6.134
```

```
YOR_CL_PE-4(22-Feb-2026-10:09:52)# show bgp ipv4 flowspec-vpn

Route Distinguisher: 1.1.1.1:100

 U*>i DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
         00:01:06, localpref:100 AS path: 123 1234567 65200 i, next hop: 10.0.0.230, from: 2.2.2.2
```

The rule is valid in BGP (`*>` = best), received from ExaBGP on PE-1 and reflected via RR-SA-2 to PE-4.

---

## 6. Root Cause — Trace Evidence

The processing pipeline:

```
bgpd ──► rib-manager (zebra) ──► fib-manager ──► NCP
              │                       ▲
              │ _eval_rnh():          │ ADD_NEXTHOP protobuf:
              │   resolves correctly  │   missing vrf_id
              │   in the right VRF    │   missing nexthops array
              │                       │   → fib-manager cannot resolve
              └───────────────────────┘
```

### PE-1 — VRF-Local eBGP Resolution (SAFI 134)

**rib-manager resolves correctly in VRF 16:**
```
2026-02-22T09:33:37.518860+02:00 [DEBUG] [zebra_rnh.c:1050:_eval_rnh] [rib-manager:1182:1182]
  rnh 10.0.0.230/32 in vrf 16 resolved through route 10.0.0.230/32
  - sending nexthop 16.16.16.2 if 14340 (protocol: 9) flags: 0x3 (reachable), nexthop_num: 1 event to clients
```

**ADD_NEXTHOP protobuf sent to fib-manager — THE BUG:**
```
2026-02-22T09:33:37.519090+02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1384:1384]
  nexthop { type: ADD_NEXTHOP add_nexthop {
    oid: 59
    address { v4 { value: 167772390 } }        ← 10.0.0.230
    is_flowspec: true
    protocol: UNKNOWN_PROTO
  } }
```
Missing: `vrf_id` (should be 16), `nexthops` array (should contain `{vrf_id: 16, if_id: 14340, gate: 16.16.16.2}`).

**FLOWSPEC_RULE_ADD correctly carries vrf_id but points to the broken NH:**
```
2026-02-22T09:33:37.519594+02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1384:1384]
  fpm_message { type: FLOWSPEC_RULE_ADD flowspec_add {
    key { afi: IPV4 nlri: "..." bgp_as: 1234567 vrf_id: 16 }
    action { type: REDIRECT_IP_NH nh_oid: 59 }
  } }
```

### PE-4 — MPLS/VPN Resolution (SAFI 134)

**rib-manager resolves correctly in VRF 104 via MPLS:**
```
2026-02-22T10:08:46.194111+02:00 [DEBUG] [zebra_rnh.c:1050:_eval_rnh] [rib-manager:1215:1215]
  rnh 10.0.0.230/32 in vrf 104 resolved through route 10.0.0.230/32
  - sending nexthop 1.1.1.1 if 0 (protocol: 9) labels: 1040400 flags: 0x1603 (reachable), nexthop_num: 1 event to clients
```

**ADD_NEXTHOP protobuf — identical bug:**
```
2026-02-22T10:08:46.194340+02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1352:1352]
  nexthop { type: ADD_NEXTHOP add_nexthop {
    oid: 24
    address { v4 { value: 167772390 } }        ← 10.0.0.230
    is_flowspec: true
    protocol: UNKNOWN_PROTO
  } }
```

**FLOWSPEC_RULE_ADD with vrf_id 104, broken NH:**
```
2026-02-22T10:08:46.194596+02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1352:1352]
  fpm_message { type: FLOWSPEC_RULE_ADD flowspec_add {
    key { afi: IPV4 nlri: "..." bgp_as: 1234567 vrf_id: 104 }
    action { type: REDIRECT_IP_NH nh_oid: 24 }
  } }
```

### PE-1 — Plain FlowSpec Inside VRF (SAFI 133)

Same bug with plain FlowSpec (no RD, no RT), ExaBGP peering directly inside VRF ALPHA:

**rib-manager resolves correctly in VRF 16:**
```
2026-02-22T10:43:41.213449+02:00 [DEBUG] [zebra_rnh.c:1050:_eval_rnh] [rib-manager:1182:1182]
  rnh 10.0.0.230/32 in vrf 16 resolved through route 10.0.0.230/32
  - sending nexthop 16.16.16.2 if 14340 (protocol: 9) flags: 0x3 (reachable), nexthop_num: 1 event to clients
```

**ADD_NEXTHOP protobuf — identical bug:**
```
2026-02-22T10:43:41.213630+02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1384:1384]
  nexthop { type: ADD_NEXTHOP add_nexthop {
    oid: 62
    address { v4 { value: 167772390 } }        ← 10.0.0.230
    is_flowspec: true
    protocol: UNKNOWN_PROTO
  } }
```

**FLOWSPEC_RULE_ADD with vrf_id 16, broken NH:**
```
2026-02-22T10:43:41.213742+02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1384:1384]
  fpm_message { type: FLOWSPEC_RULE_ADD flowspec_add {
    key { afi: IPV4 nlri: "..." bgp_as: 1234567 vrf_id: 16 }
    action { type: REDIRECT_IP_NH nh_oid: 62 }
  } }
```

---

## 7. Comparison Across All Scenarios

| | PE-1 SAFI 134 | PE-4 SAFI 134 | PE-1 SAFI 133 |
|--|--|--|--|
| Scenario | FlowSpec-VPN, VRF-local eBGP NH | FlowSpec-VPN, MPLS/VPN NH | Plain FlowSpec, in-VRF eBGP peer |
| VRF `vrf_id` | 16 | 104 | 16 |
| `_eval_rnh` result | reachable, `16.16.16.2` if 14340 | reachable, `1.1.1.1` label 1040400 | reachable, `16.16.16.2` if 14340 |
| `ADD_NEXTHOP` has `vrf_id`? | NO | NO | NO |
| `ADD_NEXTHOP` has `nexthops[]`? | NO | NO | NO |
| `FLOWSPEC_RULE_ADD` has `vrf_id`? | Yes (16) | Yes (104) | Yes (16) |
| `show flowspec ncp` status | **(unreachable)** | **(unreachable)** | **(unreachable)** |

---

## 8. Code-Level Root Cause

Three cascading issues in `rib-manager` on branch `easraf/flowspec_vpn/wbox_side`:

**1. `zebra_flowspec_db.c:create_rn_for_nh_tracking` (~line 146):**
Creates the FlowSpec redirect-IP nexthop with `nexthop_new()` and sets `NEXTHOP_FLAG_BGP_FLOWSPEC`, but never sets `nexthop->vrf_id` — it defaults to 0 (default VRF).

**2. `zebra_fpm_protobuf.c:create_add_nexthop_message` (~line 1051):**
When `is_support_indirection` and the NH is inactive, sends `n_nexthops = 0`. Even when active, `add_nexthops()` → `should_use_nh()` skips the nexthop because `ifindex == 0`. Result: empty `nexthops` array in the protobuf.

**3. `fpm.proto:AddNexthop` message schema:**
Has no top-level `vrf_id` field. The `vrf_id` only exists inside `repeated Nexthop nexthops`. Since the array is empty for FlowSpec redirect-IP, there is no field to carry the VRF context.

---

## 9. Trigger Condition

**Single condition:** Any FlowSpec rule with redirect-ip action in any non-default VRF.

**Does NOT matter:**
- SAFI 134 (FlowSpec-VPN) or SAFI 133 (plain FlowSpec)
- NH resolution path: eBGP, static, connected, OSPF, IS-IS, or MPLS/VPN
- Whether the NH interface is in the VRF or in the default VRF
- Whether the resolution is recursive or direct

**Only works:** In the default VRF (`vrf_id=0`), because the missing `vrf_id` defaults to 0, which happens to be correct.

---

## 10. Reproduction Steps

1. Configure any non-default VRF with a reachable route to a target IP
2. Inject a FlowSpec rule with `redirect-ip` action targeting that IP (via any BGP peer)
3. Run `show flowspec ncp <ncp-id>` — observe `(unreachable)` next to the redirect NH
4. Run `show route vrf <name> <redirect-ip>` — confirm the target is `best, fib`
5. Check `show file traces routing_engine/fibmgrd_traces | include is_flowspec` — the `ADD_NEXTHOP` protobuf will have no `vrf_id` and no `nexthops` array

---

## 11. Retest History

| Date | Device | Image | Verdict | Notes |
|------|--------|-------|---------|-------|
| 2026-02-18 | PE-1 | 26.1.0.24_priv...build_26 | BUG PRESENT | Original discovery |
| 2026-02-22 | PE-4 | 26.1.0.24_priv...build_26 | BUG PRESENT | MPLS/VPN resolution path |
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | BUG PRESENT | Jira SW-242876 closed but fix not in build |
| 2026-03-02 | PE-1 | 26.1.0.24_priv...build_28 | FIX CONFIRMED | ADD_NEXTHOP protobuf now has vrf_id + nexthops array. Rule Installed, NH no longer (unreachable). Session log: `SESSION_2026-03-02_1225_PE-1_verify-SW-242876.md` |
| 2026-03-02 | PE-1 | 26.1.0.24_priv...build_28 | DATAPATH CONFIRMED | Spirent traffic (8.4M fps) redirected via FlowSpec to 10.0.0.230. Match counter: 641M. Loss: 0.0002%. Requires `flowspec enabled` on interface. |

---

## 12. Related Bugs

- **SW-240206**: Stale redirect target after VRF RT change (similar NHT area)
- **SW-241907**: FlowSpec-VPN Redirect-IP outbound UPDATE encoding (20 extra 0 bytes in NH)
