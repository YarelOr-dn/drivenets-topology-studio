# BUG: FlowSpec BGP Rules Not Recovered After TCAM Overflow Clears

| Field | Value |
|-------|-------|
| **Date Discovered** | 2026-02-26 |
| **Device** | RR-SA-2 |
| **Image (discovered)** | 26.1.0.27_priv.easraf_flowspec_vpn_wbox_side_29 |
| **Branch** | `easraf/flowspec_vpn/wbox_side` |
| **Severity** | Critical — BGP FlowSpec rules permanently lost after TCAM overflow resolves |
| **Component** | NCP / wb_agent FlowSpec (datapath) |
| **Jira** | TBD |

## Retest History

| Date | Image (full path) | Build | Result | Notes |
|------|-------------------|-------|--------|-------|
| 2026-02-26 | 26.1.0.27_priv.easraf_flowspec_vpn_wbox_side_29 | 29 | BUG PRESENT | Initial discovery. Full scale: 12K IPv4 + 4K IPv6 per SAFI. |

## One-Line Summary

When FlowSpec TCAM is full and BGP FlowSpec rules fail to install, they are never retried when TCAM space becomes available — even after all blocking rules are withdrawn and TCAM is completely empty.

## Expected Results

When FlowSpec rules that failed TCAM installation due to capacity are still present in the BGP table and routing database, and TCAM space is freed by withdrawing other rules, the pending rules should be automatically installed into the available TCAM space. `show system npu-resources resource-type flowspec` should reflect the newly installed rules.

## Actual Results

After TCAM space is fully freed (0/12000 IPv4, 0/4000 IPv6 installed), BGP FlowSpec rules that previously failed installation remain permanently stuck. `show system npu-resources` shows 0 installed despite routes being present in BGP and zebra FlowSpec DB. Only the first 400 rules per address family are retained as "received" by the NCP; all remaining rules are silently discarded. No automatic retry occurs.

## Steps to Reproduce

1. Configure a VRF with `import-vpn route-target` for FlowSpec-VPN (SAFI 134)
2. Inject FlowSpec rules at full TCAM capacity via plain FlowSpec (SAFI 133) — e.g., 12,000 IPv4 + 4,000 IPv6 rules
3. Simultaneously inject the same scale of FlowSpec-VPN (SAFI 134) rules with matching RTs
4. Verify SAFI 133 fills the TCAM first and SAFI 134 rules are rejected (`BGP_FLOWSPEC_UNSUPPORTED_RULE` syslog)
5. Withdraw all SAFI 133 rules — TCAM becomes completely empty
6. Observe: SAFI 134 rules are NOT installed into the freed TCAM space
7. Verify with `show system npu-resources resource-type flowspec` — shows 0 installed

---

## Test Setup

- **Injector:** ExaBGP on 100.64.6.134 peering with PE-1 (eBGP AS 1234567)
- **Route Reflector:** RR-SA-2 (iBGP AS 123, receives from PE-1)
- **VRF:** ZULU on RR-SA-2, configured with:
  - `import-vpn route-target 300:300` under `address-family ipv4-flowspec`
  - `import-vpn route-target 1234567:401` under `address-family ipv6-flowspec`
- **TCAM capacity:** IPv4: 12,000 / IPv6: 4,000

| Route Set | Count | SAFI | Base Prefix | RD | RD Type | RT |
|-----------|-------|------|-------------|-----|---------|-----|
| IPv4 FlowSpec | 12,000 | 133 | 10.0.0.0/24 | N/A | N/A | N/A |
| IPv6 FlowSpec | 4,000 | 133 | 2001:db8::/48 | N/A | N/A | N/A |
| IPv4 FlowSpec-VPN | 12,000 | 134 | 172.16.0.0/24 | 1.1.1.1:200 | Type 1 (IP) | 300:300 |
| IPv6 FlowSpec-VPN | 4,000 | 134 | 2001:db9::/48 | 1234567:200 | Type 2 (4B-ASN) | 1234567:401 |

---

## Phase 1: BEFORE — Both SAFIs Injected, TCAM Full

### Syslog — SAFI 134 IPv4 rules rejected (TCAM full at 12:58:17)

```
local7.warning 2026-02-26T12:58:17.215+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv4 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=172.48.74.0/24,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:58:17.215+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv4 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=172.48.73.0/24,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:58:17.216+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv4 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=172.48.72.0/24,SrcPrefix:=*, Actions: traffic rate
```

