protocols isis instance interface address-family metric level level-2 max-metric
--------------------------------------------------------------------------------

**Minimum user role:** operator

IS-IS uses metrics to calculate the path's cost as part of the SPF algorithm. The path's cost is the sum of all metric values for each outgoing interface to the destination.
You can set different metrics for each routing level.
When IS-IS operates in multi-topology mode, you can set a different metric value for each address-family.
Set a GRE tunnel interface with a metric value of 16777215 so that no IS-IS routes will be routable through the GRE interface.
To configure the metric for the interface address-family:

**Command syntax: metric level level-2 max-metric**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**

- By default, the IS-IS te-metric is the same as the igp level-2 metric.

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

To revert the metric to the configured metric value:
::

    dnRouter(cfg-inst-if-afi)# no metric max-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
