network-services vrf instance protocols bgp address-family ipv6-unicast import-vpn route-target
-----------------------------------------------------------------------------------------------

**Minimum user role:** operator

To import BGP routes with the route-target specified in the VRF tables:

**Command syntax: import-vpn route-target [import-vpn-route-target]** [, import-vpn-route-target, import-vpn-route-target]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- You can import different multiple route-target tagged routes.

- All paths in the VPN SAFI are candidates for import, filter by route-target and then by import-vpn policy.

**Parameter table**

+-------------------------+-----------------------------------------------------------------------+-------+---------+
| Parameter               | Description                                                           | Range | Default |
+=========================+=======================================================================+=======+=========+
| import-vpn-route-target | Enable import of routes with route-target specified to the vrf tables | \-    | \-      |
+-------------------------+-----------------------------------------------------------------------+-------+---------+

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
    dnRouter(cfg-inst-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# import-vpn route-target 49844:20, 49844:30
    dnRouter(cfg-protocols-bgp-afi)# import-vpn route-target 49844:40


**Removing Configuration**

To stop th exporting routes with the specified route-target:
::

    dnRouter(cfg-bgp-neighbor-afi)# no import-vpn route-target 49844:50

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
