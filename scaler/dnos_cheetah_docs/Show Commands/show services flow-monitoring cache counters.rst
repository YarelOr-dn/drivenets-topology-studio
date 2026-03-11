show services flow-monitoring cache counters
--------------------------------------------

**Minimum user role:** viewer

To display counters per NCP flow-monitoring cache:



**Command syntax: show services flow-monitoring cache counters**  ncp [ncp-id]

**Command mode:** operational



.. 
	**Internal Note**

	- "show services flow-monitoring cache counters" without parameter, shows cache counters for all NCPs.

**Parameter table**

+-----------+--------------------------------------------------------+--------+
| Parameter | Description                                            | Range  |
+===========+========================================================+========+
| ncp-id    | Filters the displayed information to the specified NCP | 0..255 |
+-----------+--------------------------------------------------------+--------+

The following information is displayed per NCP:

+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter                                | Description                                                                                                                                    |
+==========================================+================================================================================================================================================+
| Total cache size                         | The current size of the flow cache table                                                                                                       |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Number of flows in cache                 | The number of flows in the flow cache table                                                                                                    |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Number of sampled IPv4/IPv6/MPLS packets | The number of IPv4/IPv6/MPLS packets that were sampled by the data plane and handled by the flow-tracker                                       |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Total number of sampled packets          | The total number of packets that were sampled by the data plane and handled by the flow-tracker (IPv4+IPv6+MPLS)                               |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Rate of sampled packets                  | The current rate of sampled packets by the data plane                                                                                          |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Total number of dropped sampled packets  | The packets that were sampled by the data plane but dropped by the flow-tracker because they exceeded the flow rate                            |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Cache hits                               | The number of sampled packets that match existing flow records in the cache                                                                    |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Cache misses (new flows)                 | The number of sampled packets that don't match existing flow records in the cache. As a result, new flow-records are added to the cache.       |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Cache overflows                          | The number of flow-records that were removed from the cache to make room for new flow-records because the flow-cache table was full populated. |
+------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show services flow-monitoring cache counters ncp 5
	Total cache size: 1,000,000 flows
	Number of flows in cache: 120
	Number of sampled IPv4 packets: 45
	Number of sampled IPv6 packets: 21
	Number of sampled MPLS packets: 2000
	Total number of sampled packets: 2066
	Rate of sampled packets: 100 pps
	Total number of dropped sampled packets: 120
	Cache hits: 220
	Cache misses (new flows): 66
	Cache overflows: 45000
	
	
	dnRouter# show services flow-monitoring cache counters
	
	NCP-1
	
	Total cache size: 1,000,000 flows
	Number of flows in cache: 120
	Number of sampled IPv4 packets: 45
	Number of sampled IPv6 packets: 21
	Number of sampled MPLS packets: 2000
	Total number of sampled packets: 2066
	Rate of sampled packets: 100 pps
	Total number of dropped sampled packets: 120
	Cache hits: 220
	Cache misses (new flows): 66
	Cache overflows: 45000
	
	
	NCP-5
	
	Total cache size: 1,000,000 flows
	Number of flows in cache: 120
	Number of sampled IPv4 packets: 45
	Number of sampled IPv6 packets: 21
	Number of sampled MPLS packets: 2000
	Total number of sampled packets: 2066
	Rate of sampled packets: 100 pps
	Total number of dropped sampled packets: 120
	Cache hits: 220
	Cache misses: 66
	Cache overflows: 45000
	
	

.. **Help line:** show counters per NCP flow-monitoring cache.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+


