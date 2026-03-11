# Debug Session: PE-4 -- Reproduce FlowSpec redirect-ip with MPLS NH (Action skipped)
Started: 2026-03-02 13:45:00 UTC | Device: YOR_CL_PE-4
Image: DNOS [26.1.0] build [27_priv]
Topic: FlowSpec redirect-ip rule where NCP skips Action 4 because NH resolves via MPLS tunnel
Session mode: INVESTIGATE
Related: BUG_FLOWSPEC_REDIRECT_IP_MPLS_NH_SKIPPED.md

---

## Phase 0: Pre-Flight

### [13:34:31] [show] show system version
```
System Name: YOR_CL_PE-4
Version: DNOS [26.1.0] build [27_priv], Copyright 2026 DRIVENETS LTD.
Patch: N/A
```

### [13:34:34] [show] show bgp ipv4 flowspec-vpn summary
```
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 1

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567      46254        976    0     0       0 01:39:53                   1

Total number of established neighbors with IPv4 Flowspec-VPN 1/1
Total number of NSR capable BGP sessions 0
```

### [13:34:36] [show] show flowspec ncp 18 (BEFORE withdraw/re-inject)
```
Address-Family IPv4
	Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
		Vrf: ALPHA
		Actions: Redirect-ip-nh: N/A
		Status: Installed
```

### [13:34:39] [show] show flowspec instance vrf ALPHA ipv4 (BEFORE)
```
Address-family: IPv4

	Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
		Actions: flowspec-redirect-ip-nh:10.0.0.230
		Match packet counter: 0
```

### [13:34:48] [show] show route vrf ALPHA 10.0.0.230
```
VRF: ALPHA
Routing entry for 10.0.0.230/32
  Known via "bgp", priority low, distance 200, metric 0, vrf ALPHA, best, fib
  Last update 01:21:30 ago, ack
    1.1.1.1 [vrf default] (recursive) label 1040385
  *   14.14.14.1, via ge100-18/0/0.14 [vrf default] label 3
```

### [13:34:51] [show] show bgp ipv4 flowspec-vpn
```
BGP IPv4 Flowspec-VPN, local router ID is 4.4.4.4
Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path, P - Pending, F - RIB-Install-Filtered
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
Origin codes: i - IGP, e - EGP, ? - incomplete
Next hop codes: v - Via another VRF
RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


Route Distinguisher: 1.1.1.1:100

 U*>i DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
         00:51:43, localpref:100 AS path: 123 1234567 65200 i, next hop: 10.0.0.230, from: 2.2.2.2

Displayed 1 out of 1 total prefixes, 1 out of 1 total paths
```

### [13:34:53] [show] show system npu-resources resource-type flowspec
```
Flowspec usage:

| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 6     | 1                     | 1                      | 1/12000                      | 0                     | 0                      | 0/4000                       |
| 18    | 1                     | 1                      | 1/12000                      | 0                     | 0                      | 0/4000                       |
```

---

## Phase 1: Reproduce (withdraw + re-inject via ExaBGP)

### [13:35:08] [local] ExaBGP withdraw
```
echo "withdraw flow route rd 1.1.1.1:100 next-hop 10.0.0.230 destination 100.100.100.1/32 source 16.16.16.0/30 redirect-to-nexthop extended-community [ target:1234567:100 ]" > /run/exabgp/exabgp.in
Withdraw sent at 2026-03-02 11:35:08 UTC
```

### [13:35:17] [local] ExaBGP re-announce (after 5s wait)
```
echo "announce flow route rd 1.1.1.1:100 next-hop 10.0.0.230 destination 100.100.100.1/32 source 16.16.16.0/30 redirect-to-nexthop extended-community [ target:1234567:100 ]" > /run/exabgp/exabgp.in
Re-announce sent at 2026-03-02 11:35:17 UTC
```

---

## Phase 2: Trace Collection — PE-4 (all fresh, timestamp 13:35)

