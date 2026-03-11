[18:16:00] Starting FlowSpec HA tests on PE-4
[18:16:00] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[18:16:00] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1816
[18:16:00] Setting up Spirent: connect + reserve
[18:16:01] Port already reserved (reusing existing session)
[18:16:01] Creating Spirent BGP device
[18:16:02] Starting BGP peer
[18:16:43] Injecting 200 FlowSpec rules
[18:16:44] FlowSpec injection failed: FlowSpec not supported in this STC version: 500 Internal Server Error: STC exception: in create: invalid bgpflowspecconfig attribute "destinationprefix": should be Active, AlarmState, AsNum, AsPath, AsPathIncrement, AsPathIncrementModePerRoute, AsPathIncrementPerRouter, AsPathPerBlockCount, AsPathSegmentType, ClusterIdList, ComponentTypes, CopyBit, Dscp, EnableRedirect, EnableRedirectToIpNextHop, EnableTrafficAction, EnableTrafficMarking, EnableTrafficRate, EncodedBgpSrTlvs, ExtendedCommunity, ExtendedCommunityIncrement, ExtendedCommunityPerBlockCount, Handle, Ipv6ExtendedCommunity, Ipv6ExtendedCommunityIncrement, Ipv6ExtendedCommunityPerBlockCount, IsEditable, LocalActive, LocalPreference, LocalPreferenceIncrement, LocalPreferenceIncrementPerRouter, Med, MedIncrement, MedIncrementPerRouter, Name, NextHop, NextHopPlaceHolder, Origin, RouteCategory, RouteCount, RouteCountPerRouter, RouteTarget, SampleBit, SessionIpVersion, SubAfi, Tags, TerminateBit, or TrafficRate
Use ExaBGP or /BGP for FlowSpec injection.
Traceback (most recent call last):
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1518, in <module>
    main()
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1514, in main
    cmds[args.command](args)
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 747, in cmd_add_routes
    flowspec = stc.create(
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 383, in create
    data = self.createx(object_type, under, attributes, **kwattrs)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 408, in createx
    status, data = self._rest.post_request('objects', None, params)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 231, in post_request
    return self._handle_response(rsp)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 450, in _handle_response
    raise RestHttpError(rsp.status_code, rsp.reason, detail, code)
stcrestclient.resthttp.RestHttpError: 500 Internal Server Error: STC exception: in create: invalid bgpflowspecconfig attribute "destinationprefix": should be Active, AlarmState, AsNum, AsPath, AsPathIncrement, AsPathIncrementModePerRoute, AsPathIncrementPerRouter, AsPathPerBlockCount, AsPathSegmentType, ClusterIdList, ComponentTypes, CopyBit, Dscp, EnableRedirect, EnableRedirectToIpNextHop, EnableTrafficAction, EnableTrafficMarking, EnableTrafficRate, EncodedBgpSrTlvs, ExtendedCommunity, ExtendedCommunityIncrement, ExtendedCommunityPerBlockCount, Handle, Ipv6ExtendedCommunity, Ipv6ExtendedCommunityIncrement, Ipv6ExtendedCommunityPerBlockCount, IsEditable, LocalActive, LocalPreference, LocalPreferenceIncrement, LocalPreferenceIncrementPerRouter, Med, MedIncrement, MedIncrementPerRouter, Name, NextHop, NextHopPlaceHolder, Origin, RouteCategory, RouteCount, RouteCountPerRouter, RouteTarget, SampleBit, SessionIpVersion, SubAfi, Tags, TerminateBit, or TrafficRate

[18:16:44] Falling back to ExaBGP
[18:16:44] Using ExaBGP session: gobgp_test
[18:16:44] ExaBGP FlowSpec batch inject not yet implemented in orchestrator.
[18:16:44] Falling back to pre-existing rules (workaround)
[18:16:44] Checking DUT for existing FlowSpec-VPN rules...
[18:16:49] Using 12000 pre-existing FlowSpec rules (workaround)
[18:16:54] Device mode: cluster (CL-86,)
[18:16:54]   Active NCC: None, Standby NCC: None
[18:16:54]   Standby NCC IP provided: will use for NCC restart tests
[18:16:59] FlowSpec routes on DUT: 12000
[18:17:04] BGP FlowSpec-VPN state: Established
[18:17:04] === test_01: RIB Manager Process Restart ===
[18:18:05] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[18:18:18]   Poll #1: BGP=Established routes=2
[18:18:28]   Poll #2: BGP=Established routes=2
[18:18:38]   Poll #3: BGP=Established routes=2
[18:18:48]   Poll #4: BGP=Established routes=2
[18:19:05]   Poll #5: BGP=Established routes=2
[18:19:15]   Poll #6: BGP=Established routes=2
[18:19:25]   Poll #7: BGP=Established routes=2
[18:19:35]   Poll #8: BGP=Established routes=2
[18:19:45]   Poll #9: BGP=Established routes=2
[18:19:55]   Poll #10: BGP=Established routes=2
[18:20:05]   Poll #11: BGP=Established routes=2
[18:20:15]   Poll #12: BGP=Established routes=2
[18:21:11] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:21:11] === test_02: BGPd Process Restart ===
[18:22:07] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[18:23:20]   Poll #1: BGP=Established routes=2
[18:24:20]   Poll #2: BGP=Established routes=2
[18:27:05] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:27:05] === test_03: wb_agent Process Restart ===
[18:28:06] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[18:28:26]   Poll #1: BGP=Established routes=2
[18:28:37]   Poll #2: BGP=Established routes=2
[18:28:47]   Poll #3: BGP=Established routes=2
[18:28:57]   Poll #4: BGP=Established routes=2
[18:29:07]   Poll #5: BGP=Established routes=2
[18:29:42]   Poll #6: BGP=Established routes=2
[18:29:52]   Poll #7: BGP=Established routes=2
[18:30:02]   Poll #8: BGP=Established routes=2
[18:30:12]   Poll #9: BGP=Established routes=2
[18:31:57] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:31:57] Cooldown 45s after datapath-affecting test...
[18:32:42] === test_04: BGP Container Restart ===
[18:33:22] Triggering (1/1): request system container restart ncc 0 routing-engine
[18:34:03]   Poll #1: BGP=Established routes=2
[18:34:13]   Poll #2: BGP=Established routes=2
[18:34:23]   Poll #3: BGP=Established routes=2
[18:34:33]   Poll #4: BGP=Established routes=2
[18:34:43]   Poll #5: BGP=Established routes=2
[18:34:53]   Poll #6: BGP=Established routes=2
[18:35:03]   Poll #7: BGP=Established routes=2
[18:35:39]   Poll #8: BGP=Established routes=2
[18:35:49]   Poll #9: BGP=Established routes=2
[18:35:59]   Poll #10: BGP=Established routes=2
[18:36:34]   Poll #11: BGP=Established routes=2
[18:39:05] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:39:05] === test_05: NCP Container Restart ===
[18:40:49] Triggering (1/1): request system container restart ncp 0 datapath
[18:41:59]   Poll #1: BGP=Established routes=2
[18:42:10]   Poll #2: BGP=Established routes=2
[18:42:20]   Poll #3: BGP=Established routes=2
[18:42:55]   Poll #4: BGP=Established routes=2
[18:43:05]   Poll #5: BGP=Established routes=2
[18:43:15]   Poll #6: BGP=Established routes=2
[18:43:50]   Poll #7: BGP=Established routes=2
[18:44:00]   Poll #8: BGP=Established routes=2
[18:44:10]   Poll #9: BGP=Established routes=2
[18:44:20]   Poll #10: BGP=Established routes=2
[18:44:56]   Poll #11: BGP=Established routes=2
[18:46:06]   SSH retry 1/3 in 15s (timed out)
[18:46:50]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:47:47]   Snapshot command failed: show flowspec ncp...
[18:48:10]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:48:53]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:49:48]   Snapshot command failed: show flowspec instance vrf ALPHA ipv4...
[18:50:14]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:50:57]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:51:54]   Snapshot command failed: show system detail...
[18:52:18] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)
[18:52:18] Cooldown 45s after datapath-affecting test...
[18:53:03] === test_06: Cold System Restart ===
[18:55:05]   SSH retry 1/3 in 15s (timed out)
[18:55:49]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:57:18]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:57:59]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[18:58:54] Triggering (1/1): request system restart
[18:59:23] TEST ERROR: [Errno None] Unable to connect to port 22 on 100.64.6.82
[18:59:23] === test_07: Warm System Restart ===
[18:59:50]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:00:33]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:01:38] Triggering (1/1): request system restart warm
[19:01:46] Waiting for reconnect (60s)...
[19:03:10]   SSH retry 1/3 in 15s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:03:41]   Poll #1: BGP=Established routes=2
[19:03:51]   Poll #2: BGP=Established routes=2
[19:04:01]   Poll #3: BGP=Established routes=2
[19:04:11]   Poll #4: BGP=Established routes=2
[19:04:21]   Poll #5: BGP=Established routes=2
[19:05:03]   Poll #6: BGP=Established routes=2
[19:05:14]   Poll #7: BGP=Established routes=2
[19:06:14]   Poll #8: BGP=Established routes=2
[19:06:24]   Poll #9: BGP=Established routes=2
[19:07:34]   SSH retry 1/3 in 15s (timed out)
[19:08:26]   SSH retry 2/3 in 30s ([Errno None] Unable to connect to port 22 on 100.64.6.82)
[19:09:12]   Poll #10: BGP=Established routes=2
[19:10:43] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)