show route pending-fib-install
------------------------------

**Minimum user role:** viewer

Use the following command syntax to display route that are expected to be installed to FIB and are pending successful installation:

**Command syntax: show route** {vrf [vrf-name] | all} table [table] **pending-fib-install**

**Command mode:** operational


**Note**

- By default, the command output displays ipv4-unicast, ipv6-unicast. Use the table filter to display a specific table.



**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Parameter |                                                                                  Description                                                                                  |      Range     |
+===========+===============================================================================================================================================================================+================+
| table     | Displays only the specified table (where applicable, [vrf-name] is used).                                                                                                     | IPv4-unicast   |
|           | If you do not specify a table, all will be displayed.                                                                                                                         | IPv6-unicast   |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| vrf-name  | Displays the routing table for the specified VRF. If not specified, routes for the default VRF are displayed. When 'all' is specified as the VRF, then each VRF is displayed. | String | all   |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+

The following information is displayed on each route:

+-------------------+------------------------------------------------------+
| Attribute         | Description                                          |
+===================+======================================================+
| Flags             | K - kernel route                                     |
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

    dnRouter# show route pending-fib-install

    VRF: default
    IPv4 Route Table:
    Codes: K - kernel route, C - connected, S - static, r - RIP,
        O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
        L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
        O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
        EVI - EVI,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    B>            17.17.17.17/32 [200/0] via 30.30.30.30 (recursive), 00:00:01
    *                                    via tunnel1, 00:00:01

    IPv6 Route Table:
    Codes: K - kernel route, C - connected, S - static, r - RIPng,
        O - OSPFv3, I - IS-IS, B - BGP, A - Babel, D - BFD,
        L - LDP, R - RSVP, I-SR - IS-IS Segment-Routing,
        SRTE - Segment-Routing TE, EVI - EVI,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    B>            33::33/128 [200/0] via 30::30 (recursive), 00:07:20
    *                                via fe80::7411:b9ff:fecb:a94f, vdev_3, 00:07:20

    dnRouter# show route table ipv4-unicast pending-fib-install

    Codes: K - kernel route, C - connected, S - static, r - RIP,
        O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
        L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
        O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
        EVI - EVI,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    B>            17.17.17.17/32 [200/0] via 30.30.30.30 (recursive), 00:00:01
    *                                    via tunnel1, 00:00:01

    dnRouter# show route table ipv6-unicast pending-fib-install

    Codes: K - kernel route, C - connected, S - static, r - RIPng,
        O - OSPFv3, I - IS-IS, B - BGP, A - Babel, D - BFD,
        L - LDP, R - RSVP, I-SR - IS-IS Segment-Routing,
        SRTE - Segment-Routing TE, EVI - EVI,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    B>            33::33/128 [200/0] via 30::30 (recursive), 00:07:20
    *                                via fe80::7411:b9ff:fecb:a94f, vdev_3, 00:07:20

    dnRouter# show route vrf vrf_1 pending-fib-install

    VRF: vrf_1
    IPv4 Route Table:
    Codes: K - kernel route, C - connected, S - static, r - RIP,
        O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
        L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
        O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
        EVI - EVI,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    B>*    25.0.0.0/24 [20/0] via 20.0.0.2, ge100-0/0/0.100, 03:41:36


    dnRouter# show route vrf vrf_1 table ipv4-unicast pending-fib-install

    VRF: vrf_1
    Codes: K - kernel route, C - connected, S - static, r - RIP,
        O - OSPF, I - IS-IS, B - BGP, P - PIM, A - Babel, D - BFD,
        L - LDP, R - RSVP, M - OAM, I-SR - IS-IS Segment-Routing,
        O-SR - OSPF Segment-Routing, SRTE - Segment-Routing TE,
        EVI - EVI,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    B>*    25.0.0.0/24 [20/0] via 20.0.0.2, ge100-0/0/0.100, 03:41:36


    dnRouter# show mpls route pending-fib-install

    Codes: S - static, B - BGP, L - LDP, R - RSVP, I - IS-IS,
        I-SR - IS-IS Segment-Routing, O-SR - OSPF Segment-Routing,
        SRTE - Segment-Routing TE,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    R>*           257 [100/0] via tunnel1, 00:02:25

.. **Help line:** show routing table

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
