protocols ospf instance area interface bfd min-rx
-------------------------------------------------

**Minimum user role:** operator

To set the OSPF BFD minimum receive interval for the interface:

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface bfd

**Note**
- 'no' command returns to default settings

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# bfd
    dnRouter(cfg-ospf-area-if-bfd)# min-rx 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-ospf-area-if-bfd)# no min-rx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
