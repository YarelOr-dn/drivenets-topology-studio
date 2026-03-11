# KNOWN LIMITATION: FlowSpec Redirect-IP Only Supports Local (Direct L3) Next-Hops

**Date discovered**: 2026-03-02
**Reclassified**: 2026-03-02 — changed from "bug" to "by-design limitation" after review with dev (Lior Ashkenazi) and spec verification
**Devices tested**: YOR_CL_PE-4 (MPLS NH — skipped by design), YOR_PE-1 (direct L3 NH — works)
**Image**: `DNOS [26.1.0] build [27_priv]` (PE-4), `DNOS [26.1.0] build [28_priv]` (PE-1)
**Branch**: easraf/flowspec_vpn/wbox_side
**Severity**: Not a bug — by-design limitation of SW-41148 (BGP Flowspec Redirect Action)
**Component**: NCP datapath — `FlowspecTcamManager.cpp:271` (`WriteRuleInTcam`)
**Implementation epic**: SW-41148 (BGP Flowspec Redirect Action, Status: Verified, Assignee: Omri Nir)
**Session log**: `~/SCALER/FLOWSPEC_VPN/debug_sessions/SESSION_2026-03-02_1345_PE-4_repro-redirect-mpls-nh.md`

---

## Summary

DNOS implements FlowSpec redirect-ip as a **local redirect only** — the redirect target IP must resolve to a **directly connected L3 next-hop** (e.g., a CE on the same PE). When the target IP is learned via L3VPN (ipv4-vpn) and resolves through an MPLS tunnel, the NCP correctly skips the redirect action because MPLS-tunneled redirect was never in the implementation scope.

The rule is marked `Status: Installed` with `Redirect-ip-nh: N/A`, meaning the TCAM entry exists (matching packets) but performs no redirect — traffic is forwarded normally.

**This is by design, not a bug.** The implementation epic SW-41148 scopes redirect-ip as "redirect to next-hop IPv4 and IPv6 next-hops" per `draft-simpson-idr-flowspec-redirect-02`. That draft (Section 3) explicitly states that constraints on tunnel types used for the redirection next-hop are *"outside its scope"*. The earlier draft-00 informatively mentioned MPLS tunnels, but this language was removed in draft-02 which DNOS follows.

**Developer confirmation** (Lior Ashkenazi, 2026-03-02): *"our code specifically say: case E_FLOWSPEC_ACTION_REDIRECT_IP_NH: return 'redirect-ip-nh'; we never supported redirect to tunnel"*

---

## 1. Retest History

| Date | Device | Image | Verdict | Notes |
|------|--------|-------|---------|-------|
| 2026-03-02 | PE-4 | 26.1.0 build 27_priv | BY DESIGN | NCP 6 + NCP 18 both skip Action 4 for MPLS NH. Reclassified as by-design after dev review + draft-02 spec check. SW-41148 scopes redirect-ip to direct L3 NH only. |

---

## 2. Expected Behavior (By Design)

FlowSpec redirect-ip programs the redirect action only when the target IP resolves to a direct L3 next-hop (locally connected). When the target resolves via MPLS tunnel, the redirect action is skipped and `show flowspec ncp` shows `Redirect-ip-nh: N/A`.

## 3. Observed Behavior (Confirmed By Design)

The NCP skips the redirect-ip action when the target IP resolves through an MPLS tunnel (e.g., VPN label + LDP), showing `Redirect-ip-nh: N/A` in `show flowspec ncp` despite the rule being marked `Status: Installed`. This is the intended behavior per SW-41148 implementation scope.

## 4. Steps to Reproduce

1. Configure two PEs in the same VPN (VRF with matching RT import/export)
2. On PE-A: have a directly connected CE advertising the redirect target IP (e.g., 10.0.0.230/32) via eBGP
3. On PE-B: the redirect target IP is imported into the VRF via L3VPN (recursive resolution through MPLS tunnel)
4. Inject a FlowSpec-VPN rule with `redirect-ip` targeting that IP
5. On PE-A: verify `show flowspec ncp <id>` shows `Redirect-ip-nh: <IP>`, `Status: Installed` — redirect works with direct L3 next-hop
6. On PE-B: verify `show flowspec ncp <id>` — shows `Redirect-ip-nh: N/A`, `Status: Installed` (redirect skipped by design — MPLS NH not supported)

