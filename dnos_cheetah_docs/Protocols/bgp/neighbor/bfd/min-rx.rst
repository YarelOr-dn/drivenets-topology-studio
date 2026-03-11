protocols bgp neighbor bfd min-rx
---------------------------------

**Minimum user role:** operator

Set the desired minimum receive interval for the BFD session for a single neighbor or neighbor group:

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor bfd
- protocols bgp neighbor-group bfd
- protocols bgp neighbor-group neighbor bfd
- network-services vrf instance protocols bgp neighbor bfd
- network-services vrf instance protocols bgp neighbor-group bfd
- network-services vrf instance protocols bgp neighbor-group neighbor bfd

**Note**

- This could be invoked inside a neighbor-group or as a single neighbor.

- Neighbors within a neighbor-group derive the neighbor-group configuration or can have a unique setting from the group.

- For neighbors within a neighbor-group, the default value is the group's parameter value.

**Parameter table**

+-----------+------------------------------------------------------+--------+---------+
| Parameter | Description                                          | Range  | Default |
+===========+======================================================+========+=========+
| min-rx    | set desired minimum receive interval for BFD session | 5-1700 | 300     |
+-----------+------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bfd
    dnRouter(cfg-bgp-neighbor-bfd)# min-rx 400
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# min-rx 400
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# min-rx 400
    dnRouter(cfg-bgp-group-bfd)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# bfd
    dnRouter(cfg-group-neighbor-bfd)# min-rx 300


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-bgp-neighbor-bfd)# no min-rx

::

    dnRouter(cfg-bgp-group-bfd)# no min-rx

::

    dnRouter(cfg-group-neighbor-bfd)# no min-rx

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.4    | Command introduced               |
+---------+----------------------------------+
| 15.1    | Added support for 5msec interval |
+---------+----------------------------------+
