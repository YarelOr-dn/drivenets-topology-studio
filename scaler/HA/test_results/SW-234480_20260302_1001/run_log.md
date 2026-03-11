[10:01:07] Starting FlowSpec Scale tests on PE-4
[10:01:07] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[10:01:07] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_1001
[10:01:07] === Pre-flight Checks ===
[10:01:07] Checking DUT SSH connectivity...
[10:01:08]   DUT reachable
[10:01:08] Checking BGP FlowSpec-VPN session...
[10:01:09]   BGP state: Established
[10:01:10]   Peer IP: 2.2.2.2
[10:01:10] Detecting NCP ID...
[10:01:11]   NCP ID: 6
[10:01:11] Checking ExaBGP session...
[10:01:11]   bgp_tool: status --session-id pe_1
[10:01:11]   ExaBGP session 'pe_1' active
[10:01:11] 
============================================================
[10:01:11] === test_02: IPv4 + IPv6 Combined (12K + 4K) ===
[10:01:11] ============================================================
[10:01:11]   Ensuring clean state (withdraw existing routes)...
[10:01:11]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:01:12]   No existing routes to withdraw (clean)
[10:01:12]   Ensuring clean state (withdraw existing routes)...
[10:01:12]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[10:01:12]   No existing routes to withdraw (clean)
[10:01:12]   Ensuring clean state (withdraw existing routes)...
[10:01:12]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv6 --withdraw
[10:01:12]   No existing routes to withdraw (clean)
[10:01:12]   Injecting 4000 IPv6 FlowSpec-VPN routes...
[10:01:12]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv6 --count
[10:01:35]   IPv6 PfxRcd=3313 state=Established t=1.2s
[10:01:39]   IPv6 PfxRcd=4000 state=Established t=4.3s
[10:01:39]   IPv6 converged: PfxRcd=4000 in 4.3s
[10:01:39]   IPv6 BGP: converged=True PfxRcd=4000
[10:01:39]   Waiting 5s for IPv6 TCAM programming...
[10:01:44]   Injecting 12000 IPv4 FlowSpec-VPN routes...
[10:01:44]   bgp_tool: scale --session-id pe_1 --mode stress --count
[10:03:02]   PfxRcd=11493 state=Established t=1.3s
[10:03:06]   PfxRcd=12000 state=Established t=4.5s
[10:03:06]   Converged: PfxRcd=12000 in 4.5s
[10:03:06]   IPv4 BGP: converged=True PfxRcd=12000
[10:03:06]   Waiting 12s for IPv4 TCAM programming...
[10:03:19]   TCAM: IPv4=12000/12000  IPv6=0/4000
[10:03:20]   Verdict: FAIL
[10:03:20] Cooldown: withdrawing + 10s settle...
[10:03:20]   Ensuring clean state (withdraw existing routes)...
[10:03:20]   bgp_tool: scale --session-id pe_1 --mode combined --withdraw
[10:03:20]   No existing routes to withdraw (clean)
[10:03:20]   Ensuring clean state (withdraw existing routes)...
[10:03:20]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:03:58]   Cleaned: 0 routes withdrawn
[10:03:58]   Ensuring clean state (withdraw existing routes)...
[10:03:58]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[10:03:58]   No existing routes to withdraw (clean)
[10:03:58]   Ensuring clean state (withdraw existing routes)...
[10:03:58]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv6 --withdraw
[10:04:10]   Cleaned: 0 routes withdrawn
[10:04:20] 
============================================================
[10:04:20] === test_10: Withdraw All at Once (20K bulk) ===
[10:04:20] ============================================================
[10:04:20]   Ensuring clean state (withdraw existing routes)...
[10:04:20]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:04:20]   No existing routes to withdraw (clean)
[10:04:20]   Ensuring clean state (withdraw existing routes)...
[10:04:20]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[10:04:20]   No existing routes to withdraw (clean)
[10:04:20]   Injecting 20000 routes (mode=stress)...
[10:04:20]   bgp_tool: scale --session-id pe_1 --mode stress --count
[10:06:32]   PfxRcd=19672 state=Established t=1.2s
[10:06:35]   PfxRcd=20000 state=Established t=4.4s
[10:06:35]   Converged: PfxRcd=20000 in 4.4s
[10:06:35]   Waiting 20s for TCAM programming...
[10:06:59]   Pre-withdraw: PfxRcd=20000 DP=12000
[10:06:59]   Withdrawing ALL routes in one shot...
[10:06:59]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:08:03]   Polling until PfxRcd drops to 0...
[10:08:05]   Withdraw poll: PfxRcd=455 state=Established t=1.7s
[10:08:09]   Withdraw poll: PfxRcd=0 state=Established t=5.9s
[10:08:21]   Post-withdraw: DP=0 TCAM={'installed': 0, 'total': 12000, 'percent': 0.0, 'ipv6_installed': 0, 'ipv6_total': 4000}
[10:08:22]   Verdict: PASS (withdraw took 69.3s)
[10:08:22] Cooldown: withdrawing + 10s settle...
[10:08:22]   Ensuring clean state (withdraw existing routes)...
[10:08:22]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:08:22]   No existing routes to withdraw (clean)
[10:08:22]   Ensuring clean state (withdraw existing routes)...
[10:08:22]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[10:08:22]   No existing routes to withdraw (clean)
[10:08:32] 
============================================================
[10:08:32] === test_11: Exceed BGP Limit (25K) ===
[10:08:32] ============================================================
[10:08:32]   Ensuring clean state (withdraw existing routes)...
[10:08:32]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:08:32]   No existing routes to withdraw (clean)
[10:08:32]   Ensuring clean state (withdraw existing routes)...
[10:08:32]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[10:08:33]   No existing routes to withdraw (clean)
[10:08:33]   Injecting 25000 routes (mode=stress) -- exceeding 20K limit...
[10:08:33]   bgp_tool: scale --session-id pe_1 --mode stress --count
[10:11:18]   Polling BGP convergence (may cap below 25K)...
[10:11:19]   PfxRcd=25000 state=Established t=1.3s
[10:11:19]   Converged: PfxRcd=25000 in 1.3s
[10:11:19]   Waiting 25s for TCAM programming...
[10:11:49]   BGP accepted: 25000  DP installed: 12000
[10:11:49]   Capacity warning: False
[10:11:49]   Stability check (15s)...
[10:12:07]   Post-test BGP state: Established
[10:12:07]   Verdict: PASS
[10:12:07] Final cleanup: withdrawing all routes...
[10:12:07]   Ensuring clean state (withdraw existing routes)...
[10:12:07]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[10:13:28]   Cleaned: 0 routes withdrawn
[10:13:28]   Ensuring clean state (withdraw existing routes)...
[10:13:28]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[10:13:28]   No existing routes to withdraw (clean)
[10:13:28]   Ensuring clean state (withdraw existing routes)...
[10:13:28]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv6 --withdraw
[10:13:28]   No existing routes to withdraw (clean)