### NPU Resources at 12:58:20 — SAFI 133 fills TCAM, SAFI 134 IPv4 overflows

```
RR-SA-2(cfg 26-Feb-2026-12:58:20)# show system npu-resources resource-type flowspec


Flowspec usage:

| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 0     | 12400                 | 12000                  | 12000/12000                  | 4000                  | 4000                   | 4000/4000                    |
```

### Syslog — SAFI 134 IPv6 rules rejected (12:59:02)

```
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f6e::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f6d::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f6c::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f6b::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f6a::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f69::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f68::/48,SrcPrefix:=*, Actions: traffic rate
local7.warning 2026-02-26T12:59:02.197+02:00 RR-SA-2 BGP - - - BGP_FLOWSPEC_UNSUPPORTED_RULE:BGP flowspec IPv6 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=2001:db9:f67::/48,SrcPrefix:=*, Actions: traffic rate
```

### NPU Resources at 13:00:18 — Both AFs overflowing (IPv6 SAFI 134 now also rejected)

```
RR-SA-2(cfg 26-Feb-2026-13:00:18)# show system npu-resources resource-type flowspec


Flowspec usage:

| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 0     | 12400                 | 12000                  | 12000/12000                  | 4400                  | 4000                   | 4000/4000                    |
```

### show flowspec ncp 0 at 13:00:52 — SAFI 133 occupying TCAM (first ~240 rules shown)

```
RR-SA-2(cfg 26-Feb-2026-13:00:52)# show flowspec ncp 0


Address-Family IPv4
	Flow: DstPrefix:=10.0.0.0/24,SrcPrefix:=*
		Vrf: default
		Actions: Traffic-rate: 0 bps
		Status: Installed
	Flow: DstPrefix:=10.0.1.0/24,SrcPrefix:=*
		Vrf: default
		Actions: Traffic-rate: 0 bps
		Status: Installed
	Flow: DstPrefix:=10.0.2.0/24,SrcPrefix:=*
		Vrf: default
		Actions: Traffic-rate: 0 bps
		Status: Installed

[... 12,000 SAFI 133 rules, all Status: Installed in default VRF ...]

	Flow: DstPrefix:=10.0.242.0/24,SrcPrefix:=*
		Vrf: default
		Actions: Traffic-rate: 0 bps
		Status: Installed
```

### show flowspec ncp 0 — SAFI 134 rules: "Not Installed, out of resources" (13:01:10)

```
RR-SA-2(cfg 26-Feb-2026-13:01:10)# show flowspec ncp 0 | include " not installed"

		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		Status: Not Installed, out of resources
		[... continues ...]
```

```
RR-SA-2(cfg 26-Feb-2026-13:01:18)# show flowspec ncp 0 | include " not installed" | count
lines: 800
```

800 lines = 400 IPv4 SAFI 134 + 400 IPv6 SAFI 134 rules marked "Not Installed, out of resources".
This confirms the NCP received exactly 400 per AF before stopping, matching `show npu-resources` (12400 - 12000 = 400 IPv4, 4400 - 4000 = 400 IPv6).

### bgpd traces — Control plane import PERMIT for all SAFI 134 routes (routing did its job)

```
RR-SA-2(26-Feb-2026-14:29:59)# show file traces routing_engine/bgpd_traces | include PERMIT | tail 10 | no-more
2026-02-26T12:59:02.189620 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411156:111106: Import policy for route DstPrefix:=2001:db9:f70::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189637 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411162:111106: Import policy for route DstPrefix:=2001:db9:f6f::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189655 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411168:111106: Import policy for route DstPrefix:=2001:db9:f6e::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189679 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411174:111106: Import policy for route DstPrefix:=2001:db9:f6d::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189721 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411180:111106: Import policy for route DstPrefix:=2001:db9:f6c::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189753 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411186:111106: Import policy for route DstPrefix:=2001:db9:f6b::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189784 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411192:111106: Import policy for route DstPrefix:=2001:db9:f6a::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189810 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411198:111106: Import policy for route DstPrefix:=2001:db9:f69::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189838 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411204:111106: Import policy for route DstPrefix:=2001:db9:f68::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
2026-02-26T12:59:02.189867 +02:00 [DEBUG     ] [bgp_service.c:846:bgp_service_is_deny_by_import_vpn_policy] [bgpd:1158:1158] 411210:111106: Import policy for route DstPrefix:=2001:db9:f67::/48,SrcPrefix:=* peer 1.1.1.1 vrf ZULU returned PERMIT
```