### [13:35:42] [show] show file traces routing_engine/fibmgrd_traces | include is_flowspec
```
2026-03-02T12:11:03.455445 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:20189:20189] 3474146:1077929: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 61 is_support_indirection: true address { v4 { value: 167772390 } } is_flowspec: true } }
2026-03-02T12:11:08.456187 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:20189:20189] 3477994:1078036: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 61 is_support_indirection: true address { v4 { value: 167772390 } } is_flowspec: true } }
2026-03-02T12:11:13.457048 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:20189:20189] 3481837:1078147: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 61 is_support_indirection: true address { v4 { value: 167772390 } } is_flowspec: true } }
2026-03-02T12:11:18.451105 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:20189:20189] 3485689:1078257: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 61 is_support_indirection: true address { v4 { value: 167772390 } } is_flowspec: true } }
2026-03-02T13:17:01.125031 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:20189:20189] 3785302:1189494: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 62 is_support_indirection: true nexthops { if_id { index: 14377 cheetah_index: 13353 } if_name: "ge100-18/0/0.14" address { v4 { value: 235802113 } } vrf_id: 0 mpls_labels: 1040385 ecmp_weight: 0 protocol: LDP } address { v4 { value: 167772390 } } is_flowspec: true protocol: BGP } }
2026-03-02T13:35:23.475690 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:20189:20189] 3786523:1211375: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 63 is_support_indirection: true nexthops { if_id { index: 14377 cheetah_index: 13353 } if_name: "ge100-18/0/0.14" address { v4 { value: 235802113 } } vrf_id: 0 mpls_labels: 1040385 ecmp_weight: 0 protocol: LDP } address { v4 { value: 167772390 } } is_flowspec: true protocol: BGP } }
```

**Analysis — Three distinct protobuf phases visible:**
1. **12:11:03 — oid 61 (BROKEN):** Old protobuf before SW-242876 fix was triggered. No `nexthops` array, no `vrf_id`, bare `address` only.
2. **13:17:01 — oid 62 (FIXED CP):** After VRF RT import config was applied. Full `nexthops` array with `if_name`, `vrf_id: 0`, `mpls_labels: 1040385`, `protocol: LDP`.
3. **13:35:23 — oid 63 (FRESH REPRO):** Our fresh re-injection. Identical correct protobuf — `nexthops { if_name: "ge100-18/0/0.14" address: 235802113 vrf_id: 0 mpls_labels: 1040385 protocol: LDP }`. **Control plane is correct.**

