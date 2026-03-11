show bgp link-state neighbors advertised-routes
-----------------------------------------------

**Minimum user role:** viewer

To display advertised routes under link-state neighbors sessions:



**Command syntax: show bgp link-state neighbors [neighbor-address] advertised-routes** nlri [nlri]

**Command mode:** operational


..
	**Internal Note**

	- use "nlri" to display detail information matching a specific nlri

**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| Parameter         | Description                                                                                                                                                                   | Range                                                            |
+===================+===============================================================================================================================================================================+==================================================================+
| neighbor-address  | Neighbor address                                                                                                                                                              | A.B.C.D xx:xx::xx:xx                                             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| advertised-routes | Displays the routes advertised to a BGP neighbor                                                                                                                              |  \-                                                              |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| nlri              | Filter the displayed information for a specific Network Layer Reachability Information (NLRI). Each link-state NLRI describes either a node, a link, or a prefix.             | \-                                                               |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+

**Example**
::

	dnRouter# show bgp link-state neighbors 1.1.1.1 advertised-routes
	
	dnRouter# show bgp link-state neighbors 1.1.1.1 advertised-routes nlri NODE { AS:7019 iso-network:0121.2207.5102.00 ISIS_LEVEL2:11 }
	BGP BGP LS Link-state routing table entry for NODE { AS:7019 iso-network:0121.2207.5102.00 ISIS_LEVEL2:11 }
	Paths: (1 available, best #1)
	  Not advertised to any peer
	     Level: 2
	     Local AS: 7019
	     Hostname: RR2-LU
	     IPv4 Router-ids: 102.102.102.102
	     Iso-network: 0121.2207.5102.00
	     Area(s): 49.0001
	     Flags: None
	     Last update: 02:25:32

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

