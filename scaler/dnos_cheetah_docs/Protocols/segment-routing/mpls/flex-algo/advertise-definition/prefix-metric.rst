protocols segment-routing mpls flex-algo advertise-definition prefix-metric
---------------------------------------------------------------------------

**Minimum user role:** operator

Set prefix metric flag in flex algorithm definition. When set, specific prefix and ASBR metric must be used for inter-area end external prefix calculation. If specific metric is not provided (Flexible Algorithm Prefix Metric Sub-TLV type 3) inter-area/external prefix will be rejected from flex-algo topology
For ISIS inter-area prefix are propagated prefixes from Level-2 to Level-1
For OSPF inter-area prefix are summary prefixes advertised by ABR
For ISIS & OSPF, external prefixes are redistributed prefixes

**Command syntax: prefix-metric [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo advertise-definition

**Note**

- the FAD's prefix metric option is a shared feature between OSPF and ISIS; When configuring the prefix metric it will be set for both OSPF and ISIS, and while this is not yet implemented in ISIS, ISIS will ignore this option with no side-effects.

**Parameter table**

+-------------+--------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                              | Range        | Default  |
+=============+==========================================================================+==============+==========+
| admin-state | Set prefix metric flag in flex algorithm definition, default is disabled | | enabled    | disabled |
|             |                                                                          | | disabled   |          |
+-------------+--------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)# prefix-metric enabled


**Removing Configuration**

To revert prefix-metric to default behavior:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no prefix-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
