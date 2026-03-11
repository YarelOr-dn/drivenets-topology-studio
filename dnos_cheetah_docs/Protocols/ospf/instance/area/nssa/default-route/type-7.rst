protocols ospf instance area nssa default-route type-7
------------------------------------------------------

**Minimum user role:** operator

When a default-route advertisement is required by an ABR for an NSSA area, the user may control the default-route being advertised as a type 7 external route (instead of the default type 3).

The default metric type for the default route is 2. The user may change the metric type to 1.

**Command syntax: type-7** metric-type [metric-type]

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa default-route

**Parameter table**

+-------------+----------------------------------------------------+-------+---------+
| Parameter   | Description                                        | Range | Default |
+=============+====================================================+=======+=========+
| metric-type | Configure type7 metric type  --> 1 or 2 (N1 or N2) | | 1   | 2       |
|             |                                                    | | 2   |         |
+-------------+----------------------------------------------------+-------+---------+

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
    dnRouter(cfg-area-nssa-default-route)# type-7
    dnRouter(cfg-area-nssa-default-route)# type-7 metric-type 1
    dnRouter(cfg-area-nssa-default-route)#


**Removing Configuration**

To return the admin-state to its default value: 
::

    dnRouter(cfg-area-nssa-default-route)# no type-7

To return the metric-type to its default value: 
::

    dnRouter(cfg-area-nssa-default-route)# no type-7 metric-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
