[16:11:12] Starting FlowSpec HA tests on PE-4
[16:11:12] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[16:11:12] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1611
[16:11:12] Setting up Spirent: connect + reserve
[16:12:35] Creating Spirent BGP device
[16:12:36] Starting BGP peer
[16:12:49] ERROR: bgp-peer failed: Starting ARP/ND and device protocols...
Traceback (most recent call last):
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1507, in <module>
    main()
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1503, in main
    cmds[args.command](args)
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 516, in cmd_bgp_peer
    stc.apply()
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 342, in apply
    self._rest.put_request(None, 'apply')
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 247, in put_request
    return self._handle_response(rsp)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 450, in _handle_response
    raise RestHttpError(rsp.status_code, rsp.reason, detail, code)
stcrestclient.resthttp.RestHttpError: 500 Internal Server Error: server error: failed to connect user "dn_spirent" to test session "ha_flowspec_pe4": STC exception: in perform: Unable to connect to Remote Test Session at 127.0.0.1:40016

[16:12:49] Spirent setup failed. Trying pre-existing rules workaround...
[16:12:49] Checking DUT for existing FlowSpec-VPN rules...
[16:12:54] Using 12000 pre-existing FlowSpec rules (workaround)
[16:12:54] Proceeding with pre-existing FlowSpec rules
[16:12:59] Device mode: cluster (CL-86,)
[16:12:59]   Active NCC: None, Standby NCC: None
[16:12:59]   Standby NCC IP provided: will use for NCC restart tests
[16:13:04] FlowSpec routes on DUT: 12000
[16:13:34] BGP FlowSpec-VPN state: Established
[16:13:34] === test_01: RIB Manager Process Restart ===
[16:14:24] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[16:14:39]   Poll: BGP=Established routes=12000
[16:14:39] Recovered
[16:15:32] Verdict: PASS
[16:15:32] === test_02: BGPd Process Restart ===
[16:15:58] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[16:17:03]   Poll: BGP=Established routes=12000
[16:17:03] Recovered
[16:17:54] Verdict: PASS
[16:17:54] === test_03: wb_agent Process Restart ===
[16:18:35] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[16:19:40]   Poll: BGP=Established routes=12000
[16:19:40] Recovered
[16:19:56] Verdict: PASS
[16:19:56] Cooldown 45s after datapath-affecting test...
[16:20:41] === test_04: BGP Container Restart ===
[16:21:14] Triggering (1/1): request system container restart ncc 0 routing-engine
[16:21:54]   Poll: BGP=Established routes=12000
[16:21:54] Recovered
[16:23:10] Verdict: PASS
[16:23:10] === test_05: NCP Container Restart ===
[16:23:25] Triggering (1/1): request system container restart ncp 0 datapath
[16:23:40]   Poll: BGP=Established routes=12000
[16:23:40] Recovered
[16:24:20] Verdict: PASS
[16:24:20] Cooldown 45s after datapath-affecting test...
[16:25:06] === test_06: Cold System Restart ===
[16:25:31] Triggering (1/1): request system restart
[16:25:36] Waiting for reconnect (60s)...
[16:26:46]   Poll: BGP=Established routes=12000
[16:26:46] Recovered
[16:27:37] Verdict: PASS
[16:27:37] === test_07: Warm System Restart ===
[16:28:27] Triggering (1/1): request system restart warm
[16:28:32] Waiting for reconnect (60s)...
[16:29:43]   Poll: BGP=Established routes=12000
[16:29:43] Recovered
[16:30:58] Verdict: PASS
[16:30:58] === test_08: NCC Switchover ===
[16:31:29] Triggering (1/1): request system ncc switchover
[16:31:41] Waiting for reconnect (60s)...
[16:32:55]   Poll: BGP=Established routes=12000
[16:32:55] Recovered
[16:33:25] Verdict: PASS
[16:33:25] === test_09: NCC Failover by Power Cycle ===
[16:33:25] MANUAL: User must perform physical action
[16:33:25] === test_10: NCE Power Cycle ===
[16:33:25] MANUAL: User must perform physical action
[16:33:25] === test_11: BGP Graceful Restart ===
[16:33:56] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[16:34:36]   Poll: BGP=Established routes=12000
[16:34:36] Recovered
[16:34:56] Verdict: PASS
[16:34:56] === test_12: Clear BGP Neighbors Multiple Times ===
[16:35:17] Triggering (1/10): clear bgp neighbor 10.99.212.1
[16:35:52] Triggering (2/10): clear bgp neighbor 10.99.212.1
[16:36:02] Triggering (3/10): clear bgp neighbor 10.99.212.1
[16:37:02] Triggering (4/10): clear bgp neighbor 10.99.212.1
[16:37:12] Triggering (5/10): clear bgp neighbor 10.99.212.1
[16:37:22] Triggering (6/10): clear bgp neighbor 10.99.212.1
[16:37:59] Triggering (7/10): clear bgp neighbor 10.99.212.1
[16:38:09] Triggering (8/10): clear bgp neighbor 10.99.212.1
[16:38:19] Triggering (9/10): clear bgp neighbor 10.99.212.1
[16:38:29] Triggering (10/10): clear bgp neighbor 10.99.212.1
[16:39:14]   Poll: BGP=Established routes=12000
[16:39:14] Recovered
[16:39:45] Verdict: PASS
[16:39:45] === test_13: NCC Switchover with FlowSpec Admin-Disabled ===
[16:40:32] Triggering (1/1): request system ncc switchover
[16:40:37] Waiting for reconnect (60s)...
[16:41:47]   Poll: BGP=Established routes=12000
[16:41:47] Recovered
[16:42:53] Verdict: PASS
[16:42:53] === test_14: LOFD with FlowSpec Rules ===
[16:42:53] SKIP: LOFD requires special forwarding failure simulation - manual test
[16:42:53] === test_15: Multiple HA Events in Sequence ===
[16:43:51] Triggering (1/4): request system process restart ncc 0 routing-engine routing:rib_manager
[16:44:06] Triggering (2/4): request system process restart ncc 0 routing-engine routing:bgpd
[16:44:21] Triggering (3/4): clear bgp neighbor 10.99.212.1
[16:44:36] Triggering (4/4): request system ncc switchover
[16:44:58] Waiting for reconnect (60s)...
[16:46:12]   Poll: BGP=Established routes=12000
[16:46:12] Recovered
[16:46:40] Verdict: PASS