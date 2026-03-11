[08:36:44] Starting FlowSpec Scale tests on PE-4
[08:36:44] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[08:36:44] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_0836
[08:36:44] === Pre-flight Checks ===
[08:36:44] Checking DUT SSH connectivity...
[08:36:45]   DUT reachable
[08:36:45] Checking BGP FlowSpec-VPN session...
[08:36:46]   BGP state: Established
[08:36:47]   Peer IP: 2.2.2.2
[08:36:47] Detecting NCP ID...
[08:36:49]   NCP ID: 6
[08:36:49] Checking ExaBGP session...
[08:36:49]   bgp_tool: status --session-id pe_1
[08:36:49]   WARNING: ExaBGP session 'pe_1' may not be active
[08:36:49]   Start it: python3 bgp_tool.py start --session-id pe_1 --peer-ip <RR_IP>
[08:36:49] 
============================================================
[08:36:49] === test_01: Max BGP Routes (20K) + Convergence ===
[08:36:49] ============================================================
[08:36:49]   Ensuring clean state (withdraw existing routes)...
[08:36:49]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[08:36:49]   Cleaned: 0 routes withdrawn
[08:36:49]   Ensuring clean state (withdraw existing routes)...
[08:36:49]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:36:49]   Cleaned: 0 routes withdrawn
[08:36:49] Injecting 20000 routes (mode=stress)...
[08:36:49]   bgp_tool: scale --session-id pe_1 --mode stress --count
[08:36:49]   Injection: ok=True time=0.0s result=?
[08:36:49] Polling convergence (target=20000, timeout=180s)...
[08:36:50]   PfxRcd=12000 state=Established t=1.5s
[08:39:56]   DP: NCP installed=0 TCAM={'installed': 0, 'total': 0, 'percent': 0.0}
[08:39:56]   Verdict: FAIL (not_converged (got 12000/20000))
[08:39:56] Final cleanup: withdrawing all routes...
[08:39:56]   Ensuring clean state (withdraw existing routes)...
[08:39:56]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[08:39:56]   Cleaned: 0 routes withdrawn
[08:39:56]   Ensuring clean state (withdraw existing routes)...
[08:39:56]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:39:56]   Cleaned: 0 routes withdrawn