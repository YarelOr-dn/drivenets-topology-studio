protocols segment-routing mpls path segment-list hop include prefix-sid ipv6-address
------------------------------------------------------------------------------------

**Minimum user role:** operator

The segment-list hop represents a single segment within the path. Each hop is associated with a specific label, a prefix-SID index, or a prefix-SID IPv6-address. You can configure up to 5 segments per segment-list.

To configure a segment-list hop:


**Command syntax: hop [hop] include prefix-sid ipv6-address [include-ipv6-address] [algorithm-ipv6]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path segment-list

**Note**
Required validations:

- The ipv6-address must be a legal unicast ipv6 address, i.e not a multicast of a broadcast address.


**Parameter table**

+----------------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter            | Description                                                                      | Range    | Default |
+======================+==================================================================================+==========+=========+
| hop                  | Hop identifier. The segment list path is defined according to the hop order.     | 1-9      | \-      |
|                      | Lowest value will be the first hop                                               |          |         |
+----------------------+----------------------------------------------------------------------------------+----------+---------+
| include-ipv6-address | Configure a given address. DNOS will resolve the given address to the matching   | X:X::X:X | \-      |
|                      | SID according to SR DB                                                           |          |         |
+----------------------+----------------------------------------------------------------------------------+----------+---------+
| algorithm-ipv6       | algorithm associated with the prefix to match the SID                            | \-       | \-      |
+----------------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# segment-list 1
    dnRouter(cfg-mpls-path-sl)# hop 1 include prefix-sid ipv6-address 1:1::1::1 spf


**Removing Configuration**

To remove a specific hop from the segment-list:
::

    dnRouter(cfg-mpls-path-sl)# no hop 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
