protocols ospfv3 area interface bfd multiplier
----------------------------------------------

**Minimum user role:** operator

To set the OSPFv3 BFD minimum receive interval for the interface:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface bfd

**Note**
- The 'no' command returns to the default settings.

**Parameter table**

+------------+--------------------------+-------+---------+
| Parameter  | Description              | Range | Default |
+============+==========================+=======+=========+
| multiplier | set local BFD multiplier | 2-16  | \-      |
+------------+--------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# bfd
    dnRouter(cfg-ospfv3-area-if-bfd)# multiplier 2


**Removing Configuration**

To return to the default value:
::

    dnRouter(cfg-ospfv3-area-if-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
