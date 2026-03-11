[20:08:59] Starting FlowSpec HA tests on PE-4
[20:08:59] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[20:08:59] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2008
[20:08:59] Setting up Spirent: connect + reserve
[20:09:02] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[20:09:02] Spirent setup failed. Trying pre-existing rules workaround...
[20:09:02] Checking DUT for existing FlowSpec-VPN rules...
[20:09:05] Using 12000 pre-existing FlowSpec rules (workaround)
[20:09:05] Proceeding with pre-existing FlowSpec rules
[20:09:12] Device mode: cluster (CL-86,)
[20:09:12]   Active NCC: 0, Standby NCC: 1
[20:09:12]   Standby NCC IP provided: will use for NCC restart tests
[20:09:15] Device Lock: System Name = YOR_CL_PE-4
[20:09:18] FlowSpec routes on DUT: 12000
[20:09:21] BGP FlowSpec-VPN state: Established
[20:09:21] === test_01: RIB Manager Process Restart ===
[20:10:09]   SSH retry 1/3 in 5s (timed out)
[20:10:21] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[20:10:28]   Poll #1 (0s): BGP=Established routes=2
[20:10:36]   Poll #2 (7s): BGP=Established routes=0
[20:10:43]   Poll #3 (15s): BGP=Established routes=12000
[20:10:43] Recovered in 15s
[20:11:24]   XRAY CP capture: BGP traffic check
[20:11:28]   XRAY: 2 packets captured -> PASS
[20:11:28] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:11:28] === test_02: BGPd Process Restart ===
[20:12:18] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[20:12:25]   Poll #1 (0s): BGP=Established routes=2
[20:12:33]   Poll #2 (7s): BGP=Established routes=12000
[20:12:33] Recovered in 7s
[20:13:21]   XRAY CP capture: BGP traffic check
[20:13:25]   XRAY: 2 packets captured -> PASS
[20:13:25] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:13:25] === test_03: wb_agent Process Restart ===
[20:14:15] Triggering (1/1): request system process restart ncp 6 datapath wb_agent
[20:14:22]   Poll #1 (0s): BGP=Established routes=12000
[20:14:22] Recovered in 0s
[20:14:39]   XRAY CP capture: BGP traffic check
[20:14:51]   XRAY: 2 packets captured -> PASS
[20:14:51] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:14:51] Cooldown 15s after datapath-affecting test...
[20:15:06] === test_04: BGP Container Restart ===
[20:15:37] Triggering (1/1): request system container restart ncc 0 routing-engine
[20:16:00]   Poll #1 (0s): BGP=Established routes=0
[20:16:07]   Poll #2 (23s): BGP=Established routes=12000
[20:16:07] Recovered in 23s
[20:16:28]   XRAY CP capture: BGP traffic check
[20:16:32]   XRAY: 2 packets captured -> PASS
[20:16:32] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:16:32] === test_05: NCP Container Restart ===
[20:16:52] Triggering (1/1): request system container restart ncp 18 datapath
[20:16:59]   Poll #1 (0s): BGP=Established routes=12000
[20:16:59] Recovered in 0s
[20:17:46]   XRAY CP capture: BGP traffic check
[20:17:51]   XRAY: 2 packets captured -> PASS
[20:17:51] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:17:51] Cooldown 15s after datapath-affecting test...
[20:18:06] === test_06: Cold System Restart ===
[20:18:42] Triggering (1/1): request system restart
[20:18:46] SSH will drop. Initial wait 20s, then multi-IP polling...
[20:19:39]   NCE IP refresh failed (non-fatal): Authentication timeout.
[20:19:39]   Poll #1 (0s): BGP=Established routes=12000
[20:19:39] Recovered in 0s
[20:20:06]   Identity check failed (SSH error, will retry later): [Errno None] Unable to connect to port 22 on 100.64.4.98
[20:20:25]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:20:49]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:21:18]   Snapshot command failed: show config protocols bgp...
[20:21:38]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:22:02]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:22:31]   Snapshot command failed: show bgp ipv4 flowspec-vpn summary...
[20:22:50]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:23:14]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:23:44]   Snapshot command failed: show bgp ipv4 flowspec-vpn routes...
[20:24:03]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:24:27]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:24:56]   Snapshot command failed: show flowspec ncp...
[20:25:14]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.4.98)
[20:25:44]   XRAY CP capture: BGP traffic check
[20:25:48]   XRAY: 2 packets captured -> PASS
[20:25:48] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:25:48] === test_07: Warm System Restart ===
[20:26:08] Triggering (1/1): request system restart warm
[20:26:12] SSH will drop. Initial wait 20s, then multi-IP polling...
[20:26:42]   Poll #1 (0s): 100.64.4.98 not ready
[20:26:47]   Poll #2 (15s): 100.64.4.122 not ready
[20:26:55]   Poll #3 (20s): 100.64.4.98 not ready
[20:27:00]   Poll #4 (28s): 100.64.4.122 not ready
[20:27:08]   Poll #5 (33s): 100.64.4.98 not ready
[20:27:13]   Poll #6 (41s): 100.64.4.122 not ready
[20:27:21]   Poll #7 (46s): 100.64.4.98 not ready
[20:27:26]   Poll #8 (54s): 100.64.4.122 not ready
[20:27:34]   Poll #9 (59s): 100.64.4.98 not ready
[20:27:39]   Poll #10 (67s): 100.64.4.122 not ready
[20:27:47]   Poll #11 (72s): 100.64.4.98 not ready
[20:27:53]   Poll #12 (80s): 100.64.4.122 not ready
[20:28:01]   Poll #13 (85s): 100.64.4.98 not ready
[20:28:06]   Poll #14 (93s): 100.64.4.122 not ready
[20:28:16]   Poll #15 (98s): BGP=Established routes=2
[20:28:24]   Poll #16 (109s): BGP=Established routes=2
[20:28:32]   Poll #17 (117s): BGP=Established routes=2
[20:28:40]   Poll #18 (124s): BGP=Established routes=2
[20:28:48]   Poll #19 (132s): BGP=Established routes=2
[20:28:56]   Poll #20 (140s): BGP=Established routes=2
[20:29:03]   Poll #21 (148s): BGP=Established routes=2
[20:29:11]   Poll #22 (156s): BGP=Established routes=2
[20:29:19]   Poll #23 (164s): BGP=Established routes=2
[20:29:27]   Poll #24 (171s): BGP=Established routes=2
[20:29:35]   Poll #25 (179s): BGP=Established routes=2
[20:29:43]   Poll #26 (187s): BGP=Established routes=2
[20:29:51]   Poll #27 (195s): BGP=Established routes=2
[20:29:58]   Poll #28 (203s): BGP=Established routes=2
[20:30:06]   Poll #29 (211s): BGP=Established routes=2
[20:30:21]   Poll #30 (219s): BGP=Established routes=2
[20:30:29]   Poll #31 (234s): BGP=Established routes=2
[20:30:37]   Poll #32 (242s): BGP=Established routes=2
[20:30:45]   Poll #33 (250s): BGP=Established routes=2
[20:30:53]   Poll #34 (257s): BGP=Established routes=2
[20:31:01]   Poll #35 (265s): BGP=Established routes=2
[20:31:09]   Poll #36 (273s): BGP=Established routes=2
[20:31:16]   Poll #37 (281s): BGP=Established routes=2
[20:31:24]   Poll #38 (289s): BGP=Established routes=2
[20:31:32]   Poll #39 (297s): BGP=Established routes=2
[20:31:40]   Poll #40 (305s): BGP=Established routes=2
[20:31:48]   Poll #41 (312s): BGP=Established routes=2
[20:31:56]   Poll #42 (320s): BGP=Established routes=12000
[20:31:56] Recovered in 320s
[20:31:59]   Identity OK: YOR_CL_PE-4
[20:32:42]   XRAY CP capture: BGP traffic check
[20:32:53]   XRAY: 2 packets captured -> PASS
[20:32:53] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:32:53] === test_08: NCC Switchover ===
[20:32:56] Device mode: cluster (CL-86,)
[20:32:56]   Active NCC: 0, Standby NCC: 1
[20:32:56]   Standby NCC IP provided: will use for NCC restart tests
[20:33:42] Triggering (1/1): request system ncc switchover
[20:33:53] SSH will drop. Initial wait 10s, then multi-IP polling...
[20:34:13]   Poll #1 (0s): BGP=Unknown routes=-1
[20:34:21]   Poll #2 (15s): BGP=Established routes=12000
[20:34:21] Recovered in 15s
[20:34:24]   Identity OK: YOR_CL_PE-4
[20:34:47]   XRAY CP capture: BGP traffic check
[20:34:51]   XRAY: 2 packets captured -> PASS
[20:34:51] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)