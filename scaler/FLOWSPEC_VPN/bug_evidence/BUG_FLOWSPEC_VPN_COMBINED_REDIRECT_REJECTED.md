# BUG: FlowSpec-VPN Combined redirect-ip + redirect-to-rt Rejected Entirely

| Field | Value |
|-------|-------|
| Date Discovered | 2026-03-04 |
| Device | YOR_CL_PE-4 |
| Image | 26.1.0.27 (priv) |
| Build Branch | Unknown (production) |
| Severity | Medium |
| Component | Control Plane (bgpd) -- missing action stripping per SW-206876 spec |
| Related Epic | SW-206876 (FlowSpec-VPN in default VRF) |
| Session Log | Terminal output from `/tmp/bgp_update_investigation.py` |
| Pcap (server) | `~/SCALER/FLOWSPEC_VPN/bug_evidence/xray_cp_PE-4_bgp_update_20260304_204636.pcap` |
| Pcap (NCC) | `/tmp/xray_bgp_update_v3_20260304_204636.pcap` (preserved on active NCC) |

## Retest History

| Date | Image (full path) | Build | Result | Notes |
|------|-------------------|-------|--------|-------|
| 2026-03-04 | 26.1.0.27 (priv) | current | BUG PRESENT | Full pipeline trace with debug bgp updates-in |
| 2026-03-05 | 26.1.0.27 (priv) | current | BUG PRESENT | After fixing ExaBGP encoding: 49.49.49.9 now correctly encoded in MP_REACH_NLRI NH. PE-4 shows redirect-ip-nh:49.49.49.9 but NCP still rejects combined actions. ExaBGP encoding was a separate tooling bug (not DNOS). |

---

## One-Line Summary

When a FlowSpec-VPN rule carries both `redirect-ip` (Simpson) and `redirect-to-rt` extended communities, bgpd passes both actions downstream to NCP instead of stripping redirect-ip per SW-206876 spec, causing NCP to reject the entire rule.

## Expected Results

Per SW-206876: "If NLRI includes both redirect-to-ip and redirect-to-rt, ignore redirect-to-ip and perform only redirect-to-rt (VRF redirect)." The rule should be installed in TCAM with only the RT-redirect action. No syslog, no rejection.

## Actual Results

NCP rejects the entire rule with `BGP_FLOWSPEC_UNSUPPORTED_RULE: unsupported action. Actions: redirect to next hop|redirect to vrf`. Neither action gets applied. Rule is NOT installed in TCAM.

## Steps to Reproduce

1. Configure any non-default VRF with FlowSpec-VPN import for a given RT
2. Establish an eBGP FlowSpec-VPN peering (SAFI 134) with an external speaker
3. Inject a FlowSpec-VPN rule carrying BOTH extended communities:
   - `flowspec-redirect-ip-nh` (Simpson draft, type 0x08)
   - `flowspec-redirect-vrf-rt:<ASN>:<NN>` (RFC 8955 redirect-to-rt)
   - Plus a route target matching the VRF's FlowSpec import policy
4. Observe `show flowspec ncp <id>` shows "Status: Not installed, nlri and/or action not supported"
5. Observe syslog: `BGP_FLOWSPEC_UNSUPPORTED_RULE: unsupported action. Actions: redirect to next hop|redirect to vrf`
6. Observe `show flowspec instance vrf <VRF>` shows `flowspec-redirect-ip-nh:0.0.0.0` (NH not resolved)

---

## Investigation Evidence

### Route Injected

```
announce flow route rd 4.4.4.4:100 destination 100.100.100.1/32
  redirect-ip 49.49.49.9
  redirect 1234567:101
  extended-community [ target:1234567:300 ]
```

### BGP Received-Routes (decoded by PE-4)

```
BGP Adj-in table entry for DstPrefix:=100.100.100.1/32,SrcPrefix:=* with RD: 4.4.4.4:100
  65200
     Origin IGP
     Extended Community: RT:1234567L:300 flowspec-redirect-ip-nh flowspec-redirect-vrf-rt:1234567L:101
```

Three ext-communities decoded correctly:
- `RT:1234567L:300` -- route target for VRF ALPHA import
- `flowspec-redirect-ip-nh` -- redirect-ip (Simpson draft, 0x08 type, NH from MP_REACH_NLRI)
- `flowspec-redirect-vrf-rt:1234567L:101` -- redirect-to-rt, VRF lookup by import RT

