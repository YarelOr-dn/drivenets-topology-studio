protocols segment-routing mpls path dynamic constraints metric
--------------------------------------------------------------

**Minimum user role:** operator


To enter metric configuration level of dynamic path constraints and set metric related constraints:

**Command syntax: metric**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

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
    dnRouter(cfg-dynamic-constraints-metric)#


**Removing Configuration**

To revert all dynamic path metric constraints configurations to default:
::

    dnRouter(cfg-path-dynamic-constraints)# metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
