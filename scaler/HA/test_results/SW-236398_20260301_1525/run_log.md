[15:25:33] Starting FlowSpec HA tests on PE-4
[15:25:33] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2
[15:25:33] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1525
[15:25:33] Setting up Spirent: connect + reserve
[15:25:38] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[15:25:38] Spirent setup failed. Trying pre-existing rules workaround...
[15:25:38] Checking DUT for existing FlowSpec-VPN rules...
[15:25:43] Using 12000 pre-existing FlowSpec rules (workaround)
[15:25:43] Proceeding with pre-existing FlowSpec rules
[15:25:48] FlowSpec routes on DUT: 12000
[15:25:53] BGP FlowSpec-VPN state: Established
[15:25:53] === test_01: RIB Manager Process Restart ===
[15:26:17] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[15:26:32]   Poll: BGP=Established routes=12000
[15:26:32] Recovered
[15:26:59] Verdict: PASS
[15:26:59] === test_02: BGPd Process Restart ===
[15:27:31] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[15:27:53]   Poll: BGP=Established routes=12000
[15:27:53] Recovered
[15:28:18] Verdict: PASS
[15:28:18] === test_03: wb_agent Process Restart ===
[15:28:40] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[15:28:58]   Poll: BGP=Established routes=12000
[15:28:58] Recovered
[15:29:13] Verdict: PASS
[15:29:13] Cooldown 45s after datapath-affecting test...
[15:29:58] === test_04: BGP Container Restart ===
[15:30:29] Triggering (1/1): request system container restart ncc 0 routing-engine
[15:31:09]   Poll: BGP=Established routes=12000
[15:31:09] Recovered
[15:31:34] Verdict: PASS
[15:31:34] === test_05: NCP Container Restart ===
[15:31:52] Triggering (1/1): request system container restart ncp 0 datapath
[15:32:14]   Poll: BGP=Established routes=12000
[15:32:14] Recovered
[15:32:30] Verdict: PASS
[15:32:30] Cooldown 45s after datapath-affecting test...
[15:33:15] === test_06: Cold System Restart ===
[15:33:42] Triggering (1/1): request system restart
[15:33:47] Waiting for reconnect (60s)...
[15:34:58]   Poll: BGP=Established routes=12000
[15:34:58] Recovered
[15:35:23] Verdict: PASS
[15:35:23] === test_07: Warm System Restart ===
[15:36:15] Triggering (1/1): request system restart warm
[15:36:20] Waiting for reconnect (60s)...
[15:37:38]   Poll: BGP=Established routes=12000
[15:37:38] Recovered
[15:38:10] Verdict: PASS
[15:38:10] === test_08: NCC Switchover ===
[15:38:47] Triggering (1/1): request system ncc switchover
[15:39:17] Waiting for reconnect (60s)...
[15:40:27]   Poll: BGP=Established routes=12000
[15:40:27] Recovered
[15:41:23] Verdict: PASS
[15:41:23] === test_09: NCC Failover by Power Cycle ===
[15:41:23] MANUAL: User must perform physical action
[15:41:23] === test_10: NCE Power Cycle ===
[15:41:23] MANUAL: User must perform physical action
[15:41:23] === test_11: BGP Graceful Restart ===
[15:41:47] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[15:42:02]   Poll: BGP=Established routes=12000
[15:42:02] Recovered
[15:42:30] Verdict: PASS
[15:42:30] === test_12: Clear BGP Neighbors Multiple Times ===
[15:42:55] Triggering (1/10): clear bgp neighbor 10.99.212.1
[15:43:05] Triggering (2/10): clear bgp neighbor 10.99.212.1
[15:43:15] Triggering (3/10): clear bgp neighbor 10.99.212.1
[15:43:25] Triggering (4/10): clear bgp neighbor 10.99.212.1
[15:43:35] Triggering (5/10): clear bgp neighbor 10.99.212.1
[15:43:46] Triggering (6/10): clear bgp neighbor 10.99.212.1
[15:43:56] Triggering (7/10): clear bgp neighbor 10.99.212.1
[15:44:06] Triggering (8/10): clear bgp neighbor 10.99.212.1
[15:44:16] Triggering (9/10): clear bgp neighbor 10.99.212.1
[15:44:26] Triggering (10/10): clear bgp neighbor 10.99.212.1
[15:44:53]   Poll: BGP=Established routes=12000
[15:44:53] Recovered
[15:45:42] Verdict: PASS
[15:45:42] === test_13: NCC Switchover with FlowSpec Admin-Disabled ===
[15:46:06] Triggering (1/1): request system ncc switchover
[15:46:11] Waiting for reconnect (60s)...
[15:47:22]   Poll: BGP=Established routes=12000
[15:47:22] Recovered
[15:48:27] Verdict: PASS
[15:48:27] === test_14: LOFD with FlowSpec Rules ===
[15:48:27] SKIP: LOFD requires special forwarding failure simulation - manual test
[15:48:27] === test_15: Multiple HA Events in Sequence ===
[15:49:28] Triggering (1/4): request system process restart ncc 0 routing-engine routing:rib_manager
[15:49:43] Triggering (2/4): request system process restart ncc 0 routing-engine routing:bgpd
[15:50:23] Triggering (3/4): clear bgp neighbor 10.99.212.1
[15:50:38] Triggering (4/4): request system ncc switchover
[15:50:53] Waiting for reconnect (60s)...
[15:52:04]   Poll: BGP=Established routes=12000
[15:52:04] Recovered
[15:52:29] Verdict: PASS