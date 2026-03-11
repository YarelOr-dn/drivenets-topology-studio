[20:56:29] Starting FlowSpec HA tests on PE-4
[20:56:29] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2 standby_ip=None
[20:56:29] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_2056
[20:56:29] Setting up Spirent: connect + reserve
[20:56:32] ERROR: Spirent connect failed: Traceback (most recent call last):
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 121, in new_session
    status, data = self._rest.post_request('sessions', None,
[20:56:32] Spirent setup failed. Trying pre-existing rules workaround...
[20:56:32] Checking DUT for existing FlowSpec-VPN rules...
[20:56:36] ERROR: Only 0 rules found after 4s. Need >= 10. Inject via /BGP first.
[20:56:36] ERROR: Setup failed (Spirent + pre-existing). Exiting.