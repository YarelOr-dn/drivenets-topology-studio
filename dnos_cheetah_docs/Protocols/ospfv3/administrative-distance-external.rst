protocols ospfv3 administrative-distance external
-------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance external [administrative-distance-external]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+----------------------------------+----------------------------------------------------------+-------+---------+
| Parameter                        | Description                                              | Range | Default |
+==================================+==========================================================+=======+=========+
| administrative-distance-external | Set the administrative distance for ospf external routes | 1-255 | \-      |
+----------------------------------+----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance external 120


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance external

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