### [13:36:02] [show] show file ncp 18 traces datapath/wb_agent.flowspec | include 13:35
```
2026-03-02T13:35:08.934421 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2019] Flowspec: Received BGP IPv4 NLRI: 012064646401021e10101000 : DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
2026-03-02T13:35:08.934466 +02:00 [DEBUG     ] [FlowspecTable.cpp:238 DeleteRule()] [wb_fib_fpm:2019] Flowspec: Deleting NLRI rule id 69000
2026-03-02T13:35:08.934616 +02:00 [INFO      ] [FlowspecTcamManager.cpp:63 DeleteRule()] [wb_fib_fpm:2019] Flowspec: Deleting rule with priority 3000000
2026-03-02T13:35:08.934782 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2019] Flowspec: Succeeded to delete rule in BCM. Num entries: 1
2026-03-02T13:35:08.934809 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2019] Flowspec: Succeeded to delete flowspec rule with length=12
2026-03-02T13:35:23.476435 +02:00 [DEBUG     ] [FlowspecManager.cpp:151 AddRuleInternal()] [wb_fib_fpm:2019] Flowspec: Received BGP IPv4 NLRI: 012064646401021e10101000 : DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
2026-03-02T13:35:23.476467 +02:00 [DEBUG     ] [FlowspecManager.cpp:161 AddRuleInternal()] [wb_fib_fpm:2019] Flowspec: actions - type: redirect-ip-nh(4)
2026-03-02T13:35:23.476479 +02:00 [DEBUG     ] [FlowspecManager.cpp:183 AddRuleInternal()] [wb_fib_fpm:2019] Flowspec: actions - nh_oid: 63 mirror: 0
2026-03-02T13:35:23.476673 +02:00 [DEBUG     ] [FlowspecTcamManager.cpp:309 ReserveQualifiers()] [wb_fib_fpm:2019] Flowspec: local_config_flowspec_should_validate_resources: 1
2026-03-02T13:35:23.476683 +02:00 [DEBUG     ] [FlowspecRuleData.cpp:290 DeterminePriority()] [wb_fib_fpm:2019] Flowspec: Adding rule between priority 2000000 to priority 4000000
2026-03-02T13:35:23.476691 +02:00 [INFO      ] [FlowspecTcamManager.cpp:241 WriteRuleInTcam()] [wb_fib_fpm:2019] Flowspec: Adding rule with priority 3000000
2026-03-02T13:35:23.476706 +02:00 [DEBUG     ] [FlowspecTcamManager.cpp:271 WriteRuleInTcam()] [wb_fib_fpm:2019] Flowspec: Action 4 skipped, probably because it is unreachable
2026-03-02T13:35:23.479198 +02:00 [INFO      ] [FlowspecTcamManager.cpp:195 operator()()] [wb_fib_fpm:2019] Flowspec: Succeeded to add rule in BCM
2026-03-02T13:35:23.479227 +02:00 [INFO      ] [FlowspecTcamManager.cpp:283 WriteRuleInTcam()] [wb_fib_fpm:2019] Flowspec: Succeeded to write 1 rules in TCAM for rule id 69001
2026-03-02T13:35:23.479247 +02:00 [DEBUG     ] [FlowspecManager.cpp:222 AddRuleInternal()] [wb_fib_fpm:2019] Flowspec: Succeeded to add IPv4 flowspec rule with length=12
2026-03-02T13:35:23.486446 +02:00 [INFO      ] [FlowspecTcamManager.cpp:241 WriteRuleInTcam()] [wb_fib_fpm:2019] Flowspec: Updating rule with priority 3000000
2026-03-02T13:35:23.486512 +02:00 [INFO      ] [FlowspecTcamManager.cpp:199 operator()()] [wb_fib_fpm:2019] Flowspec: Succeeded to update rule in BCM
2026-03-02T13:35:23.486537 +02:00 [INFO      ] [FlowspecTcamManager.cpp:283 WriteRuleInTcam()] [wb_fib_fpm:2019] Flowspec: Succeeded to write 1 rules in TCAM for rule id 69001
```

**SMOKING GUN: `FlowspecTcamManager.cpp:271` — "Action 4 skipped, probably because it is unreachable"**
- Action 4 = redirect-ip-nh
- nh_oid: 63 (the correct protobuf with MPLS labels)
- Rule IS added to TCAM but WITHOUT the redirect action → Status: Installed, but Redirect-ip-nh: N/A

### [13:36:06] [show] show file traces routing_engine/bgpd_traces | include 13:35 | include flowspec
```
2026-03-02T13:35:08.933212 +02:00 [INFO      ] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb] [bgpd:19982:19982] 365431:460496: On vrf 0, bgpid 1(default): Finished bestpath marker IPv4 Flowspec-VPN after 1 steps
2026-03-02T13:35:08.933244 +02:00 [NOTICE    ] [bgp_chain.c:3777:bgp_chain_done] [bgpd:19982:19982] 365432:460496: On vrf 0, bgpid 1(default) IPv4 Flowspec-VPN: Chain is done!
2026-03-02T13:35:08.933373 +02:00 [INFO      ] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb] [bgpd:19982:19982] 365434:460496: On vrf 104, bgpid 2(ALPHA): Finished bestpath marker IPv4 Flowspec after 1 steps
2026-03-02T13:35:08.933386 +02:00 [NOTICE    ] [bgp_chain.c:3777:bgp_chain_done] [bgpd:19982:19982] 365435:460496: On vrf 104, bgpid 2(ALPHA) IPv4 Flowspec: Chain is done!
2026-03-02T13:35:23.474770 +02:00 [INFO      ] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb] [bgpd:19982:19982] 365465:460582: On vrf 0, bgpid 1(default): Finished bestpath marker IPv4 Flowspec-VPN after 1 steps
2026-03-02T13:35:23.474872 +02:00 [NOTICE    ] [bgp_chain.c:3777:bgp_chain_done] [bgpd:19982:19982] 365466:460582: On vrf 0, bgpid 1(default) IPv4 Flowspec-VPN: Chain is done!
2026-03-02T13:35:23.474996 +02:00 [INFO      ] [bgp_chain.c:373:bgp_chain_bestpath_marker_finished_cb] [bgpd:19982:19982] 365468:460582: On vrf 104, bgpid 2(ALPHA): Finished bestpath marker IPv4 Flowspec after 1 steps
2026-03-02T13:35:23.475002 +02:00 [NOTICE    ] [bgp_chain.c:3777:bgp_chain_done] [bgpd:19982:19982] 365469:460582: On vrf 104, bgpid 2(ALPHA) IPv4 Flowspec: Chain is done!
```

