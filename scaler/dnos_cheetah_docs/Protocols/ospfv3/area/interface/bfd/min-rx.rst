protocols ospfv3 area interface bfd min-rx
------------------------------------------

**Minimum user role:** operator

To set the OSPFv3 BFD minimum receive interval for the interface:

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface bfd

**Note**
- The 'no' command returns to the default settings.

**Parameter table**

+-----------+------------------------------------------------------+--------+---------+
| Parameter | Description                                          | Range  | Default |
+===========+======================================================+========+=========+
| min-rx    | set desired minimum receive interval for BFD session | 5-1700 | \-      |
+-----------+------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# bfd
    dnRouter(cfg-ospfv3-area-if-bfd)# min-rx 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-ospfv3-area-if-bfd)# no min-rx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
