protocols segment-routing mpls path segment-list hop include prefix-sid index
-----------------------------------------------------------------------------

**Minimum user role:** operator

The segment-list hop represents a single segment within the path. Each hop is associated with a specific label, a prefix-SID index, or a prefix-SID IPv4-address. You can configure up to 5 segments per segment-list.

To configure a segment-list hop:


**Command syntax: hop [hop] include prefix-sid index [include-index]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path segment-list

**Note**
Required validations:

- The index must be within the configured SRGB range.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter     | Description                                                                      | Range    | Default |
+===============+==================================================================================+==========+=========+
| hop           | Hop identifier. The segment list path is defined according to the hop order.     | 1-9      | \-      |
|               | Lowest value will be the first hop                                               |          |         |
+---------------+----------------------------------------------------------------------------------+----------+---------+
| include-index | Configure the SID index for the associated hop                                   | 0-999999 | \-      |
+---------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# segment-list 1
    dnRouter(cfg-mpls-path-sl)# hop 2 prefix-sid include index 2


**Removing Configuration**

To remove a specific hop from the segment-list:
::

    dnRouter(cfg-mpls-path-sl)# no hop 2

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 15.0    | Command introduced       |
+---------+--------------------------+
| 18.1    | Extend support to 9 hops |
+---------+--------------------------+
