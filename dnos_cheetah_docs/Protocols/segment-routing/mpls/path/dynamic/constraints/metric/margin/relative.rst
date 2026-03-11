protocols segment-routing mpls path dynamic constraints metric margin relative
------------------------------------------------------------------------------

**Minimum user role:** operator


To set metric margin as relative value from best path accumulated metric:

**Command syntax: relative [relative]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints metric margin

**Parameter table**

+-----------+-----------------------------------------------------+-------+---------+
| Parameter | Description                                         | Range | Default |
+===========+=====================================================+=======+=========+
| relative  | margin by relative percent above shortest path cost | 1-100 | \-      |
+-----------+-----------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# constraints
    dnRouter(cfg-path-dynamic-constraints)# metric
    dnRouter(cfg-dynamic-constraints-metric)# margin
    dnRouter(cfg-constraints-metric-margin)# relative 10


**Removing Configuration**

To remove relative metric margin:
::

    dnRouter(cfg-constraints-metric-margin)# no relative

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
