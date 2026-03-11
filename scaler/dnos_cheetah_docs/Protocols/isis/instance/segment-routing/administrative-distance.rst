protocols isis instance segment-routing administrative-distance
---------------------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance. This setting affects which protocol is preferred in mpls-nexthop table in the RIB.

To configure the administrative distance for IS-IS segment routing:

**Command syntax: administrative-distance [admin-distance]**

**Command mode:** config

**Hierarchies**

- protocols isis instance segment-routing

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| admin-distance | Sets the administrative distance for IS-IS segment-routing. A value of 255 will  | 1-255 | 107     |
|                | cause the router to remove the route from the routing table.                     |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# segment-routing
    dnRouter(cfg-isis-inst-sr)# administrative-distance 103


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-isis-inst-sr)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
