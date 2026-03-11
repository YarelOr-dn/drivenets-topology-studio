show bgp neighbors
------------------

**Minimum user role:** viewer

The following command displays detailed information on BGP neighbor connections:

**Command syntax: show bgp** {instance vrf [vrf-name]} [address-family] [sub-address-family] **neighbors** {[neighbor-address] {advertised-routes \| received-routes \| routes \| dampened-routes \| flap-statistics \| prefix-counts \| received-orf}}

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- advertised-routes - Display the routes advertised to a BGP neighbor

	- received-routes - Display the routes received to a BGP neighbor

	- routes - Display routes learned from neighbor

	- dampened-routes - Display the dampened routes received from neighbor

	- flap-statistics - Display flap statistics of the routes learned from neighbor

	- prefix-count - Display detailed prefix count information

	- received-orf - Display received ORF prefix-lists from ORF capable neighbor (supported only for "unicast" sub-address-family)

	- advertised-routes, received-routes, routes, dampened-routes, received-orf \| flap-statistics \| prefix-counts - can only be set with a specific neighbor address

	- for BGP NSR capable sessions, BGP NSR last recovery status will present:

	-  recoved - last BGP NSR s/o has been done successfully

	-  not recoved - last BGP NSR s/o has been failed, fallback to BGP GR will be done if GR is enabled

	-  N/A - no BGP NSR s/o has happened yet

**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
|      Parameter     |                                                                                  Description                                                                                  |                               Range                              |
+====================+===============================================================================================================================================================================+==================================================================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                                             | 1..255 characters                                                |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                                               | IPv4 IPv6 Link-State                                             |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF. N/A for link-state address-family              | unicast multicast vpn flowspec rt-constrains 'l2vpn evpn'        |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| neighbor-address   | Neighbor address                                                                                                                                                              | A.B.C.D                                                          |
|                    |                                                                                                                                                                               | xx:xx::xx:xx                                                     |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| advertised-routes  | Displays the routes advertised to a BGP neighbor                                                                                                                              | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| received-routes    | Displays the routes received from a BGP neighbor                                                                                                                              | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| routes             | Displays routes learned from the neighbor                                                                                                                                     | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| dampened-routes    | Displays the dampened routes received from the neighbor                                                                                                                       | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| flap-statistics    | Displays flap statistics of the routes learned from the neighbor                                                                                                              | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| prefix-counts      | Displays detailed prefix count information                                                                                                                                    | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| received-orf       | Display received ORF prefix-lists from an ORF capable neighbor (supports only the "unicast" sub-address-family)                                                               | \-                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+


Displayed NSR-related information includes:

+-----------------------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter                   | Description                                                                                                                    | Range                       |
+=============================+================================================================================================================================+=============================+
| BGP NSR capability          | Shows if the neighbor is NSR capable                                                                                           | Capable                     |
|                             |                                                                                                                                | Non-capable                 |
+-----------------------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| BGP NSR capability reason   | Shows the reason for NSR                                                                                                       | Add-path-Tx configured      |
|                             |                                                                                                                                | RT-constrains AF configured |
|                             |                                                                                                                                | BGP-LS AF configured        |
+-----------------------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| BGP NSR last recovery state | Shows the last recovery state for BGP NSR capable sessions:                                                                    | Recovered                   |
|                             |                                                                                                                                | Not-recovered               |
|                             | Recovered - the last BGP NSR s/o was successful                                                                                | N/A                         |
|                             | Not recovered - the last BGP NSR s/o has failed, fallback to BGP graceful restart will be done if graceful-restart is enabled. |                             |
|                             | N/A - BGP NSR s/o has not happened yet.                                                                                        |                             |
+-----------------------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+


