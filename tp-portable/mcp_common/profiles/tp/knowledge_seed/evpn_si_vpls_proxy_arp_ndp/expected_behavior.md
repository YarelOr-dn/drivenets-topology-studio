# Expected Behavior -- `EVPN-SI VPLS IRB: proxy-NDP PW-suppression vs SW-277948 (2-way split + DP-drop confound)`

- **feature_id:** `evpn_si_vpls_proxy_arp_ndp`
- **primary device:** `PE-1`
- **epics:** SW-228552, SW-65398
- **captured at:** 2026-05-13T05:24:07Z
- **live-validated at:** 2026-07-08T17:44:05Z

Two orthogonal PW-side proxy-NDP behaviors that must never be conflated. (1) SUPPRESSION (correct): proxy-NDP must NEVER emit an NA toward the VPLS PW for a third-party/LL/OOS/fresh target, and a PW-learned MAC-IP is never re-advertised in RT-2. (2) SW-277948 (bug): an NS to the IRB's OWN IP over the PW is dropped in DP (shouldSendUpwards=0, is_vpls_pw=1) instead of punted to Routing. The DP-drop is a CONFOUND for suppression tests: it guarantees 'no NA / proxy counter unchanged' for ANY target regardless of whether suppression logic is correct, so a negative-only suppression test cannot distinguish 'proxy declined' from 'NS never reached proxy'. Live-verified 2026-07-08 on PE-1 DNOS 26.3.0-7_priv: 4 PW-source NS variants (LL fe80::face:1, in-subnet fresh ::a2/::f1, OOS 2001:dead:beef::99) from RR-SA-2 bundle-100.2001 inner3001 -> proxy_arp/tx txPktsResponse 423->423 (delta 0), no mac-ip, no RT-2, 0 icmp6 at irb4001.

## Configuration Paths

| Hierarchy | Syntax | Purpose | Live Status |
|---|---|---|---|
| network-services evpn instance <NAME> router-interface <irb> irb-mac-ip enabled |  | Required on PE-1 (EVPN-with-IRB side). Enables proxy-ARP/NDP for in-IRB-subnet hosts. | LIVE_VALIDATED |
| network-services evpn instance EVPN_SI_VPLS_1 router-interface irb4001 irb-mac-ip enabled | network-services evpn instance EVPN_SI_VPLS_1 router-interface irb4001 irb-mac-ip enabled | Binds the IRB and enables proxy-ARP/NDP MAC-IP for in-subnet hosts. No per-instance proxy-ARP disable knob exists; XRAY is capture-only (no packet inject). | LIVE_VALIDATED |

## Show Commands (live-validated)

_Live Status legend: **LIVE_VALIDATED** = accepted + real data; **LIVE_VALID_NO_ENTRIES** = valid command, empty table / object-not-found now; **LIVE_EMPTY** = blank output; **LIVE_INCOMPLETE** = valid stem, missing argument (auto `?`-discovery ran -- see Syntax Discovery below); **LIVE_REJECTED** = wrong command (fix syntax); **LIVE_ERROR** = valid command, run failed (auth/transport/timeout/crash -- retry)._

| Command | Device Role | Expected Keywords | Live Status |
|---|---|---|---|
| show evpn instance <NAME> detail | no-more | pe_with_irb | MAC IP table aging time, Number of VPLS PW entries | LIVE_VALID_NO_ENTRIES |
| show evpn mac-ip-table instance <NAME> | no-more | pe_with_irb | v> | LIVE_VALID_NO_ENTRIES |
| show evpn mac-table instance <NAME> | no-more | pe_with_irb | v> | LIVE_VALID_NO_ENTRIES |
| show ndp | include irb4001 | pe_with_irb | evpn | LIVE_VALIDATED |
| show evpn instance EVPN_SI_VPLS_1 vpls-pw | no-more | pe_with_irb | Installed, Remote Site Id | LIVE_VALIDATED |
| show arp interface irb4001 | no-more | pe_with_irb | irb4001, 10.214.40 | LIVE_VALIDATED |
| show evpn mac-ip-table instance EVPN_SI_VPLS_1 | no-more | pe_with_irb | EVI ID, 10.214.40.2 | LIVE_VALIDATED |
| show config network-services evpn instance EVPN_SI_VPLS_1 | no-more | pe_with_irb | router-interface irb4001, seamless-integration | LIVE_VALIDATED |

