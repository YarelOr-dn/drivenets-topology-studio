# EVPN Proxy-ARP Source Notes

This file records the Proxy-ARP knowledge sources used by the merged `/TP`
pipeline for EVPN-SI IRB / IP mobility test plans.

## Debug Cheat Sheet

| Field | Value |
|---|---|
| Title | `Proxy-ARP Debug tools cheat sheet` |
| Confluence page | `https://drivenets.atlassian.net/wiki/spaces/DV/pages/5485461507` |
| Page ID | `5485461507` |
| Provenance | `CHEATSHEET_DEBUG` |
| Role | Debug and evidence commands only |

This page provides useful Routing, DP, Neighbor Manager, and Infra debug commands
for ARP/NDP and Proxy-ARP analysis. It does not replace the behavioral source of
truth from the EVPN-SI IRB Jira stories or design documents.

## Commands Imported As Debug-Cheat-Sheet

- `ip monitor`
- `arp`
- `show dnos-internal routing fib-manager database neighbor`
- `show fib-manager database global-mac-neigh`
- `show dnos-internal routing fib-manager database l2-maintained-neighbors statistics`
- `clear dnos-internal routing fib-manager l2-maintained-neighbors statistics`
- `wbox-cli proxy arp tracing enable`
- `wbox-cli packet processor tracing enable`
- `xraycli /wb_agent/proxy_arp/db`
- `xraycli /wb_agent/proxy_arp/db_info`
- `xraycli /wb_agent/proxy_arp/msg_recv`
- `xraycli /wb_agent/proxy_arp/msg_sent`
- `xraycli /wb_agent/proxy_arp/rx`
- `xraycli /wb_agent/proxy_arp/tx`
- `xraycli /neighbour_manager/neigh`
- `ip neigh`
- `ip link`

## Usage Rule

Use these commands for evidence collection and debug layers. Do not treat them
as canonical DNOS CLI syntax for pass/fail assertions unless they are promoted
to `LIVE_VALIDATED` by a captured device transcript.
