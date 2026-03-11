protocols ospfv3 area bfd multiplier
------------------------------------

**Minimum user role:** operator

To set the OSPFv3 BFD default multiplier for the area:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area bfd

**Note**
- The 'no' command returns to the default settings.

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
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-ospfv3-area)# bfd
    dnRouter(cfg-ospfv3-area-bfd)# multiplier 2


**Removing Configuration**

To return to the default value:
::

    dnRouter(cfg-ospfv3-area-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
