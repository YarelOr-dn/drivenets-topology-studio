show bgp neighbors network-route
--------------------------------

**Minimum user role:** viewer

Advertised-routes - To display the routes advertised to a BGP neighbor:

Received-routes - To display the routes received to a BGP neighbor:

**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] [sub-address-family] neighbors [neighbor-address] {advertised-routes \| received-routes} network-route [ip-prefix]**

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
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                    | unicast                     |
|                    |                                                                                                                                                                   | multicast                   |
|                    |                                                                                                                                                                   | vpn                         |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| neighbor-address   | Neighbor address                                                                                                                                                  | A.B.C.D                     |
|                    |                                                                                                                                                                   | xx:xx::xx:xx                |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| advertised-routes  | Displays the routes advertised to a BGP neighbor                                                                                                                  | A.B.C.D/x                   |
|                    |                                                                                                                                                                   | xx:xx::xx:xx/X              |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| received-routes    | Displays the routes received from a BGP neighbor                                                                                                                  | A.B.C.D/x                   |
|                    |                                                                                                                                                                   | xx:xx::xx:xx/X              |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| ip-prefix          | IP-prefix in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                               | A.B.C.D/x                   |
|                    |                                                                                                                                                                   | xx:xx::xx:xx/x              |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4 unicast neighbors 1.1.1.1 advertised-routes network-route 10.10.0.0/16

	dnRouter# show bgp ipv6 vpn neighbors 1.1.1.1 received-routes route 5:5::5:/32

	dnRouter# show bgp ipv4 unicast neighbors  5.5.5.5 received-routes network-route 6.6.6.6/32
	BGP Adj-in table entry for 6.6.6.6/32
	  Local
	    5.5.5.5
	      Origin incomplete, metric 20, localpref 100, aigp metric 10, remote-label 3
	      LLGR capable, Remaining LLGR stalepath time 16776942 seconds

	dnRouter# show bgp ipv4 unicast neighbors  3.3.3.3 advertised-routes network-route 6.6.6.6/32
	BGP Adj-out table entry for 6.6.6.6/32
	  Local
	    5.5.5.5  interface eth1
	      Origin incomplete, metric 20, localpref 100, aigp metric 10, local-label 3, weight 32768


.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 6.0     | Command introduced                           |
+---------+----------------------------------------------+
| 7.0     | Added AIGP information to output             |
+---------+----------------------------------------------+
| 9.0     | Changed "route" to "network-route" in syntax |
+---------+----------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI        |
+---------+----------------------------------------------+