## XRAY / wbox-cli Paths

| Path | Counter | Increments On | Does NOT Increment On |
|---|---|---|---|
| /wb_agent/proxy_arp/tx | txPktsResponse |  |  |

## Cross-Feature Interactions

| Scenario | Expected | Anti-Pattern |
|---|---|---|
| Fresh in-IRB-subnet IPv4 ARP arrives via PW (e.g. ARP for 10.214.40.6 with src MAC 00:fe:11:00:40:06) |  | Looking at mac-ip-table 20+ min after last ARP and concluding feature is broken when it's actually just aged out. Verify by sending fresh ARP and re-checking within 20 min. |
| Fresh in-IRB-subnet IPv6 NA arrives via PW (e.g. solicited NA for 2001:214:4001::3) |  | BUG: NEVER produces v> in mac-ip-table for IPv6 PW. Across every /TEST run in the catalog, zero v> IPv6 mac-ip entries observed. Kernel NDP stays Origin=dynamic (RFC 4861 fallback only). This is a real DNOS bug specific to IPv6 PW NDP integration. |
| Out-of-IRB-subnet host traffic via PW |  | Trying to test mac-ip integration with out-of-subnet hosts; will always show empty mac-ip-table regardless of v4/v6 and regardless of bug state. |
| Spirent stream stopped for >20 min, then checking mac-ip-table |  | Concluding the feature is broken when you're just looking at stale state. Restart ARP traffic and re-check within 20 min before declaring the bug. |
| PW(core)-ingress ARP arrives at PE-1 for a host PE-1 already owns on its LOCAL AC (10.214.40.2 / 00:fe:11:00:40:01, L>) | PE-1 floods the ARP to its local AC; the REAL host replies; PE-1 does NOT proxy-answer a core/PW-ingress ARP back into the VPLS-PW (proxy reply is never sent to a PW; core-ingress ARP/NDP is not punted). VERIFIED correct on PE-1 build 14, 2026-06-25. | Concluding from the reply's sender MAC who answered. DriveNets proxy-ARP answers with the TARGET HOST's REAL MAC, so the sender MAC cannot distinguish 'host replied' from 'PE proxied'. Use the negative control. |
| Decisive negative control for who answers a PW-ingress ARP | Remove the target host while PE-1 STILL holds its L> mac-ip entry, then re-ARP over the PW. Still resolves => PE-1 proxied into the PW (BUG). Fails (Destination Host Unreachable, ARP dynamic/failed) => the real host answered (CORRECT). ICMP can never be proxied, so ICMP success across the PW also proves the real host. | Chasing per-packet datapath proxy-arp traces first: 'wbox-cli proxy arp tracing enable' logs no per-packet decision at default verbosity, and routing-engine fibmgrd/neighbour_manager full reads time out under PE-1 mgmt contention. |
| Selecting a remote PE to source a PW-ingress ARP into PE-1 | Source PE must (a) have a DIRECT Installed PW to PE-1 and (b) NOT already know the target MAC-IP. RR-SA-2 (2.2.2.2) is correct: direct PW to PE-1 and VPLS-only for this EVI (empty mac-ip-table => no proxy-suppression). Source the ARP with a transient IRB in 10.214.40.0/24 + 'run ping <target> source-interface <irb>'. | Using PE-4 as the source: fabric is hub-and-spoke (PE-4<->RR-SA-2 only; no direct PE-4<->PE-1 PW; split-horizon blocks PW->PW relay), AND PE-4 holds the target via RT-2 so its own proxy-ARP suppresses the flood before it crosses any PW. |
| PW-side NS for a THIRD-PARTY target (LL / in-subnet fresh / out-of-subnet) arrives at an EVPN-SI IRB PE | SUPPRESSION: no proxy-NDP NA emitted toward the PW; no mac-ip entry learned for the target; no RT-2 advertised (no sanction); wb_agent proxy_arp/tx txPktsResponse unchanged. This is CORRECT behavior. | Concluding suppression logic is proven correct from the negative result alone. SW-277948 drops the PW NS in DP before the proxy engine sees it, so 'no NA' is guaranteed regardless. A rigorous suppression test needs a POSITIVE control in the same window (e.g. IPv4 proxy-ARP-from-PW which works, or an on-AC NS the proxy DOES answer). |
| Choosing the CP capture point to prove 'no proxy-NDP NA toward PW' | Authoritative proof = wb_agent proxy_arp/tx (txPktsResponse delta 0) + BGP RT-2 absence + mac-ip-table absence. A proxy NA toward the PW would egress the MPLS core (encapsulated), NOT irb4001. | Treating a 0-packet CP capture on irb4001 as the proof. irb4001 returns 0 for structural reasons (punted NS is DP-dropped and any toward-PW NA egresses the core), so its 0-count is expected either way and is corroborating-only, not decisive. |
| Distinguishing suppression PASS from SW-277948 fixed | They are orthogonal. Suppression = no NA toward PW for third-party targets. SW-277948 fix = NS to the IRB's own IP over PW is punted (GRE-IRB + MACT_Recycle) and the IRB answers. Test each with its own target: third-party target for suppression, IRB's own IP for SW-277948. | Reporting 'proxy-NDP PW feature works' from a suppression PASS while SW-277948 (own-IP NS drop) is still open, or vice-versa. |

