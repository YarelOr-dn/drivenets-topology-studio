protocols ospf instance area interface bfd multiplier
-----------------------------------------------------

**Minimum user role:** operator

To set the OSPF BFD minimum receive interval for the interface:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface bfd

**Note**
- 'no' command returns to default settings

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# bfd
    dnRouter(cfg-ospf-area-if-bfd)# multiplier 2


**Removing Configuration**

To return to the default value:
::

    dnRouter(cfg-ospf-area-if-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