---

## Wire-Level Analysis (pcap capture, 2026-03-04 20:47 UTC)

Pcap: `xray_cp_PE-4_bgp_update_20260304_204636.pcap` (2829 bytes, 25 packets)
Capture point: NCC routing_engine, `tcpdump -i any` via `run start shell`
BPF filter: `host 100.64.6.134 and host 100.70.0.206 and port 179`
Source MAC on all ExaBGP packets: `Fortinet_09:00:1a (00:09:0f:09:00:1a)` -- confirms FortiGate transit path

### Frame 6 -- BGP UPDATE: WITHDRAW (84 bytes payload)

```
20:47:13.635976 100.64.6.134:34797 -> 100.70.0.206:179 (TTL=63, DF)

  UPDATE Message (Length: 84)
    Path Attributes:
      ORIGIN: IGP
      AS_PATH: 65200
      EXTENDED_COMMUNITIES (24 bytes, 3 communities):
        1. Route Target: 1234567:300       [Type 0x02, Subtype 0x02, 4-Octet AS-Specific]
        2. Redirect-IP-NH: 0x0000000000000000  [Type 0x08, Subtype 0x00 -- Simpson draft]
        3. Redirect-VRF:   1234567:101      [Type 0x82, Subtype 0x08 -- AS-4byte redirect]
    MP_UNREACH_NLRI (18 bytes):
      AFI: IPv4 (1), SAFI: Flow Spec Filter VPN (134)
      RD: 4.4.4.4:100 (Type 1, Admin 4.4.4.4, Assigned 100)
      NLRI: DstPrefix:=100.100.100.1/32
```

### Frame 11 -- BGP UPDATE: RE-ANNOUNCE (86 bytes payload)

```
20:47:16.815230 100.64.6.134:34797 -> 100.70.0.206:179 (TTL=63, DF)

  UPDATE Message (Length: 86)
    Path Attributes:
      ORIGIN: IGP
      AS_PATH: 65200
      EXTENDED_COMMUNITIES (24 bytes, 3 communities):
        1. Route Target: 1234567:300       [Type 0x02, Subtype 0x02, 4-Octet AS-Specific]
        2. Redirect-IP-NH: 0x0000000000000000  [Type 0x08, Subtype 0x00 -- Simpson draft]
        3. Redirect-VRF:   1234567:101      [Type 0x82, Subtype 0x08 -- AS-4byte redirect]
    MP_REACH_NLRI:
      AFI: IPv4 (1), SAFI: Flow Spec Filter VPN (134)
      RD: 4.4.4.4:100
      NLRI: DstPrefix:=100.100.100.1/32
```

### Wire-Level Conclusions

1. **Redirect-IP target IP (49.49.49.9) is MISSING from the UPDATE.** Neither location contains it:
   - Ext-community `0x08:00` value: `0x000000000000` (all zeros -- should be `0x31313109xxxx` for 49.49.49.9 per Simpson draft)
   - MP_REACH_NLRI next-hop length: **0 bytes** (no next-hop encoded at all)
   - This is an **ExaBGP encoding bug** -- the `redirect-ip 49.49.49.9` command is accepted but the IP is not encoded in the UPDATE
2. **This explains DNOS showing `flowspec-redirect-ip-nh:0.0.0.0`** -- DNOS correctly reports no redirect-ip target because none was encoded on the wire. The `nh_oid: 0` in the fib-manager protobuf and the rib-manager `Got NULL parameter` error during withdraw are direct consequences.
3. **Redirect-VRF encoding IS correct** -- AS-4byte format (0x82:08), `1234567:101` matches VRF ZULU import RT.
4. **Two independent issues discovered:**
   - **Issue 1 (DNOS -- SW-206876 gap):** bgpd does not strip redirect-ip when combined with redirect-to-rt, causing NCP to reject the entire rule
   - **Issue 2 (ExaBGP encoding):** redirect-ip target IP is not encoded in the UPDATE. Even if DNOS stripped redirect-to-rt and kept only redirect-ip, the action would fail because the target IP is 0.0.0.0
5. **FortiGate is in-path** -- source MAC `00:09:0f:09:00:1a` (Fortinet OUI) and TTL=63 (decremented from 64) confirm single-hop transit through the firewall.

