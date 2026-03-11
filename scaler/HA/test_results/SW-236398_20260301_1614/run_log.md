[16:14:35] Starting FlowSpec HA tests on PE-4
[16:14:35] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[16:14:35] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1614
[16:14:35] Setting up Spirent: connect + reserve
[16:14:35] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[16:14:35] Spirent setup failed. Trying pre-existing rules workaround...
[16:14:35] Checking DUT for existing FlowSpec-VPN rules...
[16:14:40] Using 12000 pre-existing FlowSpec rules (workaround)
[16:14:40] Proceeding with pre-existing FlowSpec rules
[16:14:45] Device mode: cluster (CL-86,)
[16:14:45]   Active NCC: None, Standby NCC: None
[16:14:45]   Standby NCC IP provided: will use for NCC restart tests
[16:14:50] FlowSpec routes on DUT: 12000
[16:14:55] BGP FlowSpec-VPN state: Established
[16:14:55] === test_01: RIB Manager Process Restart ===
[16:16:38] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[16:16:54]   Poll: BGP=Established routes=12000
[16:16:54] Recovered
[16:18:04] Verdict: PASS
[16:18:04] === test_02: BGPd Process Restart ===
[16:18:56] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[16:19:11]   Poll: BGP=Established routes=12000
[16:19:11] Recovered
[16:20:51] Verdict: PASS
[16:20:51] === test_03: wb_agent Process Restart ===
[16:21:57] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[16:22:15]   Poll: BGP=Established routes=12000
[16:22:15] Recovered
[16:22:55] Verdict: PASS
[16:22:55] Cooldown 45s after datapath-affecting test...
[16:23:40] === test_04: BGP Container Restart ===
[16:24:31] Triggering (1/1): request system container restart ncc 0 routing-engine
[16:25:11]   Poll: BGP=Established routes=12000
[16:25:11] Recovered
[16:26:26] Verdict: PASS
[16:26:26] === test_05: NCP Container Restart ===
[16:26:42] Triggering (1/1): request system container restart ncp 0 datapath
[16:27:47]   Poll: BGP=Established routes=12000
[16:27:47] Recovered
[16:28:52] Verdict: PASS
[16:28:52] Cooldown 45s after datapath-affecting test...
[16:29:38] === test_06: Cold System Restart ===
[16:30:03] Triggering (1/1): request system restart
[16:30:40] Waiting for reconnect (60s)...
[16:31:54]   Poll: BGP=Established routes=12000
[16:31:54] Recovered
[16:32:20] Verdict: PASS
[16:32:20] === test_07: Warm System Restart ===
[16:33:47]   SSH retry 1/3 in 15s (timed out)
[16:34:16] Triggering (1/1): request system restart warm
[16:34:21] Waiting for reconnect (60s)...
[16:35:56]   Poll: BGP=Established routes=12000
[16:35:56] Recovered
[16:36:22] Verdict: PASS
[16:36:22] === test_08: NCC Switchover ===
[16:37:18] Triggering (1/1): request system ncc switchover
[16:37:23] Waiting for reconnect (60s)...
[16:38:33]   Poll: BGP=Established routes=12000
[16:38:33] Recovered
[16:39:39] Verdict: PASS
[16:39:39] === test_09: NCC Failover by Power Cycle ===
[16:39:39] MANUAL: User must perform physical action
[16:39:39] === test_10: NCE Power Cycle ===
[16:39:39] MANUAL: User must perform physical action
[16:39:39] === test_11: BGP Graceful Restart ===
[16:40:35] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[16:40:57]   Poll: BGP=Established routes=12000
[16:40:57] Recovered
[16:41:35] Verdict: PASS
[16:41:35] === test_12: Clear BGP Neighbors Multiple Times ===
[16:41:59] Triggering (1/10): clear bgp neighbor 10.99.212.1
[16:42:12] Triggering (2/10): clear bgp neighbor 10.99.212.1
[16:42:47] Triggering (3/10): clear bgp neighbor 10.99.212.1
[16:42:57] Triggering (4/10): clear bgp neighbor 10.99.212.1
[16:43:07] Triggering (5/10): clear bgp neighbor 10.99.212.1
[16:43:17] Triggering (6/10): clear bgp neighbor 10.99.212.1
[16:43:52] Triggering (7/10): clear bgp neighbor 10.99.212.1
[16:44:02] Triggering (8/10): clear bgp neighbor 10.99.212.1
[16:44:12] Triggering (9/10): clear bgp neighbor 10.99.212.1
[16:44:22] Triggering (10/10): clear bgp neighbor 10.99.212.1
[16:45:08]   Poll: BGP=Established routes=12000
[16:45:08] Recovered
[16:45:35] Verdict: PASS
[16:45:35] === test_13: NCC Switchover with FlowSpec Admin-Disabled ===
[16:46:23] Triggering (1/1): request system ncc switchover
[16:46:31] Waiting for reconnect (60s)...
[16:47:41]   Poll: BGP=Established routes=12000
[16:47:41] Recovered
[16:47:56] Verdict: PASS
[16:47:56] === test_14: LOFD with FlowSpec Rules ===
[16:47:56] SKIP: LOFD requires special forwarding failure simulation - manual test
[16:47:56] === test_15: Multiple HA Events in Sequence ===
[16:48:22] Triggering (1/4): request system process restart ncc 0 routing-engine routing:rib_manager
[16:49:02] Triggering (2/4): request system process restart ncc 0 routing-engine routing:bgpd
[16:49:17] Triggering (3/4): clear bgp neighbor 10.99.212.1
[16:49:32] Triggering (4/4): request system ncc switchover
[16:49:47] Waiting for reconnect (60s)...
[16:50:57]   Poll: BGP=Established routes=12000
[16:50:57] Recovered
[16:51:23] Verdict: PASS