### bgpd traces — RT lookup success for all routes

```
RR-SA-2(26-Feb-2026-14:27:54)# show file traces routing_engine/bgpd_traces | include rt_node | tail 10 | no-more
2026-02-26T12:59:02.189617 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411154:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189635 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411160:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189652 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411166:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189673 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411172:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189716 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411178:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189748 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411184:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189778 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411190:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189805 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411196:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189831 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411202:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
2026-02-26T12:59:02.189861 +02:00 [DEBUG     ] [bgp_service.c:933:bgp_service_fill_import_vpn_bitmap_per_type] [bgpd:1158:1158] 411208:111106: Found rt_node 0x7f565d2032b0 for 1234567L:401
```

---

## Phase 2: AFTER — SAFI 133 Withdrawn (~13:02), TCAM Empty, SAFI 134 NOT Recovered

### NPU Resources at 13:04:19 — First post-withdrawal check (THE BUG APPEARS)

```
RR-SA-2(cfg 26-Feb-2026-13:04:19)# show system npu-resources resource-type flowspec


Flowspec usage:

| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 0     | 400                   | 0                      | 0/12000                      | 400                   | 0                      | 0/4000                       |
```

SAFI 133 withdrawn at ~13:02. TCAM is empty. The 400 SAFI 134 rules that were "Not Installed, out of resources" are still received but NOT installed. The other 11,600 IPv4 + 3,600 IPv6 SAFI 134 rules are gone entirely.

### BGP Summary — SAFI 134 routes still present, SAFI 133 gone

```
RR-SA-2(26-Feb-2026-14:25:15)# show bgp ipv4 flowspec-vpn summary | no-more

BGP router identifier 2.2.2.2, local AS number 123
BGP table node count 1

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  1.1.1.1         4    1234567       8948        613    0     0       0 01:36:54               12000
  4.4.4.4         4    1234567        108       3861    0     0   12000 01:32:59                   0
  25.25.25.1      4      65000          0          0    0     0       0 never      Active          
  100.64.6.134    4      65200          0          0    0     0       0 never     Idle (Admin)

Total number of established neighbors with IPv4 Flowspec-VPN 2/4
```

```
RR-SA-2(26-Feb-2026-14:25:18)# show bgp ipv4 flowspec summary | no-more

BGP router identifier 2.2.2.2, local AS number 123
BGP table node count 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  1.1.1.1         4    1234567       8948        613    0     0       0 01:36:57                   0
  4.4.4.4         4    1234567        109       3862    0     0       0 01:33:02                   0
  25.25.25.1      4      65000          0          0    0     0       0 never      Active          
  100.64.6.134    4      65200          0          0    0     0       0 never     Idle (Admin)

Total number of established neighbors with IPv4 Flowspec 2/4
```

```
RR-SA-2(26-Feb-2026-14:25:21)# show bgp ipv6 flowspec-vpn summary | no-more

BGP router identifier 2.2.2.2, local AS number 123
BGP table node count 1

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  1.1.1.1         4    1234567       8949        614    0     0       0 01:37:00                4000
  4.4.4.4         4    1234567        109       3862    0     0    4000 01:33:05                   0
  25.25.25.1      4      65000          0          0    0     0       0 never      Connect         
  100.64.6.134    4      65200          0          0    0     0       0 never     Idle (Admin)

Total number of established neighbors with IPv6 Flowspec-VPN 2/4
```

```
RR-SA-2(26-Feb-2026-14:26:18)# show bgp ipv6 flowspec summary | no-more

BGP router identifier 2.2.2.2, local AS number 123
BGP table node count 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  1.1.1.1         4    1234567       8954        619    0     0       0 01:37:57                   0
  4.4.4.4         4    1234567        110       3863    0     0       0 01:34:02                   0
  25.25.25.1      4      65000          0          0    0     0       0 never      Active          
  100.64.6.134    4      65200          0          0    0     0       0 never     Idle (Admin)

Total number of established neighbors with IPv6 Flowspec 2/4
```

### NPU Resources at 14:30 — THE BUG (TCAM empty, nothing installed, 1.5 hours later)