**Example**
::

	dnRouter# show bgp neighbors

	BGP neighbor is 9.9.9.3, remote AS 1, local AS 1, internal link
	  BGP version 4, remote router ID 9.9.9.3
	  BGP state = Established, up for 00:02:54
	  Last read 00:00:54, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: inactive, Reason: peer support GR
	  NSR last recovery state: N/A, Reason: N/A
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    AddPath:
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Unicast: advertised and received (currently active)
		Address family IPv4 Vpn: advertised and received
		Address family Route Target Constrains: advertised and received
	    Graceful Restart Capabilty: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
	  Graceful restart informations:
	    End-of-RIB send: IPv4 Unicast
	    End-of-RIB received: IPv4 Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          0
	    Notifications:          0          0
	    Updates:                2          1
	    Keepalives:             4          3
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                  7          4
	  Minimum time between advertisement runs is 5 seconds (next due in 2 seconds)
	  Update source is lo1

	 For address family: IPv4 Unicast
	  0 prefixes accepted
	  1 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 9.9.9.2, Local port: 179
	Foreign host: 9.9.9.3, Foreign port: 35935
	Nexthop: 9.9.9.2
	Nexthop global: ::ffff:9.9.9.2
	Nexthop local: fe80::c472:40ff:fe92:ce7
	BGP connection: non shared network
	Read thread: on  Write thread: off

	BGP neighbor is 9.9.9.6, remote AS 1, local AS 1, internal link
	  BGP version 4, remote router ID 9.9.9.6
	  BGP state = Established, up for 00:02:48
	  Last read 00:00:48, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: inactive, Reason: peer support GR
	  NSR last recovery state: N/A, Reason: N/A
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    AddPath:
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Unicast: advertised and received (currently active)
	    Graceful Restart Capabilty: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
	  Graceful restart informations:
	    End-of-RIB send: IPv4 Unicast
	    End-of-RIB received: IPv4 Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          0
	    Notifications:          0          0
	    Updates:                2          1
	    Keepalives:             4          3
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                  7          4
	  Minimum time between advertisement runs is 5 seconds (next due in 3 seconds)
	  Update source is lo1

	 For address family: IPv4 Unicast
	  0 prefixes accepted
	  1 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 9.9.9.2, Local port: 179
	Foreign host: 9.9.9.6, Foreign port: 45665
	Nexthop: 9.9.9.2
	Nexthop global: ::ffff:9.9.9.2
	Nexthop local: fe80::c472:40ff:fe92:ce7
	BGP connection: non shared network
	Read thread: on  Write thread: off

	BGP neighbor is 9.9.9.7, remote AS 1, local AS 1, internal link
	  BGP version 4, remote router ID 9.9.9.7
	  BGP state = Established, up for 00:02:57
	  Last read 00:00:57, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: inactive, Reason: peer support GR
	  NSR last recovery state: N/A, Reason: N/A
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    AddPath:
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Unicast: advertised and received (currently active)
	    Graceful Restart Capabilty: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
	  Graceful restart informations:
	    End-of-RIB send: IPv4 Unicast
	    End-of-RIB received: IPv4 Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          0
	    Notifications:          0          0
	    Updates:                2          1
	    Keepalives:             4          3
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                  7          4
	  Minimum time between advertisement runs is 5 seconds (next due in 4 seconds)
	  Update source is lo1

	 For address family: IPv4 Unicast
	  0 prefixes accepted
	  1 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 9.9.9.2, Local port: 179
	Foreign host: 9.9.9.7, Foreign port: 44663
	Nexthop: 9.9.9.2
	Nexthop global: ::ffff:9.9.9.2
	Nexthop local: fe80::c472:40ff:fe92:ce7
	BGP connection: non shared network
	Read thread: on  Write thread: off

	dnRouter# show bgp neighbors 192.168.1.2 routes

	BGP IPv4 Unicast, local router ID is 9.9.9.3
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	*> |1.2.3.4/32          | 192.168.1.2    |     0|          |       0|       1 i|

	Displayed  1 out of 1 total prefixes

	BGP IPv4 Flowspec, local router ID is 9.9.9.3
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	*>  DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
	         00:21:16,     AS path: 1 i, from: 192.168.1.2

	Displayed  1 total prefixes

	BGP IPv6 Flowspec, local router ID is 9.9.9.3
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	*>  DstPrefix:=aaaa::11:11:0:0/96,SrcPrefix:=bbbb::11:22:33:44/128,DstPort:<9&>6|=12,SrcPort:=50|=30,TrafficClass:=6
	         00:21:16,     AS path: 1 i, from: 192.168.1.2

	Displayed  1 total prefixes


	dnRouter# show bgp instance vrf A neighbors

	dnRouter# show bgp instance vrf A ipv4 neighbors

	dnRouter# show bgp instance vrf A ipv6 unicast neighbors

	dnRouter# show bgp instance vrf A ipv4 unicast neighbors 1.1.1.1

	dnRouter# show bgp instance vrf A ipv4 unicast neighbors 1.1.1.1 received-routes

	dnRouter# show bgp instance vrf A ipv4 unicast neighbors 1.1.1.1 dampened-routes

	dnRouter# show bgp neighbors 1.1.1.1 flap-statistics

	dnRouter# show bgp ipv4 unicast neighbors 1.1.1.1 prefix-count

	dnRouter# show bgp neighbors 5.5.5.5

	BGP neighbor is 5.5.5.5, remote AS 5, local AS 1, internal link
	  BGP version 4, remote router ID 5.5.5.5
	  BGP state = Established, up for 01:55:00
	  Last read 00:00:00, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: active, Reason: N/A
	  NSR last recovery state: recovered, Reason: N/A
	  NSR: Recovered, Capable
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Labeled-Unicast: advertised and received (currently active)
	    Graceful Restart Capability: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
        Long Lived Graceful Restart Capabilty: advertised and received
        Address families by peer:
            IPv4 Unicast: Remote restart time is  600 seconds (preserved)
            IPv4 VPN: Remote restart time is  600 seconds (preserved)
            IPv6 Unicast: Remote restart time is  600 seconds (preserved)
            IPv6 VPN: Remote restart time is  600 seconds (preserved)
	  Graceful restart information:
	    End-of-RIB send: IPv4 Labeled-Unicast
	    End-of-RIB received: IPv4 Labeled-Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          1
	    Notifications:          0          0
	    Updates:               10         39
	    Keepalives:           117        116
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                128        156
	  Minimum time between advertisement runs is 0 seconds (next due in 0 seconds)
	  Update source is 3.3.3.3

	For address family: IPv4 Unicast
	  MPLS Labeled-Unicast capability is enabled
      Long Lived Graceful restart configuration:
          Address families by peer:
          IPv4 Unicast is enabled with published restart time 600.
          IPv4 Vpn is enabled with published restart time 600.
          IPv6 Unicast is enabled with published restart time 600.
          IPv6 Vpn is enabled with published restart time 600.
	  AIGP is enabled
	  as-loop-check is enabled
	  Inbound path policy configured
	  Route map for incoming advertisements is *SET_MED_177
	  20 prefixes accepted
	  2 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 3.3.3.3, Local port: 39049
	Foreign host: 5.5.5.5, Foreign port: 179
	Nexthop: 3.3.3.3
	Nexthop global: ::
	Nexthop local: ::
	BGP connection: non shared network
	Read thread: on  Write thread: off


	dnRouter# show bgp neighbors 9.9.9.3 advertised-routes

	BGP IPv4 Unicast table , local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	*> |8.7.6.5/32          | 9.9.9.2        |     0|       100|   32768|         i|

	Total number of prefixes 1
	Number of prefixes sent or ready to be sent 1


	dnRouter# show bgp neighbors 2.2.2.2

	BGP neighbor is 2.2.2.2, remote AS 65000, local AS 65000, confederation identifier 1, internal link
	  BGP version 4, remote router ID 2.2.2.2
	  BGP state = Established, up for 01:55:00
	  Last read 00:00:00, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: Recovered, Capable
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Labeled-Unicast: advertised and received (currently active)
	    Graceful Restart Capability: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
	  Graceful restart information:
	    End-of-RIB send: IPv4 Labeled-Unicast
	    End-of-RIB received: IPv4 Labeled-Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          1
	    Notifications:          0          0
	    Updates:               10         39
	    Keepalives:           117        116
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                128        156
	  Minimum time between advertisement runs is 0 seconds (next due in 0 seconds)
	  Update source is lo0

	For address family: IPv4 Unicast
	  MPLS Labeled-Unicast capability is enabled
	  Long-Lived-Graceful-Restart configuration: enabled
	    remaining stalepath time 16007249
	  Inbound soft reconfiguration allowed
	  AIGP is enabled
	  as-loop-check is enabled
	  Inbound path policy configured
	  Route map for incoming advertisements is *SET_MED_177
	  20 prefixes accepted
	  2 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 9.9.9.9, Local port: 39049
	Foreign host: 2.2.2.2, Foreign port: 179
	Nexthop: 9.9.9.9
	Nexthop global: ::
	Nexthop local: ::
	BGP connection: non shared network
	Read thread: on  Write thread: off


	dnRouter# show bgp neighbors 3.3.3.3

	BGP neighbor is 3.3.3.3, remote AS 65001, local AS 65000, confederation identifier 1, external link
	Neighbor under common administration
	  BGP version 4, remote router ID 3.3.3.3
	  BGP state = Established, up for 01:55:00
	  Last read 00:00:00, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: Recovered, Capable
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Labeled-Unicast: advertised and received (currently active)
	    Graceful Restart Capability: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
	  Graceful restart information:
	    End-of-RIB send: IPv4 Labeled-Unicast
	    End-of-RIB received: IPv4 Labeled-Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          1
	    Notifications:          0          0
	    Updates:               10         39
	    Keepalives:           117        116
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                128        156
	  Minimum time between advertisement runs is 0 seconds (next due in 0 seconds)
	  Update source is lo0

	For address family: IPv4 Unicast
	  MPLS Labeled-Unicast capability is enabled
	  Long-Lived-Graceful-Restart configuration: enabled
	    remaining stalepath time 16007249
	  Inbound soft reconfiguration allowed
	  AIGP is enabled
	  as-loop-check is enabled
	  Inbound path policy configured
	  Route map for incoming advertisements is *SET_MED_177
	  20 prefixes accepted
	  2 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 9.9.9.9, Local port: 39049
	Foreign host: 3.3.3.3, Foreign port: 179
	Nexthop: 9.9.9.9
	Nexthop global: ::
	Nexthop local: ::
	BGP connection: non shared network
	Read thread: on  Write thread: off


	dnRouter# show bgp neighbors 11.11.11.1

	BGP neighbor is 11.11.11.1, remote AS 100, local AS 65000, confederation identifier 1, external link
	  BGP version 4, remote router ID 11.11.11.11
	  BGP state = Established, up for 01:55:00
	  Last read 00:00:00, hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: Recovered, Capable
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Labeled-Unicast: advertised and received (currently active)
	    Graceful Restart Capability: advertised and received
	      Remote Restart timer is 120 seconds
	      Restart bit is on
	      Address families by peer:
	        none
	  Graceful restart information:
	    End-of-RIB send: IPv4 Labeled-Unicast
	    End-of-RIB received: IPv4 Labeled-Unicast
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          1
	    Notifications:          0          0
	    Updates:               10         39
	    Keepalives:           117        116
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                128        156
	  Minimum time between advertisement runs is 0 seconds (next due in 0 seconds)
	  Update source is lo0

	For address family: IPv4 Unicast
	  MPLS Labeled-Unicast capability is enabled
	  Long-Lived-Graceful-Restart configuration: enabled
	    remaining stalepath time 16007249
	  Inbound soft reconfiguration allowed
	  AIGP is enabled
	  as-loop-check is enabled
	  Inbound path policy configured
	  Route map for incoming advertisements is *SET_MED_177
	  20 prefixes accepted
	  2 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 11.11.11.2, Local port: 39049
	Foreign host: 11.11.11.1, Foreign port: 179
	Nexthop: 11.11.11.2
	Nexthop global: ::
	Nexthop local: ::
	BGP connection: non shared network
	Read thread: on  Write thread: off

	dnRouter# show bgp neighbors 9.9.9.3 advertised-routes

	BGP IPv4 Unicast table , local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	*> |8.7.6.5/32          | 9.9.9.2        |     0|       100|   32768|         i|

	Total number of prefixes 1
	Number of prefixes sent or ready to be sent 1


	dnRouter# show bgp neighbors

	BGP neighbor is 1.1.1.1, remote AS 100, local AS 100, internal link
	  BGP version 4, remote router ID 8.8.8.8
	  Local BGP cluster ID 65.65.65.65
	  BGP state = Established, up for 00:00:03
	  Last read 00:00:03, hold time is 180, keepalive interval is 60 seconds
	  Configured hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: enable
	  Local Restart timer is 120 seconds
	  Local Stalepath timer is 360 seconds
	  Local Purge timer is 420 seconds
	  NSR: active
	  NSR last recovery state: not recovered, Reason: N/A
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    AddPath:
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Unicast: advertised and received (currently active)
	    Graceful Restart Capabilty: advertised
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  3          2
	    Notifications:          1          0
	    Updates:              264          1
	    Keepalives:           924        920
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:               1192        923
	  Minimum time between advertisement runs is 0 seconds (next due in 0 seconds)
	  Update source is lo0

	 For address family: IPv4 Unicast
	  Route-Reflector Client
	  AS loop detection is enabled
	  0 prefixes accepted
	  30000 prefixes out

	  Connections established 2; dropped 1
	  Last reset 00:00:06, due to RR client config change
	Local host: 5.5.5.5, Local port: 37343
	Foreign host: 1.1.1.1, Foreign port: 179
	Nexthop: 5.5.5.5
	BGP connection: non shared network
	Estimated round trip time: 3 ms
	Read thread: on  Write thread: off

	dnRouter# show bgp neighbors 10.250.1.1 received-orf

	Address family: IPv4 Unicast
	ip prefix-list 10.250.1.1.1.1: 2 entries
	  seq 1 permit 111.111.111.111/32
	  seq 2 permit 111.111.111.112/32

	Address family: IPv6 Unicast
	ipv6 prefix-list 10.250.1.1.2.1: 2 entries
	   seq 1 permit 111:111::111/128
	   seq 2 permit 111:111::112/128



	dnRouter# show bgp ipv4 multicast neighbors

	BGP neighbor is 205.0.0.1, remote AS 100, local AS 23456, external link
	 Member of peer-group EBGP_23456 for session parameters
	  BGP version 4, remote router ID 192.0.0.1
	  BGP state = Established, up for 00:39:12
	  Using BFD to detect fast fallover in standard mode
	  BFD session status = Up, last event = Up updated at 09:48:37
	  Last read 00:00:12, hold time is 180, keepalive interval is 60 seconds
	  Configured hold time is 180, keepalive interval is 60 seconds
	  Graceful restart configuration: disable
	  Local Restart timer is 120 seconds
  	  Local Stalepath timer is 360 seconds
  	  Local Purge timer is 420 seconds
	  NSR: active
	  NSR last recovery state: not recovered, Reason: N/A
	  Neighbor capabilities:
	    4 Byte AS: advertised and received
	    Route refresh: advertised and received(old & new)
	    Address family IPv4 Multicast: advertised and received (currently active)
	  Message statistics:
	    Inq depth is 0
	    Outq depth is 0
	                         Sent       Rcvd
	    Opens:                  1          1
	    Notifications:          0          0
	    Updates:               10         39
	    Keepalives:           117        116
	    Route Refresh:          0          0
	    Capability:             0          0
	    Total:                128        156
	  Minimum time between advertisement runs is 30 seconds (next due in 26 seconds)

	For address family: IPv4 Multicast
	  EBGP_23456 peer-group member
	  Inbound soft reconfiguration allowed
	  Community attribute sent to this neighbor(both)
	  AS loop detection is enabled
	  Flap Dampening is enabled
	  AIGP is enabled
	  Inbound path policy configured
	  Outbound path policy configured
	  Route map for incoming advertisements is *IBGP_v4_MC_IN_ALL
	  Route map for outgoing advertisements is *IBGP_v4_MC_OUT_ALL
	  20 prefixes accepted
	  2 prefixes out

	  Connections established 1; dropped 0
	  Last reset never
	Local host: 5.5.5.5 Local port: 39049
	Foreign host: 205.0.0.1, Foreign port: 179
	Nexthop: 5.5.5.5
	Nexthop global: ::
	Nexthop local: ::
	BGP connection: non shared network
	Read thread: on  Write thread: off

	dnRouter# show bgp l2vpn evpn neighbors 54.54.54.54

	BGP neighbor is 54.54.54.54, remote AS 100001, local AS 100001, internal link
  		BGP version 4, remote router ID 54.54.54.54
  		Local BGP cluster ID 53.53.53.53
  		BGP state = Established, up for 00:00:31
  		Last read 00:00:32, hold time is 180, keepalive interval is 60 seconds
  		Configured hold time is 180, keepalive interval is 60 seconds
  		Graceful restart configuration: enable
  		Local Restart timer is 120 seconds
  		Local Stalepath timer is 360 seconds
  		Local Purge timer is 420 seconds
  		NSR: inactive, Reason: peer support GR
  		Neighbor capabilities:
    		4 Byte AS: advertised and received
    		Route refresh: advertised and received(old & new)
    		Address family IPv4 Route Target Constrains: advertised
    		Address family L2vpn EVPN: advertised and received (currently active)
    		Graceful Restart Capabilty: advertised and received
      			Remote Restart timer is 120 seconds
      			Remote Restart bit is on
      			Remote Address families by peer:
        			L2VPN EVPN(preserved)
  		Graceful restart informations:
    		End-of-RIB send: L2VPN EVPN
    		End-of-RIB received:
    		The remaining time of stalepath timer is 325
  		Message statistics:
    		Inq depth is 0
    		Outq depth is 0
       	                 		 Sent       Rcvd
    		Opens:                  3          0
    		Notifications:          0          0
    		Updates:            16647       5699
    		Keepalives:          1556       1553
    		Route Refresh:          0          0
    		Capability:             0          0
    		Total:              18206       7252
  		Minimum time between advertisement runs is 0 seconds (next due in 0 seconds)
  		Update source is lo0

 	For address family: IPv4 Route Target Constrains
  	  AS loop detection is enabled
  	  0 prefixes accepted
  	  0 prefixes out

 	For address family: L2vpn EVPN
  	  Inbound soft reconfiguration allowed
  	  Community attribute sent to this neighbor(both)
  	  AS loop detection is enabled
  	  4716 prefixes accepted
   	  9984 prefixes out

  	  Connections established 2; dropped 1
  	  Last reset 00:00:35, due to NSF peer closed the session
	Local host: 53.53.53.53, Local port: 179
	Foreign host: 54.54.54.54, Foreign port: 45999
	Nexthop: 53.53.53.53
	BGP connection: non shared network
	Read thread: on  Write thread: on


.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+-----------------------------------------------------------------------------------------+
| Release | Modification                                                                            |
+=========+=========================================================================================+
| 6.0     | Command introduced                                                                      |
+---------+-----------------------------------------------------------------------------------------+
| 7.0     | Added AIGP information to output                                                        |
+---------+-----------------------------------------------------------------------------------------+
| 11.6    | Added BGP confederation show command output                                             |
+---------+-----------------------------------------------------------------------------------------+
| 13.0    | Added NSR information to output                                                         |
+---------+-----------------------------------------------------------------------------------------+
| 15.0    | Added Route Reflector information to output                                             |
+---------+-----------------------------------------------------------------------------------------+
| 16.0    | Added support for IPv4 Route Target Constrain SAFI and added received-orf to the output |
+---------+-----------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                                                   |
|         | Added support for displaying prefix-lists received from orf capable neighbor            |
+---------+-----------------------------------------------------------------------------------------+
