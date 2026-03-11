protocols segment-routing mpls path dynamic constraints metric margin
---------------------------------------------------------------------

**Minimum user role:** operator


To support multiple paths of unequal cost, set allowed margin from overall best path (lowest cost):

**Command syntax: margin**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints metric

**Note**

- The allowed margin will be consumed first by hops that are closer to the source node Resulting that DNOS ECMP finding using “margin” will might be sub optimal and not find all possible paths that meet metric+margin constraint.

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
    dnRouter(cfg-constraints-metric-margin)#


**Removing Configuration**

To revert all margin configurations to default:
::

    dnRouter(cfg-dynamic-constraints-metric)# no margin

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