```
RR-SA-2(26-Feb-2026-14:30:12)# show system npu-resources resource-type flowspec | no-more


Flowspec usage:

| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 0     | 400                   | 0                      | 0/12000                      | 400                   | 0                      | 0/4000                       |
```

### rib-manager FlowSpec DB — default VRF empty (SAFI 133 withdrawn successfully)

```
RR-SA-2(26-Feb-2026-14:26:27)# show dnos-internal routing rib-manager database flowspec | no-more

VRF: default

IPv4 Flowspec table (total size: 12000):
-------------------------------

IPv6 Flowspec table (total size: 4000):
-------------------------------
```

### rib-manager FlowSpec DB VRF ZULU — All 16,000 SAFI 134 routes STILL present

```
RR-SA-2(26-Feb-2026-14:27:13)# show dnos-internal routing rib-manager database flowspec vrf ZULU | no-more

VRF: ZULU

IPv4 Flowspec table (total size: 12000):
-------------------------------
DstPrefix:=172.16.0.0/24,SrcPrefix:=*
vrf_id: 9, bgp_as: 123
    flowspec-traffic-rate:0


DstPrefix:=172.16.1.0/24,SrcPrefix:=*
vrf_id: 9, bgp_as: 123
    flowspec-traffic-rate:0


DstPrefix:=172.16.2.0/24,SrcPrefix:=*
vrf_id: 9, bgp_as: 123
    flowspec-traffic-rate:0

[... 12,000 IPv4 entries + 4,000 IPv6 entries = 80,015 lines total ...]

DstPrefix:=2001:db9:f9d::/48,SrcPrefix:=*
vrf_id: 9, bgp_as: 123
    flowspec-traffic-rate:0


DstPrefix:=2001:db9:f9e::/48,SrcPrefix:=*
vrf_id: 9, bgp_as: 123
    flowspec-traffic-rate:0


DstPrefix:=2001:db9:f9f::/48,SrcPrefix:=*
vrf_id: 9, bgp_as: 123
    flowspec-traffic-rate:0
```

### NCP wb_agent traces — SAFI 133 TCAM deletion (entries count down to 0)

```
RR-SA-2(26-Feb-2026-14:27:34)# show file ncp 0 traces datapath/wb_agent.flowspec | include Num | tail 20 | no-more
2026-02-26T13:02:32.908576 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 20
2026-02-26T13:02:32.908764 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 19
2026-02-26T13:02:32.908926 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 18
2026-02-26T13:02:32.909083 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 17
2026-02-26T13:02:32.909241 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 16
2026-02-26T13:02:32.909383 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 15
2026-02-26T13:02:32.909540 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 14
2026-02-26T13:02:32.909701 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 13
2026-02-26T13:02:32.909850 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 12
2026-02-26T13:02:32.910004 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 11
2026-02-26T13:02:32.910147 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 10
2026-02-26T13:02:32.910305 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 9
2026-02-26T13:02:32.910468 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 8
2026-02-26T13:02:32.952252 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 7
2026-02-26T13:02:32.954240 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 6
2026-02-26T13:02:32.954418 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 5
2026-02-26T13:02:32.954542 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 4
2026-02-26T13:02:32.954648 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 3
2026-02-26T13:02:32.954784 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 2
2026-02-26T13:02:32.955134 +02:00 [INFO      ] [FlowspecTcamManager.cpp:50 DeleteTcamRule()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete rule in BCM. Num entries: 1
```

### NCP wb_agent traces — Last SAFI 133 IPv6 deletions

