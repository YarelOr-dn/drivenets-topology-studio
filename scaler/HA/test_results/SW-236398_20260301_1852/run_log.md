[18:52:39] Starting FlowSpec HA tests on PE-4
[18:52:39] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=100.64.4.122
[18:52:39] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1852
[18:52:39] Setting up Spirent: connect + reserve
[18:52:42] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[18:52:42] Spirent setup failed. Trying pre-existing rules workaround...
[18:52:42] Checking DUT for existing FlowSpec-VPN rules...
[18:52:45] ERROR: Only 2 rules found. Need >= 10 for HA test. Inject via /BGP first.
[18:52:45] ERROR: Setup failed (Spirent + pre-existing). Exiting.