---

## Pipeline Trace (all timestamps UTC+2, 2026-03-04)

### Layer 1: bgpd (debug bgp updates-in active)

**WITHDRAW at 22:22:32:**
```
22:22:32.209906 [DEBUG] [bgp_packet.c:2957:bgp_update_receive] [bgpd:6975:6975]
  vrf default peer 100.64.6.134: rcvd UPDATE w/ attr: , origin i,
  extended community RT:1234567L:300 flowspec-redirect-ip-nh flowspec-redirect-vrf-rt:1234567L:101, path 65200

22:22:32.209957 [DEBUG] [bgp_route.c:10647:bgp_withdraw] [bgpd:6975:6975]
  vrf id 0(default) peer 100.64.6.134: rcvd UPDATE DstPrefix:=100.100.100.1/32,SrcPrefix:=* (IPv4 Flowspec-VPN) -- withdrawn

22:22:32.210284 [NOTICE] [bgp_chain.c:3777:bgp_chain_done] [bgpd:6975:6975]
  On vrf 0, bgpid 1(default) IPv4 Flowspec-VPN: Chain is done!

22:22:32.210491 [NOTICE] [bgp_chain.c:3777:bgp_chain_done] [bgpd:6975:6975]
  On vrf 104, bgpid 2(ALPHA) IPv4 Flowspec: Chain is done!
```

**RE-INJECT at 22:22:41:**
```
22:22:41.386560 [DEBUG] [bgp_packet.c:2957:bgp_update_receive] [bgpd:6975:6975]
  vrf default peer 100.64.6.134: rcvd UPDATE w/ attr: , origin i,
  extended community RT:1234567L:300 flowspec-redirect-ip-nh flowspec-redirect-vrf-rt:1234567L:101, path 65200

22:22:41.386610 [DEBUG] [bgp_route.c:10411:bgp_update_main] [bgpd:6975:6975]
  vrf id 0(default) peer 100.64.6.134: rcvd UPDATE DstPrefix:=100.100.100.1/32,SrcPrefix:=* (IPv4 Flowspec-VPN), addpath rx id 0

22:22:41.386860 [NOTICE] [bgp_chain.c:3777:bgp_chain_done] [bgpd:6975:6975]
  On vrf 0, bgpid 1(default) IPv4 Flowspec-VPN: Chain is done!

22:22:41.387092 [NOTICE] [bgp_chain.c:3777:bgp_chain_done] [bgpd:6975:6975]
  On vrf 104, bgpid 2(ALPHA) IPv4 Flowspec: Chain is done!
```

**Observation:** bgpd correctly decodes all three ext-communities from the UPDATE. It processes the route through chain evaluation for both default VRF (FlowSpec-VPN SAFI 134) and VRF ALPHA (FlowSpec SAFI 133 after import). bgpd does NOT strip redirect-ip before passing to zebra.

### Layer 2: rib-manager (zebra)

```
22:22:32.210725 [ERROR] [zebra_flowspec_db.c:182:destroy_rn_for_nh_tracking] [rib-manager:6977:6977]
  Got NULL parameter!
```

**Observation:** During WITHDRAW, rib-manager throws an ERROR in the FlowSpec DB NH tracking function. This suggests the redirect-ip NH tracking entry was never properly created (possibly because nh_oid was always 0).

### Layer 3: fib-manager (fibmgrd)

**DELETE at 22:22:32:**
```
22:22:32.210873 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:7275:7275]
  [PACKET] Got protobuf message from RIB-Manager: fpm_message {
    type: FLOWSPEC_RULE_DELETE
    flowspec_delete { key { afi: IPV4 nlri: "\001 ddd\001" bgp_as: 1234567 vrf_id: 104 } }
  }
```

**ADD at 22:22:41:**
```
22:22:41.387356 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:7275:7275]
  [PACKET] Got protobuf message from RIB-Manager: fpm_message {
    type: FLOWSPEC_RULE_ADD
    flowspec_add {
      key { afi: IPV4 nlri: "\001 ddd\001" bgp_as: 1234567 vrf_id: 104 }
      action { type: REDIRECT_IP_NH nh_oid: 0 }
      action { type: REDIRECT_VRF num_of_vrf: 1 vrf_id: 106 }
    }
  }
```

