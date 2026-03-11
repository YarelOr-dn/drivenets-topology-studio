show bgp link-state neighbors received-routes
---------------------------------------------

**Minimum user role:** viewer

To display received routes under link-state neighbors sessions:



**Command syntax: show bgp link-state neighbors [neighbor-address] received-routes** nlri [nlri]

**Command mode:** operational


..
	**Internal Note**

	- use "nlri" to display detail information matching a specific nlri

**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| Parameter         | Description                                                                                                                                                                   | Range                                                                      |
+===================+===============================================================================================================================================================================+============================================================================+
| neighbor-address  | Neighbor address                                                                                                                                                              | A.B.C.D xx:xx::xx:xx                                                       |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| received-routes   | Displays the routes received from a BGP neighbor                                                                                                                              |  \-                                                                        |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| nlri              | Filter the displayed information for a specific Network Layer Reachability Information (NLRI). Each link-state NLRI describes either a node, a link, or a prefix.             | \-                                                                         |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+

**Example**
::

	dnRouter# show bgp link-state neighbors 1.1.1.1 received-routes
	
	dnRouter# show bgp link-state neighbors 1.1.1.1 received-routes nlri NODE { AS:7019 iso-network:0121.2207.5102.00 ISIS_LEVEL2:11 }

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

