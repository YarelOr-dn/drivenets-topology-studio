protocols isis instance interface level
---------------------------------------

**Minimum user role:** operator

ISs that are configured as Level-1-2 may have multiple interfaces for various routing levels. For example, focusing on Area 1 in the following diagram, R3, which is a Level-1-2 IS, has 4 interfaces: 2 interfaces towards R1 and R2 for routing within Area 1 (indicated by the blue lines), 1 interface facing R5 in Area 2 for routing between Area 1 and Area 2, and a fourth interface facing R4, another Level-1-2 IS within Area 1. The R3-R4 link must allow both level-1 routing to enable traffic within Area 1 (as indicated by the blue dashed arrow) and also level-2 routing to enable traffic between the areas (as indicated by the orange dashed arrow). In this case, you would configure the R1- and R2-facing interfaces to circuit-type level-1 in order to form only level-1 adjacencies. Similarly, the R5-facing interface would be configured to form only level-2 adjacencies, while the R4-facing interface would be configured to form level-1-2 adjacencies to enable both routing levels.

A level-1 adjacency can only be formed when both routers are working in level-1 and both share the same Area-ID and prefix portion of the router IS-IS ISO-network.

To configure an interface to support a specific adjacency level:

**Command syntax: level [level]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Note**

- You cannot set a level for loopback interfaces. For loopback interfaces, the interface level is always according to the IS-IS level within the same IS-IS instance.

**Parameter table**

+-----------+--------------------------------------------------------------+---------------+-----------+
| Parameter | Description                                                  | Range         | Default   |
+===========+==============================================================+===============+===========+
| level     | Sets the interface to support the specified adjacency level. | | level-1     | level-1-2 |
|           |                                                              | | level-2     |           |
|           |                                                              | | level-1-2   |           |
+-----------+--------------------------------------------------------------+---------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# level level-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# level level-2

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# level level-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-3
    dnRouter(cfg-isis-inst-if)# level level-1


**Removing Configuration**

To revert to the default interface level:
::

    dnRouter(cfg-isis-inst-if)# no level

**Command History**

+---------+------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                               |
+=========+============================================================================================================+
| 6.0     | Command introduced                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------+
| 9.0     | Removed level-1 and level-1-2 routing, changed   the argument in the syntax from "circuit-type" to "level" |
+---------+------------------------------------------------------------------------------------------------------------+
| 14.0    | Added support for level-1-2 (default changed to level-1-2)                                                 |
+---------+------------------------------------------------------------------------------------------------------------+
