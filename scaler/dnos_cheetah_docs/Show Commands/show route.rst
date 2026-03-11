show route
-----------

**Minimum user role:** viewer

Use the following command syntax to display routing table information:

**Command syntax: show route** {vrf [vrf-name] | all} table [table] {[prefix] \| protocol [protocol-name]}

**Command mode:** operational


**Note**

- By default, the command output displays ipv4-unicast, ipv6-unicast, and mpls-nh routing. Use the table filter to display a specific table.

- The MPLS-NH table is applicable to the default VRF only.

.. Show route mpls-nh = quagga "show mpls route"


**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter |                                                                                  Description                                                                                  |        Range       |
+===========+===============================================================================================================================================================================+====================+
| table     | Displays only the specified table (where applicable, [vrf-name] is used).                                                                                                     | IPv4-unicast       |
|           | If you do not specify a table, all will be displayed.                                                                                                                         | IPv6-unicast       |
|           |                                                                                                                                                                               | MPLS-NH            |
|           |                                                                                                                                                                               | COLOR-MPLS-NH      |
|           |                                                                                                                                                                               | COLOR-MPLS-NH-IPv6 |
|           |                                                                                                                                                                               | Management         |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| protocol  | Displays the routing table for the specified protocol only.                                                                                                                   | Access             |
| protocol  | Valid for unicast routing                                                                                                                                                     | Connected          |
|           |                                                                                                                                                                               | Static             |
|           |                                                                                                                                                                               | OSPF               |
|           |                                                                                                                                                                               | ISIS               |
|           |                                                                                                                                                                               | eBGP               |
|           |                                                                                                                                                                               | iBGP               |
|           |                                                                                                                                                                               | RSVP               |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| prefix    | Displays detailed routing information for the specified IPv4, or IPv6 prefix. By default, only information from the unicast table is displayed.                               | A.B.C.D/M          |
|           |                                                                                                                                                                               | xx:xx::xx:xx/x     |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| vrf-name  | Displays the routing table for the specified VRF. If not specified, routes for the default VRF are displayed. When 'all' is specified as the VRF, then each VRF is displayed. | String | all       |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

The following information is displayed on each route:

+-------------------+------------------------------------------------------+
| Attribute         | Description                                          |
+===================+======================================================+
| Flags             | K - kernel route                                     |
|                   | X - Access (indicates a route obtained via DHCP/RA)  |
|                   | C - connected                                        |
|                   | S - static (indicates a static route)                |
|                   | r - RIP                                              |
|                   | O - OSPF (indicates an OSPF route)                   |
|                   | I - IS-IS (indicates and IS-IS route)                |
|                   | B - BGP (indicates a BGP route)                      |
|                   | P - PIM                                              |
|                   | A - Babel                                            |
|                   | D - BFD                                              |
|                   | L - LDP (indicates an LDP route)                     |
|                   | R - RSVP                                             |
|                   | > - indicates a selected route                       |
|                   | * - indicates an installed route (in RIB)            |
+-------------------+------------------------------------------------------+
| IP Prefix         | The route's prefix                                   |
+-------------------+------------------------------------------------------+
| Next Hop          | The next destination router on the route             |
+-------------------+------------------------------------------------------+
| MPLS              | The label used                                       |
+-------------------+------------------------------------------------------+
| Resolved Next Hop | The recursive next hop leading to the destination    |
+-------------------+------------------------------------------------------+
| Resolved MPLS     | The label of the next hop leading to the destination |
+-------------------+------------------------------------------------------+
| Interface         | The interface of the route                           |
+-------------------+------------------------------------------------------+