---

## 5. Route Resolution Comparison

### PE-1 (WORKS — direct L3)
```
show route vrf ALPHA 10.0.0.230
VRF: ALPHA
Routing entry for 10.0.0.230/32
  Known via "bgp", priority low, distance 20, metric 0, vrf ALPHA, best, fib
  * 16.16.16.2, via ge400-0/0/5.1
```

### PE-4 (FAILS — MPLS recursive)
```
show route vrf ALPHA 10.0.0.230
VRF: ALPHA
Routing entry for 10.0.0.230/32
  Known via "bgp", priority low, distance 200, metric 0, vrf ALPHA, best, fib
    1.1.1.1 [vrf default] (recursive) label 1040385
  *   14.14.14.1, via ge100-18/0/0.14 [vrf default] label 3
```

---

## 6. Protobuf Evidence (ADD_NEXTHOP)

Both protobuf messages are **correct** — the control plane fix (SW-242876) works properly on both devices.

### PE-1 protobuf (WORKS — at 13:35:17)
```
nexthop { type: ADD_NEXTHOP add_nexthop {
  oid: 65
  is_support_indirection: true
  nexthops {
    if_id { index: 14340 cheetah_index: 13316 }
    if_name: "ge400-0/0/5.1"
    address { v4 { value: 269488130 } }        // 16.16.16.2 (direct CE)
    vrf_id: 1                                   // VRF ALPHA
    ecmp_weight: 0
    protocol: BGP
  }
  address { v4 { value: 167772390 } }           // 10.0.0.230 (redirect target)
  is_flowspec: true
  protocol: BGP
} }
```

### PE-4 protobuf (MPLS NH — at 13:35:23)
```
nexthop { type: ADD_NEXTHOP add_nexthop {
  oid: 63
  is_support_indirection: true
  nexthops {
    if_id { index: 14377 cheetah_index: 13353 }
    if_name: "ge100-18/0/0.14"
    address { v4 { value: 235802113 } }        // 14.14.14.1 (underlay LDP peer)
    vrf_id: 0                                   // default VRF (underlay)
    mpls_labels: 1040385                        // VPN label
    ecmp_weight: 0
    protocol: LDP
  }
  address { v4 { value: 167772390 } }           // 10.0.0.230 (redirect target)
  is_flowspec: true
  protocol: BGP
} }
```

### Key Differences

| Field | PE-1 (WORKS) | PE-4 (FAILS) |
|-------|--------------|---------------|
| Gateway | 16.16.16.2 (direct CE) | 14.14.14.1 (LDP underlay peer) |
| vrf_id | 1 (VRF ALPHA) | 0 (default — underlay) |
| mpls_labels | NONE | 1040385 (VPN label) |
| protocol | BGP | LDP |
| NCP Action 4 | Programmed | **Skipped** |

---

## 7. NCP Trace Evidence (Smoking Gun)

### NCP 18 — wb_agent.flowspec (timestamp 13:35:23)
```
[FlowspecManager.cpp:151 AddRuleInternal()] Flowspec: Received BGP IPv4 NLRI: 012064646401021e10101000 : DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
[FlowspecManager.cpp:161 AddRuleInternal()] Flowspec: actions - type: redirect-ip-nh(4)
[FlowspecManager.cpp:183 AddRuleInternal()] Flowspec: actions - nh_oid: 63 mirror: 0
[FlowspecTcamManager.cpp:309 ReserveQualifiers()] Flowspec: local_config_flowspec_should_validate_resources: 1
[FlowspecRuleData.cpp:290 DeterminePriority()] Flowspec: Adding rule between priority 2000000 to priority 4000000
[FlowspecTcamManager.cpp:241 WriteRuleInTcam()] Flowspec: Adding rule with priority 3000000
[FlowspecTcamManager.cpp:271 WriteRuleInTcam()] Flowspec: Action 4 skipped, probably because it is unreachable   ← BY DESIGN (MPLS NH not supported)
[FlowspecTcamManager.cpp:195 operator()()] Flowspec: Succeeded to add rule in BCM
[FlowspecTcamManager.cpp:283 WriteRuleInTcam()] Flowspec: Succeeded to write 1 rules in TCAM for rule id 69001
```

