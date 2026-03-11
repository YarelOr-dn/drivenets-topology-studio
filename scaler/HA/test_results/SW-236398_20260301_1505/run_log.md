[15:05:45] Starting FlowSpec HA tests on PE-4
[15:05:45] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2
[15:05:45] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1505
[15:05:45] Setting up Spirent: connect + reserve
[15:05:47] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[15:05:47] Spirent setup failed. Trying pre-existing rules workaround...
[15:05:47] Checking DUT for existing FlowSpec-VPN rules...
[15:05:48] ERROR: Only 0 rules found. Need >= 10 for HA test. Inject via /BGP first.
[15:05:48] ERROR: Setup failed (Spirent + pre-existing). Exiting.