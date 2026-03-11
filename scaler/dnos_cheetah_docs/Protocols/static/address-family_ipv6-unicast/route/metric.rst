protocols static address-family ipv6-unicast route metric
---------------------------------------------------------

**Minimum user role:** operator

Specify a metric value that will be used for RIB route tie-break between routes with similar administrative-distance. Default metric value is 0.
To set route metric:

**Command syntax: metric [metric]**

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv6-unicast route
- network-services vrf instance protocols static address-family ipv6-unicast route

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| metric    | A metric which is utilised to specify the preference of the route entry when it  | 0-16777215 | 0       |
|           | is installed into the RIB.Metric will be taken into account as RIB route         |            |         |
|           | tie-break between routers with similar administrative-distance                   |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route 232:16::8:0/96
    dnRouter(cfg-static-ipv6-route)# metric 10


**Removing Configuration**

To revert metric to default value:
::

    dnRouter(cfg-static-ipv4-route)# no metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
