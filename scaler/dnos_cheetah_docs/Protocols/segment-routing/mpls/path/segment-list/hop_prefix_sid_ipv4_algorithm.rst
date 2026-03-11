protocols segment-routing mpls path segment-list hop include prefix-sid ipv4-address
------------------------------------------------------------------------------------

**Minimum user role:** operator

The segment-list hop represents a single segment within the path. Each hop is associated with a specific label, a prefix-SID index, or a prefix-SID IPv4-address. You can configure up to 5 segments per segment-list.

To configure a segment-list hop:


**Command syntax: hop [hop] include prefix-sid ipv4-address [include-ipv4-address] [algorithm]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path segment-list

**Note**
Required validations:

- The ipv4-address must be a legal unicast ipv4 address, i.e not a multicast of broadcast address.


**Parameter table**

+----------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter            | Description                                                                      | Range   | Default |
+======================+==================================================================================+=========+=========+
| hop                  | Hop identifier. The segment list path is defined according to the hop order.     | 1-9     | \-      |
|                      | Lowest value will be the first hop                                               |         |         |
+----------------------+----------------------------------------------------------------------------------+---------+---------+
| include-ipv4-address | Configure a given address. DNOS will resolve the given address to the matching   | A.B.C.D | \-      |
|                      | SID according to SR DB                                                           |         |         |
+----------------------+----------------------------------------------------------------------------------+---------+---------+
| algorithm            | algorithm associated with the prefix to match the SID                            | \-      | \-      |
+----------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# segment-list 1
    dnRouter(cfg-mpls-path-sl)# hop 1 include prefix-sid ipv4-address 1.2.3.4 spf


**Removing Configuration**

To remove a specific hop from the segment-list:
::

    dnRouter(cfg-mpls-path-sl)# no hop 1

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 15.0    | Command introduced                |
+---------+-----------------------------------+
| 18.1    | Extend support to 9 hops          |
+---------+-----------------------------------+
| 18.1    | Add algorithm flex-algo id option |
+---------+-----------------------------------+