### [13:36:22] [show] show file traces routing_engine/rib-manager_traces | include 13:35 | include lowspec
```
2026-03-02T13:35:08.933553 +02:00 [DEBUG     ] [zebra_rnh.c:568:zebra_remove_rnh_client] [rib-manager:19984:19984] 1139992:472109: NHT: Client bgp (bgp-flowspec) unregisters rnh 10.0.0.230/32 vrf 104
2026-03-02T13:35:08.933593 +02:00 [ERROR     ] [zebra_flowspec_db.c:182:destroy_rn_for_nh_tracking] [rib-manager:19984:19984] 1139995:472109: Got NULL parameter!
2026-03-02T13:35:23.475225 +02:00 [DEBUG     ] [zebra_rnh.c:511:zebra_add_rnh_client] [rib-manager:19984:19984] 1140012:472242: NHT: Client bgp (bgp-flowspec) registers rnh 10.0.0.230/32 in vrf 104
```

**Notable:** `zebra_flowspec_db.c:182:destroy_rn_for_nh_tracking — Got NULL parameter!` — an ERROR during withdraw. May indicate cleanup issue but doesn't affect the MPLS NH bug.

### [13:36:35] [show] show file ncp 6 traces datapath/wb_agent.flowspec | include 13:35
```
2026-03-02T13:35:08.934674 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2012] Flowspec: Received BGP IPv4 NLRI: 012064646401021e10101000 : DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
2026-03-02T13:35:08.934751 +02:00 [DEBUG     ] [FlowspecTable.cpp:238 DeleteRule()] [wb_fib_fpm:2012] Flowspec: Deleting NLRI rule id 69000
2026-03-02T13:35:08.934892 +02:00 [INFO      ] [FlowspecTcamManager.cpp:63 DeleteRule()] [wb_fib_fpm:2012] Flowspec: Deleting rule with priority 3000000
2026-03-02T13:35:08.935066 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2012] Flowspec: Succeeded to delete rule in BCM. Num entries: 1
2026-03-02T13:35:08.935087 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2012] Flowspec: Succeeded to delete flowspec rule with length=12
2026-03-02T13:35:23.476784 +02:00 [DEBUG     ] [FlowspecManager.cpp:151 AddRuleInternal()] [wb_fib_fpm:2012] Flowspec: Received BGP IPv4 NLRI: 012064646401021e10101000 : DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
2026-03-02T13:35:23.476819 +02:00 [DEBUG     ] [FlowspecManager.cpp:161 AddRuleInternal()] [wb_fib_fpm:2012] Flowspec: actions - type: redirect-ip-nh(4)
2026-03-02T13:35:23.476842 +02:00 [DEBUG     ] [FlowspecManager.cpp:183 AddRuleInternal()] [wb_fib_fpm:2012] Flowspec: actions - nh_oid: 63 mirror: 0
2026-03-02T13:35:23.477059 +02:00 [DEBUG     ] [FlowspecTcamManager.cpp:309 ReserveQualifiers()] [wb_fib_fpm:2012] Flowspec: local_config_flowspec_should_validate_resources: 1
2026-03-02T13:35:23.477069 +02:00 [DEBUG     ] [FlowspecRuleData.cpp:290 DeterminePriority()] [wb_fib_fpm:2012] Flowspec: Adding rule between priority 2000000 to priority 4000000
2026-03-02T13:35:23.477078 +02:00 [INFO      ] [FlowspecTcamManager.cpp:241 WriteRuleInTcam()] [wb_fib_fpm:2012] Flowspec: Adding rule with priority 3000000
2026-03-02T13:35:23.477094 +02:00 [DEBUG     ] [FlowspecTcamManager.cpp:271 WriteRuleInTcam()] [wb_fib_fpm:2012] Flowspec: Action 4 skipped, probably because it is unreachable
2026-03-02T13:35:23.479607 +02:00 [INFO      ] [FlowspecTcamManager.cpp:195 operator()()] [wb_fib_fpm:2012] Flowspec: Succeeded to add rule in BCM
2026-03-02T13:35:23.479646 +02:00 [INFO      ] [FlowspecTcamManager.cpp:283 WriteRuleInTcam()] [wb_fib_fpm:2012] Flowspec: Succeeded to write 1 rules in TCAM for rule id 69001
2026-03-02T13:35:23.479662 +02:00 [DEBUG     ] [FlowspecManager.cpp:222 AddRuleInternal()] [wb_fib_fpm:2012] Flowspec: Succeeded to add IPv4 flowspec rule with length=12
2026-03-02T13:35:23.486780 +02:00 [INFO      ] [FlowspecTcamManager.cpp:241 WriteRuleInTcam()] [wb_fib_fpm:2012] Flowspec: Updating rule with priority 3000000
2026-03-02T13:35:23.486852 +02:00 [INFO      ] [FlowspecTcamManager.cpp:199 operator()()] [wb_fib_fpm:2012] Flowspec: Succeeded to update rule in BCM
2026-03-02T13:35:23.486878 +02:00 [INFO      ] [FlowspecTcamManager.cpp:283 WriteRuleInTcam()] [wb_fib_fpm:2012] Flowspec: Succeeded to write 1 rules in TCAM for rule id 69001
```

