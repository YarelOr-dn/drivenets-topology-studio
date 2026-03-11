[22:37:36] VLAN from spirent_learning: 219 (profile pe4_vrf_alpha_v219)
[22:37:36] Starting FlowSpec HA tests on PE-4
[22:37:36] VLAN=219 Spirent=49.49.49.1 DUT=49.49.49.4 standby_ip=None
[22:37:36] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2237
[22:37:36] Phase 0: Cleaning zombie sessions before Spirent setup
[22:38:07] Setting up Spirent: connect + reserve (VLAN=219)
[22:38:10] Creating Spirent BGP device: 49.49.49.1 -> 49.49.49.4
[22:38:11] Starting BGP peer
[22:38:48] Injecting 200 FlowSpec rules
[22:38:49] FlowSpec injection failed: FlowSpec not supported in this STC version: 500 Internal Server Error: STC exception: in create: invalid bgpflowspecconfig attribute "destinationprefix": should be Active, AlarmState, AsNum, AsPath, AsPathIncrement, AsPathIncrementModePerRoute, AsPathIncrementPerRouter, AsPathPerBlockCount, AsPathSegmentType, ClusterIdList, ComponentTypes, CopyBit, Dscp, EnableRedirect, EnableRedirectToIpNextHop, EnableTrafficAction, EnableTrafficMarking, EnableTrafficRate, EncodedBgpSrTlvs, ExtendedCommunity, ExtendedCommunityIncrement, ExtendedCommunityPerBlockCount, Handle, Ipv6ExtendedCommunity, Ipv6ExtendedCommunityIncrement, Ipv6ExtendedCommunityPerBlockCount, IsEditable, LocalActive, LocalPreference, LocalPreferenceIncrement, LocalPreferenceIncrementPerRouter, Med, MedIncrement, MedIncrementPerRouter, Name, NextHop, NextHopPlaceHolder, Origin, RouteCategory, RouteCount, RouteCountPerRouter, RouteTarget, SampleBit, SessionIpVersion, SubAfi, Tags, TerminateBit, or TrafficRate
Use ExaBGP or /BGP for FlowSpec injection.
Traceback (most recent call last):
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1783, in <module>
    main()
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1779, in main
    cmds[args.command](args)
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 922, in cmd_add_routes
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

[22:38:49] Falling back to ExaBGP
[22:38:49] Using ExaBGP session: gobgp_test
[22:38:49] ExaBGP FlowSpec batch inject not yet implemented in orchestrator.
[22:38:49] Falling back to pre-existing rules (workaround)
[22:38:49] Checking DUT for existing FlowSpec-VPN rules...
[22:38:50] Using 12000 pre-existing FlowSpec rules (workaround)
[22:38:51] Device mode: cluster (CL-86,)
[22:38:51]   Active NCC: 1, Standby NCC: 0
[22:38:51]   Hint: Use --standby-ip <standby_mgmt_ip> to connect to standby NCC during active NCC restart (avoids SSH loss)
[22:38:52] Device Lock: System Name = YOR_CL_PE-4
[22:38:54]   NCE IP map refreshed: {'mgmt0': '100.64.4.98', 'mgmt-ncc-0': '100.64.7.2', 'mgmt-ncc-1': '100.64.4.122'}
[22:38:54]   Updated standby NCC IP: 100.64.7.2 (mgmt-ncc-0)
[22:38:54]   Updated standby NCC IP: 100.64.4.122 (mgmt-ncc-1)
[22:38:55] FlowSpec routes on DUT: 12000
[22:38:57] BGP FlowSpec-VPN state: Established
[22:38:57] === test_01: RIB Manager Process Restart ===
[22:39:37]   SSH retry 1/3 in 5s (timed out)
[22:39:57] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[22:39:58]   Poll #1 (0s): BGP=Established routes=12000
[22:39:58] Recovered in 1.2s
[22:40:43]   SSH retry 1/3 in 5s (timed out)
[22:40:52] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=SKIP)