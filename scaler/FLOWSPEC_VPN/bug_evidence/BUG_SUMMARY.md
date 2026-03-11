# FlowSpec-VPN Redirect-IP MP_REACH_NLRI Encoding Bug

**Device:** RR-SA-2 (DNOS 26.1.0.22)
**Process:** `bgpd` in `routing_engine` container
**Code path:** `bgp_attr.c` → `bgp_packet_mpattr_start_v4_flowspec_vpn()`
**Reproduced:** 2026-02-16 19:05:58 IST

---

## One-Line Summary

`bgpd` on RR-SA-2 corrupts **every** outbound FlowSpec-VPN UPDATE containing a redirect-ip next-hop — **both IPv4 (AFI 1/SAFI 134) and IPv6 (AFI 2/SAFI 134)**: it allocates a 24-byte IPv6 buffer for the next-hop, fills it with zeros, and pads the MP_REACH_NLRI with extra zero bytes — causing peers to send NOTIFICATION 3/9 and tear down the session in an infinite flap loop.

---

## Reproduction Steps

```
1. ExaBGP (100.64.6.134) peers with RR-SA-2 (100.70.0.205) — iBGP, ASN 123
2. Inject: announce flow route rd 2.2.2.2:100 destination 10.0.0.0/24 redirect 10.0.0.254 extended-community [ target:1234567:300 ]
3. RR-SA-2 receives correct UPDATE, runs bestpath, reflects to PE-1 (1.1.1.1) and PE-4 (4.4.4.4)
4. Outbound UPDATE has corrupted MP_REACH_NLRI → PE-1 sends NOTIFICATION 3/9 → session down
5. Session re-establishes → bgpd re-advertises same broken route → PE-1 rejects again → infinite loop
```

---

## Evidence: Pcap Frames

**Pcap:** `reproduce_full_flow_v2.pcap`

**Wireshark display filter to isolate the bug:**
```
(bgp.type == 3) || (bgp.type == 2 && bgp.update.path_attribute.mp_reach_nlri.afi == 1 && bgp.update.path_attribute.mp_reach_nlri.safi == 134)
```
Shows: all FlowSpec-VPN (SAFI 134) UPDATEs + all NOTIFICATION messages.

| Frame | Pcap Time (UTC) | Delta from inject | Direction | What |
|-------|-----------------|-------------------|-----------|------|
| 11 | 17:05:58.659978 | T+0ms | ExaBGP → RR-SA-2 | Correct UPDATE (FlowSpec-VPN, SAFI 134) |
| 26 | 17:05:59.755407 | T+1095ms | RR-SA-2 → PE-1 | **BROKEN UPDATE** (corrupted MP_REACH_NLRI) |
| 31 | 17:05:59.757263 | T+1097ms | PE-1 → RR-SA-2 | **NOTIFICATION 3/9** (1.9ms after broken UPDATE) |
| 79 | 17:06:01.535044 | T+2875ms | RR-SA-2 → PE-4 | **BROKEN UPDATE** (identical corruption) |
| 81 | 17:06:01.537888 | T+2878ms | PE-4 → RR-SA-2 | **NOTIFICATION 3/9** (2.8ms after broken UPDATE) |

**Cross-correlation: pcap wire times vs bgpd trace log times (IST=UTC+2):**

| Event | Pcap wire (UTC) | bgpd trace (UTC) | Offset |
|-------|-----------------|-------------------|--------|
| ExaBGP UPDATE received | 17:05:58.659978 | 17:05:58.660147 | +169µs (TCP rx → bgpd log) |
| Broken UPDATE sent PE-1 | 17:05:59.755407 | 17:05:59.755233 | −174µs (bgpd log → wire tx) |
| NOTIFICATION from PE-1 | 17:05:59.757263 | 17:05:59.757382 | +119µs (wire rx → bgpd log) |

### Frame 11: CORRECT Inbound (ExaBGP → RR-SA-2) — Raw Hex

```
0080  0e 17 00 01 86 04 0a 00 00 fe 00 0d 00 01 02 02
0090  02 02 00 64 01 18 0a 00 00
```

