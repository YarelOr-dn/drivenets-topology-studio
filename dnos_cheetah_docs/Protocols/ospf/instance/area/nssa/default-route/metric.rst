protocols ospf instance area nssa default-route metric
------------------------------------------------------

**Minimum user role:** operator

Set the NSSA default-route metric. Default metric value is 1.

**Command syntax: metric [metric]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa default-route

**Parameter table**

+-----------+---------------------------------------------------------------+------------+---------+
| Parameter | Description                                                   | Range      | Default |
+===========+===============================================================+============+=========+
| metric    | Set the nssa default-route metric.  Default metric value is 1 | 1-16777215 | 1       |
+-----------+---------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 2
    dnRouter(cfg-protocols-ospf-inst)# area 1
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# default-route
    dnRouter(cfg-area-nssa-default-route)# admin-state enabled
    dnRouter(cfg-area-nssa-default-route)# metric
    dnRouter(cfg-area-nssa-default-route)#


**Removing Configuration**

To return the metric to its default value: 
::

    dnRouter(cfg-area-nssa-default-route)# no metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
