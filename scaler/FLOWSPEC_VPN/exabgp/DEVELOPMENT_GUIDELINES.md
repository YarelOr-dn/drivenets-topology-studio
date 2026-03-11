# BGP Peering Tool - Development Guidelines

Updated: 2026-02-16 for modular restructure (builders/, malform/, backends/, attributes/).

## Modular Structure (2026-02)

- **bgp_tool.py** — CLI entry point; delegates to modules
- **session.py, pipe.py, config_gen.py** — ExaBGP lifecycle, pipe, config
- **builders/** — Route string generators (flowspec, flowspec_vpn, unicast, vpn, evpn, scale, ...)
- **malform/** — BGP malformation builders (bad-marker, truncated-nlri, bad-extcommunity-0x0c, ...)
- **backends/** — exabgp.py, gobgp.py, scapy_tcp.py (Simpson redirect-ip)
- **attributes/** — Attribute testing lab (communities, as_path, med_locpref, flowspec_ec, next_hop)

**GoBGP:** Use `bgp_tool.py engine-start`, `engine-stop`, `engine-inject` for unicast, l3vpn, flowspec. FlowSpec-VPN (SAFI 134) is parked — GoBGP FSM sends TCP FIN after OPEN. Use ExaBGP for flow-vpn.

## Critical ExaBGP Config for DNOS Peering

When generating ExaBGP config for DNOS devices, always include:

- `passive true` - ExaBGP listens; PE initiates TCP (required for BgpTrius/NSR compatibility)
- `listen 179` - Bind to BGP port (requires setcap'd Python binary at /tmp/python3_bgp)
- `outgoing-ttl 64` - For eBGP multihop
- `hold-time 600` - 10-minute hold timer for stability during long operations
- `router-id` - Use same value as local-address (e.g. 100.64.6.134)
- **Do NOT use** `incoming-ttl` - it sets IP_TTL on the socket (not MIN_TTL), killing SYN-ACKs
- **Do NOT use** `passive false` / `connect 179` - BgpTrius iptables DROP unmarked inbound SYN-ACKs

### Why passive mode?

DNOS BgpTrius (BGP NSR) installs iptables rules that DROP all TCP port 179 traffic
without mark 0x65179. When ExaBGP initiates (active mode), the PE's SYN-ACK comes
back to our server, but the return SYN from ExaBGP hits the PE's INPUT chain and
gets dropped because BgpTrius NFQUEUE doesn't mark packets from external peers.
Passive mode reverses the flow: PE initiates the SYN (marked by BgpTrius OUTPUT chain),
ExaBGP just accepts it.

### Device-side iptables (ephemeral)

NSR devices also need ACCEPT rules inserted before the DROP rules:
```
iptables -I INPUT 3 -p tcp -s 100.64.6.134 --sport 179 -j ACCEPT
iptables -I INPUT 3 -p tcp -s 100.64.6.134 --dport 179 -j ACCEPT
iptables -I INPUT 3 -p tcp -d <device_ip> --dport 179 -j ACCEPT
```
These are lost on NCC restart/reboot. Re-apply after any such event.

## Supported AFI/SAFI (All 15 DNOS Families)

All 15 DNOS address families are supported. See `DNOS_TO_EXABGP` and `ALL_EXABGP_FAMILIES` in `bgp_tool.py`.

| DNOS | ExaBGP |
|------|--------|
| ipv4-unicast | ipv4 unicast |
| ipv6-unicast | ipv6 unicast |
| ipv4-flowspec | ipv4 flow |
| ipv4-flowspec-vpn | ipv4 flow-vpn |
| ipv6-flowspec | ipv6 flow |
| ipv6-flowspec-vpn | ipv6 flow-vpn |
| ipv4-vpn | ipv4 mpls-vpn |
| ipv6-vpn | ipv6 mpls-vpn |
| ipv4-labeled-unicast | ipv4 nlri-mpls |
| ipv6-labeled-unicast | ipv6 nlri-mpls |
| ipv4-multicast | ipv4 multicast |
| ipv4-rt-constrains | ipv4 rtc |
| l2vpn-evpn | l2vpn evpn |
| l2vpn-vpls | l2vpn vpls |
| link-state | bgp-ls bgp-ls |

## ExaBGP Patches Required (site-packages)

1. **Extended communities (IPv6 flow-vpn):**
   - `exabgp/bgp/message/update/attribute/community/extended/communities.py`: ExtendedCommunitiesIPv6.unpack - fallback to 8-byte when total not multiple of 20
   - `exabgp/bgp/message/update/attribute/community/extended/traffic.py`: TrafficRedirectIPv6.unpack - use data[2:20] and data[:20] (was data[2:11]/data[:11])

2. **RTC (ipv4 rtc) family:**
   - `exabgp/configuration/neighbor/family.py`: Add `'rtc': (AFI.ipv4, SAFI.rtc)` to ipv4 convert dict

3. **Route-target announce/withdraw:**
   - `exabgp/configuration/static/__init__.py`: Add `route_target` handler and `_parse_route_target`
   - `exabgp/configuration/configuration.py`: Add `'route-target'` to static commands
   - `exabgp/reactor/api/command/announce.py`: Add `announce route-target` and `withdraw route-target` handlers

4. **FlowSpec-VPN rd/next-hop via API pipe (2026-02):**
   - `exabgp/configuration/flow/__init__.py`: Add `ParseFlowRoute.known` and `ParseFlowRoute.action` to `ParseFlow`; add `nlri-set` and `nlri-nexthop` handlers in `route()` function
   - `exabgp/configuration/announce/flow.py`: Add `rd`, `route-distinguisher`, `next-hop` to `known`; add `nlri-set` and `nlri-nexthop` to `action`; add handlers in `flow()` function
   - Enables: `announce flow route rd 1.1.1.1:100 destination 10.0.0.0/24 redirect 10.0.0.230 extended-community [ target:1234567:300 ]` via pipe (FLAT format only!)

5. **4-byte ASN Route Target encoding fix (2026-02-16):**
   - `exabgp/configuration/static/parser.py`: `_HEADER['target4']` was `bytes([0x01, 0x02])` (Type 1 = IPv4). Fixed to `bytes([0x02, 0x02])` (Type 2 = 4-byte ASN, per RFC 5668). Same fix for `origin4`.
   - Without this fix, RT:1234567:300 encodes as IPv4 type, causing DNOS to display `RT:0.18.214.135:300` and fail VRF import.

## Route Injection

Use `bgp_tool.py inject` with route strings from `route_builder.py`. Named pipe: `/run/exabgp/exabgp.in`.

Route types: flowspec, flowspec-vpn, unicast, multicast, labeled-unicast, l3vpn, evpn-type2, evpn-type5, vpls, rtc.

**FlowSpec-VPN:** Requires ExaBGP patch #4 above. GoBGP is parked (FSM sends TCP FIN after OPEN). Use ExaBGP for flow-vpn. `bgp_tool.py` routes flowspec-vpn through ExaBGP pipe when session has `exabgp_pid` and `status=active`. Malformation testing via `malform/` package; Simpson redirect-ip via `backends/scapy_tcp.py`.

**CRITICAL - FlowSpec-VPN API Pipe Format:**
Use FLAT format only (no `match { }` / `then { }` wrappers). The ExaBGP tokenizer cannot handle section-style blocks when `rd` is present in the route string.

Working:  `announce flow route rd 1.1.1.1:100 destination 10.0.0.0/24 source 16.16.16.0/30 redirect 10.0.0.230 extended-community [ target:1234567:300 ]`
Broken:   `announce flow route rd 1.1.1.1:100 match { destination 10.0.0.0/24; } then { redirect 10.0.0.230; }`

## Session Management (Critical)

### Orphan Process Cleanup
`session.kill_orphan_exabgp_processes()` kills only orphaned ExaBGP processes. It NEVER kills ExaBGP of other active sessions (pe_4, pe_1, etc. can run concurrently). Multiple ExaBGP instances connecting to the same peer cause BGP NOTIFICATION 6/7 (Connection Collision) - but different sessions peer to different devices, so they can coexist.

### Cleanup at Stop
Kill ExaBGP + children. Verify dead after 2 seconds:
```bash
kill -TERM <pid>; sleep 2; kill -9 <pid> 2>/dev/null; pkill -f 'socat.*exabgp'
```

### Post-Injection Verification
After injecting FlowSpec-VPN redirect-ip routes, verify:
1. `show flowspec ncp 0` on target device — rule installed locally
2. `show bgp ipv4 flowspec-vpn summary` — check PE peers still Established
3. If PE sessions flap (NOTIFICATION 3/9) → **DNOS reflection encoding bug**, not ExaBGP

## Known DNOS Bug: FlowSpec-VPN Redirect-IP Reflection (2026-02-16)

**Root cause**: `bgp_attr.c` `bgp_packet_mpattr_start_v4_flowspec_vpn` allocates 24-byte NH buffer (IPv6 VPN size) for ALL FlowSpec-VPN MP_REACH_NLRI. For redirect-ip routes with IPv4 next-hop:
- Sets NH_LEN=4, writes 0.0.0.0 instead of the actual redirect IP
- stream_forward() advances by 24, not 4
- 20 zero bytes bleed into NLRI space
- PE cannot parse the NLRI → NOTIFICATION 3/9

**Local install works**: RR installs the route correctly in its own VRF. `show flowspec ncp 0` shows "Redirect-ip-nh: 10.0.0.230". The bug is ONLY in the reflected UPDATE to PE peers.

**Proof via XRAY**:
```
run packet-capture ncc interface any count 100 filter-expression "port 179" verbose
```
Compare non-redirect FlowSpec-VPN UPDATE (NH_LEN=0, clean NLRI) vs redirect-ip UPDATE (NH_LEN=4, 24 zero bytes, corrupted NLRI). PE responds with NOTIFICATION 3/9 and TCP FIN.

## Revert if Broken

If changes cause session failure: verify `passive true`, `listen 179`, `outgoing-ttl 64`,
`hold-time 600` in generated config. Check that `/tmp/python3_bgp` exists with setcap
`cap_net_bind_service`. Check device-side iptables ACCEPT rules are present.
Never revert to `passive false` / `connect 179` / `incoming-ttl` -- those are confirmed broken
on NSR devices (BgpTrius iptables mark filtering).

## BgpTrius Diagnosis (bgp_tool.py diagnose)

When session is stuck in Connect after start:
```bash
python3 bgp_tool.py diagnose --session-id <id>           # inspect iptables
python3 bgp_tool.py diagnose --session-id <id> --fix      # inspect + auto-apply ACCEPT rules
```
Auto-resolves device OOB IP from SCALER DB. SSHes to device shell, inspects INPUT chain for
BgpTrius DROP rules on port 179, checks if ACCEPT rules for server IP exist. With `--fix`,
inserts ACCEPT rules at position 3 (before DROP). Reports JSON with root cause, fix commands,
and post-fix TCP state. Rules are ephemeral -- re-run after NCC restart/reboot.
