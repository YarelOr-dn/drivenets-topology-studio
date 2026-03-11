show bgp neighbors nlri
-----------------------

**Minimum user role:** viewer

Advertised-routes - To display the routes advertised to a BGP neighbor:

Received-routes - To display the routes received to a BGP neighbor:

**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] [sub-address-family] neighbors [neighbor-address] {advertised-routes \| received-routes} nlri [nlri]**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                                       | Range                       |
+====================+===================================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                    |                                                                                                                                                                   | IPv6                        |
|                    |                                                                                                                                                                   | Link-state                  |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                    | flowspec                    |
|                    | N/A for link-state address-family                                                                                                                                 | rt-constrains               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| neighbor-address   | Neighbor address                                                                                                                                                  | A.B.C.D                     |
|                    |                                                                                                                                                                   | xx:xx::xx:xx                |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| advertised-routes  | Displays the routes advertised to a BGP neighbor                                                                                                                  |                             |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| received-routes    | Displays the routes received from a BGP neighbor                                                                                                                  |                             |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| nlri               | Filter the displayed information for a specific Network Layer Reachability Information (NLRI). Each link-state NLRI describes either a node, a link, or a prefix. | \-                          |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4 flowspec neighbors 1.1.1.1 advertised-routes nlri

	dnRouter# show bgp ipv6 flowspec neighbors 1.1.1.1 received-routes nlri

	dnRouter# show bgp ipv4 rt-constrains neighbors 5.5.5.5 received-routes nlri

	dnRouter# show bgp link-state neighbors 1.1.1.1 advertised-routes nlri



.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.0    | Command introduced                                 |
+---------+----------------------------------------------------+
| 13.0    | Added support for flowspec SAFI                    |
+---------+----------------------------------------------------+
| 16.1    | Added support for IPv4 Route Target Constrain SAFI |
+---------+----------------------------------------------------+
