protocols ospf instance area bfd multiplier
-------------------------------------------

**Minimum user role:** operator

To set the OSPF BFD default multiplier for the area:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area bfd

**Note**
- 'no' command returns to default settings

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-ospf-area)# bfd
    dnRouter(cfg-ospf-area-bfd)# multiplier 2


**Removing Configuration**

To return to the default value:
::

    dnRouter(cfg-ospf-area-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
