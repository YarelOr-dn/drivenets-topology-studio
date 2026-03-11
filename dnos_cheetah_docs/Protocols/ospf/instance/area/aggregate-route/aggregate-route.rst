protocols ospf instance area aggregate-route
--------------------------------------------

**Minimum user role:** operator

The aggregate route is advertised as an inter-area route. Aggregation reduces the number of inter-area routes, by advertising shorter summary routes to other areas.
The summarizing ABR node will create an aggregate route with a next-hop null 0 (discard) in the OSPFv2 routing table and advertise it when a more specific intra-area route exists in OSPF.
To create route aggregation:

**Command syntax: aggregate-route [ipv4-prefix]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Parameter table**

+-------------+-------------------------------+-----------+---------+
| Parameter   | Description                   | Range     | Default |
+=============+===============================+===========+=========+
| ipv4-prefix | IP aggregation summary prefix | A.B.C.D/x | \-      |
+-------------+-------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# aggregate-route 3.3.0.0/16
    dnRouter(cfg-ospf-area-aggregate)#


**Removing Configuration**

To remove route aggregation:
::

    dnRouter(cfg-protocols-ospf-area)# no aggregate-route 3.3.0.0/16

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