**Observations:**
1. The protobuf carries BOTH actions: `REDIRECT_IP_NH` (nh_oid=0) + `REDIRECT_VRF` (vrf_id=106/ZULU)
2. `nh_oid: 0` means the redirect-ip NH (49.49.49.9) was NOT resolved to a valid NH object
3. fib-manager does NOT filter the combination -- sends both to NCP

### Layer 4: NCP wb_agent (FlowspecManager) -- THE REJECTION POINT

```
22:22:41.388099 [DEBUG] [FlowspecManager.cpp:151:AddRuleInternal()] [wb_fib_fpm:2013]
  Flowspec: Received BGP IPv4 NLRI: 012064646401 : DstPrefix:=100.100.100.1/32,SrcPrefix:=*

22:22:41.388151 [DEBUG] [FlowspecManager.cpp:161:AddRuleInternal()] [wb_fib_fpm:2013]
  Flowspec: actions - type: redirect-ip-nh(4)

22:22:41.388163 [DEBUG] [FlowspecManager.cpp:183:AddRuleInternal()] [wb_fib_fpm:2013]
  Flowspec: actions - nh_oid: 0 mirror: 0

22:22:41.388174 [DEBUG] [FlowspecManager.cpp:161:AddRuleInternal()] [wb_fib_fpm:2013]
  Flowspec: actions - type: redirect-vrf(5)

22:22:41.388186 [DEBUG] [FlowspecManager.cpp:189:AddRuleInternal()] [wb_fib_fpm:2013]
  Flowspec: actions - num_vrf: 1 vrf_id: 106

22:22:41.388198 [WARNING] [FlowspecRuleData.cpp:255:CheckActionSupport()] [wb_fib_fpm:2013]
  Flowspec: Cannot add redirect next hop rule with redirect vrf        <<<--- REJECTION

22:22:41.388220 [INFO] [FlowspecTable.cpp:101:InternalAddRule()] [wb_fib_fpm:2013]
  Flowspec: Rule is not supported

22:22:41.388236 [DEBUG] [FlowspecTable.cpp:460:SendUnsupportedSystemEvent()] [wb_fib_fpm:2013]
  Flowspec: Will not send UnsupportedSystemEvent as this is not master ncp
```

**Root cause function:** `FlowspecRuleData.cpp:255:CheckActionSupport()` -- this function checks for unsupported action combinations and rejects redirect-ip-nh + redirect-vrf.

### Layer 5: Syslog (from master NCP)

```
local7.warning 2026-03-04T22:22:41.388+02:00 YOR_CL_PE-4 BGP - - -
  BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv4 rule cannot be applied due to unsupported action.
  Rule NLRI: DstPrefix:=100.100.100.1/32,SrcPrefix:=*,
  Actions: redirect to next hop|redirect to vrf
```

### Layer 6: Final device state

**show flowspec ncp 18:**
```
Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=*
  Vrf: ALPHA
  Actions: Redirect-ip-nh: Invalid, Redirect-vrf: ZULU
  Status: Not installed, nlri and/or action not supported
```

**show flowspec instance vrf ALPHA:**
```
Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=*
  Actions: flowspec-redirect-ip-nh:0.0.0.0, flowspec-redirect-vrf-rt: ZULU 1234567L:101
  Match packet counter: 0
```

---

## Complete Timeline

