[09:36:42] Starting FlowSpec Scale tests on PE-4
[09:36:42] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[09:36:42] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_0936
[09:36:42] === Pre-flight Checks ===
[09:36:42] Checking DUT SSH connectivity...
[09:36:43]   DUT reachable
[09:36:43] Checking BGP FlowSpec-VPN session...
[09:36:45]   BGP state: Established
[09:36:46]   Peer IP: 2.2.2.2
[09:36:46] Detecting NCP ID...
[09:36:47]   NCP ID: 6
[09:36:47] Checking ExaBGP session...
[09:36:47]   bgp_tool: status --session-id pe_1
[09:36:48]   ExaBGP session 'pe_1' active
[09:36:48] 
============================================================
[09:36:48] === test_12: Session Flap Recovery at Scale (20K < 90s) ===
[09:36:48] ============================================================
[09:36:48]   Ensuring clean state (withdraw existing routes)...
[09:36:48]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:36:48]   No existing routes to withdraw (clean)
[09:36:48]   Ensuring clean state (withdraw existing routes)...
[09:36:48]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:36:48]   No existing routes to withdraw (clean)
[09:36:48]   Pre-loading 20000 routes...
[09:36:48]   bgp_tool: scale --session-id pe_1 --mode stress --count
[09:39:00]   PfxRcd=19737 state=Established t=1.4s
[09:39:03]   PfxRcd=20000 state=Established t=5.0s
[09:39:03]   Converged: PfxRcd=20000 in 5.0s
[09:39:03]   Waiting 20s for TCAM programming...
[09:39:28]   Pre-flap: PfxRcd=20000 DP=12000
[09:39:28]   Flapping session: clear bgp neighbor 2.2.2.2
[09:39:32]   Polling recovery (target=20000, timeout=150s)...
[09:39:33]   PfxRcd=20000 state=Established t=1.3s
[09:39:33]   Converged: PfxRcd=20000 in 1.3s
[09:39:33]   Waiting 20s for TCAM programming...
[09:39:57]   Post-flap: PfxRcd=20000 DP=12000 recovery=5.5s
[09:39:57]   Verdict: PASS
[09:39:57] Final cleanup: withdrawing all routes...
[09:39:57]   Ensuring clean state (withdraw existing routes)...
[09:39:57]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[09:41:01]   Cleaned: 0 routes withdrawn
[09:41:01]   Ensuring clean state (withdraw existing routes)...
[09:41:01]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[09:41:01]   No existing routes to withdraw (clean)