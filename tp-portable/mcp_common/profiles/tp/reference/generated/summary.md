# TP Knowledge DB Export

Generated: 2026-06-29T07:51:45.519069+00:00

- `source_documents`: 14 rows
- `rubric_rules`: 274 rows
- `command_catalog`: 83 rows
- `flow_catalog`: 0 rows
- `test_case_catalog`: 0 rows
- `dedup_fingerprints`: 0 rows
- `coverage_links`: 0 rows

## Command Catalog Sample
- `dual_pe_shared_rt_inner_vlan_divergence` (EXPECTED_LIVE_VALIDATE)
- `m_LocalArp` (EXPECTED_LIVE_VALIDATE)
- `sections/arp-nd-punt-rules.md` (EXPECTED_LIVE_VALIDATE)
- `sections/show-commands.md` (CANONICAL)
- `sh evpn instance <name> mac-table mac <mac> detail` (CANONICAL)
- `show bgp l2vpn vpls` (EXPECTED_LIVE_VALIDATE)
- `show evpn forwarding-table mac-address-table instance VPLS-1` (EXPECTED_LIVE_VALIDATE)
- `show evpn instance VPLS-1 detail` (EXPECTED_LIVE_VALIDATE)
- `show evpn instance VPLS-1 mac-table` (EXPECTED_LIVE_VALIDATE)
- `show evpn instance VPLS-1 vpls-pw` (EXPECTED_LIVE_VALIDATE)
- `show evpn mac-ip-table` (CANONICAL)
- `show evpn summary` (EXPECTED_LIVE_VALIDATE)
- `| Show evpn mac-ip-table | The` (EXPECTED_LIVE_VALIDATE)
- `sh bgp l2vpn evpn route-type 2` (EXPECTED_LIVE_VALIDATE)
- `-- needs guard against PW path | mac-table shows` (EXPECTED_LIVE_VALIDATE)
- `-- needs is_pw branch | mac-ip-table shows entry as` (EXPECTED_LIVE_VALIDATE)
- `-- needs new event types for SI IRB | History shows generic` (EXPECTED_LIVE_VALIDATE)
- `arp_send_broadcast_probe()` (EXPECTED_LIVE_VALIDATE)
- `nh_proxy_arp_reply_should_send()` (EXPECTED_LIVE_VALIDATE)
- `proxy-arp reply suppressed` (EXPECTED_LIVE_VALIDATE)
- `show evpn instance EVPN_SI_VPLS_1 detail` (EXPECTED_LIVE_VALIDATE)
- `show_evpn_mac_ip_table_render_flags()` (EXPECTED_LIVE_VALIDATE)
- `. Then AC ARP -> behaves like row 10 (local wins) |` (EXPECTED_LIVE_VALIDATE)
- `flag) | New AC ARP (same MAC) | **PW->AC transition** -- uninstall PW ARP from FIB; install AC ARP; **advertise RT-2** for AC MAC-IP; send **broadcast probe** on AC | move to` (EXPECTED_LIVE_VALIDATE)
- `flag) | PW ARP refresh (same MAC, same IP) | Refresh aging timer | unchanged (still` (EXPECTED_LIVE_VALIDATE)
- `m_RemoteArpDb` (EXPECTED_LIVE_VALIDATE)
- `sh bgp l2vpn vpls` (CANONICAL)
- `sh evpn forwarding-table mac-address-table instance <name>` (CANONICAL)
- `sh evpn instance <name> mac-ip-table` (CANONICAL)
- `sh evpn instance <name> mac-table` (CANONICAL)
