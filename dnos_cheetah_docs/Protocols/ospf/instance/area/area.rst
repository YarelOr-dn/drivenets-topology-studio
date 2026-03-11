protocols ospf instance area
----------------------------

**Minimum user role:** operator

DNOS supports participating in the OSPFv2 backbone area (Area 0), non-backbone areas (Other than area 0), backbone-area (Area 0, in multiple areas – acting as an area border router), and NSSa and stub areas. 
NSSA and stub are supported both for ABR roles and for non-ABR roles.
To set an OSPF area ID and enter its configuration mode:

**Command syntax: area [area-id]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- No command disables the ospf process for the specified area.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| area-id   | An identifier for the OSPFv2 area - described as either a 32-bit unsigned        | \-    | \-      |
|           | integer, or a dotted-quad                                                        |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)#
    dnRouter(cfg-protocols-ospf)# area 0.0.0.0
    dnRouter(cfg-protocols-ospf-area)#


**Removing Configuration**

To disable the ospf process for the specified area:
::

    dnRouter(cfg-protocols-ospf)# no area 0.0.0.0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
