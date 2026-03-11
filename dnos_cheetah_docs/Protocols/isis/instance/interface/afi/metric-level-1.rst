protocols isis instance interface address-family metric level level-1
---------------------------------------------------------------------

**Minimum user role:** operator

IS-IS uses metrics to calculate the path's cost as part of the SPF algorithm. The path's cost is the sum of all metric values for each outgoing interface to the destination. You can set different metrics for each routing level.
When IS-IS operates in multi-topology mode, you can set a different metric value for each address-family.
Set a GRE tunnel interface with a metric value of 16777215 so that no IS-IS routes will be routable through the GRE interface.
To configure the metric for the interface address-family:

**Command syntax: metric level level-1 [metric]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**

- By default, the IS-IS te-metric is the same as the igp level-2 metric.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+------------------------------------------------+
| Parameter | Description                                                                      | Range      | Default                                        |
+===========+==================================================================================+============+================================================+
| metric    | The metric that will be set for the link. The range is dependent on the          | 1-16777215 | per global address-family metric configuration |
|           | metric-style configured.                                                         |            |                                                |
|           | The IS-IS TE-metric is the same as the IGP level-2 metric by default.            |            |                                                |
|           | A metric value of 16777215 will cause the interface to not be routable except    |            |                                                |
|           | for interface local address.                                                     |            |                                                |
|           | If you do not specify level-1 and level-2 for level-1-2 ISs, then the same       |            |                                                |
|           | metric is set for both level-1 and level-2.                                      |            |                                                |
+-----------+----------------------------------------------------------------------------------+------------+------------------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# metric 20

    dnRouter(cfg-protocols-isis-inst)# interface bundle-3
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# metric max-metric

    dnRouter(cfg-protocols-isis-inst)# interface bundle-4
    dnRouter(cfg-isis-inst-if)# level level-1-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# metric level level-1 15
    dnRouter(cfg-inst-if-afi)# metric level level-2 20

    dnRouter(cfg-protocols-isis-inst)# interface bundle-5
    dnRouter(cfg-isis-inst-if)# level level-1-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# metric level level-1 15
    dnRouter(cfg-inst-if-afi)# metric 20


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-fa-afi)# no metric 60

To revert to the default metric (when metric per level is not set):
::

    dnRouter(cfg-inst-if-afi)# no metric
    dnRouter(cfg-inst-if-afi)# no metric 15

To revert from max-metric to the last configured metric:
::

    dnRouter(cfg-inst-if-afi)# no metric level-1 max-metric

To revert to the default metric for a specific routing level:
::

    dnRouter(cfg-inst-if-afi)# no metric level-2

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                             |
+=========+==========================================================================================================================+
| 6.0     | Command introduced                                                                                                       |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 9.0     | Removed level-1 and level-1-2 routing, removed support of narrow and transition metric styles, changed range and         |
|         | defaults metric value                                                                                                    |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 11.4    | Added support for GRE-tunnels                                                                                            |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 14.0    | Added support for level-1-2                                                                                              |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 15.0    | Updated command syntax                                                                                                   |
+---------+--------------------------------------------------------------------------------------------------------------------------+
