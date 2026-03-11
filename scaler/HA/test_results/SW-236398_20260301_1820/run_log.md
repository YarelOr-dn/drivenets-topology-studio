[18:20:54] Starting FlowSpec HA tests on PE-4
[18:20:54] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[18:20:54] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1820
[18:20:54] Setting up Spirent: connect + reserve
[18:20:57] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[18:20:57] Spirent setup failed. Trying pre-existing rules workaround...
[18:20:57] Checking DUT for existing FlowSpec-VPN rules...
[18:21:02] Using 12000 pre-existing FlowSpec rules (workaround)
[18:21:02] Proceeding with pre-existing FlowSpec rules
[18:21:18] Device mode: cluster (CL-86,)
[18:21:18]   Active NCC: 0, Standby NCC: 1
[18:21:18]   Standby NCC IP provided: will use for NCC restart tests
[18:22:23]   SSH retry 1/3 in 15s (timed out)
[18:22:46] FlowSpec routes on DUT: 12000
[18:22:59] BGP FlowSpec-VPN state: Established
[18:22:59] === test_01: RIB Manager Process Restart ===
[18:25:24] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[18:26:02]   Poll #1: BGP=Established routes=12000
[18:26:02] Recovered
[18:27:33]   XRAY CP capture: BGP traffic check
[18:27:44]   XRAY: 2 packets captured -> PASS
[18:27:44] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[18:27:44] === test_02: BGPd Process Restart ===
[18:29:42] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[18:29:55]   Poll #1: BGP=Established routes=2
[18:30:05]   Poll #2: BGP=Established routes=12000
[18:30:05] Recovered
[18:31:18]   XRAY CP capture: BGP traffic check
[18:31:51]   XRAY: 2 packets captured -> PASS
[18:31:51] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[18:31:51] === test_03: wb_agent Process Restart ===
[18:32:17] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[18:32:30]   Poll #1: BGP=Established routes=12000
[18:32:30] Recovered
[18:34:10]   XRAY CP capture: BGP traffic check
[18:34:18]   XRAY: 2 packets captured -> PASS
[18:34:18] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[18:34:18] Cooldown 45s after datapath-affecting test...
[18:35:03] === test_04: BGP Container Restart ===
[18:36:38] Triggering (1/1): request system container restart ncc 0 routing-engine
[18:36:51]   Poll #1: BGP=Established routes=12000
[18:36:51] Recovered
[18:38:01]   XRAY CP capture: BGP traffic check
[18:38:12]   XRAY: 2 packets captured -> PASS
[18:38:12] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[18:38:12] === test_05: NCP Container Restart ===
[18:39:09] Triggering (1/1): request system container restart ncp 0 datapath
[18:39:48]   Poll #1: BGP=Established routes=12000
[18:39:48] Recovered
[18:40:53]   SSH retry 1/3 in 15s (timed out)
[18:42:07]   XRAY CP capture: BGP traffic check
[18:42:18]   XRAY: 2 packets captured -> PASS
[18:42:18] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[18:42:18] Cooldown 45s after datapath-affecting test...
[18:43:03] === test_06: Cold System Restart ===
[18:45:18] Triggering (1/1): request system restart
[18:45:26] Waiting for reconnect (60s)...
[18:46:50]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:47:34]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:48:32]   Reconnecting... ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:49:06]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:49:48]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:50:45]   Reconnecting... ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:51:18]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:52:00]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:52:36]   Poll #3: BGP=Established routes=2
[18:55:06]   SSH retry 1/3 in 15s (timed out)
[18:55:49]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:56:49] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:56:49] === test_07: Warm System Restart ===
[18:57:18]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:57:59]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:58:54]   Snapshot command failed: show bgp ipv4 flowspec-vpn summary...
[18:59:23]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:00:00]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:00:54]   Snapshot command failed: show bgp ipv4 flowspec-vpn routes...
[19:01:33] Triggering (1/1): request system restart warm
[19:01:40] Waiting for reconnect (60s)...
[19:03:10]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:03:41]   Poll #1: BGP=Established routes=2
[19:03:51]   Poll #2: BGP=Established routes=2
[19:04:01]   Poll #3: BGP=Established routes=2
[19:04:11]   Poll #4: BGP=Established routes=2
[19:04:21]   Poll #5: BGP=Established routes=2
[19:05:21]   Poll #6: BGP=Established routes=2
[19:06:04]   Poll #7: BGP=Established routes=2
[19:06:14]   Poll #8: BGP=Established routes=2
[19:06:24]   Poll #9: BGP=Established routes=2
[19:07:34]   SSH retry 1/3 in 15s (timed out)
[19:08:26]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:09:12]   Poll #10: BGP=Established routes=2
[19:10:42] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)