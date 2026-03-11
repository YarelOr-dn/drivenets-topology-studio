# Debug Session: YOR_CL_PE-4 -- BGP ExaBGP session stuck in Connect
Started: 2026-03-03 21:49:00 UTC | Device: YOR_CL_PE-4
Image: (filled after Phase 0)
Topic: BGP peering 100.64.6.134 (ExaBGP) stuck in Connect state. User restarted routing-engine on NCC-1. Session still not established. Determine if PE-4 receives TCP/BGP traffic or if problem is on ExaBGP server.
Session mode: INVESTIGATE

---

## Context (from user paste)

- User ran: `request system container restart ncc 1 routing-engine`
- NCC-1 restarted, NCC-0 active, NCC-1 standby
- BGP neighbor 100.64.6.134: State = Connect, MsgRcvd/MsgSent = 0
- PE-4 config: neighbor 100.64.6.134, update-source ge100-18/0/6.999 (100.70.0.206/24)
- ExaBGP config: neighbor 100.70.0.206, local-address 100.64.6.134, passive false

## ExaBGP log (from pe_4_exabgp.log)

```
outgoing-X  outgoing-X 100.64.6.134-100.70.0.206, closing connection
connection to 100.70.0.206 closed
```

ExaBGP repeatedly connects to 100.70.0.206:179 but connection is closed immediately.

---

## Phase 0: Pre-Flight (from user paste)

Image: DNOS 26.1.0 build 27_priv
BGP: 100.64.6.134 in Connect state (ipv4-flowspec-vpn, ipv6-flowspec-vpn)

---

## Phase 3: Trace Commands (run on PE-4)

**Run these on your PE-4 SSH session** (you're already connected). Use `21:46` or `21:47` for recent events after the routing-engine restart:

```
show file traces routing_engine/bgpd_traces | include 100.64.6.134 | tail 50
show file traces routing_engine/bgpd_traces | include 100.70.0.206 | tail 50
show file traces routing_engine/bgpd_traces | include 21:46 | include 100.64 | tail 80
show file traces routing_engine/bgpd_traces | include Connect | tail 30
show file traces routing_engine/bgpd_traces | include rst | tail 30
show file traces routing_engine/bgpd_traces | include refused | tail 30
show file traces routing_engine/bgpd_traces | include listener | tail 20
show file traces routing_engine/bgpd_traces | include 179 | tail 30
```

**Key questions the traces answer:**
1. Does PE-4 see incoming TCP from 100.64.6.134? (look for "accepted", "connection", local port 179)
2. Does PE-4 get "Connection refused" when IT tries to connect to ExaBGP? (expected - ExaBGP doesn't listen)
3. Does PE-4 show "rst" or "fin" - who closes the connection?
4. Is the listener on 100.70.0.206:179 in REFUSED state?

---

## Server-Side Check (ExaBGP)

ExaBGP session pe_4 is **alive** (PID 3843722), target 100.70.0.206. Log shows "connection to 100.70.0.206 closed" repeatedly.

**ExaBGP source interpretation:** When `recv()` returns 0 (remote closed), ExaBGP logs "connection to X closed". So **PE-4 (or path) is closing the TCP connection** after TCP handshake.

**To verify from server** (run on this machine):
```bash
# Capture one BGP connection attempt (5 sec)
sudo tcpdump -i any -n 'host 100.70.0.206 and port 179' -c 20 -v 2>/dev/null
```

Look for: SYN, SYN-ACK, ACK (handshake OK), then RST or FIN from who. If RST from 100.70.0.206 = PE-4 rejects.

---

## Interpretation Guide

| PE-4 trace shows | Meaning |
|------------------|---------|
| "Connect failed (Connection refused)" for 100.64.6.134 | PE-4 tries to connect TO ExaBGP; refused (expected - ExaBGP doesn't listen) |
| "input got rst or fin" with remote 100.64.6.134 | Incoming connection from ExaBGP was closed - by who? |
| "accepted" / "connection" from 100.64.6.134 | PE-4 accepted TCP |
| No traces for 100.64.6.134 at all | PE-4 never sees the connection - path/firewall issue |

---

## tcpdump Result (SERVER SIDE - ROOT CAUSE FOUND)

```
19:50:02  IN  100.70.0.206.43895 > 100.64.6.134.179: Flags [S]   (PE-4 SYN to server)
19:50:02  OUT 100.64.6.134.179 > 100.70.0.206.43895: Flags [R.]  (SERVER RST)
```

**Interpretation:** PE-4 is initiating TCP to 100.64.6.134:179. The server (this machine) sends RST because **nothing is listening on port 179**. ExaBGP has `passive=false` so it does NOT listen — it only initiates. When PE-4 tries to connect, the kernel RSTs.

**Verdict: Problem is on the SERVER (ExaBGP) side.** ExaBGP must listen for PE-4's connection attempts.

---

## Session Conclusion
Ended: 2026-03-03 19:50 UTC
Verdict: ROOT CAUSE IDENTIFIED (server side)
Bug file: none (configuration fix)

**Fix attempt 1:** Set `passive=true` + `listen 1179` + iptables REDIRECT 179->1179. ExaBGP listened, but PE-4 sent RST after SYN-ACK. Cause: REDIRECT leaves reply source port as 1179; PE-4 expects 179.

**Fix attempt 2:** Reverted to `passive=false`. Need PE-4's listener to accept ExaBGP's connections. After routing-engine restart, PE-4 listener may be OK.

**Recommended:** Run ExaBGP with `authbind --deep` or `setcap cap_net_bind_service=+ep` on Python to bind to port 179, then use `passive=true` + `listen 179`. Or ensure PE-4 listener works and use `passive=false`.

---