**Decode:**
```
80       Attr flags: Optional
0e       Type 14 = MP_REACH_NLRI
17       Length = 23 bytes
00 01    AFI = 1 (IPv4)
86       SAFI = 134 (FlowSpec-VPN)
04       NH length = 4 bytes
0a000afe NH = 10.0.0.254  ← CORRECT
00       Reserved
0d       NLRI length = 13
00 01 02020202 0064  RD = 0:2.2.2.2:100
01 18 0a0000         FlowSpec type 1 (dest), /24, 10.0.0.0
```

**Total MP_REACH_NLRI: 23 bytes. NH = 10.0.0.254. CORRECT.**

### Frame 26: BROKEN Outbound (RR-SA-2 → PE-1) — Raw Hex

```
005f                                              90
0060  0e 00 2b 00 01 86 04 00 00 00 00 00 00 00 00 00
0070  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0080  0d 00 01 02 02 02 02 00 64 01 18 0a 00 00
```

**Decode:**
```
90       Attr flags: Optional + Extended Length
0e       Type 14 = MP_REACH_NLRI
00 2b    Length = 43 bytes  ← INFLATED (should be 23!)
00 01    AFI = 1 (IPv4)
86       SAFI = 134 (FlowSpec-VPN)
04       NH length = 4

--- 24 ZERO BYTES WHERE NH SHOULD BE ---
00000000 00000000 00000000 00000000
00000000 00000000
← NH = 0.0.0.0 + 20 bytes padding (IPv6 buffer for IPv4 addr!)

00       Reserved
0d       NLRI length = 13
00 01 02020202 0064  RD = 0:2.2.2.2:100
01 18 0a0000         FlowSpec type 1 (dest), /24, 10.0.0.0
```

**Total MP_REACH_NLRI: 43 bytes (20 bytes too long). NH = 0.0.0.0 (zeroed). BROKEN.**

### What PE-1 Sees When Parsing

PE-1 reads NH_LEN=4, consumes 4 zero bytes as NH, reads 1 reserved byte, then tries to parse the remaining 34 bytes as NLRI. Those 34 bytes start with 19 zero bytes (the leftover padding) followed by the real NLRI — invalid FlowSpec encoding → **NOTIFICATION 3/9**.

---

## Evidence: Raw bgpd Traces (RR-SA-2)

Captured with `debug bgp updates-in` + `debug bgp updates-out` enabled. Timestamps in IST (UTC+2).

### 17:05:58.660147 UTC (T+0.169ms): ExaBGP UPDATE Received (CORRECT)

Pcap Frame 11 wire time: `17:05:58.659978 UTC`

```
2026-02-16T19:05:58.660147 +02:00 [DEBUG     ] [bgp_packet.c:2957:bgp_update_receive] [bgpd:1184:1184] 1208195:869936: vrf default peer 100.64.6.134: rcvd UPDATE w/ attr: , origin i, mp_nexthop 10.0.0.254, extended community RT:1234567L:300 flowspec-redirect-ip-nh, path 65200
```

### 17:05:58.660189 UTC (T+0.211ms): Route Processed

```
2026-02-16T19:05:58.660189 +02:00 [DEBUG     ] [bgp_route.c:10371:bgp_update_main] [bgpd:1184:1184] 1208196:869936: vrf id 0(default) peer 100.64.6.134: rcvd UPDATE DstPrefix:=10.0.0.0/24,SrcPrefix:=* (IPv4 Flowspec-VPN), addpath rx id 0
```

### 17:05:58.660323 UTC (T+0.345ms): Bestpath Done

```
2026-02-16T19:05:58.660323 +02:00 [INFO      ] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb] [bgpd:1184:1184] 1208197:869937: On vrf 0, bgpid 1(default): Finished bestpath marker IPv4 Flowspec-VPN after 1 steps
```

### 17:05:58.660366 UTC (T+0.388ms): Adj-Out Evaluation for PE-1 (upd_group 1) and PE-4 (upd_group 2)

