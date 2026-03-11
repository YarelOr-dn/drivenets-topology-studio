protocols ospfv3 administrative-distance
----------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance [administrative-distance]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+-------------------------+------------------------------------------+-------+---------+
| Parameter               | Description                              | Range | Default |
+=========================+==========================================+=======+=========+
| administrative-distance | Set the administrative distance for ospf | 1-255 | 110     |
+-------------------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance 20
    dnRouter(cfg-protocols-ospfv3)# administrative-distance external 22
    dnRouter(cfg-protocols-ospfv3)# administrative-distance inter-area 25
    dnRouter(cfg-protocols-ospfv3)# administrative-distance intra-area 30


**Removing Configuration**

To revert administrative distances to the default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
