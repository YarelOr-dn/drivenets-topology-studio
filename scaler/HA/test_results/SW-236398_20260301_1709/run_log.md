[17:09:26] Starting FlowSpec HA tests on PE-4
[17:09:26] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=None
[17:09:26] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1709
[17:09:26] Setting up Spirent: connect + reserve
[17:09:26] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[17:09:26] Spirent setup failed. Trying pre-existing rules workaround...
[17:09:26] Checking DUT for existing FlowSpec-VPN rules...
[17:09:32] Using 12000 pre-existing FlowSpec rules (workaround)
[17:09:32] Proceeding with pre-existing FlowSpec rules
[17:09:37] Device mode: cluster (CL-86,)
[17:09:37]   Active NCC: None, Standby NCC: None
[17:09:37]   Hint: Use --standby-ip <standby_mgmt_ip> to connect to standby NCC during active NCC restart (avoids SSH loss)
[17:09:42] FlowSpec routes on DUT: 12000
[17:09:47] BGP FlowSpec-VPN state: Established
[17:09:47] === test_09: NCC Failover by Cold Restart (Power Reset) ===
[17:09:52] SAFETY ABORT: No standby NCC detected
[17:09:52] === test_10: NCP Force Restart (IPMI Power Cycle) ===
[17:10:02]   Safety: NCP-6 is operational
[17:10:52] Triggering (1/1): request system restart ncp 6 force
[17:11:03]   Poll: BGP=Established routes=12000
[17:11:03] Recovered
[17:11:13]   NCP-6 recovered to up in 5s
[17:11:58] Verdict: PASS
[17:11:58] === test_14: LOFD Simulation (NCF Admin-Disable) ===
[17:12:08]   Safety: NCF-0 is operational
[17:12:08]   WARNING: Only 1 active NCF. Disabling it will sever ALL fabric connectivity.
[17:12:08]            System will lose NCP-to-NCC communication. This is expected for LOFD test.
[17:12:33] Triggering LOFD: disabling NCF via config mode
[17:12:33] LOFD: fabric down, waiting 30s to observe impact...
[17:12:33] LOFD: re-enabling NCF now...
[17:12:33] LOFD Recovery: re-enabling NCF...
[17:12:38]   Config commands: ['configure', 'system', 'ncf 0', 'admin-state enabled', 'commit']
[17:12:38]   NCF re-enable committed successfully
[17:13:14]   Poll: BGP=Established routes=12000
[17:13:14] Recovered
[17:13:39] Verdict: PASS