```
2026-02-16T19:05:58.660366 +02:00 [DEBUG     ] [bgp_route.c:11101:bgp_route_handle_update_group_adj_out_reeval_out_route] [bgpd:1184:2720] 1208198:0: vrf id 0(default) upd_group 1: afi IPv4 safi flowspec-vpn announce check prefix DstPrefix:=10.0.0.0/24,SrcPrefix:=*
2026-02-16T19:05:58.660468 +02:00 [DEBUG     ] [bgp_route.c:11101:bgp_route_handle_update_group_adj_out_reeval_out_route] [bgpd:1184:2718] 1208199:0: vrf id 0(default) upd_group 2: afi IPv4 safi flowspec-vpn announce check prefix DstPrefix:=10.0.0.0/24,SrcPrefix:=*
```

### 17:05:58.660534 UTC (T+0.556ms): Chain Done

```
2026-02-16T19:05:58.660534 +02:00 [NOTICE    ] [bgp_chain.c:3777:bgp_chain_done] [bgpd:1184:1184] 1208200:869937: On vrf 0, bgpid 1(default) IPv4 Flowspec-VPN: Chain is done!
```

### 17:05:59.755233 UTC (T+1095ms): BROKEN UPDATE Sent to PE-1 (the buggy packet)

Pcap Frame 26 wire time: `17:05:59.755407 UTC` (+174µs from bgpd log to wire)

```
2026-02-16T19:05:59.755233 +02:00 [DEBUG     ] [bgp_packet.c:686:bgp_update_packet] [bgpd:1184:2720] 1208205:0: vrf default peer 1.1.1.1 send UPDATE DstPrefix:=10.0.0.0/24,SrcPrefix:=*, addpath tx id 2 (IPv4 Flowspec-VPN)
```

### 17:05:59.757382 UTC (T+1097ms): PE-1 Rejects → NOTIFICATION 3/9

Pcap Frame 31 wire time: `17:05:59.757263 UTC` (−119µs = wire arrives before bgpd logs it)

```
2026-02-16T19:05:59.757382 +02:00 [WARNING   ] [bgp_debug.c:447:bgp_notify_print] [bgpd:1184:1184] 1208206:869952: %NOTIFICATION: vrf default received from neighbor 1.1.1.1 3/9 (UPDATE Message Error/Optional Attribute Error) 0 bytes
```

### 17:05:59.757406 UTC (T+1097ms): Session Tear-down

```
2026-02-16T19:05:59.757406 +02:00 [DEBUG     ] [bgp_fsm.c:2142:bgp_event] [bgpd:1184:1184] 1208208:869953: 1.1.1.1 0x7f94783be048 on vrf default [FSM] Receive_NOTIFICATION_message (Established->Clearing)
2026-02-16T19:05:59.757411 +02:00 [WARNING   ] [bgp_fsm.c:849:bgp_stop] [bgpd:1184:1184] 1208209:869953: %ADJCHANGE: vrf default neighbor 1.1.1.1 Down BGP Notification received : UPDATE Message Error
```

### 17:05:59.757527 UTC (T+1097ms): All AFIs Cleared for PE-1

```
2026-02-16T19:05:59.757527 +02:00 [INFO      ] [bgp_chain.c:4750:bgp_chain_adj_out_and_advertise_marker_deinit] [bgpd:1184:1184] 1208219:869953: On vrf 0, bgpid 1(default) IPv4 Flowspec-VPN: remove peer 1.1.1.1 from advertise update group marker
```

### 17:05:59.758303 UTC (T+1098ms): FSM → Idle

```
2026-02-16T19:05:59.758303 +02:00 [DEBUG     ] [bgp_fsm.c:2142:bgp_event] [bgpd:1184:1184] 1208292:869955: 1.1.1.1 0x7f94783be048 on vrf default [FSM] Clearing_Completed (Clearing->Idle)
```

---

## Root Cause

**File:** `bgp_attr.c` → function `bgp_packet_mpattr_start_v4_flowspec_vpn()`