**NCP 6 shows IDENTICAL behavior to NCP 18: Action 4 skipped on BOTH NCPs.**

### [13:36:12] [show] show flowspec ncp 18 (AFTER repro)
```
Address-Family IPv4
	Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
		Vrf: ALPHA
		Actions: Redirect-ip-nh: N/A
		Status: Installed
```

### [13:36:38] [show] show flowspec ncp 6 (AFTER repro)
```
Address-Family IPv4
	Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
		Vrf: ALPHA
		Actions: Redirect-ip-nh: N/A
		Status: Installed
```

### [13:36:41] [show] show flowspec instance vrf ALPHA ipv4 (AFTER repro)
```
Address-family: IPv4

	Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
		Actions: flowspec-redirect-ip-nh:10.0.0.230
		Match packet counter: 0
```

---

## Phase 3: Comparison — PE-1 (WORKING case, direct L3 NH)

### [13:36:55] [show] PE-1: show file traces routing_engine/fibmgrd_traces | include is_flowspec
```
2026-03-02T12:36:47.083442 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1554:1554] 2586966:1599967: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 63 is_support_indirection: true nexthops { if_id { index: 14340 cheetah_index: 13316 } if_name: "ge400-0/0/5.1" address { v4 { value: 269488130 } } vrf_id: 1 ecmp_weight: 0 protocol: BGP } address { v4 { value: 167772390 } } is_flowspec: true protocol: BGP } }
2026-03-02T12:43:05.674084 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1554:1554] 2639335:1618670: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 64 is_support_indirection: true nexthops { if_id { index: 14340 cheetah_index: 13316 } if_name: "ge400-0/0/5.1" address { v4 { value: 269488130 } } vrf_id: 1 ecmp_weight: 0 protocol: BGP } address { v4 { value: 167772390 } } is_flowspec: true protocol: BGP } }
2026-03-02T13:35:17.853998 +02:00 [DEBUG     ] [MessageParser.cpp:280:HandleMessageFromZebra] [fibmgrd:1554:1554] 2641031:1671017: [PACKET] Got protobuf message from RIB-Manager: nexthop { type: ADD_NEXTHOP add_nexthop { oid: 65 is_support_indirection: true nexthops { if_id { index: 14340 cheetah_index: 13316 } if_name: "ge400-0/0/5.1" address { v4 { value: 269488130 } } vrf_id: 1 ecmp_weight: 0 protocol: BGP } address { v4 { value: 167772390 } } is_flowspec: true protocol: BGP } }
```

