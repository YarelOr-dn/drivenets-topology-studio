protocols segment-routing mpls path segment-list hop include adjacency-sid
--------------------------------------------------------------------------

**Minimum user role:** operator

The segment-list hop represents a single segment within the path. Each hop is associated with a specific label, a prefix-SID index, or a prefix-SID IPv4-address. You can configure up to 5 segments per segment-list.

To configure a segment-list hop:


**Command syntax: hop [hop] include adjacency-sid [include-adjacency-sid]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path segment-list

**Note**

- This command may also be invoked inside the mesh-group peer or inside the default-peer configuration hierarchy.

- The hold-time timer must be greater than the hop timer. The user is warned in case the hop timer is greater or equal to the hold-time.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter             | Description                                                                      | Range        | Default |
+=======================+==================================================================================+==============+=========+
| hop                   | Hop identifier. The segment list path is defined according to the hop order.     | 1-9          | \-      |
|                       | Lowest value will be the first hop                                               |              |         |
+-----------------------+----------------------------------------------------------------------------------+--------------+---------+
| include-adjacency-sid | Add adjacency SID to policy path according to the matching inteface local ipv4   | | A.B.C.D    | \-      |
|                       | address (of either local or remote node)                                         | | X:X::X:X   |         |
+-----------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# segment-list 1
    dnRouter(cfg-mpls-path-sl)# hop 2 include adjacency-sid 1.1.1.1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# segment-list 1
    dnRouter(cfg-mpls-path-sl)# hop 2 include adjacency-sid 2001:77:44::1


**Removing Configuration**

To remove a specific hop from the segment-list:
::

    dnRouter(cfg-mpls-path-sl)# no hop 2

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 15.0    | Command introduced                                       |
+---------+----------------------------------------------------------+
| 17.0    | Add adjacency-sid hop option                             |
+---------+----------------------------------------------------------+
| 18.2    | Extend support to 9 hops. Add support for ipv6 adjacency |
+---------+----------------------------------------------------------+
