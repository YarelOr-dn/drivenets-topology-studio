[15:44:26] Starting FlowSpec HA tests on PE-4
[15:44:26] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[15:44:26] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1544
[15:44:26] Setting up Spirent: connect + reserve
[15:44:28] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[15:44:28] Spirent setup failed. Trying pre-existing rules workaround...
[15:44:28] Checking DUT for existing FlowSpec-VPN rules...
[15:44:33] Using 12000 pre-existing FlowSpec rules (workaround)
[15:44:33] Proceeding with pre-existing FlowSpec rules
[15:45:03] Device mode: cluster (CL-86,)
[15:45:03]   Active NCC: None, Standby NCC: None
[15:45:03]   Standby NCC IP provided: will use for NCC restart tests
[15:45:16] FlowSpec routes on DUT: 12000
[15:45:22] BGP FlowSpec-VPN state: Established
[15:45:22] === test_01: RIB Manager Process Restart ===
[15:46:21] Triggering (1/1): request system process restart ncc 0 routing-engine routing:rib_manager
[15:47:01]   Poll: BGP=Established routes=12000
[15:47:01] Recovered
[15:47:21] Verdict: PASS
[15:47:21] === test_02: BGPd Process Restart ===
[15:48:16] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[15:48:31]   Poll: BGP=Established routes=12000
[15:48:31] Recovered
[15:50:11] Verdict: PASS
[15:50:11] === test_03: wb_agent Process Restart ===
[15:50:54] Triggering (1/1): request system process restart ncp 0 datapath wb_agent
[15:51:17]   Poll: BGP=Established routes=12000
[15:51:17] Recovered
[15:51:32] Verdict: PASS
[15:51:32] Cooldown 45s after datapath-affecting test...
[15:52:17] === test_04: BGP Container Restart ===
[15:53:10] Triggering (1/1): request system container restart ncc 0 routing-engine
[15:53:25]   Poll: BGP=Established routes=12000
[15:53:25] Recovered
[15:53:51] Verdict: PASS
[15:53:51] === test_05: NCP Container Restart ===
[15:54:19] Triggering (1/1): request system container restart ncp 0 datapath
[15:54:34]   Poll: BGP=Established routes=12000
[15:54:34] Recovered
[15:54:49] Verdict: PASS
[15:54:49] Cooldown 45s after datapath-affecting test...
[15:55:34] === test_06: Cold System Restart ===
[15:56:04] Triggering (1/1): request system restart
[15:56:09] Waiting for reconnect (60s)...
[15:57:19]   Poll: BGP=Established routes=12000
[15:57:19] Recovered
[15:57:44] Verdict: PASS
[15:57:44] === test_07: Warm System Restart ===
[15:58:37] Triggering (1/1): request system restart warm
[15:58:42] Waiting for reconnect (60s)...
[15:59:52]   Poll: BGP=Established routes=12000
[15:59:52] Recovered
[16:00:17] Verdict: PASS
[16:00:17] === test_08: NCC Switchover ===
[16:01:15] Triggering (1/1): request system ncc switchover
[16:01:20] Waiting for reconnect (60s)...
[16:02:31]   Poll: BGP=Established routes=12000
[16:02:31] Recovered
[16:03:01] Verdict: PASS
[16:03:01] === test_09: NCC Failover by Power Cycle ===
[16:03:01] MANUAL: User must perform physical action
[16:03:01] === test_10: NCE Power Cycle ===
[16:03:01] MANUAL: User must perform physical action
[16:03:01] === test_11: BGP Graceful Restart ===
[16:03:49] Triggering (1/1): request system process restart ncc 0 routing-engine routing:bgpd
[16:04:04]   Poll: BGP=Established routes=12000
[16:04:04] Recovered
[16:04:55] Verdict: PASS
[16:04:55] === test_12: Clear BGP Neighbors Multiple Times ===
[16:05:19] Triggering (1/10): clear bgp neighbor 10.99.212.1
[16:05:32] Triggering (2/10): clear bgp neighbor 10.99.212.1
[16:05:42] Triggering (3/10): clear bgp neighbor 10.99.212.1
[16:05:53] Triggering (4/10): clear bgp neighbor 10.99.212.1
[16:06:03] Triggering (5/10): clear bgp neighbor 10.99.212.1
[16:06:13] Triggering (6/10): clear bgp neighbor 10.99.212.1
[16:06:23] Triggering (7/10): clear bgp neighbor 10.99.212.1
[16:06:33] Triggering (8/10): clear bgp neighbor 10.99.212.1
[16:06:43] Triggering (9/10): clear bgp neighbor 10.99.212.1
[16:06:53] Triggering (10/10): clear bgp neighbor 10.99.212.1
[16:07:14]   Poll: BGP=Established routes=12000
[16:07:14] Recovered
[16:07:34] Verdict: PASS
[16:07:34] === test_13: NCC Switchover with FlowSpec Admin-Disabled ===
[16:07:50] Triggering (1/1): request system ncc switchover
[16:08:02] Waiting for reconnect (60s)...
[16:09:12]   Poll: BGP=Established routes=12000
[16:09:12] Recovered
[16:09:27] Verdict: PASS
[16:09:27] === test_14: LOFD with FlowSpec Rules ===
[16:09:27] SKIP: LOFD requires special forwarding failure simulation - manual test
[16:09:27] === test_15: Multiple HA Events in Sequence ===
[16:09:53] Triggering (1/4): request system process restart ncc 0 routing-engine routing:rib_manager
[16:10:33] Triggering (2/4): request system process restart ncc 0 routing-engine routing:bgpd
[16:10:48] Triggering (3/4): clear bgp neighbor 10.99.212.1
[16:11:03] Triggering (4/4): request system ncc switchover
[16:11:18] Waiting for reconnect (60s)...
[16:12:28]   Poll: BGP=Established routes=12000
[16:12:28] Recovered
[16:12:54] Verdict: PASS