### [13:37:07] [show] PE-1: show flowspec ncp 0
```
Address-Family IPv4
	Flow: DstPrefix:=100.100.100.1/32,SrcPrefix:=16.16.16.0/30
		Vrf: ALPHA
		Actions: Redirect-ip-nh: 10.0.0.230
		Status: Installed
```

### [13:37:09] [show] PE-1: show route vrf ALPHA 10.0.0.230
```
VRF: ALPHA
Routing entry for 10.0.0.230/32
  Known via "bgp", priority low, distance 20, metric 0, vrf ALPHA, best, fib
  Last update 01:23:55 ago, ack
  * 16.16.16.2, via ge400-0/0/5.1
```

---

## Phase 4: Root Cause Comparison

### Protobuf Comparison (ADD_NEXTHOP)

| Field | PE-1 (WORKS) | PE-4 (FAILS) |
|-------|--------------|---------------|
| oid | 65 | 63 |
| if_name | ge400-0/0/5.1 | ge100-18/0/0.14 |
| address (gateway) | 269488130 (16.16.16.2) | 235802113 (14.14.14.1) |
| vrf_id | 1 (VRF ALPHA) | 0 (default) |
| mpls_labels | **NONE** | **1040385** |
| protocol | BGP | LDP |
| target address | 167772390 (10.0.0.230) | 167772390 (10.0.0.230) |
| is_flowspec | true | true |

### Route Resolution Comparison

| Aspect | PE-1 (WORKS) | PE-4 (FAILS) |
|--------|--------------|---------------|
| 10.0.0.230 known via | bgp, distance 20 | bgp, distance 200 |
| Resolution | Direct: 16.16.16.2 via ge400-0/0/5.1 | Recursive: 1.1.1.1 [vrf default] label 1040385 → 14.14.14.1 via ge100-18/0/0.14 label 3 |
| Encapsulation | None (plain IP) | MPLS (2 labels: VPN + LDP) |
| NCP result | Redirect-ip-nh: 10.0.0.230 | Redirect-ip-nh: N/A |
| FlowspecTcamManager | Action programmed | **Action 4 skipped, probably because it is unreachable** |

### Root Cause

`FlowspecTcamManager.cpp:271` in NCP's `WriteRuleInTcam()` explicitly skips programming the redirect-ip action (Action type 4) when the resolved next-hop object (nh_oid) requires MPLS encapsulation. The check considers MPLS-tunneled next-hops as "unreachable" from the TCAM programming perspective.

The control plane (rib-manager → fib-manager protobuf) is correct — it sends a fully resolved `ADD_NEXTHOP` with MPLS labels, interface, and gateway. The NCP receives it, resolves nh_oid 63, but when it attempts to program the TCAM redirect action, it finds the NH object requires MPLS encapsulation and skips it.

### RFC Violation

**draft-ietf-idr-flowspec-redirect-ip-02, Section 3:**
> "If the 'target route' has one or more tunnel next-hops then the appropriate encapsulations SHOULD be added to the redirected/copied packets."

The NCP should add MPLS encapsulation to redirected packets, not skip the action entirely.

---

## Session Conclusion
Ended: 2026-03-02 13:38:00 UTC
Verdict: BUG CONFIRMED (reproducible, fresh traces)
Bug file: ~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_FLOWSPEC_REDIRECT_IP_MPLS_NH_SKIPPED.md
