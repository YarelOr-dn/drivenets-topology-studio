show bgp flowspec neighbors received-routes
-------------------------------------------

**Minimum user role:** viewer

To display received routes under flowspec neighbors sessions:



**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] flowspec neighbors [neighbor-address] received-routes** nlri [nlri]

**Command mode:** operational



**Note**

-  Use "nlri" to display detailed information matching a specific NLRI.

.. -  nlri - require to use apostrophes when entring the nlri string


**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter         | Description                                                                                                                                                       | Range                       |
+===================+===================================================================================================================================================================+=============================+
| vrf-name          | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family    | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                   |                                                                                                                                                                   | IPv6                        |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| neighbor-address  | Neighbor address                                                                                                                                                  | A.B.C.D                     |
|                   |                                                                                                                                                                   | xx:xx::xx:xx                |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| received-routes   | Displays the routes received from a BGP neighbor                                                                                                                  | \-                          |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| nlri              | Filter the displayed information for a specific Network Layer Reachability Information (NLRI).                                                                    | \-                          |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4 flowspec neighbors 1.1.1.1 received-routes


	dnRouter# show bgp ipv4 flowspec neighbors 1.1.1.1 received-routes nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5"

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 13.0    | Command introduced                 |
+---------+------------------------------------+