**Example**
::

	dnRouter# show route

	VRF: default
	IPv4 Route Table:
	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route


	C>*    1.1.1.1/32 is directly connected, lo10
	I L2>*    2.2.2.2/32 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	I L2>*    3.3.3.3/32 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	I L2>*    4.4.4.4/32 [115/10] via 14.14.14.2, bundle-2.1202, 03:41:09
	I L2>*    5.5.5.5/32 [115/30] via 14.14.14.2, bundle-2.1202, 03:41:09
	  *                        via 12.12.12.2, bundle-2.1201, 03:41:09
	I L2>*    6.6.6.6/32 [115/21] via 12.12.12.2, bundle-2.1201, 03:41:29
	C>*    10.0.0.0/30 is directly connected, gre-tunnel-3
	C>*    12.12.12.0/30 is directly connected, bundle-2.1201
	C>*    14.14.14.0/30 is directly connected, bundle-2.1202
	C>*    20.0.0.0/30 is directly connected, bundle-1.1101
	I L2>*    23.23.23.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	B>*    25.0.0.0/24 [20/0] via 20.0.0.2, bundle-1.1101, 03:41:36
	I L2>*    25.25.25.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	B>     35.0.0.0/24 [200/0] via 6.6.6.6 (recursive), 02:37:59
	  *                          via TUNNEL1, 02:37:59
	I L2>*    36.36.36.0/30 [115/21] via 12.12.12.2, bundle-2.1201, 03:41:29
	B>*    44.33.2.0/24 [20/0] via 173.0.23.3, eth2 label 100001, 00:01:40
	  *                        via 173.0.25.5, eth3 alternate label 100001, 00:01:40
	I L2>*    45.45.45.0/30 [115/20] via 14.14.14.2, bundle-2.1202, 03:41:09
	I L2>*    56.56.56.0/30 [115/30] via 14.14.14.2, bundle-2.1202, 03:41:09
	  *                           via 12.12.12.2, bundle-2.1201, 03:41:09
	C>*    127.0.0.0/8 is directly connected, lo


	IPv6 Route Table:
	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	C>*    ::1/128 is directly connected, lo
	C *    fe80::/64 is directly connected, f1_v0
	C *    fe80::/64 is directly connected, bundle-1.1101
	C *    fe80::/64 is directly connected, bundle-1
	C *    fe80::/64 is directly connected, bundle-2.1202
	C *    fe80::/64 is directly connected, bundle-2.1201
	C>*    fe80::/64 is directly connected, bundle-2


	IPv4 MPLS Route Table:
	Codes: K - kernel route, X - access, C - connected,  S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary routet


	R>*    6.6.6.6/32 [0/0] via TUNNEL1 label 24001, 02:37:59


    show route vrf mgmt-ncc-0

    VRF: mgmt-ncc-0
    S>*     0.0.0.0/0 via 100.64.15.254, mgmt-ncc-0
    C>*     100.64.0.0/20 is directly connected, mgmt-ncc-0
    C>*     100.64.0.0/32 is directly connected, mgmt-ncc-0
    C>*     100.64.14.117/32 is directly connected, mgmt-ncc-0
    C>*     100.64.15.255/32 is directly connected, mgmt-ncc-0
    S>*     ::/0 via cafe::1, mgmt-ncc-0
    C>*     cafe::/64 is directly connected, mgmt-ncc-0
    C>*     fd80:1::/96 is directly connected, mgmt-ncc-0
    C>*     fe80::/64 is directly connected, mgmt-ncc-0
    C>*     fe80::30b3:33ff:fe34:a7fc/128 is directly connected, mgmt-ncc-0
    C>*     ff00::/8 is directly connected, mgmt-ncc-0


    show route vrf mgmt-ncc-1

    VRF: mgmt-ncc-1
    S>*     0.0.0.0/0 via 100.64.15.254, mgmt-ncc-1
    C>*     100.64.0.0/20 is directly connected, mgmt-ncc-1
    C>*     100.64.0.0/32 is directly connected, mgmt-ncc-1
    C>*     100.64.14.117/32 is directly connected, mgmt-ncc-1
    C>*     100.64.15.255/32 is directly connected, mgmt-ncc-1
    S>*     ::/0 via cafe::1, mgmt-ncc-1
    C>*     cafe::/64 is directly connected, mgmt-ncc-1
    C>*     fd80:1::/96 is directly connected, mgmt-ncc-1
    C>*     fe80::/64 is directly connected, mgmt-ncc-1
    C>*     fe80::30b3:33ff:fe34:a7fc/128 is directly connected, mgmt-ncc-1


    show route vrf mgmt0

    VRF: mgmt0
    C>*     100.64.14.17/32 is directly connected, mgmt0
    C>*     fe80::862d:b3ff:fe7d:fd7b/128 is directly connected, mgmt0


    dnRouter# show route protocol isis

	VRF: default
	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I L2>*    2.2.2.2/32 [115/20] via 12.12.12.2, bundle-2.1201, weight 3, 03:45:57
	I L2>*    3.3.3.3/32 [115/20] via 12.12.12.2, bundle-2.1201, 03:45:57
	I L2>*    4.4.4.4/32 [115/10] via 14.14.14.2, bundle-2.1202, weight 3, 03:45:37
	I L2>*    5.5.5.5/32 [115/30] via 14.14.14.2, bundle-2.1202, weight 4, 03:45:37
	  *                        via 12.12.12.2, bundle-2.1201, weight 2, 03:45:37
	I L2>*    6.6.6.6/32 [115/21] via 12.12.12.2, bundle-2.1201, weight 3, 03:45:57
	I L2>*    23.23.23.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:45:57
	I L2>*    25.25.25.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:45:57
	I L2>*    36.36.36.0/30 [115/21] via 12.12.12.2, bundle-2.1201, 03:45:57
	I L2>*    45.45.45.0/30 [115/20] via 14.14.14.2, bundle-2.1202, 03:45:37
	I L2>*    56.56.56.0/30 [115/30] via 14.14.14.2, bundle-2.1202, 03:45:37
	  *                           via 12.12.12.2, bundle-2.1201, 03:45:37


	dnRouter# show route protocol ospf

	VRF: default
	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	O>*(S)    2.2.2.2/32 [110/20] via 12.12.12.2, bundle-2.1201, 03:45:57
	O>*(S)    3.3.3.3/32 [110/20] via 12.12.12.2, bundle-2.1201, 03:45:57
	O>*(S)    4.4.4.4/32 [110/10] via 14.14.14.2, bundle-2.1202, 03:45:37
	O>*(S)    5.5.5.5/32 [110/30] via 14.14.14.2, bundle-2.1202, 03:45:37
	  *(S)                        via 12.12.12.2, bundle-2.1201, 03:45:37
	O>*(S)    6.6.6.6/32 [110/21] via 12.12.12.2, bundle-2.1201, 03:45:57



	dnRouter# show route protocol ospfv3

	VRF: default
	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	O>*(S)    2003::/64 [110/20] via 1234::1, bundle-2.1201, 03:45:57
	O>*(S)    C001:1234::/64 [110/20] via 1234::1, bundle-2.1201, 03:45:57
	O>*(S)    4321:2345::/120 [110/10] via 1235:C23, bundle-2.1202, 03:45:37
	O>*(S)    2000:76CC::12/64 [115/30] via 1235:C23, bundle-2.1202, 03:45:37
	  *(S)                              via 1234::1, bundle-2.1201, 03:45:37


	dnRouter# show route 2.2.2.2/32

	VRF: default
	Routing entry for 2.2.2.2/32
	  Known via "isis", priority high, distance 115, metric 20, vrf default, best, fib
	  Last update 03:44:38 ago
	  * 12.12.12.2, via bundle-2.1201, weight 2


	dnRouter# show route 55.55.55.55

	Routing entry for 55.55.55.55/32
	  Known via "bgp", priority low, distance 200, metric 0, vrf default, best, fib, *urpf-check ignore*
	 * Last update 00:00:21 ago*
	   llgr-stale stalepath time 16776942 seconds
	    30.0.0.0 (recursive)
	  *   10.99.0.66, via bundle-20.2004 label 20


	dnRouter# show route 44.33.2.0/24

	Routing entry for 44.33.2.0/24
	  Known via "bgp", priority high, distance 20, metric 0, vrf default, best, fib
	  Last update 00:01:51 ago
	  * 173.0.23.3, via eth2 label 100001
	  * 173.0.25.5, via eth3 alternate label 100001


	dnRouter# show route 5.13.100.0/24

	VRF: default
	Routing entry for 5.13.100.0/24
  		Known via "bgp", priority low, distance 200, metric 0, vrf default, best, fib
  		Qppb classes: src-class: 10 dest-class: 20
  		Last update 1d11h47m ago
    	100.13.13.13 (recursive)
  		* 1.13.16.0, via bundle-1316


	dnRouter# show route 2.2.2.2/32

	Routing entry for 2.2.2.2/32
		Known via "isis" level 2, priority medium, distance 115, metric 10, vrf default, best, fib
		Last update 04:18:43 ago
		* 10.0.12.2, via bundle-12
		* 10.0.13.3, via bundle-13 alternate remote merge-point 4.4.4.4 label 57228


	dnRouter# show route
	dnRouter# show route vrf A
	dnRouter# show route table mpls-nh
	dnRouter# show route table color-mpls-nh
	dnRouter# show route table color-mpls-nh-ipv6
	dnRouter# show route table ipv4-unicast protocol bgp
	dnRouter# show route table ipv6-unicast fe80::/64
	dnRouter# show route vrf A table ipv6-unicast protocol bgp
	dnRouter# show route vrf default table ipv4-unicast


	dnRouter# show route table mpls-nh

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I L2     8.8.8.9/32 [115/30] via plot2_9, 00:00:04
	                          via plot3_9, 00:00:04
	                          via plot_9, 00:00:04
	R>*   8.8.8.9/32 [100/30] via plot_9, 00:07:25
	  *                       via plot3_9, 00:07:25
	  *                       via plot2_9, 00:07:25
	I L2     8.8.8.10/32 [115/40] via plot2_10, 00:00:04
	                           via plot3_10, 00:00:04
	                           via plot_10, 00:00:04
	R>*   8.8.8.10/32 [100/40] via plot_10, 00:07:25
	  *                        via plot3_10, 00:07:25
	  *                        via plot2_10, 00:07:25
	I L2  !  8.8.8.12/32 [115/50] via plot2_11, 00:00:04
	                           via plot3_11, 00:00:04
	                           via plot_11, 00:00:04
	R>*   8.8.8.11/32 [100/50] via plot_11, 00:07:25
	  *                        via plot3_11, 00:07:25
	  *                        via plot2_11, 00:07:25


	dnRouter# show route table mpls-nh

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I L2     8.8.8.9/32 [115/30] via plot2_9, 00:00:04
	                          via plot3_9, 00:00:04
	                          via plot_9, 00:00:04
	R>*   8.8.8.9/32 [100/30] via plot_9, 00:07:25
	  *                       via plot3_9, 00:07:25
	  *                       via plot2_9, 00:07:25
	I L2     8.8.8.10/32 [115/40] via plot2_10, 00:00:04
	                           via plot3_10, 00:00:04
	                           via plot_10, 00:00:04
	R>*   8.8.8.10/32 [100/40] via plot_10, 00:07:25
	  *                        via plot3_10, 00:07:25
	  *                        via plot2_10, 00:07:25
	I L2  !  8.8.8.12/32 [115/50] via plot2_11, 00:00:04
	                           via plot3_11, 00:00:04
	                           via plot_11, 00:00:04
	R>*   8.8.8.11/32 [100/50] via plot_11, 00:07:25
	  *                        via plot3_11, 00:07:25
	  *                        via plot2_11, 00:07:25


	dnRouter# show route protocol isis

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I L1>*    1.101.102.0/31 [115/320] via 1.3.19.0, bundle-319.319, 00:07:21
	I L1>*    4.0.0.0/24 [115/320] via 1.3.19.0, bundle-319.319, 00:07:21
	I L1      100.0.0.2/32 [115/16777414] via 1.2.19.0, bundle-219.219, 00:00:46
	I L1      100.0.0.3/32 [115/300] via 1.3.19.0, bundle-319.319, 00:07:21
	I L1>*    100.10.0.2/32 [115/16777414] via 1.2.19.0, bundle-219.219, 00:00:46
	I L1>*    100.10.0.3/32 [115/300] via 1.3.19.0, bundle-319.319, 00:07:21
	I L1>*    101.0.0.6/32 [115/10] via 1.6.19.0, bundle-3.1119, 06:54:57
	                             via 1.3.19.0, bundle-319.319 alternate, 06:54:57

	dnRouter# show route table color-mpls-nh

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I-SR>*        2.2.2.2/32 <c> 3 [107/10] via 10.0.12.2, bundle-12 label 3, 00:08:06
	I-SR>*        3.3.3.3/32 <c> 4 [107/10] via 10.0.13.3, bundle-13 label 3, 00:08:01
	I-SR>*        5.5.5.5/32 <c> 4 [107/30] via 10.0.13.3, bundle-13 label 17405, 00:08:01
	SRTE>*        22.22.22.2/32 <c> 0 [105/10] via pol_22.22.22.2_0, 00:05:36
	SRTE>*        22.22.22.2/32 <c> 1 [105/10] via pol_22.22.22.2_1, 00:05:36
	SRTE>*        22.22.22.3/32 <c> 1 [105/10] via pol_22.22.22.3_1, 00:05:36


	dnRouter# show route table color-mpls-nh

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I-SR>* (S)    2.2.2.2/32 <c> 3 [107/10] via 10.0.12.2, bundle-12 label 3, 00:08:06
	SRTE>* (S)    22.22.22.3/32 <c> 2 [105/10] via pol_22.22.22.3_2, 00:05:35


	dnRouter# show route table color-mpls-nh color 3

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I-SR>*        2.2.2.2/32 <c> 3 [107/10] via 10.0.12.2, bundle-12 label 3, 00:08:06
	SRTE>*        22.22.22.2/32 <c> 2 [105/10] via pol_22.22.22.2_3, 00:06:25
	SRTE>*        22.22.22.3/32 <c> 2 [105/10] via pol_22.22.22.3_3, 00:06:25


	dnRouter# show route table color-mpls-nh destination 22.22.22.8

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	SRTE>*        22.22.22.8/32 <c> 0 [105/10] via pol_22.22.22.8_0, 00:06:18
	SRTE>*        22.22.22.8/32 <c> 1 [105/10] via pol_22.22.22.8_1, 00:06:18
	SRTE>*        22.22.22.8/32 <c> 2 [105/10] via pol_22.22.22.8_2, 00:06:17


	dnRouter# show route table color-mpls-nh destination 22.22.22.7/32

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	SRTE>*        22.22.22.7/32 <c> 0 [105/10] via pol_22.22.22.7_0, 18:04:28
	SRTE>*        22.22.22.7/32 <c> 1 [105/10] via pol_22.22.22.7_1, 18:04:28
	SRTE>*        22.22.22.7/32 <c> 2 [105/10] via pol_22.22.22.7_2, 18:04:28


	dnRouter# show route table color-mpls-nh destination 2.2.2.2 color 3

	Routing entry for 2.2.2.2/32 <c> 3
	  Known via "isis-sr", priority medium, distance 107, metric 10, vrf default, best, fib
	  Last update 00:16:39 ago
	  * 10.0.12.2, via bundle-12 label 3


	dnRouter# show route table color-mpls-nh destination 22.22.22.11/32 color 3

	Routing entry for 22.22.22.11/32 <c> 3
	  Known via "sr-te (isis)", priority high, distance 105, metric 10, vrf default, best, fib
	  Last update 00:06:21 ago
	  * via pol_22.22.22.11_3


