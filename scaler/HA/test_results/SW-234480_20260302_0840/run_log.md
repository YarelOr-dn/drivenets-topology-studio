[08:40:14] Starting FlowSpec Scale tests on PE-4
[08:40:14] Session: pe_1 | RT: 1234567:301 | RD: 1.1.1.1:100
[08:40:14] Results: /home/dn/SCALER/HA/test_results/SW-234480_20260302_0840
[08:40:14] === Pre-flight Checks ===
[08:40:14] Checking DUT SSH connectivity...
[08:40:15]   DUT reachable
[08:40:15] Checking BGP FlowSpec-VPN session...
[08:40:17]   BGP state: Established
[08:40:18]   Peer IP: 2.2.2.2
[08:40:18] Detecting NCP ID...
[08:40:40]   NCP ID: 6
[08:40:40] Checking ExaBGP session...
[08:40:40]   bgp_tool: status --session-id pe_1
[08:40:40]   ExaBGP session 'pe_1' active
[08:40:40] 
============================================================
[08:40:40] === test_01: Max BGP Routes (20K) + Convergence ===
[08:40:40] ============================================================
[08:40:40]   Ensuring clean state (withdraw existing routes)...
[08:40:40]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[08:40:40]   No existing routes to withdraw (clean)
[08:40:40]   Ensuring clean state (withdraw existing routes)...
[08:40:40]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:41:14]   Cleaned: 0 routes withdrawn
[08:41:14] Injecting 20000 routes (mode=stress)...
[08:41:14]   bgp_tool: scale --session-id pe_1 --mode stress --count
[08:43:21]   Injection: ok=True time=126.9s result=?
[08:43:21] Polling convergence (target=20000, timeout=180s)...
[08:43:23]   PfxRcd=19973 state=Established t=1.5s
[08:43:26]   Converged: PfxRcd=20000 in 4.7s
[08:43:30]   DP: NCP installed=11 TCAM={'installed': 0, 'total': 0, 'percent': 0.0}
[08:43:30]   Verdict: PASS (OK)
[08:43:30] Cooldown: withdrawing + 10s settle...
[08:43:30]   Ensuring clean state (withdraw existing routes)...
[08:43:30]   bgp_tool: scale --session-id pe_1 --mode stress --withdraw
[08:44:31]   Cleaned: 0 routes withdrawn
[08:44:31]   Ensuring clean state (withdraw existing routes)...
[08:44:31]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:44:31]   No existing routes to withdraw (clean)
[08:44:41] 
============================================================
[08:44:41] === test_03: Route Churn -- Bulk Add/Remove x5 ===
[08:44:41] ============================================================
[08:44:41]   Ensuring clean state (withdraw existing routes)...
[08:44:41]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:44:41]   No existing routes to withdraw (clean)
[08:44:41]   Churn cycle 1/5: injecting 10000...
[08:44:41]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[08:45:40]   Converged: PfxRcd=10000 in 1.7s
[08:45:41]   Churn cycle 1/5: withdrawing...
[08:45:46]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:46:21]   Cycle 1 done: inject_pfx=0 withdraw_pfx=0 state=Established
[08:46:21]   Churn cycle 2/5: injecting 10000...
[08:46:21]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[08:47:20]   Converged: PfxRcd=10000 in 1.3s
[08:47:21]   Churn cycle 2/5: withdrawing...
[08:47:26]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:48:01]   Cycle 2 done: inject_pfx=0 withdraw_pfx=0 state=Established
[08:48:01]   Churn cycle 3/5: injecting 10000...
[08:48:01]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[08:49:00]   Converged: PfxRcd=10000 in 1.7s
[08:49:01]   Churn cycle 3/5: withdrawing...
[08:49:06]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:49:41]   Cycle 3 done: inject_pfx=0 withdraw_pfx=0 state=Established
[08:49:41]   Churn cycle 4/5: injecting 10000...
[08:49:41]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[08:50:40]   PfxRcd=9930 state=Established t=1.2s
[08:50:46]   Converged: PfxRcd=10000 in 7.5s
[08:50:48]   Churn cycle 4/5: withdrawing...
[08:50:53]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:51:28]   Cycle 4 done: inject_pfx=9930 withdraw_pfx=0 state=Established
[08:51:28]   Churn cycle 5/5: injecting 10000...
[08:51:28]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --count
[08:52:27]   PfxRcd=9693 state=Established t=1.3s
[08:52:30]   Converged: PfxRcd=10000 in 4.5s
[08:52:32]   Churn cycle 5/5: withdrawing...
[08:52:37]   bgp_tool: scale --session-id pe_1 --mode flowspec-vpn-ipv4 --withdraw
[08:53:12]   Cycle 5 done: inject_pfx=9693 withdraw_pfx=0 state=Established
[08:53:12]   Verdict: PASS
[08:53:12] FATAL: [Errno 2] No such file or directory: '/home/dn/SCALER/HA/test_results/SW-234480_20260302_0840/test_03_route_churn_--_bulk_add/remove_x5.json'
[08:53:12] Traceback (most recent call last):
  File "/home/dn/SCALER/HA/sw_234480_scale_test.py", line 813, in main
    results = orch.run_all_tests(test_ids)
  File "/home/dn/SCALER/HA/sw_234480_scale_test.py", line 699, in run_all_tests
    r = self.run_single_test(t)
  File "/home/dn/SCALER/HA/sw_234480_scale_test.py", line 679, in run_single_test
    (self.run_dir / fname).write_text(json.dumps(result, indent=2))
  File "/usr/lib/python3.10/pathlib.py", line 1154, in write_text
    with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
  File "/usr/lib/python3.10/pathlib.py", line 1119, in open
    return self._accessor.open(self, mode, buffering, encoding, errors,
FileNotFoundError: [Errno 2] No such file or directory: '/home/dn/SCALER/HA/test_results/SW-234480_20260302_0840/test_03_route_churn_--_bulk_add/remove_x5.json'
