show bgp
---------

**Minimum user role:** viewer

To display BGP routing table information:



**Command syntax: show bgp** instance vrf [vrf-name] [address-family] [sub-address-family]
**Command syntax: show bgp** instance evpn [evpn-name]
**Command syntax: show bgp** instance evpn-vpws [evpn-vpws-name]

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display routing information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- use address-family, sub-address-family for specific afi-safi routes

	- Path inside ( ) - represents Confederation Peer Autonomous Systems that route passed through

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
|      Parameter     | Description                                                                                                                    |       Range       | Default |
+====================+================================================================================================================================+===================+=========+
| vrf-name           | Display routing information for a non-default VRF                                                                              | 1..255 characters | \-      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                | IPv4              | \-      |
|                    |                                                                                                                                | IPv6              |         |
|                    |                                                                                                                                | Link-state        |         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF. | unicast           | \-      |
|                    | N/A for link-state address-family                                                                                              | multicast         |         |
|                    |                                                                                                                                | vpn               |         |
|                    |                                                                                                                                | flowspec          |         |
|                    |                                                                                                                                | rt-constrains     |         |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| evpn-name          | Display routing information for a evpn instance                                                                                | 1..255 characters | \-      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| evpn-vpws-name     | Display routing information for a evpn-vpws instance                                                                           | 1..255 characters | \-      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# # show bgp

	BGP IPv4 Unicast, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

        |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
    ------------------------------------------------------------------------------------
    V*> |2.0.0.0/8           | 10.0.1.3       |     0|          |       0|       2 i|
    V*> |3.0.0.0/8           | 10.0.2.3       |     0|          |       0|   23541 i|
    N*> |4.0.0.0/8           | 10.0.3.3       |     0|          |       0|       2 i|

	Displayed  1 out of 2 total prefixes
	No BGP IPv4 Multicast prefixes displayed, 0 exist

	BGP IPv4 Vpn, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	Route Distinguisher: 100.14.14.14:1601

    	|       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	U*>i|16.14.100.0/32      | 100.16.16.16   |      |       100|       0|7018 1461 i|
	U*>i|16.14.100.1/32      | 100.16.16.16   |      |       100|       0|7018 1461 i|
	U*>i|16.14.100.2/32      | 100.16.16.16   |      |       100|       0|7018 1461 i|
	U*>i|16.14.100.3/32      | 100.16.16.16   |      |       100|       0|7018 1461 i|
	U*>i|16.14.100.4/32      | 100.16.16.16   |      |       100|       0|7018 1461 i|

	Displayed  5 out of 5 total prefixes
	No BGP IPv4 Flowspec prefixes displayed, 0 exist

	BGP IPv4 Route Target Constrains, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network            |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------------
	*i |0:0:0                     | 10.0.3.3       |     0|        50|       0|       2 i|
	*i |65000:0:0/96              | 10.0.1.1       |     0|        50|       0|       2 i|
	*>i|                          | 10.0.2.2       |     0|        50|       0|       2 i|
	*> |1:1:100/96                | 10.0.2.2       |     0|          |       0|  235417 i|
	*> |1:200:200/96              | 10.0.2.2       |     0|          |       0|       2 i|
	*> |12200:12200:1040181101/96 | 0.0.0.0        |     0|          |       0|       2 i|

	Displayed  5 out of 5 total prefixes

	BGP IPv6 Unicast, local router ID is 100.115.115.115
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |                   Network                  |                Next hop                |Metric|  LocPref | Weight |   Path   |
	------------------------------------------------------------------------------------------------------------------------------------
	U*>i|1212:1212::1/128                            | 1212:1212::1                           |     0|       100|       0|         ?|
	U*>i|1212:1212:1212:1212::1/128                  | 1212:1212::1                           |     0|       100|       0|         ?|
	U*>i|1313:1313::1/128                            | 1313:1313::1                           |     0|       100|       0|         ?|
	U*>i|1313:1313:1313:1313::1/128                  | 1313:1313::1                           |     0|       100|       0|         ?|
	U*> |1414:1414::1/128                            | 2001:14:15::                           |     0|          |       0|    7018 ?|
	U*> |1414:1414:1414:1414::1/128                  | 2001:14:15::                           |     0|          |       0|    7018 ?|
	U*> |1515:1515::1/128                            | ::                                     |     0|          |   32768|         ?|
	U*> |1515:1515:1515:1515::1/128                  | ::                                     |     0|          |   32768|         ?|

	Displayed  8 out of 8 total prefixes
	No BGP IPv6 Vpn prefixes displayed, 0 exist
	No BGP IPv6 Flowspec prefixes displayed, 0 exist
	No BGP Link-state prefixes displayed, 0 exist


	dnRouter# show bgp ipv4 unicast

	BGP IPv4 Unicast, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	------------------------------------------------------------------------------------
	V*> |2.0.0.0/8           | 10.0.1.3       |     0|          |       0|       2 i|
	V*> |2.0.1.0/8           | 10.0.2.3       |     0|          |       0|  235417 i|
	V*> |2.0.2.0/8           | 10.0.3.3       |     0|          |       0|       2 i|

	Displayed  1 out of 2 total prefixes


	dnRouter# show bgp ipv4 flowspec

	BGP IPv4 Flowspec, local router ID is 9.9.9.3
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified
	*>  DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
             00:19:32,     AS path: 1 i, from: 192.168.1.2

	    |                   Network                  |                Next hop                |Metric|  LocPref | Weight |   Path   |
	--------------------------------------------------------------------------------------------------------------------------------------
	I*  |2001:1:3:11::/127                           | 2001:100::2                            |      |          |       0|4210010000 ?|
	I*  |                                            | 2001:1:2:16::                          |      |          |       0|4210010000 ?|
	N*ai|                                            | 2001:101::21                           |     0|       100|       0|4210010000 ?|
	V*> |                                            | 2001:100::3                            |     0|          |    1000|4210010000 ?|
	I* i|2001:100::2/128                             | 2001:101::21                           |     0|       100|       0|4210010000 ?|
	V*> |                                            | 2001:100::3                            |      |          |    1000|4210010000 ?|
	I*  |                                            | 2001:100::2                            |     0|          |       0|4210010000 ?|
	N*a |                                            | 2001:1:2:16::                          |     0|          |       0|4210010000 ?|
	...


	dnRouter# show bgp ipv6 unicast

	BGP IPv6 Unicasts, local router ID is 101.0.0.16
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |                   Network                  |                Next hop                |Metric|  LocPref | Weight |   Path   |
	------------------------------------------------------------------------------------------------------------------------------------
	I*  |2001:1:3:11::/127                           | 2001:100::2                            |      |          |       0|4210010000 ?|
	I*  |                                            | 2001:1:2:16::                          |      |          |       0|4210010000 ?|
	N*ai|                                            | 2001:101::21                           |     0|       100|       0|4210010000 ?|
	V*> |                                            | 2001:100::3                            |     0|          |    1000|4210010000 ?|
	I* i|2001:100::2/128                             | 2001:101::21                           |     0|       100|       0|4210010000 ?|
	V*> |                                            | 2001:100::3                            |      |          |    1000|4210010000 ?|
	I*  |                                            | 2001:100::2                            |     0|          |       0|4210010000 ?|
	N*a |                                            | 2001:1:2:16::                          |     0|          |       0|4210010000 ?|
	I*  |2001:100::3/128                             | 2001:100::2                            |      |          |       0|4210010000 ?|
	I*  |                                            | 2001:1:2:16::                          |      |          |       0|4210010000 ?|
	V*ai|                                            | 2001:101::21                           |     0|       100|       0|4210010000 ?|
	V*> |                                            | 2001:100::3                            |     0|          |    1000|4210010000 ?|
	V*> |2001:101::16/128                            | ::                                     |     0|          |   32768|           ?|
	V*>i|2001:101::21/128                            | 2001:101::21                           |     0|       100|       0|           ?|

	Displayed  5 out of 14 total prefixes


	dnRouter# show bgp ipv4 rt-constrains

	BGP IPv4 Route Target Constrains, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network            |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------------
	*i |0:0:0                     | 10.0.3.3       |     0|        50|       0|       2 i|
	*i |65000:0:0/96              | 10.0.1.1       |     0|        50|       0|       2 i|
	*>i|                          | 10.0.2.2       |     0|        50|       0|       2 i|
	*> |1:1:100/96                | 10.0.2.2       |     0|          |       0|  235417 i|
	*> |1:200:200/96              | 10.0.2.2       |     0|          |       0|       2 i|
	*> |12200:12200:1040181101/96 | 0.0.0.0        |     0|          |       0|       2 i|

	Displayed  5 out of 12 total prefixes


	dnRouter# show bgp ipv4 multicast

	BGP IPv4 Multicast, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	------------------------------------------------------------------------------------
	U*> |10.100.100.0/24     | 10.1.1.1       |     0|          |       0|       2 i|
	U*> |210.0.0.0/32        | 205.0.0.1      |     0|          |       0|  235417 i|

	Displayed  2 out of 2 total prefixes

	dnRouter# show bgp instance evpn EVPN-SH-CFM3001


	BGP L2vpn EVI, local router ID is 101.4.4.4
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	U*>i  type:=2,eth-tag:=0,mac-address:=00:10:94:00:00:10  (MAC)
         00:36:43, localpref:100 i, from: 101.3.3.3
	U*>i  type:=2,eth-tag:=0,mac-address:=48:40:76:ff:00:01  (MAC)
         00:36:43, localpref:100 i, from: 101.3.3.3
	U*>i  type:=3,eth-tag:=0,ipv4:=101.3.3.3 (IM)
         00:36:43, localpref:100 i, from: 101.3.3.3
	U*>   type:=3,eth-tag:=0,ipv4:=101.4.4.4 (IM)
         00:45:06,     i, from: Local
	U*>i  type:=3,eth-tag:=0,ipv4:=123.254.254.197 (IM)
         00:36:43, localpref:100 AS path: 7015 i, from: 101.3.3.3

	Displayed  5 out of 5 total prefixes

	FM_NCP3(20-Dec-2023-20:13:44)# show bgp instance evpn-vpws EVPN-VPWS-SH-CFM1001


	BGP L2vpn EVI, local router ID is 101.4.4.4
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	U*=i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=1001 (AD EVI)
         00:35:46, localpref:100 i, from: 101.3.3.3
	U*>
         00:36:06,     i, from: Local

	Displayed  1 out of 2 total prefixes

.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 6.0     | Command introduced                                         |
+---------+------------------------------------------------------------+
| 11.6    | Added BGP confederation show command output                |
+---------+------------------------------------------------------------+
| 13.0    | Added support for FlowSpec in the sub-address family       |
+---------+------------------------------------------------------------+
| 15.0    | Added support for the display of Route Reflector in output |
+---------+------------------------------------------------------------+
| 15.1    | Added support for the display of RPKI validation codes     |
+---------+------------------------------------------------------------+
| 16.0    | Added support for IPv4 Route Target Constrain SAFI         |
+---------+------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                      |
+---------+------------------------------------------------------------+