```
RR-SA-2(26-Feb-2026-14:25:41)# show file ncp 0 traces datapath/wb_agent.flowspec | include DeleteRuleInternal | tail 10 | no-more
2026-02-26T13:02:32.954286 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Received BGP IPv6 NLRI: 01300020010db80f9b : DstPrefix:=2001:db8:f9b::/48,SrcPrefix:=*
2026-02-26T13:02:32.954437 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete flowspec rule with length=9
2026-02-26T13:02:32.954453 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Received BGP IPv6 NLRI: 01300020010db80f9c : DstPrefix:=2001:db8:f9c::/48,SrcPrefix:=*
2026-02-26T13:02:32.954561 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete flowspec rule with length=9
2026-02-26T13:02:32.954576 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Received BGP IPv6 NLRI: 01300020010db80f9d : DstPrefix:=2001:db8:f9d::/48,SrcPrefix:=*
2026-02-26T13:02:32.954677 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete flowspec rule with length=9
2026-02-26T13:02:32.954692 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Received BGP IPv6 NLRI: 01300020010db80f9e : DstPrefix:=2001:db8:f9e::/48,SrcPrefix:=*
2026-02-26T13:02:32.954809 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete flowspec rule with length=9
2026-02-26T13:02:32.954833 +02:00 [DEBUG     ] [FlowspecManager.cpp:253 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Received BGP IPv6 NLRI: 01300020010db80f9f : DstPrefix:=2001:db8:f9f::/48,SrcPrefix:=*
2026-02-26T13:02:32.955152 +02:00 [DEBUG     ] [FlowspecManager.cpp:280 DeleteRuleInternal()] [wb_fib_fpm:2468] Flowspec: Succeeded to delete flowspec rule with length=9
```

### NCP wb_agent traces — No AddRuleInternal after TCAM freed

```
RR-SA-2(26-Feb-2026-14:29:04)# show file ncp 0 traces datapath/wb_agent.flowspec | include AddRule | tail 20 | no-more

(empty — zero AddRule entries after TCAM freed at 13:02:32)
```

---

## Timeline

| Time (IST) | Event | Source |
|---|---|---|
| ~12:48 | Inject 32K routes: 12K IPv4 + 4K IPv6 SAFI 133 + 12K IPv4 + 4K IPv6 SAFI 134 | ExaBGP |
| 12:58:17 | `BGP_FLOWSPEC_UNSUPPORTED_RULE` IPv4: `172.48.74.0/24` — SAFI 134 rejected, TCAM full | syslog |
| 12:58:20 | NPU: IPv4 12400/12000/12000. IPv6 4000/4000 | show npu-resources |
| 12:59:02 | `BGP_FLOWSPEC_UNSUPPORTED_RULE` IPv6: `2001:db9:f6e::/48` — SAFI 134 IPv6 also rejected | syslog |
| 12:59:02 | bgpd traces: `Found rt_node` + `PERMIT` for all SAFI 134 routes into VRF ZULU | bgpd_traces |
| 13:00:18 | NPU: IPv4 12400/12000/12000. IPv6 now 4400/4000/4000 | show npu-resources |
| 13:00:52 | `show flowspec ncp 0`: SAFI 133 rules `10.0.x.x` all `Status: Installed` in default VRF | show flowspec ncp |
| 13:01:10 | `show flowspec ncp 0 \| include " not installed"`: SAFI 134 rules `Status: Not Installed, out of resources` | show flowspec ncp |
| 13:01:18 | `show flowspec ncp 0 \| include " not installed" \| count` → **lines: 800** (400 per AF) | show flowspec ncp |
| ~13:02 | Withdraw all SAFI 133 routes via ExaBGP | ExaBGP |
| 13:02:32 | NCP deletes all SAFI 133 TCAM entries (Num entries counts down 20→1) | wb_agent.flowspec |
| 13:02:32+ | **No AddRuleInternal for SAFI 134** — TCAM goes empty, stays empty | wb_agent.flowspec |
| 13:04:19 | **400 received, 0 installed, 0/12000, 0/4000** — bug first confirmed | show npu-resources |
| 14:30:12 | Bug persists 1h 28m later: still **400/0, 0/12000, 0/4000** | show npu-resources |

---

## BEFORE vs AFTER Comparison

