[21:06:04] Starting FlowSpec HA tests on PE-4
[21:06:04] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.7.2
[21:06:04] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2106
[21:06:04] Setting up Spirent: connect + reserve
[21:06:09] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[21:06:09] Spirent setup failed. Trying pre-existing rules workaround...
[21:06:09] Checking DUT for existing FlowSpec-VPN rules...
[21:06:10] Using 12000 pre-existing FlowSpec rules (workaround)
[21:06:10] Proceeding with pre-existing FlowSpec rules
[21:06:14] Device mode: cluster (CL-86,)
[21:06:14]   Active NCC: 1, Standby NCC: 0
[21:06:14]   Standby NCC IP provided: will use for NCC restart tests
[21:06:16] Device Lock: System Name = YOR_CL_PE-4
[21:06:17] FlowSpec routes on DUT: 12000
[21:06:19] BGP FlowSpec-VPN state: Established
[21:06:19] === test_08: NCC Switchover ===
[21:06:20] Device mode: cluster (CL-86,)
[21:06:20]   Active NCC: 1, Standby NCC: 0
[21:06:20]   Standby NCC IP provided: will use for NCC restart tests
[21:06:59]   SSH retry 1/3 in 5s (timed out)
[21:07:23] Triggering (1/1): request system ncc switchover
[21:07:24] SSH will drop. Initial wait 10s, then multi-IP polling...
[21:07:44]   Poll #1 (0s): 100.64.4.98 not ready
[21:07:50]   Reconnected via 100.64.7.2 (was 100.64.4.98)
[21:07:52]   Poll #2 (15s): BGP=Established routes=12000
[21:07:52] Recovered in 15s
[21:07:53]   Identity OK: YOR_CL_PE-4
[21:08:05]   XRAY CP capture: BGP traffic check
[21:08:06]   XRAY: 2 packets captured -> PASS
[21:08:06] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:08:06] === test_09: NCC Failover by Cold Restart (Power Reset) ===
[21:08:07] SAFETY ABORT: Standby NCC is not in standby-up state (switchover would fail)
[21:08:07] === test_10: NCP Force Restart (IPMI Power Cycle) ===
[21:08:10]   Safety: NCP-6 is operational
[21:08:23] Triggering (1/1): request system restart ncp 6 force
[21:08:26]   Poll #1 (0s): BGP=Established routes=12000
[21:08:26] Recovered in 0s
[21:08:29]   NCP-18 recovered to up in 2s
[21:09:06]   SSH retry 1/3 in 5s (timed out)
[21:09:26]   XRAY CP capture: BGP traffic check
[21:09:28]   XRAY: 2 packets captured -> PASS
[21:09:28] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:09:28] === test_11: BGP Graceful Restart ===
[21:10:10]   SSH retry 1/3 in 5s (timed out)
[21:10:20] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[21:10:30]   Poll #1 (0s): BGP=Established routes=12000
[21:10:30] Recovered in 0s
[21:11:13]   SSH retry 1/3 in 5s (timed out)
[21:11:21]   XRAY CP capture: BGP traffic check
[21:11:22]   XRAY: 2 packets captured -> PASS
[21:11:22] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:11:22] === test_12: Clear BGP Neighbors Multiple Times ===
[21:11:42] Triggering (1/10): clear bgp neighbor 2.2.2.2
[21:12:16] TEST ERROR: timed out
[21:12:16] === test_13: NCC Switchover with FlowSpec Admin-Disabled ===
[21:12:25] Device mode: cluster (CL-86,)
[21:12:25]   Active NCC: 0, Standby NCC: 1
[21:12:25]   Standby NCC IP provided: will use for NCC restart tests
[21:12:37] Triggering (1/1): request system ncc switchover
[21:12:38] SSH will drop. Initial wait 10s, then multi-IP polling...
[21:12:48]   Poll #1 (0s): 100.64.7.2 not ready
[21:12:53]   Poll #2 (5s): 100.64.7.2 not ready
[21:12:58]   Poll #3 (10s): 100.64.7.2 not ready
[21:13:03]   Poll #4 (15s): 100.64.7.2 not ready
[21:13:08]   Poll #5 (20s): 100.64.7.2 not ready
[21:13:13]   Poll #6 (25s): 100.64.7.2 not ready
[21:13:18]   Poll #7 (30s): 100.64.7.2 not ready
[21:13:23]   Poll #8 (35s): 100.64.7.2 not ready
[21:13:28]   Poll #9 (40s): 100.64.7.2 not ready
[21:13:33]   Poll #10 (45s): 100.64.7.2 not ready
[21:13:38]   Refreshing device IP from DB (DHCP may have changed after restart)
[21:13:38]   DB refresh: IP changed 100.64.7.2 -> 100.64.4.98
[21:13:48]   Poll #11 (50s): 100.64.4.98 not ready
[21:13:53]   Poll #12 (65s): 100.64.7.2 not ready
[21:14:01]   Poll #13 (70s): 100.64.4.98 not ready
[21:14:06]   Poll #14 (78s): 100.64.7.2 not ready
[21:14:14]   Poll #15 (83s): 100.64.4.98 not ready
[21:14:19]   Poll #16 (91s): 100.64.7.2 not ready
[21:14:27]   Poll #17 (96s): 100.64.4.98 not ready
[21:14:32]   Poll #18 (104s): 100.64.7.2 not ready
[21:14:40]   Poll #19 (109s): 100.64.4.98 not ready
[21:14:45]   Poll #20 (117s): 100.64.7.2 not ready
[21:15:09]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:15:32]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:16:01]   Snapshot command failed: show config protocols bgp...
[21:16:20]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:16:44]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:17:14]   Snapshot command failed: show bgp ipv4 flowspec-vpn routes...
[21:17:33]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:17:57]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:18:26]   Snapshot command failed: show system detail...
[21:18:45]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:19:10]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:19:58]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:20:22]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[21:20:51] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)