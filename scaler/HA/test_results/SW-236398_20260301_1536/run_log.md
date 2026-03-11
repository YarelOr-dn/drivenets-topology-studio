[15:36:20] Starting FlowSpec HA tests on PE-4
[15:36:20] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2
[15:36:20] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1536
[15:36:20] Setting up Spirent: connect + reserve
[15:36:24] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[15:36:24] Spirent setup failed. Trying pre-existing rules workaround...
[15:36:24] Checking DUT for existing FlowSpec-VPN rules...
[15:36:29] Using 12000 pre-existing FlowSpec rules (workaround)
[15:36:29] Proceeding with pre-existing FlowSpec rules
[15:36:34] Device mode: cluster (CL-86,)
[15:36:34]   Active NCC: None, Standby NCC: None
[15:36:34]   Hint: Use --standby-ip <standby_mgmt_ip> to connect to standby NCC during active NCC restart (avoids SSH loss)
[15:36:39] FlowSpec routes on DUT: 12000
[15:36:44] BGP FlowSpec-VPN state: Established
[15:36:44] === test_08: NCC Switchover ===
[15:37:22] Triggering (1/1): request system ncc switchover
[15:37:22] Waiting for reconnect (60s)...
[15:39:04]   Poll: BGP=Established routes=12000
[15:39:04] Recovered
[15:39:40] Verdict: PASS