| Time (UTC+2) | Component | Function | Event |
|---|---|---|---|
| 22:22:41.386560 | bgpd | bgp_update_receive | rcvd UPDATE: ext-community RT:1234567L:300 flowspec-redirect-ip-nh flowspec-redirect-vrf-rt:1234567L:101 |
| 22:22:41.386610 | bgpd | bgp_update_main | UPDATE accepted into FlowSpec-VPN RIB (addpath rx id 0) |
| 22:22:41.386730 | bgpd | bgp_chain | Bestpath marker finished (default VRF, FlowSpec-VPN) |
| 22:22:41.386860 | bgpd | bgp_chain_done | Chain done (default VRF, FlowSpec-VPN) |
| 22:22:41.386992 | bgpd | bgp_chain | Bestpath marker finished (VRF ALPHA, FlowSpec) |
| 22:22:41.387092 | bgpd | bgp_chain_done | Chain done (VRF ALPHA, FlowSpec) -- bgpd hands off to zebra |
| 22:22:41.387356 | fibmgrd | HandleMessageFromZebra | Protobuf FLOWSPEC_RULE_ADD: REDIRECT_IP_NH(nh_oid:0) + REDIRECT_VRF(vrf_id:106) |
| 22:22:41.387591 | fibmgrd | FpmNcp | Sent to NCP 18: FLOWSPEC [iid=210] |
| 22:22:41.388099 | NCP | AddRuleInternal | Received NLRI: DstPrefix:=100.100.100.1/32 |
| 22:22:41.388151 | NCP | AddRuleInternal | Action #1: redirect-ip-nh(4), nh_oid=0 |
| 22:22:41.388174 | NCP | AddRuleInternal | Action #2: redirect-vrf(5), num_vrf=1, vrf_id=106 |
| **22:22:41.388198** | **NCP** | **CheckActionSupport** | **REJECTED: "Cannot add redirect next hop rule with redirect vrf"** |
| 22:22:41.388220 | NCP | InternalAddRule | Rule is not supported |
| 22:22:41.388 | syslog | system-events | BGP_FLOWSPEC_UNSUPPORTED_RULE: unsupported action |

---

## Corrected Encoding Proof (2026-03-05, after ExaBGP fix)

After patching ExaBGP to correctly encode `redirect-ip 49.49.49.9` in the MP_REACH_NLRI NH field, re-injected the combined route. The DNOS device now correctly receives and displays the redirect-ip target IP.

### show bgp ipv4 flowspec-vpn neighbors 100.64.6.134 received-routes nlri (00:23 UTC+2)

```
BGP Adj-in table entry for DstPrefix:=100.100.100.1/32,SrcPrefix:=*
  65200

     Origin IGP
     Next hop: 49.49.49.9
     Extended Community: RT:1234567L:300 flowspec-redirect-ip-nh flowspec-redirect-vrf-rt:1234567L:101
```

**Key change:** `Next hop: 49.49.49.9` now appears -- was previously missing (empty/N/A) due to ExaBGP encoding bug.

### show flowspec instance vrf ALPHA (00:24 UTC+2)

```
Address-family: IPv4

    Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=*
        Actions: flowspec-redirect-ip-nh:49.49.49.9, flowspec-redirect-vrf-rt: ZULU 1234567L:101
        Match packet counter: 0
```

**Key change:** `flowspec-redirect-ip-nh:49.49.49.9` -- was `0.0.0.0` before the ExaBGP fix.

### show bgp instance vrf ALPHA ipv4 flowspec nlri (00:24 UTC+2)

```
BGP IPv4 Flowspec routing table entry for DstPrefix:=100.100.100.1/32,SrcPrefix:=*
Paths: (1 available, best #1)
  Advertised best to peers:
  49.49.49.9
 Path #1
  65200
     49.49.49.9 [vrf default] from 100.64.6.134 (100.64.6.134)
     Origin IGP, localpref 100, valid, external, best
     Extended Community: RT:1234567L:300 flowspec-redirect-ip-nh flowspec-redirect-vrf-rt:1234567L:101
```

**Key change:** Next hop shown as `49.49.49.9` in path info, and `Advertised best to peers: 49.49.49.9`.

### XRAY Wire Capture: MP_REACH_NLRI NH field (Method A: direct NCC capture, 00:22 UTC+2)

```
tcpdump on NCC interface (BPF: host 100.64.6.134 and port 179):

MP_REACH_NLRI:
  AFI: IPv4 (1), SAFI: FlowSpec-VPN (134)
  Next-Hop Length: 12 bytes
  Next-Hop: 00 00 00 00 00 00 00 00 31 31 31 09
            |------ 8-byte RD (zero) ----| |-- 49.49.49.9 --|
```

The 12-byte VPN next-hop correctly contains an 8-byte zero Route Distinguisher followed by the 4-byte redirect-ip target `49.49.49.9` (hex: `31 31 31 09`), per Simpson draft-02 encoding.

### NCP still rejects the combination (unchanged)

```
show flowspec ncp 18:

Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=*
  Vrf: ALPHA
  Actions: Redirect-ip-nh: Invalid, Redirect-vrf: ZULU
  Status: Not installed, nlri and/or action not supported
```

