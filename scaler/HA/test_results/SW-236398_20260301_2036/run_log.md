[20:36:54] Starting FlowSpec HA tests on PE-4
[20:36:54] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[20:36:54] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2036
[20:36:54] Setting up Spirent: connect + reserve
[20:36:57] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[20:36:57] Spirent setup failed. Trying pre-existing rules workaround...
[20:36:57] Checking DUT for existing FlowSpec-VPN rules...
[20:37:00] Using 12000 pre-existing FlowSpec rules (workaround)
[20:37:00] Proceeding with pre-existing FlowSpec rules
[20:37:06] Device mode: cluster (CL-86,)
[20:37:06]   Active NCC: 0, Standby NCC: 1
[20:37:06]   Standby NCC IP provided: will use for NCC restart tests
[20:37:09] Device Lock: System Name = YOR_CL_PE-4
[20:37:11] FlowSpec routes on DUT: 12000
[20:37:14] BGP FlowSpec-VPN state: Established
[20:37:14] === test_06: Cold System Restart ===
[20:38:09] Triggering (1/1): request system restart
[20:38:13] System restart: waiting for device to go DOWN first...
[20:38:16]   Still reachable (5s), waiting for shutdown...
[20:38:51]   Device confirmed DOWN after 10s
[20:39:01]   Poll #1 (0s): 100.64.4.98 not ready
[20:39:16]   Poll #2 (15s): 100.64.4.122 not ready
[20:39:24]   Poll #3 (30s): 100.64.4.98 not ready
[20:39:29]   Poll #4 (38s): 100.64.4.122 not ready
[20:39:37]   Poll #5 (43s): 100.64.4.98 not ready
[20:39:42]   Poll #6 (51s): 100.64.4.122 not ready
[20:39:50]   Poll #7 (56s): 100.64.4.98 not ready
[20:39:55]   Poll #8 (64s): 100.64.4.122 not ready
[20:40:04]   Poll #9 (69s): 100.64.4.98 not ready
[20:40:09]   Poll #10 (77s): 100.64.4.122 not ready
[20:40:14]   Poll #11 (82s): 100.64.4.98 not ready
[20:40:19]   Poll #12 (88s): 100.64.4.122 not ready
[20:40:27]   Poll #13 (93s): 100.64.4.98 not ready
[20:40:32]   Poll #14 (101s): 100.64.4.122 not ready
[20:40:40]   Poll #15 (106s): 100.64.4.98 not ready
[20:40:45]   Poll #16 (114s): 100.64.4.122 not ready
[20:40:54]   Poll #17 (119s): 100.64.4.98 not ready
[20:40:59]   Poll #18 (127s): 100.64.4.122 not ready
[20:41:07]   Poll #19 (132s): 100.64.4.98 not ready
[20:41:12]   Poll #20 (140s): 100.64.4.122 not ready
[20:41:20]   Poll #21 (145s): 100.64.4.98 not ready
[20:41:25]   Poll #22 (153s): 100.64.4.122 not ready
[20:41:33]   Poll #23 (158s): 100.64.4.98 not ready
[20:41:38]   Poll #24 (166s): 100.64.4.122 not ready
[20:41:46]   Poll #25 (171s): 100.64.4.98 not ready
[20:41:51]   Poll #26 (179s): 100.64.4.122 not ready
[20:41:59]   Poll #27 (184s): 100.64.4.98 not ready
[20:42:04]   Poll #28 (192s): 100.64.4.122 not ready
[20:42:12]   Poll #29 (197s): 100.64.4.98 not ready
[20:42:17]   Poll #30 (205s): 100.64.4.122 not ready
[20:42:25]   Poll #31 (210s): 100.64.4.98 not ready
[20:42:30]   Poll #32 (219s): 100.64.4.122 not ready
[20:42:38]   Poll #33 (224s): 100.64.4.98 not ready
[20:42:43]   Poll #34 (232s): 100.64.4.122 not ready
[20:42:51]   Poll #35 (237s): 100.64.4.98 not ready
[20:42:56]   Poll #36 (245s): 100.64.4.122 not ready
[20:43:04]   Poll #37 (250s): 100.64.4.98 not ready
[20:43:09]   Poll #38 (258s): 100.64.4.122 not ready
[20:43:18]   Poll #39 (263s): 100.64.4.98 not ready
[20:43:23]   Poll #40 (271s): 100.64.4.122 not ready
[20:43:31]   Poll #41 (276s): 100.64.4.98 not ready
[20:43:36]   Poll #42 (284s): 100.64.4.122 not ready
[20:43:44]   Poll #43 (289s): 100.64.4.98 not ready
[20:43:49]   Poll #44 (297s): 100.64.4.122 not ready
[20:43:57]   Poll #45 (302s): 100.64.4.98 not ready
[20:44:02]   Poll #46 (310s): 100.64.4.122 not ready
[20:44:10]   Poll #47 (315s): 100.64.4.98 not ready
[20:44:15]   Poll #48 (323s): 100.64.4.122 not ready
[20:44:23]   Poll #49 (328s): 100.64.4.98 not ready
[20:44:28]   Poll #50 (336s): 100.64.4.122 not ready
[20:44:39]   Poll #51 (341s): BGP=Established routes=2
[20:44:47]   Poll #52 (352s): BGP=Established routes=2
[20:44:54]   Poll #53 (360s): BGP=Established routes=2
[20:45:02]   Poll #54 (368s): BGP=Established routes=2
[20:45:10]   Poll #55 (376s): BGP=Established routes=2
[20:45:18]   Poll #56 (383s): BGP=Established routes=2
[20:45:26]   Poll #57 (391s): BGP=Established routes=2
[20:45:34]   Poll #58 (399s): BGP=Established routes=2
[20:45:42]   Poll #59 (407s): BGP=Established routes=2
[20:45:49]   Poll #60 (415s): BGP=Established routes=2
[20:46:05]   Poll #61 (423s): BGP=Established routes=2
[20:46:12]   Poll #62 (438s): BGP=Established routes=2
[20:46:20]   Poll #63 (446s): BGP=Established routes=2
[20:46:28]   Poll #64 (454s): BGP=Established routes=2
[20:46:36]   Poll #65 (462s): BGP=Established routes=2
[20:46:44]   Poll #66 (469s): BGP=Established routes=2
[20:46:52]   Poll #67 (477s): BGP=Established routes=2
[20:47:00]   Poll #68 (485s): BGP=Established routes=2
[20:47:07]   Poll #69 (493s): BGP=Established routes=2
[20:47:15]   Poll #70 (501s): BGP=Established routes=2
[20:47:23]   Poll #71 (509s): BGP=Established routes=2
[20:47:31]   Poll #72 (517s): BGP=Established routes=2
[20:47:39]   Poll #73 (524s): BGP=Established routes=2
[20:47:47]   Poll #74 (532s): BGP=Established routes=2
[20:47:55]   Poll #75 (540s): BGP=Established routes=2
[20:48:03]   Poll #76 (548s): BGP=Established routes=2
[20:48:10]   Poll #77 (556s): BGP=Established routes=2
[20:48:18]   Poll #78 (564s): BGP=Established routes=2
[20:48:26]   Poll #79 (572s): BGP=Established routes=0
[20:48:34]   Poll #80 (580s): BGP=Established routes=12000
[20:48:34] Recovered in 580s
[20:48:37]   Identity OK: YOR_CL_PE-4
[20:49:20]   XRAY CP capture: BGP traffic check
[20:49:28]   XRAY: 2 packets captured -> PASS
[20:49:28] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[20:49:28] === test_07: Warm System Restart ===
[20:50:28] Triggering (1/1): request system restart warm
[20:50:39] System restart: waiting for device to go DOWN first...
[20:50:42]   Still reachable (5s), waiting for shutdown...
[20:51:17]   Device confirmed DOWN after 10s
[20:51:27]   Poll #1 (0s): 100.64.4.98 not ready
[20:51:32]   Poll #2 (15s): 100.64.4.122 not ready
[20:51:40]   Poll #3 (20s): 100.64.4.98 not ready
[20:51:45]   Poll #4 (28s): 100.64.4.122 not ready
[20:51:53]   Poll #5 (33s): 100.64.4.98 not ready
[20:51:58]   Poll #6 (41s): 100.64.4.122 not ready
[20:52:06]   Poll #7 (46s): 100.64.4.98 not ready
[20:52:11]   Poll #8 (54s): 100.64.4.122 not ready
[20:52:19]   Poll #9 (59s): 100.64.4.98 not ready
[20:52:24]   Poll #10 (67s): 100.64.4.122 not ready
[20:52:33]   Poll #11 (72s): 100.64.4.98 not ready
[20:52:38]   Poll #12 (80s): 100.64.4.122 not ready
[20:52:48]   Poll #13 (85s): BGP=Established routes=2
[20:52:56]   Poll #14 (96s): BGP=Established routes=2
[20:53:04]   Poll #15 (103s): BGP=Established routes=2
[20:53:12]   Poll #16 (111s): BGP=Established routes=2
[20:53:20]   Poll #17 (119s): BGP=Established routes=2
[20:53:27]   Poll #18 (127s): BGP=Established routes=2
[20:53:35]   Poll #19 (135s): BGP=Established routes=2
[20:53:43]   Poll #20 (143s): BGP=Established routes=2
[20:53:51]   Poll #21 (151s): BGP=Established routes=2
[20:53:59]   Poll #22 (158s): BGP=Established routes=0
[20:54:07]   Poll #23 (166s): BGP=Established routes=12000
[20:54:07] Recovered in 166s
[20:54:10]   Identity OK: YOR_CL_PE-4
[20:54:51]   XRAY CP capture: BGP traffic check
[20:55:03]   XRAY: 2 packets captured -> PASS
[20:55:03] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)