## Known Bugs

| Bug | Title | Status | Signature |
|---|---|---|---|
|  | PE-1 EVPN-SI VPLS-PW IRB MAC-IP integration BROKEN for IPv6 ONLY (IPv4 works correctly) | OBSERVED | IPv4 PW works: when Spirent emulates an in-IRB-subnet PW host that periodically sends ARP (gratuitous or solicited), PE-1 populates mac-ip-table with v> entries; ages out 20min after last refresh. Evidence: RUN_20260511_082651 shows v> 00:fe:11:00:40:06 / 10.214.40.6 / src 2.2.2.2 (PW). IPv6 PW BROKEN: across every /TEST run in catalog, NO v> entry with any IPv6 address ever produced. Kernel NDP shows Origin=dynamic (RFC 4861 only); EVPN mac-ip-table never integrated with PW-side IPv6 NA. Even with RFC-correct sNA (S=1/O=1/R=0, unicast, TLLA option) the v> entry does NOT appear. Bug is specific to IPv6 proxy-NDP-from-PW; IPv4 proxy-ARP-from-PW is unaffected. |
| SW-277948 | EVPN VPLS SI IRB | NDP NS from a PW-attached host to the IRB is dropped in DP instead of punted to Routing | Open | IPv6 ping host<->IRB across the VPLS-PW fails 100% except for a few seconds after 'clear ndp'; DP ProxyArp sets shouldSendUpwards=0 and skips the proxy response for is_vpls_pw=1, so the NS never reaches Routing and no NA is generated. |
| SW-278456 | EVPN VPLS SI IRB | ARP/NS not-for-us is sent to the GRE of the IRB | Open | On an EVPN/BD with an oper-up IRB, the DP ProxyArp candidate handler SW-snoops every ARP request received on the BD. |

## Sources

- **[confluence]** [RUN_20260511_082651: v> 00:fe:11:00:40:06 / 10.214.40.6 in mac-ip-table (PROOF IPv4 PW proxy-ARP works)](/home/dn/SCALER/TEST/catalog/TEST_SW-228552_TC-IRB-IPV4-ARP-BASIC-01_017/results/RUN_20260511_082651_PE-1/evidence/10_tp_step_04_pe1_pw_source_installation_verify/stdout.md) -- fetched None
- **[confluence]** [ZERO v> IPv6 mac-ip entries across ALL test runs in catalog (PROOF IPv6 PW proxy-NDP broken)](grep result across /home/dn/SCALER/TEST/catalog/ for pattern 'v>.*2001:') -- fetched None
- **[confluence]** [EVPN(ELAN) Seamless integration with VPLS (BGP) - IRB support](https://drivenets.atlassian.net/browse/SW-228552) -- fetched None
- **[confluence]** [EVPN - proxy ARP/NDP (parent epic)](https://drivenets.atlassian.net/browse/SW-65398) -- fetched None
- **[confluence]** [(v25.4) EVPN Proxy ARP](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5614796833/v25.4+EVPN+Proxy+ARP) -- fetched None
- **[confluence]** [EVPN (ELAN) Seamless integration with VPLS (BGP) - MAC and MAC-IP Handling Design](https://drivenets.atlassian.net/wiki/spaces/DV/pages/5723357187) -- fetched None
- **[agent_evidence]** PE-1 negative control 2026-06-25: target host removed, PW-ingress re-ARP from RR-SA-2 FAILED while PE-1 still held L> mac-ip => PE-1 does not proxy into the PW (correct) -- fetched None