**Conclusion:** The ExaBGP encoding bug was a separate tooling issue. With correct encoding, DNOS correctly decodes `redirect-ip-nh:49.49.49.9` but the NCP `CheckActionSupport()` still rejects the combination per its action-exclusion table. This confirms the SW-206876 spec-vs-implementation gap is in **bgpd** (should strip redirect-ip before passing to NCP), NOT in the encoding or NCP logic.

---

## Root Cause Analysis

### Where the fix SHOULD be (per SW-206876 spec)

**bgpd** (control plane) should intercept the combination **before** sending to zebra/fib-manager:

1. During `bgp_update_main()` or the FlowSpec action evaluation, check if BOTH `flowspec-redirect-ip-nh` and `flowspec-redirect-vrf-rt` ext-communities are present
2. If both present: strip `flowspec-redirect-ip-nh`, keep only `flowspec-redirect-vrf-rt`
3. Send only `REDIRECT_VRF` action in the protobuf to fib-manager
4. No syslog, no rejection -- silently discard redirect-ip per spec

### Where the rejection currently happens

**NCP wb_agent** (datapath) at `FlowspecRuleData.cpp:255:CheckActionSupport()`:
- Receives both actions from fib-manager
- Checks `if (redirect-ip-nh AND redirect-vrf) { reject }`
- The NCP check is CORRECT for hardware -- BCM TCAM cannot program both simultaneously
- The bug is that bgpd sends both actions downstream instead of stripping redirect-ip

### Secondary Issues

1. **redirect-ip NH shows 0.0.0.0 (nh_oid=0):** Even without the combined-action issue, redirect-ip alone would fail because the NH was not resolved. The protobuf has `nh_oid: 0` which means no valid NH object was created for 49.49.49.9.

2. **rib-manager ERROR on withdraw:** `zebra_flowspec_db.c:182:destroy_rn_for_nh_tracking: Got NULL parameter!` -- the NH tracking entry was never created (because nh_oid=0), so destroy fails with NULL.

---

## ExaBGP Encoding Bug (separate issue, FIXED)

The original investigation showed `redirect-ip-nh:0.0.0.0` on PE-4. This was caused by an **ExaBGP bug**, not DNOS.

**Root cause:** In `exabgp/configuration/flow/__init__.py`, the `route()` function (registered via `@ParseFlow.register('route', 'append-route')`) processes API pipe flow commands sequentially. When a flow route has both `redirect-ip 49.49.49.9` and `redirect 1234567:101`:

1. `redirect-ip 49.49.49.9` is parsed first, correctly sets `change.nlri.nexthop = IP('49.49.49.9')`
2. `redirect 1234567:101` is parsed next, action is `'nexthop-and-attribute'` which returns `(NoNextHop, attribute)`
3. The original code: `change.nlri.nexthop = nexthop` **unconditionally** overwrites 49.49.49.9 with NoNextHop
4. Result: MP_REACH_NLRI has 0-byte next-hop, DNOS shows `0.0.0.0`

**Fix (applied to 3 files in `~/.local/lib/python3.10/site-packages/exabgp/`):**

```python
# In configuration/flow/__init__.py (route function, line 78):
elif action == 'nexthop-and-attribute':
    nexthop, attribute = ParseFlow.known[command](tokeniser)
    if nexthop is not NoNextHop:    # <-- ADDED GUARD
        change.nlri.nexthop = nexthop
    change.attributes.add(attribute)
```

Same guard added in `configuration/core/section.py` and `configuration/announce/flow.py`.

Additionally patched `protocol/family.py`: FlowSpec-VPN (SAFI 134) `rd_size` changed from `0` to `8`, enabling the 12-byte VPN next-hop format (8-byte RD + 4-byte IP) in MP_REACH_NLRI.

---

## Related Bugs

| Bug | Relationship |
|-----|-------------|
| **SW-206876** | Parent epic that specifies the combined-action behavior |
| SW-242876 | redirect-ip NH unreachable in non-default VRF (FIXED -- rib-manager protobuf now includes VRF) |
| SW-41148 | redirect-ip skipped when NH resolves via MPLS tunnel (BY DESIGN) |
| SW-48486 | Drop + RT-Redirect combined -- similar NCP rejection |
| ExaBGP encoding bug | redirect-ip IP overwritten by NoNextHop from redirect-to-rt (FIXED locally, 2026-03-05) |
