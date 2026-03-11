[09:30:44] Starting FlowSpec Scale tests on PE-4
[09:30:44] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[09:30:44] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_0930
[09:30:44] === Pre-flight Checks ===
[09:30:44] Checking DUT SSH connectivity...
[09:30:45]   DUT reachable
[09:30:45] Checking BGP FlowSpec-VPN session...
[09:30:46]   BGP state: Established
[09:30:48]   Peer IP: 2.2.2.2
[09:30:48] Detecting NCP ID...
[09:30:49]   NCP ID: 6
[09:30:49] Checking ExaBGP session...
[09:30:49]   bgp_tool: status --session-id pe_1
[09:30:49]   ExaBGP session 'pe_1' active
[09:30:49] 
============================================================
[09:30:49] === test_12: Session Flap Recovery at Scale (20K < 90s) ===
[09:30:49] ============================================================
[09:30:49]   Ensuring clean state (withdraw existing routes)...
[09:30:49]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:30:49]   No existing routes to withdraw (clean)
[09:30:49]   Ensuring clean state (withdraw existing routes)...
[09:30:49]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:30:49]   No existing routes to withdraw (clean)
[09:30:49]   Pre-loading 20000 routes...
[09:30:49]   bgp_tool: scale --session-id pe_1 --mode stress --count
[09:33:01]   PfxRcd=20000 state=Established t=1.4s
[09:33:01]   Converged: PfxRcd=20000 in 1.4s
[09:33:01]   Waiting 20s for TCAM programming...
[09:33:25]   Pre-flap: PfxRcd=20000 DP=11
[09:33:25]   Flapping session: clear bgp neighbor 2.2.2.2
[09:33:29]   Polling recovery (target=20000, timeout=150s)...
[09:33:31]   PfxRcd=20000 state=Established t=1.3s
[09:33:31]   Converged: PfxRcd=20000 in 1.3s
[09:33:31]   Waiting 20s for TCAM programming...
[09:33:55]   Post-flap: PfxRcd=20000 DP=11 recovery=5.3s
[09:33:55]   Verdict: FAIL
[09:33:55] Final cleanup: withdrawing all routes...
[09:33:55]   Ensuring clean state (withdraw existing routes)...
[09:33:55]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:34:58]   Cleaned: 0 routes withdrawn
[09:34:58]   Ensuring clean state (withdraw existing routes)...
[09:34:58]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:34:58]   No existing routes to withdraw (clean)