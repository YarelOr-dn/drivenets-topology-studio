network-services vrf instance protocols bgp route-distinguisher
---------------------------------------------------------------

**Minimum user role:** operator

To configure the route-distinguisher to enable the VRF to use a L3VPN service and to support route export and import, to and from the VRF:

**Command syntax: route-distinguisher [route-distinguisher]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp

**Note**

- The route-distinguisher must be unique for different VRFs.

- Reconfiguring the route-distinguisher causes all routes to be withdrawn from the VPN peers in the VPN safi, and then to be re-advertised with an updated route-distinguisher.

- When set to auto, system will generate route-distinguisher in format <router-id>:<16bit>, BGP router-id must be configured and 16 bit are randomnly choosen.

- User cannot configure route-distinguisher value that match a different route-distinguisher regardless how route-distinguisher was generated (manual/auto)

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter           | Description                                                                      | Range | Default |
+=====================+==================================================================================+=======+=========+
| route-distinguisher | the route distinguisher for BGP as part VPN service valid only for non-default   | \-    | \-      |
|                     | vrf                                                                              |       |         |
+---------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance customer_vrf_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# route-distinguisher 56335:1


**Removing Configuration**

To remove the route-distinguisher:
::

    dnRouter(cfg-inst-protocols-bgp))# no route-distinguisher

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
| 19.1    | Add auto option    |
+---------+--------------------+
