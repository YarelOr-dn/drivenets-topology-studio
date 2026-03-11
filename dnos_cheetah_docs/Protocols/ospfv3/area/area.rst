protocols ospfv3 area
---------------------

**Minimum user role:** operator

To set an OSPFV3 area ID and enter its configuration mode:

**Command syntax: area [area-id]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- No command disables the ospfv3 process for the specified area.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| area-id   | An identifier for the OSPFv3 area - described as either a 32-bit unsigned        | \-    | \-      |
|           | integer, or a dotted-quad                                                        |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)#
    dnRouter(cfg-protocols-ospfv3)# area 0.0.0.0
    dnRouter(cfg-protocols-ospfv3-area)#


**Removing Configuration**

To disable the ospfv3 process for the specified area:
::

    dnRouter(cfg-protocols-ospfv3)# no area 0.0.0.0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
