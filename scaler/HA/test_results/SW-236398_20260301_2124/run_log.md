[21:24:07] Starting FlowSpec HA tests on PE-4
[21:24:07] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.7.2
[21:24:07] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2124
[21:24:07] Setting up Spirent: connect + reserve
[21:24:11] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[21:24:11] Spirent setup failed. Trying pre-existing rules workaround...
[21:24:11] Checking DUT for existing FlowSpec-VPN rules...
[21:24:12] Using 12000 pre-existing FlowSpec rules (workaround)
[21:24:12] Proceeding with pre-existing FlowSpec rules
[21:24:16] Device mode: cluster (CL-86,)
[21:24:16]   Active NCC: 1, Standby NCC: 0
[21:24:16]   Standby NCC IP provided: will use for NCC restart tests
[21:24:17] Device Lock: System Name = YOR_CL_PE-4
[21:24:19]   NCE IP map refreshed: {'mgmt0': '100.64.6.125', 'mgmt-ncc-0': '100.64.7.2', 'mgmt-ncc-1': '100.64.4.122'}
[21:24:19]   Updated standby NCC IP: 100.64.7.2 (mgmt-ncc-0)
[21:24:20] FlowSpec routes on DUT: 12000
[21:24:21] BGP FlowSpec-VPN state: Established
[21:24:21] === test_09: NCC Failover by Cold Restart (Power Reset) ===
[21:24:35]   Safety: standby NCC-0 is ready
[21:24:50] Device mode: cluster (CL-86,)
[21:24:50]   Active NCC: 1, Standby NCC: 0
[21:24:50]   Standby NCC IP provided: will use for NCC restart tests
[21:24:50] Using standby NCC (100.64.7.2) for NCC restart test
[21:25:00]   SSH retry 1/3 in 5s ([Errno None] Unable to connect to port 22 on 100.64.7.2)
[21:25:15]   SSH retry 2/3 in 10s ([Errno None] Unable to connect to port 22 on 100.64.7.2)
[21:25:35] TEST ERROR: [Errno None] Unable to connect to port 22 on 100.64.7.2
[21:25:35] === test_12: Clear BGP Neighbors Multiple Times ===
[21:26:14] Triggering (1/10): clear bgp neighbor 2.2.2.2
[21:26:20] Triggering (2/10): clear bgp neighbor 2.2.2.2
[21:26:43] Triggering (3/10): clear bgp neighbor 2.2.2.2
[21:26:49] Triggering (4/10): clear bgp neighbor 2.2.2.2
[21:26:55] Triggering (5/10): clear bgp neighbor 2.2.2.2
[21:27:02] Triggering (6/10): clear bgp neighbor 2.2.2.2
[21:27:08] Triggering (7/10): clear bgp neighbor 2.2.2.2
[21:27:14] Triggering (8/10): clear bgp neighbor 2.2.2.2
[21:27:21] Triggering (9/10): clear bgp neighbor 2.2.2.2
[21:27:27] Triggering (10/10): clear bgp neighbor 2.2.2.2
[21:27:35]   Poll #1 (0s): BGP=Established routes=12000
[21:27:35] Recovered in 0s
[21:28:10]   XRAY CP capture: BGP traffic check
[21:28:18]   XRAY: 2 packets captured -> PASS
[21:28:18] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:28:18] === test_13: NCC Switchover with FlowSpec Admin-Disabled ===
[21:28:22] Device mode: cluster (CL-86,)
[21:28:22]   Active NCC: 1, Standby NCC: 0
[21:28:22]   Standby NCC IP provided: will use for NCC restart tests
[21:28:53] Triggering (1/1): request system ncc switchover
[21:29:01] SSH will drop. Initial wait 10s, then multi-IP polling...
[21:29:12]   Poll #1 (0s): 100.64.4.122 not ready
[21:29:20]   Reconnected via 100.64.7.2 (was 100.64.4.122)
[21:29:21]   Poll #2 (5s): BGP=Established routes=0
[21:29:28]   Poll #3 (14s): BGP=Established routes=12000
[21:29:28] Recovered in 14s
[21:29:29]   Identity OK: YOR_CL_PE-4
[21:29:38]   XRAY CP capture: BGP traffic check
[21:29:39]   XRAY: 2 packets captured -> PASS
[21:29:39] Verdict: PASS (CP=PASS DP=PASS Spirent=N/A XRAY=PASS)
[21:29:39] === test_14: LOFD Simulation (NCF Admin-Disable) ===
[21:29:42]   Safety: NCF-0 is operational
[21:29:42]   WARNING: Only 1 active NCF. Disabling it will sever ALL fabric connectivity.
[21:29:42]            System will lose NCP-to-NCC communication. This is expected for LOFD test.
[21:29:55] Triggering LOFD: disabling NCF via config mode
[21:29:57]   Config commands: ['configure', 'system', 'ncf 0', 'admin-state disabled', 'commit']
[21:30:02] LOFD: fabric down, waiting 30s to observe impact...
[21:30:32] LOFD: re-enabling NCF now...
[21:30:32] LOFD Recovery: re-enabling NCF...
[21:30:34]   Recovery primary exception: No operational NCF found in show system
[21:30:34]   Trying fallback recovery (no admin-state)...
[21:30:35]   CRITICAL: Fallback recovery also failed: No operational NCF found in show system
[21:30:35]   MANUAL ACTION REQUIRED: Run 'configure → system → ncf 0 → admin-state enabled → commit' on device!
[21:30:35] CRITICAL: NCF recovery failed! Manual intervention needed.
[21:30:35] === test_15: Multiple HA Events in Sequence ===
[21:31:20] Triggering (1/4): request system process restart ncc 0 routing-engine routing:rib_manager
[21:31:27] Triggering (2/4): request system process restart ncc 0 routing-engine routing:bgpd
[21:31:42] Triggering (3/4): clear bgp neighbor 2.2.2.2
[21:32:00] Triggering (4/4): request system ncc switchover
[21:32:05] SSH will drop. Initial wait 10s, then multi-IP polling...
[21:32:18]   NCE IP map refreshed: {'mgmt0': '100.64.6.125', 'mgmt-ncc-0': '100.64.7.2', 'mgmt-ncc-1': '100.64.4.122'}
[21:32:18]   Updated standby NCC IP: 100.64.4.122 (mgmt-ncc-1)
[21:32:18]   Poll #1 (0s): BGP=Established routes=2
[21:32:25]   Poll #2 (8s): BGP=Established routes=2
[21:32:31]   Poll #3 (14s): BGP=Established routes=2
[21:32:38]   Poll #4 (20s): BGP=Established routes=2
[21:32:44]   Poll #5 (27s): BGP=Established routes=2
[21:32:50]   Poll #6 (33s): BGP=Established routes=2
[21:32:57]   Poll #7 (40s): BGP=Established routes=2
[21:33:03]   Poll #8 (46s): BGP=Established routes=2
[21:33:10]   Poll #9 (52s): BGP=Established routes=2
[21:33:17]   Poll #10 (59s): BGP=Established routes=2
[21:33:24]   Poll #11 (66s): BGP=Established routes=2
[21:33:30]   Poll #12 (73s): BGP=Established routes=2
[21:33:37]   Poll #13 (79s): BGP=Established routes=2
[21:33:43]   Poll #14 (86s): BGP=Established routes=2
[21:34:25] Verdict: FAIL (CP=FAIL DP=PASS Spirent=N/A XRAY=SKIP)