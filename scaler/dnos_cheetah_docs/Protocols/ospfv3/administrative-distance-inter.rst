protocols ospfv3 administrative-distance inter-area
---------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance inter-area [administrative-distance-inter-area]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+------------------------------------+------------------------------------------------------------+-------+---------+
| Parameter                          | Description                                                | Range | Default |
+====================================+============================================================+=======+=========+
| administrative-distance-inter-area | Set the administrative distance for ospf inter-area routes | 1-255 | \-      |
+------------------------------------+------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance inter-area 200


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance inter-area

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
