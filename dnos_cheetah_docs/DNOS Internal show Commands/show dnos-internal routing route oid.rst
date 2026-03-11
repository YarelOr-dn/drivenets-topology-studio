show dnos-internal routing route oid
------------------------------------

**Minimum user role:** viewer

To display routing solutions based on nexthop-OID:

**Command syntax:show dnos-internal routing [table] route oid** 

**Command mode:** operation

**Parameter table**

+---------------+-------------------------------------------------------------+-----------+-------------+
|               |                                                             |           |             |
| Parameter     | Description                                                 | Range     | Default     |
+===============+=============================================================+===========+=============+
|               |                                                             |           |             |
| table         | The routing table for which to display routing solutions    | IP        | \-          |
|               |                                                             |           |             |
|               |                                                             | IPv6      |             |
|               |                                                             |           |             |
|               |                                                             | MPLS      |             |
+---------------+-------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# show dnos-internal routing ip route oid
	Codes: K - kernel route, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route

	I>*    1.0.0.0/30 [115/20] via 50.170.0.0, bundle-502 (oid: 289), 00:59:02
	I>*    1.0.1.0/30 [115/30] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.2.0/30 [115/30] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.3.0/30 [115/40] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.4.0/30 [115/40] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.5.0/30 [115/40] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.6.0/30 [115/50] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.7.0/30 [115/50] via 50.170.0.0, bundle-502 (oid: 289), 00:58:51
	I>*    1.0.8.0/30 [115/20] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:59:02
	I>*    1.0.9.0/30 [115/30] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51
	I>*    1.0.10.0/30 [115/30] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51
	I>*    1.0.11.0/30 [115/40] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51
	I>*    1.0.12.0/30 [115/40] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51
	I>*    1.0.13.0/30 [115/40] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51
	I>*    1.0.14.0/30 [115/50] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51
	I>*    1.0.15.0/30 [115/50] via 50.170.1.0, bundle-502.2002 (oid: 302), 00:58:51

	dnRouter# show dnos-internal routing ipv6 route oid
	Codes: K - kernel route, C - connected, S - static, r - RIPng,
	       O - OSPFv3, I - IS-IS, B - BGP, A - Babel, D - BFD,
	       L - LDP, R - RSVP,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route

	I>*    1111:1111::1/128 [115/1] via fe80::8640:76ff:fe30:333b, bundle-115 (oid: 8), 2d12h19m
	I>*    1212:1212::1/128 [115/1] via fe80::8640:76ff:fe31:3196, bundle-125 (oid: 1653), 10:42:16
	I>*    1313:1313::1/128 [115/1] via fe80::8640:76ff:fe64:3367, bundle-135 (oid: 1230), 15:32:53
	C>*    1500:1730:0:2::/64 is directly connected, bundle-243.2412 (oid: 1183)
	C>*    1500:1730:0:3::/64 is directly connected, bundle-243.2413 (oid: 1184)
	C>*    1500:1730:0:4::/64 is directly connected, bundle-243.2414 (oid: 1185)
	C>*    1500:1730:0:5::/64 is directly connected, bundle-243.2415 (oid: 1186)
	C>*    1500:1730:0:6::/64 is directly connected, bundle-243.2416 (oid: 1187)
	C>*    1500:1730:0:7::/64 is directly connected, bundle-243.2417 (oid: 1188)
	C>*    1500:1730:0:8::/64 is directly connected, bundle-243.2418 (oid: 1189)
	C>*    1500:1730:0:9::/64 is directly connected, bundle-243.2419 (oid: 1190)
	B>*    1500:2500:1500::/128 [20/0] via 1555:2555:0:2::2, bundle-248.2900 (oid: 1896), 02:52:07
	B>*    1500:2500:1500::1/128 [20/0] via 1555:2555:0:2::2, bundle-248.2900 (oid: 1896), 02:52:07


	dnRouter# show dnos-internal routing mpls route oid
	Codes: K - kernel route, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP, M - OAM,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route

	I      100.11.11.11/32 [115/1] via auto_tunnel_R15_Large_Core_R11_MC_Core_Devtest_CORE_Routers_2 inactive, 2d12h18m
	                                 via tunnel_bypass_link-bundle-115_937 alternate inactive (oid: 16), 2d12h18m
	R      100.11.11.11/32 [100/1] via auto_tunnel_R15_Large_Core_R11_MC_Core_Devtest_CORE_Routers_2 inactive, 2d12h18m
	                                 via tunnel_bypass_link-bundle-115_937 alternate inactive (oid: 16), 2d12h18m
	I      100.11.12.0/30 [115/2] via auto_tunnel_R15_Large_Core_R11_MC_Core_Devtest_CORE_Routers_2 inactive, 10:36:48
	                                via tunnel_bypass_link-bundle-115_937 alternate inactive (oid: 16), 10:36:48
	                              via auto_tunnel_R15_Large_Core_R12_Medium_Core_Devtest_CORE_Routers_157 inactive, 10:36:48
	                                via tunnel_bypass_link-bundle-125_932 alternate inactive (oid: 1657), 10:36:48
	I      100.12.12.12/32 [115/1] via auto_tunnel_R15_Large_Core_R12_Medium_Core_Devtest_CORE_Routers_157 inactive, 10:41:49
	                                 via tunnel_bypass_link-bundle-125_932 alternate inactive (oid: 1657), 10:41:49
	R      100.12.12.12/32 [100/1] via auto_tunnel_R15_Large_Core_R12_Medium_Core_Devtest_CORE_Routers_157 inactive, 10:41:49
	                                 via tunnel_bypass_link-bundle-125_932 alternate inactive (oid: 1657), 10:41:49

.. **Help line:** Displays routing solutions based on nexthop-OID

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+


