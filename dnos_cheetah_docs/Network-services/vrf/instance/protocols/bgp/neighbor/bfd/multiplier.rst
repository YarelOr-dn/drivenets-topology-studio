network-services vrf instance protocols bgp neighbor bfd multiplier
-------------------------------------------------------------------

**Minimum user role:** operator

Set the local BFD multiplier for a single neighbor or neighbor group:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor bfd
- protocols bgp neighbor bfd
- protocols bgp neighbor-group bfd
- protocols bgp neighbor-group neighbor bfd
- network-services vrf instance protocols bgp neighbor-group bfd
- network-services vrf instance protocols bgp neighbor-group neighbor bfd

**Note**

- This could be invoked inside a neighbor-group or as a single neighbor.

- Neighbors within a neighbor-group derive the neighbor-group configuration or can have a unique setting from the group.

- For neighbors within a neighbor-group, the default value is the group's parameter value.

**Parameter table**

+------------+--------------------------+-------+---------+
| Parameter  | Description              | Range | Default |
+============+==========================+=======+=========+
| multiplier | set local BFD multiplier | 2-16  | 3       |
+------------+--------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bfd
    dnRouter(cfg-bgp-neighbor-bfd)# multiplier 2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# multiplier 2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# multiplier 2
    dnRouter(cfg-bgp-group-bfd)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# bfd
    dnRouter(cfg-group-neighbor-bfd)# multiplier 3


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-bgp-neighbor-bfd)# no multiplier

::

    dnRouter(cfg-bgp-group-bfd)# no multiplier

::

    dnRouter(cfg-group-neighbor-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
