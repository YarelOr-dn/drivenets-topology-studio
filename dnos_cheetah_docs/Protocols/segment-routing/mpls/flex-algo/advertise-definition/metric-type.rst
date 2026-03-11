protocols segment-routing mpls flex-algo advertise-definition metric-type
-------------------------------------------------------------------------

**Minimum user role:** operator


Metric-type indicates which is the corresponding metric to be used for this algorithm in path calculations.
igp - IGP metric is used during the calculation. IGP is a default metric-type.
link-delay - Min Unidirectional Link Delay as defined in [RFC7810] is used during the calculation.
te - TE default metric as defined in [RFC5305] is used during the calculation.
To configure metric-type behavior:

**Command syntax: metric-type [metric-type]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo advertise-definition

**Parameter table**

+-------------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter   | Description                                                                      | Range          | Default |
+=============+==================================================================================+================+=========+
| metric-type | Indicates which is the corresponding metric type for this algorithm, default is  | | igp          | igp     |
|             | IGP                                                                              | | link-delay   |         |
|             |                                                                                  | | te           |         |
+-------------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)# metric-type te


**Removing Configuration**

To revert metric-type to default behavior:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no metric-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
