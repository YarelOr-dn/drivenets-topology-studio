show bgp large-community-list
-----------------------------

**Minimum user role:** viewer

To display routes matching the large commlunities allowed in large-community-list:


**Command syntax: show bgp** {instance vrf [vrf-name] [address-family]} [sub-address-family] **large-community-list [community-list-name]**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families

**Parameter table**

+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter           | Description                                                                                                                                            | Range                       |
+=====================+========================================================================================================================================================+=============================+
| vrf-name            | Display routing information for a non-default VRF                                                                                                      | 1..255 characters           |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family      | Display routing information for a specific address-family (AFI)                                                                                        | IPv4                        |
|                     |                                                                                                                                                        | IPv6                        |
|                     |                                                                                                                                                        | Link-state                  |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family  | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                         | unicast                     |
|                     | N/A for link-state address-family                                                                                                                      | multicast                   |
|                     |                                                                                                                                                        | vpn                         |
|                     |                                                                                                                                                        | flowspec                    |
|                     |                                                                                                                                                        | rt-constrains               |
|                     |                                                                                                                                                        | l2vpn evpn                  |       
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| community-list-name | Displays routes matching the community-list                                                                                                            |  \-                         |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp large-community-list LARGE_COMM_LIST

	BGP IPv4 Unicast, local router ID is 100.112.112.112
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path     |
	-------------------------------------------------------------------------------------
	*>i|100.100.100.100/32  | 100.116.116.116|     0|       100|       0|           ?|
	*>i|100.100.100.101/32  | 100.115.115.115|     0|       101|       0|           ?|
	* i|                    | 100.113.113.113|     0|       100|       0|           ?|
	*ai|                    | 100.118.118.118|     0|       100|       0|           ?|
	*>i|100.113.113.113/32  | 100.113.113.113|     0|       100|       0|           ?|
	*>i|100.115.115.115/32  | 100.115.115.115|     0|       101|       0|           ?|
	*>i|100.116.116.116/32  | 100.116.116.116|     0|       100|       0|           ?|
	*>i|100.118.118.118/32  | 100.118.118.118|     0|       100|       0|           ?|
	*>i|100.119.119.119/32  | 100.115.115.115|     0|       101|       0|4200000002 ?|
	*>i|100.150.150.150/32  | 100.115.115.115|      |       101|       0|4200000002 ?|

	dnRouter# show bgp ipv6 community-list LARGE_COMM_LIST

    dnRouter# show bgp l2vpn evpn large-community-list test

	BGP L2vpn EVPN, local router ID is 101.3.3.3
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


	Route Distinguisher: 101.1.1.1:0

	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=4294967295 (AD ESI)
         00:03:09, localpref:100 i, from: 101.1.1.1
	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:23,eth-tag:=4294967295 (AD ESI)
         00:03:09, localpref:100 i, from: 101.1.1.1
	U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:21,ipv4:=101.1.1.1 (ES)
         00:03:09, localpref:100 i, from: 101.1.1.1
	U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:23,ipv4:=101.1.1.1 (ES)
         00:03:09, localpref:100 i, from: 101.1.1.1


	Displayed  4 out of 56 total prefixes


.. **Help line:** show bgp route matching large community list


**Command History**

+---------+------------------------------------------------------------------------------------------+
| Release | Modification                                                                             |
+=========+==========================================================================================+
| 15.1    | Command introduced                                                                       |
+---------+------------------------------------------------------------------------------------------+
| 16.1    | Added support for link-state AFI and both flowspec and IPv4 Route Target Constrain SAFIs |
+---------+------------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                                                    |
+---------+------------------------------------------------------------------------------------------+
