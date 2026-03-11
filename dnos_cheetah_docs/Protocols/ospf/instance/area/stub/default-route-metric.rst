protocols ospf instance area stub default-route-metric
------------------------------------------------------

**Minimum user role:** operator

When acting as an ABR for a stub area, DNOS will advertise the LSA type 3 default route into the stub area (regardless if it is stub or totally-stub).

The user can control the desired metric for the advertised default route by setting the default-route-metric.

The default matric value is 1.

**Command syntax: default-route-metric [default-route-metric]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area stub

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter            | Description                                                                      | Range      | Default |
+======================+==================================================================================+============+=========+
| default-route-metric | User can control the desired metric for the advertised default route by setting  | 1-16777215 | 1       |
|                      | the default-route-metric. Default metric value is 1                              |            |         |
+----------------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 1
    dnRouter(cfg-ospf-inst-area)# stub
    dnRouter(cfg-inst-area-stub)# default-route-metric 999
    dnRouter(cfg-inst-area-stub)#


**Removing Configuration**

To return the default-route-metric to its default value:
::

    dnRouter(cfg-inst-area-stub)# no default-route-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
