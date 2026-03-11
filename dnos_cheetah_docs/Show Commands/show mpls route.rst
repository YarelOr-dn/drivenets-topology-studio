show mpls route
---------------

**Minimum user role:** viewer

The show mpls route commands displays LDP routing and forwarding table information, as follows. The MPLS routing and forwarding tables are subsets of the general routing and forwarding tables (show route and show route forwarding-table respectively).



**Command syntax: show mpls route** [mpls-label]

**Command mode:** operational



.. **Note**

	- unified "show mpls route" = quagga's "show mpls table"

**Parameter table**

+------------+---------------------------------------+-------------+---------+
| Parameter  | Description                           | Range       | Default |
+============+=======================================+=============+=========+
| mpls-label | Filters the information by mpls-label | 16..1048575 | \-      |
+------------+---------------------------------------+-------------+---------+

The following information is displayed on each route:

+-----------+-------------------------------------------+
| Attribute | Description                               |
+===========+===========================================+
| Flags     | L - LDP                                   |
|           | > - Indicates a selected route            |
|           | * - indicates an installed route (in RIB) |
|           | (L) - over limit route                    |
+-----------+-------------------------------------------+
| IP Prefix | The prefix of the route                   |
+-----------+-------------------------------------------+
| Next Hop  | The next-hop                              |
+-----------+-------------------------------------------+
| Label     | The label used                            |
+-----------+-------------------------------------------+
| Uptime    | The amount of time that the route exists  |
+-----------+-------------------------------------------+

**Example**
::

	dnRouter# show mpls route
	Codes: S - static, B - BGP, L - LDP, R - RSVP, I - IS-IS,
        I-SR - IS-IS Segment-Routing, O-SR - OSPF Segment-Routing,
        SRTE - Segment-Routing TE,
       > - selected route, * - FIB route, (S) - stale route
       (L) - over limit route

	R>*    70006 [100/0] via TUNNEL1, 04:54:58
	L>*    91550 [105/0] via 1.7.18.2, bundle-1.3986 label 39009, 06:54:58

	dnRouter# show mpls route
	Codes: S - static, B - BGP, L - LDP, R - RSVP, I - IS-IS, I-SR - IS-IS Segment-Routing
       > - selected route, * - FIB route, (S) - stale route
       (L) - over limit route

	I-SR>*    8001 [115/20] via 1.18.151.97, bundle-1.177 label 20009, 04:54:58


.. **Help line:** show mpls route

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 5.1.0   | Command introduced                              |
+---------+-------------------------------------------------+
| 9.0     | Updated command output                          |
+---------+-------------------------------------------------+
| 13.0    | Updated command output and range value          |
+---------+-------------------------------------------------+
| 14.0    | Added segment-routing information in the output |
+---------+-------------------------------------------------+
| 15.0    | Added LDP label information in the output       |
+---------+-------------------------------------------------+


