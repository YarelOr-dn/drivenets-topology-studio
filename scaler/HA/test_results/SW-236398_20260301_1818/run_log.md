[18:18:05] Starting FlowSpec HA tests on PE-4
[18:18:05] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[18:18:05] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1818
[18:18:05] Setting up Spirent: connect + reserve
[18:18:06] Port already reserved (reusing existing session)
[18:18:06] Creating Spirent BGP device
[18:18:06] Starting BGP peer
[18:18:07] ERROR: bgp-peer failed: Traceback (most recent call last):
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1518, in <module>
    main()
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1514, in main
    cmds[args.command](args)
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 500, in cmd_bgp_peer
    bgp = stc.create(
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 383, in create
    data = self.createx(object_type, under, attributes, **kwattrs)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 408, in createx
    status, data = self._rest.post_request('objects', None, params)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 231, in post_request
    return self._handle_response(rsp)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 450, in _handle_response
    raise RestHttpError(rsp.status_code, rsp.reason, detail, code)
stcrestclient.resthttp.RestHttpError: 500 Internal Server Error: STC exception: in create: Lost network connection to the server; please reconnect again.

[18:18:07] Spirent setup failed. Trying pre-existing rules workaround...
[18:18:07] Checking DUT for existing FlowSpec-VPN rules...
[18:18:12] Using 12000 pre-existing FlowSpec rules (workaround)
[18:18:12] Proceeding with pre-existing FlowSpec rules
[18:18:18] Device mode: cluster (CL-86,)
[18:18:18]   Active NCC: 0, Standby NCC: 1
[18:18:18]   Standby NCC IP provided: will use for NCC restart tests
[18:18:23] FlowSpec routes on DUT: 2
[18:18:23] WARNING: Expected ~12000 rules, got 2
[18:18:28] BGP FlowSpec-VPN state: Established
[18:18:28] === test_01: RIB Manager Process Restart ===
[18:18:28] Using standby NCC (100.64.4.122) for NCC restart test
[18:18:48]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:19:23]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:20:13] TEST ERROR: [Errno None] Unable to connect to port 22 on 100.64.4.122
[18:20:13] === test_02: BGPd Process Restart ===
[18:20:13] Using standby NCC (100.64.4.122) for NCC restart test
[18:20:33]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:21:08]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:21:58] TEST ERROR: [Errno None] Unable to connect to port 22 on 100.64.4.122
[18:21:58] === test_03: wb_agent Process Restart ===
[18:22:38] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[18:23:16]   Poll #1: BGP=Established routes=2
[18:23:26]   Poll #2: BGP=Established routes=2
[18:23:40]   Poll #3: BGP=Established routes=2
[18:23:50]   Poll #4: BGP=Established routes=2
[18:24:00]   Poll #5: BGP=Established routes=2
[18:24:10]   Poll #6: BGP=Established routes=2
[18:24:20]   Poll #7: BGP=Established routes=2
[18:24:30]   Poll #8: BGP=Established routes=2
[18:24:40]   Poll #9: BGP=Established routes=2
[18:24:50]   Poll #10: BGP=Established routes=2
[18:25:00]   Poll #11: BGP=Established routes=2
[18:25:10]   Poll #12: BGP=Established routes=2
[18:26:30] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:26:30] Cooldown 45s after datapath-affecting test...
[18:27:15] === test_04: BGP Container Restart ===
[18:27:15] Using standby NCC (100.64.4.122) for NCC restart test
[18:27:35]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:28:11]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:29:01]   Snapshot command failed: show bgp ipv4 flowspec-vpn summary...
[18:29:21]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:29:56]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:30:46]   Snapshot command failed: show bgp ipv4 flowspec-vpn routes...
[18:31:06]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:31:41]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:32:31]   Snapshot command failed: show flowspec ncp...
[18:32:51]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:33:26]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.4.122)
[18:34:16] Triggering (1/1): request system container restart ncc 0 routing-engine
[18:34:29]   Poll #1: BGP=Established routes=2
[18:34:39]   Poll #2: BGP=Established routes=2
[18:34:49]   Poll #3: BGP=Established routes=2
[18:34:59]   Poll #4: BGP=Established routes=2
[18:35:34]   Poll #5: BGP=Established routes=2
[18:36:09]   Poll #6: BGP=Established routes=2
[18:36:44]   Poll #7: BGP=Established routes=2
[18:36:56]   Poll #8: BGP=Established routes=2
[18:37:09]   Poll #9: BGP=Established routes=2
[18:37:44]   Poll #10: BGP=Established routes=2
[18:39:02]   SSH retry 1/3 in 15s (timed out)
[18:40:40] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:40:40] === test_05: NCP Container Restart ===
[18:41:09] Triggering (1/1): request system container restart ncp 0 datapath
[18:41:50]   Poll #1: BGP=Established routes=2
[18:42:50]   Poll #2: BGP=Established routes=2
[18:43:00]   Poll #3: BGP=Established routes=2
[18:43:10]   Poll #4: BGP=Established routes=2
[18:43:20]   Poll #5: BGP=Established routes=2
[18:43:55]   Poll #6: BGP=Established routes=2
[18:44:05]   Poll #7: BGP=Established routes=2
[18:44:15]   Poll #8: BGP=Established routes=2
[18:46:29]   SSH retry 1/3 in 15s (timed out)
[18:47:11]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:48:07] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:48:07] Cooldown 45s after datapath-affecting test...
[18:48:52] === test_06: Cold System Restart ===
[18:49:19]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:50:01]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:50:57]   Snapshot command failed: show config protocols bgp...
[18:51:21]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:52:04]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:53:54] Triggering (1/1): request system restart
[18:54:02] Waiting for reconnect (60s)...
[18:55:43]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:56:26]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:57:25]   Reconnecting... ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:57:59]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:58:43]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:59:39]   Reconnecting... ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:00:11]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:00:54]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:01:29]   Poll #3: BGP=Established routes=2
[19:02:40]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:03:23]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:04:18] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[19:04:18] === test_07: Warm System Restart ===
[19:06:34] Triggering (1/1): request system restart warm
[19:07:06] Waiting for reconnect (60s)...
[19:08:36]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:09:10]   Poll #1: BGP=Established routes=2
[19:09:21]   Poll #2: BGP=Established routes=2
[19:09:31]   Poll #3: BGP=Established routes=2
[19:09:41]   Poll #4: BGP=Established routes=2
[19:09:51]   Poll #5: BGP=Established routes=2
[19:10:51]   Poll #6: BGP=Established routes=2
[19:11:51]   Poll #7: BGP=Established routes=2
[19:12:01]   Poll #8: BGP=Established routes=2
[19:13:01]   Poll #9: BGP=Established routes=2
[19:14:07] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)