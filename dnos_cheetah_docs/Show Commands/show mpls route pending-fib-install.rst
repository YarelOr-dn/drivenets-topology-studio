show mpls route pending-fib-install
-----------------------------------

**Minimum user role:** viewer

The show mpls routes that are expected to be installed to FIB and are pending successful installation.

**Command syntax: show mpls route pending-fib-install**

**Command mode:** operational



**Parameter table**

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

    dnRouter# show mpls route pending-fib-install

    Codes: S - static, B - BGP, L - LDP, R - RSVP, I - IS-IS,
        I-SR - IS-IS Segment-Routing, O-SR - OSPF Segment-Routing,
        SRTE - Segment-Routing TE,
        > - selected route, * - FIB route, (S) - stale route
        (L) - over limit route, ! - partial MPLS shortcut, m - Multicast
        L1 - IS-IS level-1, L2 - IS-IS level-2, su - summary route

    R>*           257 [100/0] via tunnel1, 00:02:25

.. **Help line:** show mpls route

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 17.1    | Command introduced                              |
+---------+-------------------------------------------------+
