protocols segment-routing mpls policy administrative-distance
-------------------------------------------------------------

**Minimum user role:** operator

Administrative distance is an arbitrary numerical value that is assigned to routes to allow the router to decide which routing protocol to select for installation in the FIB and for route resolution for protocol next-hop when multiple protocols provide route information for the same destination. The assigned value denotes the preference of the route compared to other routes, such that a lower value denotes a more preferred route.

To configure the segment-routing traffic-engineering administrative distance for the specific policy:


**Command syntax: administrative-distance [administrative-distance]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Note**
-  An administrative distance of 255 will cause the router to remove the route from the routing table and not use it.

-  Reconfiguration of administrative-distance will take immediate effect.


**Parameter table**

+-------------------------+-------------------------------------------------------------------------+-------+---------+
| Parameter               | Description                                                             | Range | Default |
+=========================+=========================================================================+=======+=========+
| administrative-distance | Sets the Segment-Routing administrative-distance used for SR-TE policy. | 1-255 | \-      |
+-------------------------+-------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy POL_1
    dnRouter(cfg-sr-mpls-policy)# administrative-distance 90


**Removing Configuration**

To return to the default value:
::

    dnRouter(cfg-sr-mpls-policy)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
