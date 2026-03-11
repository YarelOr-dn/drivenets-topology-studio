show multicast rpf debug
------------------------

**Minimum user role:** viewer

You can use this command to display the complete multicast rpf route table.

**Command syntax: show multicast rpf debug** [prefix] \| protocol [protocol-name]

**Command mode:** operational



**Note**

- The command displays ipv4-unicast routes that were derived from Connected, IGP, BGP, ipv4 unicast static routes, and ipv4-multicast routes that were installed from routing protocols' multicast SAFI.

- IPv4 Unicast routes that are resolved via a tunnel in the regular Unicast RIB are resolved via IGP to a unicast next hop.

- When a prefix is used, a detailed routing information for that prefix is displayed.

- Output will include all routes installed in the table regardless of the configured RPF check mode. For output of applicable routes that shall be used for RPF check according to the configured RPF check mode, refer to the 'show multicast rpf' command.



**Parameter table**

+---------------+--------------------------------------------------------------------------+-----------------------------+---------+
| Parameter     | Description                                                              | Range                       | Default |
+===============+==========================================================================+=============================+=========+
| prefix        | The prefix for which the routing information will be displayed           | A.B.C.D/M                   | \-      |
|               |                                                                          | xx:xx::xx:xx/X              |         |
+---------------+--------------------------------------------------------------------------+-----------------------------+---------+
| protocol-name | The type of protocol for which the routing information will be displayed | connected                   |         |
|               |                                                                          | static                      |         |
|               |                                                                          | ospf                        | \-      |
|               |                                                                          | isis                        |         |
|               |                                                                          | bgp                         |         |
|               |                                                                          | (valid for unicast routing) |         |
+---------------+--------------------------------------------------------------------------+-----------------------------+---------+

**Example**
::

	dnRouter# show multicast rpf debug

	VRF: default
	Codes: K - kernel route, C - connected, S - static, r - RIP,
        O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
        L - LDP, R - RSVP,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, m - Multicast

	C>*    1.1.1.1/32 is directly connected, lo10
	I>*    2.2.2.2/32 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	I>*    5.5.5.5/32 [115/30] via 14.14.14.2, bundle-2.1202, 03:41:09
	 *                        via 12.12.12.2, bundle-2.1201, 03:41:09
	I>*    6.6.6.6/32 [115/21] via 12.12.12.2, bundle-2.1201, 03:41:29
	C>*    12.12.12.0/30 is directly connected, bundle-2.1201
	C>*    14.14.14.0/30 is directly connected, bundle-2.1202
	C>*    20.0.0.0/30 is directly connected, bundle-1.1101
	I>*    23.23.23.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	B>*    25.0.0.0/24 [20/0] via 20.0.0.2, bundle-1.1101, 03:41:36
	I>*    25.25.25.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	B>     35.0.0.0/24 [200/0] via 6.6.6.6 (recursive), 02:37:59
	 *                          via 12.12.12.2, 02:37:59
	I>*    36.36.36.0/30 [115/21] via 12.12.12.2, bundle-2.1201, 03:41:29
	I>*    56.56.56.0/30 [115/30] via 14.14.14.2, bundle-2.1202, 03:41:09
  	 *                           via 12.12.12.2, bundle-2.1201, 03:41:09



	dnRouter# show multicast rpf debug 2.2.2.2/32

	VRF: default
	RPF check mode: intact
	Routing entry for 2.2.2.2/32
	  Known via "isis", unicast, priority high, distance 115, metric 20, vrf default, best, fib,
	  Last update 03:44:38 ago
	  * 12.12.12.2, via bundle-2.1201
	  Known via "isis", multicast, priority high, distance 115, metric 30, vrf default
	  Last update 03:44:38 ago
	   12.12.12.2, via bundle-2.1201


	dnRouter# show multicast rpf debug protocol isis

	VRF: default
	RPF check mode: MRPF
	Codes: K - kernel route, C - connected, S - static, r - RIP,
	       O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
	       L - LDP, R - RSVP,
	       > - selected route, * - FIB route, (S) - stale route
	       (L) - over limit route, m - Multicast

	Im>*    2.2.2.2/32 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	Im>*    5.5.5.5/32 [115/30] via 14.14.14.2, bundle-2.1202, 03:41:09
	  *                        via 12.12.12.2, bundle-2.1201, 03:41:09
	Im>*    6.6.6.6/32 [115/21] via 12.12.12.2, bundle-2.1201, 03:41:29
	Im>*    23.23.23.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	Im>*    25.25.25.0/30 [115/20] via 12.12.12.2, bundle-2.1201, 03:41:29
	Im>*    36.36.36.0/30 [115/21] via 12.12.12.2, bundle-2.1201, 03:41:29
	Im>*    56.56.56.0/30 [115/30] via 14.14.14.2, bundle-2.1202, 03:41:09
	  *                           via 12.12.12.2, bundle-2.1201, 03:41:09

.. **Help line:** Show the complete multicast rpf route table.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