Called from: `bgp_packet.c:686:bgp_update_packet()`

The function unconditionally:
1. Allocates **24 bytes** for the NH field (IPv6 size) instead of checking if the route is IPv4 (4 bytes)
2. Writes **0.0.0.0** instead of the actual redirect-ip next-hop (10.0.0.254)
3. Calls `stream_forward(24)` padding the remaining 20 bytes with zeros

This inflates MP_REACH_NLRI from 23 → 43 bytes and corrupts both the NH value and the NLRI alignment for any downstream parser.

---

## Impact

- **Affects:** ALL outbound FlowSpec-VPN (SAFI 134) UPDATEs with redirect-ip action — **BOTH IPv4 and IPv6**
- **Not reflection-specific:** eBGP peers (e.g., Spirent at 25.25.25.1) also receive the broken encoding
- **Not AFI-specific:** IPv6 FlowSpec-VPN (AFI 2/SAFI 134) redirect-ip routes trigger the same bug. Tested 2026-02-17 with `announce flow route rd 2.2.2.2:100 destination 2001:db8::/48 redirect 2001:db8::fe` — PE-1/PE-4 sessions dropped identically
- **Session flapping:** Every BGP session that receives the corrupted UPDATE sends NOTIFICATION 3/9, causing an infinite establish→advertise→reject→teardown loop
- **Collateral:** All AFIs on the same session are torn down (IPv4 Unicast, VPN, EVPN, etc.)

---

## IPv6 FlowSpec-VPN Test (2026-02-17)

**Reproduction:** Injected `announce flow route rd 2.2.2.2:100 destination 2001:db8::/48 redirect 2001:db8::fe extended-community [ target:1234567:300 ]` via ExaBGP with `ipv6 flow-vpn` family negotiated.

**ExaBGP inbound encoding (correct):**
```
MP_REACH_NLRI:
  AFI: 2 (IPv6), SAFI: 134 (FlowSpec-VPN)
  NH length: 16 bytes
  NH: 2001:db8::fe  ← CORRECT 16-byte IPv6 address
  NLRI: RD 2.2.2.2:100, destination 2001:db8::/48
```

**Result:** PE-1 went from Established → Active, PE-4 went from Established → Idle — identical session teardown as IPv4. After withdrawing the IPv6 route, all sessions recovered within 30 seconds.

**Second test (correct RT):** Re-injected with RT `1234567:400` (matching PE-1's `ipv6-flowspec` import and RR-SA-2's new VRF `ipv6-flowspec` import) — identical session teardown. RT correctness has zero effect.

**Conclusion:** The outbound encoding bug in `bgp_packet_mpattr_start_v4_flowspec_vpn()` is hit for BOTH IPv4 and IPv6 FlowSpec-VPN redirect-ip routes. The function name itself (`_v4_`) suggests it was only designed for IPv4 but is also called for IPv6 FlowSpec-VPN outbound UPDATEs. The bug is 100% in the outbound packet builder — not related to RT matching, VRF SAFI config, IPv4 vs IPv6, or iBGP vs eBGP.

---

## Files

| File | Location | Description |
|------|----------|-------------|
| `reproduce_full_flow_v2.pcap` | Server: `/home/dn/SCALER/FLOWSPEC_VPN/bug_evidence/` | Full IPv4 pcap with frames 11/26/79/144 |
| `reproduce_full_flow_v2.pcap` | Mac: `/tmp/flowspec_vpn_encoding_bug_RR-SA-2.pcap` | Same pcap, delivered to Mac with Wireshark filter applied |
| `flowspec_vpn_redirect_ip_encoding_bug_RR-SA-2.pcap` | Server: `/home/dn/SCALER/FLOWSPEC_VPN/bug_evidence/` | Earlier capture (same bug, IPv4) |
| `ipv6_flowspec_vpn_redirect_ip_encoding_bug.pcap` | Server: `/home/dn/SCALER/FLOWSPEC_VPN/bug_evidence/` | IPv6 test capture showing inbound correct UPDATE + PE-1/PE-4 withdrawals |