dnRouter# show route table color-mpls-nh-ipv6

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I-SR>*        2:2:2::2/32 <c> 3 [107/10] via 10:12::2, bundle-12 label 3, 00:08:06
	I-SR>*        3:3:3::3/32 <c> 4 [107/10] via 10:13::3, bundle-13 label 3, 00:08:01
	I-SR>*        5:5:5::5/32 <c> 4 [107/30] via 10:13::3, bundle-13 label 17405, 00:08:01
	SRTE>*        22:22:22:2/32 <c> 0 [105/10] via pol_22.22.22.2_0, 00:05:36
	SRTE>*        22:22:22:2/32 <c> 1 [105/10] via pol_22.22.22.2_1, 00:05:36
	SRTE>*        22:22:22:3/32 <c> 1 [105/10] via pol_22.22.22.3_1, 00:05:36


	dnRouter# show route table color-mpls-nh-ipv6

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I-SR>* (S)    22::22/128 <c> 3 [107/10] via 10:12::2, bundle-12 label 3, 00:08:06
	SRTE>* (S)    2222::2222/128 <c> 2 [105/10] via pol_22.22.22.3_2, 00:05:35


	dnRouter# show route table color-mpls-nh-ipv6 color 3

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	I-SR>*        2222::2222/128 <c> 3 [107/10] via 10:12::2, bundle-12 label 3, 00:08:06
	SRTE>*        2222::2222:2/128 <c> 3 [105/10] via pol_22.22.22.2_3, 00:06:25
	SRTE>*        2222::2222:8/128 <c> 3 [105/10] via pol_22.22.22.3_3, 00:06:25


	dnRouter# show route table color-mpls-nh-ipv6 destination 2222::2222:8

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	SRTE>*        2222::2222:8/128 <c> 0 [105/10] via pol_22.22.22.8_0, 00:06:18
	SRTE>*        2222::2222:8/128 <c> 1 [105/10] via pol_22.22.22.8_1, 00:06:18
	SRTE>*        2222::2222:8/128 <c> 2 [105/10] via pol_22.22.22.8_2, 00:06:17


	dnRouter# show route table color-mpls-nh-ipv6 destination 2222::2222:7/128

	Codes: K - kernel route, X - access, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
	       O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
	       EVI - EVI,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
	       L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

	SRTE>*        2222::2222:7/128 <c> 0 [105/10] via pol_22.22.22.7_0, 18:04:28
	SRTE>*        2222::2222:7/128 <c> 1 [105/10] via pol_22.22.22.7_1, 18:04:28
	SRTE>*        2222::2222:7/128 <c> 2 [105/10] via pol_22.22.22.7_2, 18:04:28


	dnRouter# show route table color-mpls-nh-ipv6 destination 2222::2222 color 3

	Routing entry for 2222::2222/32 <c> 3
	  Known via "isis-sr", priority medium, distance 107, metric 10, vrf default, best, fib
	  Last update 00:16:39 ago
	  * 10:12::2, via bundle-12 label 3


	dnRouter# show route table color-mpls-nh-ipv6 destination 2222::2222/128 color 3

	Routing entry for 2222::2222/128 <c> 3
	  Known via "sr-te (isis)", priority high, distance 105, metric 10, vrf default, best, fib
	  Last update 00:06:21 ago
	  * via pol_22.22.22.11_3

.. **Help line:** show routing table

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 5.1.0   | Command introduced                            |
+---------+-----------------------------------------------+
| 6.0     | Added detail argument to the command syntax   |
+---------+-----------------------------------------------+
| 9.0     | Added IS-IS support                           |
+---------+-----------------------------------------------+
| 10.0    | Added management table display                |
+---------+-----------------------------------------------+
| 11.4    | Added support for GRE tunnels                 |
+---------+-----------------------------------------------+
| 16.1    | Added All filter and support for mpls-nh-ipv6 |
+---------+-----------------------------------------------+
| 17.0    | Added color-mpls-nh table                     |
+---------+-----------------------------------------------+
| 17.1    | Added display of remote merge-point for IS-IS |
+---------+-----------------------------------------------+
| 18.1    | Added next-hop path weight                    |
+---------+-----------------------------------------------+
| 18.2    | Added color-mpls-nh-ipv6 table                |
+---------+-----------------------------------------------+
| 19.1    | Added support for Access protocol (DHCP/RA)   |
+---------+-----------------------------------------------+
