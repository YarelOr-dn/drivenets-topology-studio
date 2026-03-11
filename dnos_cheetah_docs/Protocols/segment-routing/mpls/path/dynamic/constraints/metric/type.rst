protocols segment-routing mpls path dynamic constraints metric type
-------------------------------------------------------------------

**Minimum user role:** operator


Metric-type indicates which is the corresponding metric to be used for shortest path calculation.
igp - IGP metric is used during the calculation.
link-delay - Min Unidirectional Link Delay as defined in [RFC7810] is used during the calculation.
te - TE default metric as defined in [RFC5305] is used during the calculation.
By default, DNOS will calculate best path according to metric type defined by used algorithm
To configure metric-type behavior:

**Command syntax: type [metric-type]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints metric

**Parameter table**

+-------------+-------------------------------------------------------------------------+----------------+---------+
| Parameter   | Description                                                             | Range          | Default |
+=============+=========================================================================+================+=========+
| metric-type | Indicates which metric type to be used in lowest cost path calculations | | igp          | \-      |
|             |                                                                         | | link-delay   |         |
|             |                                                                         | | te           |         |
+-------------+-------------------------------------------------------------------------+----------------+---------+

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
    dnRouter(cfg-dynamic-constraints-metric)# type te


**Removing Configuration**

To revert metric type to default behavior:
::

    dnRouter(cfg-dynamic-constraints-metric)# no type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
