protocols segment-routing mpls path dynamic constraints metric limit
--------------------------------------------------------------------

**Minimum user role:** operator

To define an upper bound limit for a given metric type, which a dynamic calculated path must honor:

**Command syntax: limit [metric type]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints metric

**Parameter table**

+-------------+-------------------------------------------+----------------+---------+
| Parameter   | Description                               | Range          | Default |
+=============+===========================================+================+=========+
| metric type | metric type over which limits are imposed | | igp          | \-      |
|             |                                           | | link-delay   |         |
|             |                                           | | te           |         |
+-------------+-------------------------------------------+----------------+---------+

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
    dnRouter(cfg-dynamic-constraints-metric)# limit igp
    dnRouter(cfg-constraints-metric-limit)#


**Removing Configuration**

To remove the limit for a given metric type:
::

    dnRouter(cfg-dynamic-constraints-metric)# no limit igp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
