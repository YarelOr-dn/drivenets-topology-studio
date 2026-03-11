protocols ospf instance administrative-distance intra-area
----------------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.

To change the OSPF administrative distance for all routes:

**Command syntax: administrative-distance intra-area [administrative-distance-intra-area]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it

**Parameter table**

+------------------------------------+------------------------------------------------------------+-------+---------+
| Parameter                          | Description                                                | Range | Default |
+====================================+============================================================+=======+=========+
| administrative-distance-intra-area | Set the administrative distance for ospf intra-area routes | 1-255 | \-      |
+------------------------------------+------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# administrative-distance intra-area 150


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-ospf)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-ospf)# no administrative-distance intra-area

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
