protocols segment-routing mpls path dynamic constraints metric margin absolute
------------------------------------------------------------------------------

**Minimum user role:** operator


To set absolute metric margin:

**Command syntax: absolute [absolute]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints metric margin

**Parameter table**

+-----------+-------------------------------------------------+--------------+---------+
| Parameter | Description                                     | Range        | Default |
+===========+=================================================+==============+=========+
| absolute  | margin by absolute value, per metric type units | 1-2147483647 | \-      |
+-----------+-------------------------------------------------+--------------+---------+

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
    dnRouter(cfg-constraints-metric-margin)# absolute 200


**Removing Configuration**

To remove absolute metric margin:
::

    dnRouter(cfg-constraints-metric-margin)# no absolute

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
