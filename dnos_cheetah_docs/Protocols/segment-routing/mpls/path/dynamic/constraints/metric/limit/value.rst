protocols segment-routing mpls path dynamic constraints metric limit value
--------------------------------------------------------------------------

**Minimum user role:** operator


To set metric limit value:

**Command syntax: value [value]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints metric limit

**Parameter table**

+-----------+-----------------------------------+--------------+---------+
| Parameter | Description                       | Range        | Default |
+===========+===================================+==============+=========+
| value     | metric upper bound absolute value | 1-4294967295 | \-      |
+-----------+-----------------------------------+--------------+---------+

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
    dnRouter(cfg-constraints-metric-limit)# value 200010


**Removing Configuration**

To remove value:
::

    dnRouter(cfg-constraints-metric-limit)# no value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