| Metric | BEFORE (12:58-13:01) | AFTER (13:04 / 14:30) | Delta |
|--------|----------------------|---------------|-------|
| BGP IPv4 SAFI 133 PfxAccepted | 12,000 | 0 | withdrawn |
| BGP IPv6 SAFI 133 PfxAccepted | 4,000 | 0 | withdrawn |
| BGP IPv4 SAFI 134 PfxAccepted | 12,000 | 12,000 | unchanged |
| BGP IPv6 SAFI 134 PfxAccepted | 4,000 | 4,000 | unchanged |
| rib-manager DB default VRF IPv4 | 12,000 (SAFI 133) | 0 | withdrawn |
| rib-manager DB VRF ZULU IPv4 | 12,000 (SAFI 134) | 12,000 | unchanged |
| rib-manager DB VRF ZULU IPv6 | 4,000 (SAFI 134) | 4,000 | unchanged |
| **NPU IPv4 Received** | **12,400** | **400** | **-12,000** |
| **NPU IPv4 Installed** | **12,000** | **0** | **-12,000** |
| **NPU IPv4 TCAM** | **12000/12000 FULL** | **0/12000 EMPTY** | **12K free, nothing uses it** |
| **NPU IPv6 Received** | **4,400** | **400** | **-4,000** |
| **NPU IPv6 Installed** | **4,000** | **0** | **-4,000** |
| **NPU IPv6 TCAM** | **4000/4000 FULL** | **0/4000 EMPTY** | **4K free, nothing uses it** |
| show flowspec ncp 0 "Not Installed" | **800** (400 IPv4 + 400 IPv6) | 0 (no NCP entries visible) | rules silently dropped |
| show flowspec ncp 0 "Installed" | 12,000+ (all SAFI 133) | 0 | withdrawn |

---

## Layer-by-Layer Status (AFTER state)

| Layer | IPv4 SAFI 134 | IPv6 SAFI 134 | Working? |
|---|---|---|---|
| BGP (bgpd) | 12,000 PfxAccepted | 4,000 PfxAccepted | YES |
| Import Policy | PERMIT via rt_node for RT 300:300 | PERMIT via rt_node for RT 1234567:401 | YES |
| Zebra / rib-manager | 12,000 in VRF ZULU DB | 4,000 in VRF ZULU DB | YES |
| NCP wb_agent | 400 received, 0 installed | 400 received, 0 installed | **BUG** |
| BCM TCAM | 0/12000 (empty) | 0/4000 (empty) | EMPTY |

---

## Key Observations (QA Summary)

1. **Control plane works correctly.** BGP import traces show `PERMIT` for all SAFI 134 routes. zebra FlowSpec DB has all routes. rib-manager delivered them to fib-manager. The routing stack is not at fault.

2. **Syslog proves TCAM overflow.** `BGP_FLOWSPEC_UNSUPPORTED_RULE` messages at 12:58:17 (IPv4) and 12:59:02 (IPv6) confirm SAFI 134 rules were rejected due to `lack of resources` while TCAM was full with SAFI 133 rules.

3. **NCP discards rules during overflow.** When TCAM is full, the NCP keeps only the first 400 BGP FlowSpec rules as "received but not installed." Rules 401+ are silently dropped — they disappear from the NCP table entirely.

4. **No automatic retry after TCAM frees.** When SAFI 133 rules are withdrawn and TCAM goes from 12000/12000 to 0/12000, the NCP does NOT attempt to install the 400 retained rules, nor does it request the 11,600 discarded rules from the routing stack.

5. **No manual retry available.** `request retry-install` only works for local policies. No equivalent exists for BGP FlowSpec rules.

6. **Only workaround:** Withdraw and re-advertise the FlowSpec-VPN routes from the BGP source, or clear the BGP session to force a full re-evaluation.

## Verification Commands

```bash
show system npu-resources resource-type flowspec
show bgp ipv4 flowspec summary
show bgp ipv4 flowspec-vpn summary
show bgp ipv6 flowspec summary
show bgp ipv6 flowspec-vpn summary
show dnos-internal routing rib-manager database flowspec
show dnos-internal routing rib-manager database flowspec vrf ZULU
show file ncp 0 traces datapath/wb_agent.flowspec | include AddRule | tail 10
show file ncp 0 traces datapath/wb_agent.flowspec | include DeleteRuleInternal | tail 10
show file ncp 0 traces datapath/wb_agent.flowspec | include Num | tail 20
show file traces routing_engine/bgpd_traces | include rt_node | tail 10
show file traces routing_engine/bgpd_traces | include PERMIT | tail 10
```

## Related Bugs

- **BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST** — Deeper root cause discovered 2026-03-01: `FlowspecTcamManager::RollbackRule()` does not release `m_reserved` entries, causing phantom TCAM consumption during bulk injection. The 400-per-family threshold (`FLOWSPEC_MAX_UNWRITTEN_IN_TABLE`) and no-recovery mechanism are shared between both bugs. This bug can trigger even WITHOUT genuine TCAM overflow — pure SAFI 134 burst injection on an empty TCAM also loses rules.

## Topology

See: `~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_FLOWSPEC_TCAM_OVERFLOW_NO_RECOVERY.topology.json`
