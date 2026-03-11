show bgp dampened-paths
-----------------------

**Minimum user role:** viewer

The following command displays paths that are suppressed due to dampening:



**Command syntax: show bgp** instance vrf [vrf-name] [address-family] [sub-address-family] **dampened-path**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                             | Range                       |
+====================+=========================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                    |                                                                                                                                                         | IPv6                        |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                     |
|                    |                                                                                                                                                         | vpn                         |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp dampened-path
	
	dnRouter# show bgp instance vrf A dampened-path
	
	dnRouter# show bgp ipv4 dampened-path
	
	dnRouter# show bgp ipv6 vpn dampened-path
	
	
	

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 6.0     | Command introduced                 |
+---------+------------------------------------+

