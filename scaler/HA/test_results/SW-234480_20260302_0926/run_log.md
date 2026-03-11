[09:26:10] Starting FlowSpec Scale tests on PE-4
[09:26:10] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[09:26:10] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_0926
[09:26:10] === Pre-flight Checks ===
[09:26:10] Checking DUT SSH connectivity...
[09:26:12]   DUT reachable
[09:26:12] Checking BGP FlowSpec-VPN session...
[09:26:13]   BGP state: Established
[09:26:14]   Peer IP: 2.2.2.2
[09:26:14] Detecting NCP ID...
[09:26:15]   NCP ID: 6
[09:26:15] Checking ExaBGP session...
[09:26:15]   bgp_tool: status --session-id pe_1
[09:26:16]   ExaBGP session 'pe_1' active
[09:26:16] 
============================================================
[09:26:16] === test_12: Session Flap Recovery at Scale (20K < 90s) ===
[09:26:16] ============================================================
[09:26:16]   Ensuring clean state (withdraw existing routes)...
[09:26:16]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:26:16]   No existing routes to withdraw (clean)
[09:26:16]   Ensuring clean state (withdraw existing routes)...
[09:26:16]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:26:16]   No existing routes to withdraw (clean)
[09:26:16]   Pre-loading 20000 routes...
[09:26:16]   bgp_tool: scale --session-id pe_1 --mode stress --count
[09:28:27]   Converged: PfxRcd=20000 in 1.3s
[09:28:31]   Pre-flap: PfxRcd=0 DP=11
[09:28:31]   Flapping session: clear bgp neighbor 2.2.2.2
[09:28:35]   Polling recovery (target=20000, timeout=150s)...
[09:28:36]   Converged: PfxRcd=20000 in 1.3s
[09:28:41]   Post-flap: PfxRcd=0 DP=0 recovery=5.4s
[09:28:41]   Verdict: FAIL
[09:28:41] Final cleanup: withdrawing all routes...
[09:28:41]   Ensuring clean state (withdraw existing routes)...
[09:28:41]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:29:44]   Cleaned: 0 routes withdrawn
[09:29:44]   Ensuring clean state (withdraw existing routes)...
[09:29:44]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:29:44]   No existing routes to withdraw (clean)