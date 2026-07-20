# SW-194912 Expected Behavior

With no IRB, ARP/NDP requests and responses arriving from a VPLS PW are flood/forward-only to local ACs with no Routing punt, no MAC-IP learning, and no proxy response. With an IRB present, PW-side ARP/NDP is still flooded/forwarded to ACs and is also punted to Routing; in-subnet MAC/IP entries are learned into Routing ARP/NDP and EVPN MAC-IP tables so AC-side proxy ARP/NDP can answer later. Proxy ARP/NDP must never send generated replies toward the VPLS PW; only actual host responses may go to the PW.

## Packet Matrix (AGREED-FINAL)

Source of truth: SW-194912 comment 1050602 (Uriel Sirota, 2026-06-23, "After
talking to @Menachem Dodge, he agreed ..."). This SUPERSEDES the original
description matrix. Rows marked [CHANGED] differ from Menachem's original
description.

| Packet From VPLS PW (IRB present) | Agreed-final DP Disposition | vs description |
|---|---|---|
| IPv6 NA - Unsolicited | Proxy-ARP raw socket + MACT_Recycle | same |
| IPv6 NA - Solicited | Proxy-ARP raw socket + MACT_Recycle | same |
| IPv6 NS to MY-IP (IRB IP) | GRE-IRB + MACT_Recycle | [CHANGED] added MACT_Recycle |
| IPv6 NS to other-IP | GRE-IRB + MACT_Recycle | [CHANGED] added GRE-IRB |
| IPv6 Router Solicitation | GRE-IRB | same |
| IPv6 Router Advertisement | GRE-IRB | same |
| IPv4 ARP Request to MY-IP (IRB IP) | GRE-IRB + Proxy-ARP raw socket | same |
| IPv4 ARP Request to other-IP | GRE-IRB + Proxy-ARP raw socket + MACT_Recycle | [CHANGED] added GRE-IRB |
| IPv4 ARP Reply to MY-IP | Proxy-ARP raw socket | same |
| IPv4 ARP Reply to other-IP | Proxy-ARP raw socket + MACT_Recycle | same |

No-IRB mode (all ARP/ND request/reply): flood/forward to local ACs only; no
Routing punt, no MAC-IP learning, no proxy reply. Proxy-ARP must NEVER send a
generated reply toward the VPLS PW in any mode; only real host responses egress
the PW.

## Disposition -> Observable (how each path is proven)

| Disposition | Meaning | Proven by |
|---|---|---|
| GRE-IRB | Punted to Routing via IRB GRE | wb_agent `shouldSendUpwards=1`/GRE-IRB path + `show arp/ndp vrf` populated (in-subnet) + neighbour_manager/fibmgrd/rib-manager traces |
| Proxy-ARP raw socket | Delivered to proxy-arp daemon | `xraycli /wb_agent/proxy_arp/rx` shows delivery; later AC-side request gets a proxy reply (never toward PW) |
| MACT_Recycle | Recycled to flood/forward to ACs | Spirent/XRAY AC-egress capture shows the frame at the AC + `wb_pkt_proc` MACT_Recycle/flood trace |

## Required Evidence Layers

1. Spirent/XRAY proves the exact ARP/NDP packet type and PW ingress.
2. DNOS AC/PW counters prove the frame entered and, when expected, flooded to AC.
3. `wb_agent`/ProxyArp xray or traces prove PW source classification (ARP-FROM-PW indication, PMF `PweInLifWideData`).
4. ProxyArp TX proof shows no generated reply toward the VPLS PW.
5. `show arp vrf` / `show ndp vrf` prove Routing neighbor learning only in IRB in-subnet mode.
6. `show evpn arp-table` / `show evpn ndp-table` / `show evpn mac-ip-table` prove EVPN MAC-IP state.
7. Fib-manager internal DB and `fibmgrd_traces` prove the programmed neighbor/MAC-IP backing state.
8. Rib-manager traces prove the zebra/RIB side accepted or rejected the EVPN neighbor before fib-manager.
9. `show evpn forwarding-table mac-address-table` proves DP owner/egress agrees with Routing.
10. `show bgp l2vpn evpn route-type 2` proves PW-source MAC-IP is not illegally originated as local RT-2.
11. CPRL counters prove the run is not rate-limit contaminated.

Per-packet PASS = every disposition in the agreed-final row is observed by its
mapped observable above, AND no forbidden behavior (no proxy reply to PW; no
Routing learn in no-IRB / out-of-subnet) occurs.

## Open Questions (do NOT invent test coverage)

- **ISIS over VPLS PW = UNSPECIFIED.** The title says "ARP/NDP/ISIS/Proxy-ARP"
  but neither the description nor any comment defines ISIS-over-VPLS-PW
  behavior. ISIS is left untested pending clarification from Menachem Dodge /
  Uriel Sirota / Ben Sheffi.

## SW-277948 regression guard (NDP NS to IRB dropped)

SW-277948 is the concrete DP failure behind the two changed IPv6-NS rows: an
IPv6 NS to the IRB IP arriving over a VPLS PW was dropped in DP
(`shouldSendUpwards: 0`, `Skip pushing ARP/NDP upwards ... is_vpls_pw 1 ...
packetType: NDP-NS`) instead of being punted up via GRE-IRB, so the IRB never
answered the NA and the gateway stayed unresolved. The agreed-final fix makes
NS-to-MY-IP (and NS-to-other-IP) `GRE-IRB + MACT_Recycle`. The TEST recipe
(`TEST_SW-194912_TC-PW-ARP-NDP-IRB-DP-ROUTING-01_001`, schema_version 2) guards
this per-scenario: PASS requires `shouldSendUpwards: 1` + IRB NA answered and
FAILs on any of the bug drop fingerprints.

## IS_IP_OF_IRB negative-control (SW-278456)

Agreed with Menachem (comment 1050602) to be fixed as bug SW-278456. SW-194912
must not regress BD (BD still sends IS_IP_OF_IRB to linux) while the VPLS IRB
path follows the agreed-final matrix above.