### NCP 6 — wb_agent.flowspec (same timestamp, identical behavior)
```
[FlowspecManager.cpp:161 AddRuleInternal()] Flowspec: actions - type: redirect-ip-nh(4)
[FlowspecManager.cpp:183 AddRuleInternal()] Flowspec: actions - nh_oid: 63 mirror: 0
[FlowspecTcamManager.cpp:271 WriteRuleInTcam()] Flowspec: Action 4 skipped, probably because it is unreachable   ← BY DESIGN
[FlowspecTcamManager.cpp:195 operator()()] Flowspec: Succeeded to add rule in BCM
```

### NCP Show Output (both NCPs)
```
show flowspec ncp 18
Address-Family IPv4
  Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
    Vrf: ALPHA
    Actions: Redirect-ip-nh: N/A          ← Action was skipped
    Status: Installed                      ← Rule IS in TCAM, just without redirect
```

---

## 8. BGP Table Evidence
```
show bgp ipv4 flowspec-vpn
Route Distinguisher: 1.1.1.1:100
 U*>i DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
      00:51:43, localpref:100 AS path: 123 1234567 65200 i, next hop: 10.0.0.230, from: 2.2.2.2
```

```
show flowspec instance vrf ALPHA ipv4
Address-family: IPv4
  Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
    Actions: flowspec-redirect-ip-nh:10.0.0.230      ← Control plane knows the NH
    Match packet counter: 0                            ← No redirect happening
```

---

## 9. rib-manager Trace (NHT tracking)
```
2026-03-02T13:35:08.933553 +02:00 [DEBUG] NHT: Client bgp (bgp-flowspec) unregisters rnh 10.0.0.230/32 vrf 104
2026-03-02T13:35:08.933593 +02:00 [ERROR] zebra_flowspec_db.c:182:destroy_rn_for_nh_tracking: Got NULL parameter!
2026-03-02T13:35:23.475225 +02:00 [DEBUG] NHT: Client bgp (bgp-flowspec) registers rnh 10.0.0.230/32 in vrf 104
```

---

## 10. Implementation Context

**Implementation epic**: SW-41148 (BGP Flowspec Redirect Action, Status: Verified)
**Spec**: `draft-simpson-idr-flowspec-redirect-02` (NOT draft-00)
**Assignee**: Omri Nir
**Scope**: Redirect to direct IPv4/IPv6 next-hops only. MPLS tunnel redirect was never in scope.

**File**: `FlowspecTcamManager.cpp` (NCP wb_agent)
**Function**: `WriteRuleInTcam()`, line 271
**Logic**: Action type 4 (redirect-ip-nh) requires a direct L3 FEC (interface + gateway). When the NH object requires MPLS encapsulation, it is considered "unreachable" and the redirect action is skipped. This is consistent with the implementation scope.

**Draft-02 Section 3** (the version DNOS implements): *"Signaling and applying constraints beyond longest-prefix-match on the types of interfaces or tunnels that can be used as the redirection next-hop B are not precluded by this specification but are nevertheless outside its scope."*

**Draft-00 Section 3** (earlier version, NOT what DNOS follows): Informatively mentioned MPLS tunnels as a possible path. This language was removed in draft-02.

**Lesson learned**: Always verify which draft version the implementation follows before claiming a spec violation. SW-41148 references draft-02, not draft-00.

---

## 11. Related Issues

- **SW-41148**: BGP Flowspec Redirect Action (implementation epic, Status: Verified) — scopes redirect-ip to direct L3 NH only
- **SW-242876**: FlowSpec redirect-ip NH unreachable in non-default VRF (control plane fix — CONFIRMED FIXED, separate from this)
- **SW-182546**: FlowSpec VPN - DP enabler (parent epic)
- **SW-182545**: FlowSpec VPN (grandparent epic)
- **draft-simpson-idr-flowspec-redirect-02**: The draft DNOS implements. Tunnel type constraints are explicitly "outside its scope"

## 12. Topology Diagram

Topology JSON: `~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_FLOWSPEC_REDIRECT_IP_MPLS_NH_SKIPPED.topology.json`

Load in topology app: Topologies → Load Debug-DNOS..., or File → Load from File
