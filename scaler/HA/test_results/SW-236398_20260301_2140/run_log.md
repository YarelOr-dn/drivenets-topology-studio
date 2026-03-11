[21:40:25] Starting FlowSpec HA tests on PE-4
[21:40:25] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[21:40:25] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2140
[21:40:25] Setting up Spirent: connect + reserve
[21:40:28] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[21:40:28] Spirent setup failed. Trying pre-existing rules workaround...
[21:40:28] Checking DUT for existing FlowSpec-VPN rules...
[21:40:29] Using 12000 pre-existing FlowSpec rules (workaround)
[21:40:29] Proceeding with pre-existing FlowSpec rules
[21:40:35] Device mode: cluster (CL-86,)
[21:40:35]   Active NCC: 0, Standby NCC: 1
[21:40:35]   Standby NCC IP provided: will use for NCC restart tests
[21:40:36] Device Lock: System Name = YOR_CL_PE-4
[21:40:37]   NCE IP map refreshed: {'mgmt0': '100.64.6.125', 'mgmt-ncc-0': '100.64.7.2', 'mgmt-ncc-1': '100.64.4.122'}
[21:40:37]   Updated standby NCC IP: 100.64.4.122 (mgmt-ncc-1)
[21:40:39] FlowSpec routes on DUT: 12000
[21:41:06] BGP FlowSpec-VPN state: Established
[21:41:06] === test_09: NCC Failover by Cold Restart (Power Reset) ===
[21:41:15]   Safety: standby NCC-1 is ready
[21:41:16] Device mode: cluster (CL-86,)
[21:41:16]   Active NCC: 0, Standby NCC: 1
[21:41:16]   Standby NCC IP provided: will use for NCC restart tests
[21:41:16] Standby NCC (100.64.4.122) SSH down, using active NCC + multi-IP reconnect
[21:41:44] Triggering (1/1): request system restart ncc 0
[21:42:12] SSH will drop. Initial wait 10s, then multi-IP polling...
[21:42:22]   Poll #1 (0s): 100.64.7.2 not ready
[21:42:31]   Reconnected via 100.64.4.122 (was 100.64.7.2)
[21:42:33]   Poll #2 (5s): BGP=Established routes=0
[21:42:39]   Poll #3 (16s): BGP=Established routes=12000
[21:42:39] Recovered in 16s
[21:42:40]   Identity OK: YOR_CL_PE-4
[21:43:26]   NCC-0 recovered to standby-up in 46s
[21:43:38]   XRAY CP capture: BGP traffic check
[21:44:09]   XRAY: 2 packets captured -> PASS
[21:44:09] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:44:09] === test_14: LOFD Simulation (NCF Admin-Disable) ===
[21:44:22]   Safety: NCF-0 is operational
[21:44:22]   WARNING: Only 1 active NCF. Disabling it will sever ALL fabric connectivity.
[21:44:22]            System will lose NCP-to-NCC communication. This is expected for LOFD test.
[21:45:10] Triggering LOFD: disabling NCF via config mode
[21:45:33]   Config commands: ['configure', 'system', 'ncf 0', 'admin-state disabled', 'commit']
[21:45:38] LOFD: fabric down, waiting 30s to observe impact...
[21:46:08] LOFD: re-enabling NCF now...
[21:46:08] LOFD Recovery: re-enabling NCF-0...
[21:46:08]   Config commands: ['configure', 'system', 'ncf 0', 'admin-state enabled', 'commit']
[21:46:12]   NCF re-enable (primary) committed
[21:48:03]   NCF-0 recovered to up in 96s
[21:48:08]   Poll #1 (0s): BGP=Established routes=12000
[21:48:08] Recovered in 0s
[21:48:51]   XRAY CP capture: BGP traffic check
[21:49:00]   XRAY: 2 packets captured -> PASS
[21:49:00] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:49:00] === test_15: Multiple HA Events in Sequence ===
[21:49:44] Triggering (1/4): request system process restart ncc 0 routing-engine routing:rib_manager
[21:49:51] Triggering (2/4): request system process restart ncc 0 routing-engine routing:bgpd
[21:50:01] Triggering (3/4): clear bgp neighbor 2.2.2.2
[21:50:13] Triggering (4/4): request system ncc switchover
[21:50:21] SSH will drop. Initial wait 10s, then multi-IP polling...
[21:50:34]   NCE IP map refreshed: {'mgmt0': '100.64.4.98', 'mgmt-ncc-0': '100.64.7.2', 'mgmt-ncc-1': '100.64.4.122'}
[21:50:34]   Updated standby NCC IP: 100.64.7.2 (mgmt-ncc-0)
[21:50:34]   Poll #1 (0s): BGP=Established routes=12000
[21:50:34] Recovered in 0s
[21:50:35]   Identity OK: YOR_CL_PE-4
[21:51:20]   XRAY CP capture: BGP traffic check
[21:51:34]   XRAY: 2 packets captured -> PASS
[21:51:34] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)