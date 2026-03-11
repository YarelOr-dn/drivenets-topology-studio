show bgp policy
---------------

**Minimum user role:** viewer

To display routes matching the policy:

**Command syntax: show bgp** {instance vrf [vrf-name]} [address-family] [sub-address-family] **policy [policy-name]**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families

**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                                       | Range                       |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| vrf-name           | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                    |                                                                                                                                                                   | IPv6                        |
|                    |                                                                                                                                                                   | Link-state                  |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                    | unicast                     |
|                    | N/A for link-state address-family                                                                                                                                 | multicast                   |
|                    |                                                                                                                                                                   | vpn                         |
|                    |                                                                                                                                                                   | flowspec                    |
|                    |                                                                                                                                                                   | rt-constrains               |
|                    |                                                                                                                                                                   | l2vpn evpn                  |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| policy             | Displays only the routes matching the policy                                                                                                                      | An existing policy          |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4 policy INET3

	BGP IPv4 Unicast, local router ID is 100.115.115.115
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

		|       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	U*>i|100.12.12.12/32     | 100.12.12.12   |     0|       100|       0|         ?|
	U*>i|100.13.13.13/32     | 100.13.13.13   |     0|       100|       0|         ?|
	U*> |100.15.15.15/32     | 0.0.0.0        |     0|          |   32768|         ?|
	U*>i|100.16.16.16/32     | 100.16.16.16   |     0|       100|       0|         ?|
	U*>i|100.18.18.18/32     | 100.18.18.18   |     0|       100|       0|         ?|
	U*>i|100.30.30.30/32     | 100.30.30.30   |     0|       100|       0|         i|
	U*>i|100.51.51.51/32     | 100.51.51.51   |      |       100|       0|         i|
	U*>i|100.112.112.112/32  | 100.112.112.112|     0|       100|       0|         ?|
	U*>i|100.113.113.113/32  | 100.113.113.113|     0|       100|       0|         ?|
	U*> |100.115.115.115/32  | 0.0.0.0        |     0|          |   32768|         ?|
	U*>i|100.116.116.116/32  | 100.116.116.116|     0|       100|       0|         ?|
	U*>i|100.118.118.118/32  | 100.118.118.118|     0|       100|       0|         ?|
	U*>i|100.130.130.130/32  | 100.30.30.30   |     0|       100|       0|         i|

	Displayed  13 out of 10027 total prefixes

	dnRouter# show bgp policy POL_NAME

	dnRouter# show bgp instance vrf A policy POL_NAME

	dnRouter# show bgp ipv4 unicast policy POL_NAME

	dnRouter# show bgp l2vpn evpn policy comm


	BGP L2vpn EVPN, local router ID is 101.1.1.1
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


	Route Distinguisher: 56:10

	U*>i  type:=1,esi:=00:33:33:33:33:33:33:33:33:32,eth-tag:=0 (AD EVI)
         18:16:20, localpref:100 AS path: 7015 i, from: 101.3.3.3
	U*>i  type:=3,eth-tag:=0,ipv4:=123.254.254.197 (IM)
         18:16:20, localpref:100 AS path: 7015 i, from: 101.3.3.3

	Route Distinguisher: 65000:2113

	U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=2113 (AD EVI)
         03:47:26, localpref:100 i, from: 101.3.3.3

	Route Distinguisher: 65000:2121

	U*>i  type:=1,esi:=00:00:11:12:13:14:15:16:17:18,eth-tag:=2121 (AD EVI)
         03:09:36, localpref: 10 AS path: 1 i, from: 101.3.3.3

.. **Help line:** show bgp ipv4 policy

**Command History**

+---------+-----------------------------------------------------------------------+
| Release | Modification                                                          |
+=========+=======================================================================+
| 6.0     | Command introduced                                                    |
+---------+-----------------------------------------------------------------------+
| 13.0    | Added support for flowspec SAFI                                       |
+---------+-----------------------------------------------------------------------+
| 16.1    | Added support for link-state AFI and IPv4 Route Target Constrain SAFI |
+---------+-----------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                                 |
+---------+-----------------------------------------------------------------------+
