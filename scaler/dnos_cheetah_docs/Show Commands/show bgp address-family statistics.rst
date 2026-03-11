show bgp address-family statistics
----------------------------------

**Minimum user role:** viewer

The following command displays the BGP advertisement statistics:

**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] [sub-address-family] statistics**

**Command mode:** operational


.. **Internal Note**

	- use vrf to display information for a non-default vrf

	- for link-state address-family, there is no sub-address-family option

	- for non-default instance vrf support only "unicast" sub-address-family

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                             | Range                       |
+====================+=========================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                    |                                                                                                                                                         | IPv6                        |
|                    |                                                                                                                                                         | Link-state                  |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                     |
|                    | N/A for link-state address-family                                                                                                                       | multicast                   |
|                    |                                                                                                                                                         | vpn                         |
|                    |                                                                                                                                                         | flowspec                    |
|                    |                                                                                                                                                         | rt-constrains               |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp instance vrf A ipv4 unicast statistics


	dnRouter# show bgp ipv6 vpn statistics

	dnRouter# show bgp link-state statistics
	BGP BGP LS Link-state RIB statistics

	Total Advertisements : 13
	Total Prefixes : 13
	Average prefix length : 0.00
	Unaggregateable prefixes : 13
	Maximum aggregateable prefixes: 0
	BGP Aggregate advertisements : 0
	Address space advertised : 0

	Advertisements with paths : 13
	Longest AS-Path (hops) : 0
	Average AS-Path length (hops) : 0.00
	Largest AS-Path (bytes) : 0
	Average AS-Path size (bytes) : 0.00
	Highest public ASN : 0

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------------------------------------+
| Release | Modification                                                     |
+=========+==================================================================+
| 6.0     | Command introduced                                               |
+---------+------------------------------------------------------------------+
| 10.0    | Added link-state address-family                                  |
+---------+------------------------------------------------------------------+
| 16.1    | Added support for flowspec and IPv4 Route Target Constrain SAFIs |
+---------+------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                            |
+---------+------------------------------------------------------------------+
