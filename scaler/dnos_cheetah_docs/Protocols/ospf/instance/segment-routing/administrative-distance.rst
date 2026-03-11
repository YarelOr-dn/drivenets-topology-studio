protocols ospf instance segment-routing administrative-distance
---------------------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, the administrative distance will be compared and the preference will be given to the routes with the lower administrative distance.
This setting affects which protocol is preferred in mpls-nexthop table in the RIB.

To configure the administrative distance for OSPF segment routing:

**Command syntax: administrative-distance [administrative-distance]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance segment-routing

**Parameter table**

+-------------------------+--------------------------------------------------+-------+---------+
| Parameter               | Description                                      | Range | Default |
+=========================+==================================================+=======+=========+
| administrative-distance | Set AD for OSPF-SR routes (mpls-nh & mpls table) | 1-255 | 107     |
+-------------------------+--------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# segment-routing
    dnRouter(cfg-protocols-ospf-sr)# administrative-distance 120


**Removing Configuration**

To revert the administrative-distance to its default value:
::

    dnRouter(cfg-protocols-ospf-sr)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
