[08:58:37] Starting FlowSpec Scale tests on PE-4
[08:58:37] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[08:58:37] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_0858
[08:58:37] === Pre-flight Checks ===
[08:58:37] Checking DUT SSH connectivity...
[08:58:38]   DUT reachable
[08:58:38] Checking BGP FlowSpec-VPN session...
[08:58:40]   BGP state: Established
[08:58:41]   Peer IP: 2.2.2.2
[08:58:41] Detecting NCP ID...
[08:58:42]   NCP ID: 6
[08:58:42] Checking ExaBGP session...
[08:58:42]   bgp_tool: status --session-id pe_1
[08:58:42]   ExaBGP session 'pe_1' active
[08:58:42] 
============================================================
[08:58:42] === test_03: Route Churn -- Bulk Add/Remove x5 ===
[08:58:42] ============================================================
[08:58:42]   Ensuring clean state (withdraw existing routes)...
[08:58:42]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:58:42]   No existing routes to withdraw (clean)
[08:58:42]   Churn cycle 1/5: injecting 10000...
[08:58:42]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[08:59:41]   PfxRcd=9764 state=Established t=1.2s
[08:59:45]   Converged: PfxRcd=10000 in 4.5s
[08:59:46]   Churn cycle 1/5: withdrawing...
[08:59:51]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:00:26]   Cycle 1 done: inject_pfx=9764 withdraw_pfx=0 state=Established
[09:00:26]   Churn cycle 2/5: injecting 10000...
[09:00:26]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[09:01:25]   PfxRcd=9904 state=Established t=1.2s
[09:01:32]   Converged: PfxRcd=10000 in 7.7s
[09:01:33]   Churn cycle 2/5: withdrawing...
[09:01:38]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:02:14]   Cycle 2 done: inject_pfx=9904 withdraw_pfx=0 state=Established
[09:02:14]   Churn cycle 3/5: injecting 10000...
[09:02:14]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[09:03:13]   PfxRcd=9438 state=Established t=1.3s
[09:03:16]   Converged: PfxRcd=10000 in 4.5s
[09:03:18]   Churn cycle 3/5: withdrawing...
[09:03:23]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:03:58]   Cycle 3 done: inject_pfx=9438 withdraw_pfx=0 state=Established
[09:03:58]   Churn cycle 4/5: injecting 10000...
[09:03:58]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[09:04:58]   PfxRcd=9491 state=Established t=1.2s
[09:05:01]   Converged: PfxRcd=10000 in 4.5s
[09:05:02]   Churn cycle 4/5: withdrawing...
[09:05:07]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:05:43]   Cycle 4 done: inject_pfx=9491 withdraw_pfx=0 state=Established
[09:05:43]   Churn cycle 5/5: injecting 10000...
[09:05:43]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[09:06:43]   PfxRcd=9509 state=Established t=1.3s
[09:06:46]   Converged: PfxRcd=10000 in 4.5s
[09:06:47]   Churn cycle 5/5: withdrawing...
[09:06:52]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:07:28]   Cycle 5 done: inject_pfx=9509 withdraw_pfx=0 state=Established
[09:07:28]   Verdict: PASS
[09:07:28] Cooldown: withdrawing + 10s settle...
[09:07:28]   Ensuring clean state (withdraw existing routes)...
[09:07:28]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:07:29]   No existing routes to withdraw (clean)
[09:07:39] 
============================================================
[09:07:39] === test_08: Exceed DP Limit -- Incremental (14K) ===
[09:07:39] ============================================================
[09:07:39]   Ensuring clean state (withdraw existing routes)...
[09:07:39]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:07:39]   No existing routes to withdraw (clean)
[09:07:39]   Phase 1: Injecting 12000 (fill DP)...
[09:07:39]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[09:08:51]   PfxRcd=11951 state=Established t=1.7s
[09:08:54]   Converged: PfxRcd=12000 in 5.0s
[09:08:54]   Phase 1 converged: PfxRcd=11951
[09:08:54]   Phase 2: Injecting 2000 more (exceed)...
[09:08:54]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[09:10:19]   PfxRcd=13514 state=Established t=1.3s
[09:10:22]   Converged: PfxRcd=14000 in 4.9s
[09:10:27]   DP: installed=11 TCAM={'installed': 12000, 'total': 12000, 'percent': 100.0, 'ipv6_installed': 21, 'ipv6_total': 4000}
[09:10:27]   Capacity warning in logs: False
[09:10:27]   Verdict: PASS
[09:10:27] Cooldown: withdrawing + 10s settle...
[09:10:27]   Ensuring clean state (withdraw existing routes)...
[09:10:27]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:11:09]   Cleaned: 0 routes withdrawn
[09:11:19] 
============================================================
[09:11:19] === test_09: Exceed DP Limit -- Bulk (15K) ===
[09:11:19] ============================================================
[09:11:19]   Ensuring clean state (withdraw existing routes)...
[09:11:19]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:11:19]   No existing routes to withdraw (clean)
[09:11:19]   Ensuring clean state (withdraw existing routes)...
[09:11:19]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:11:20]   No existing routes to withdraw (clean)
[09:11:20]   Bulk injecting 15000 routes (mode=stress)...
[09:11:20]   bgp_tool: scale --session-id pe_1 --mode stress --count
[09:12:56]   PfxRcd=14942 state=Established t=1.2s
[09:13:00]   Converged: PfxRcd=15000 in 4.6s
[09:13:05]   BGP accepted: 14942  DP installed: 11
[09:13:05]   Capacity warning: False
[09:13:05]   Stability check (15s)...
[09:13:22]   Verdict: PASS
[09:13:22] Cooldown: withdrawing + 10s settle...
[09:13:22]   Ensuring clean state (withdraw existing routes)...
[09:13:22]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:14:08]   Cleaned: 0 routes withdrawn
[09:14:08]   Ensuring clean state (withdraw existing routes)...
[09:14:08]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:14:08]   No existing routes to withdraw (clean)
[09:14:18] 
============================================================
[09:14:18] === test_12: Session Flap Recovery at Scale (20K < 90s) ===
[09:14:18] ============================================================
[09:14:18]   Ensuring clean state (withdraw existing routes)...
[09:14:18]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:14:19]   No existing routes to withdraw (clean)
[09:14:19]   Ensuring clean state (withdraw existing routes)...
[09:14:19]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:14:19]   No existing routes to withdraw (clean)
[09:14:19]   Pre-loading 20000 routes...
[09:14:19]   bgp_tool: scale --session-id pe_1 --mode stress --count
[09:16:29]   PfxRcd=12570 state=Established t=1.5s
[09:16:33]   PfxRcd=2 state=Established t=4.7s
[09:20:37] Final cleanup: withdrawing all routes...
[09:20:37]   Ensuring clean state (withdraw existing routes)...
[09:20:37]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:21:40]   Cleaned: 0 routes withdrawn
[09:21:40]   Ensuring clean state (withdraw existing routes)...
[09:21:40]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:21:40]   No existing routes to withdraw (clean)