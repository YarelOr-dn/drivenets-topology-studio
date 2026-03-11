protocols bgp neighbor cluster-id
---------------------------------

**Minimum user role:** operator

You can use this command to specify a global cluster-id attribute when used as a route-reflector, or per neighbor-group or neighbor if specified explicitly.

Prior to reflecting a route, route reflectors append their cluster-id to the cluster list.

If two routers share the same BGP cluster ID, they belong to the same cluster.

**Command syntax: cluster-id [cluster-id]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor
- protocols bgp
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor

**Parameter table**

+------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter  | Description                                                                      | Range            | Default |
+============+==================================================================================+==================+=========+
| cluster-id | route-reflector cluster id to use when local router is configured as a route     | | 1-4294967295   | \-      |
|            | reflector.                                                                       | | A.B.C.D        |         |
+------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# cluster-id 65.65.65.65

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65001
    dnRouter(cfg-protocols-bgp)# cluster-id 100

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65001
    dnRouter(cfg-protocols-bgp)# neighbor 1.1.1.1
    dnRouter(cfg-protocols-bgp-neighbor)# cluster-id 101

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# cluster-id 10.0.0.1

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# cluster-id 27081


**Removing Configuration**

To revert all BGP cluster-id to the default value:
::

    dnRouter(cfg-protocols-bgp)# no cluster-id

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 15.1    | Command introduced                                           |
+---------+--------------------------------------------------------------+
| 17.1    | Extended support for neighbor and neighbor-group hierarchies |
+---------+--------------------------------------------------------------+
