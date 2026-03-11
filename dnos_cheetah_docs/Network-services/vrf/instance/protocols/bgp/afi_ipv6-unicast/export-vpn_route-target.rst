network-services vrf instance protocols bgp address-family ipv6-unicast export-vpn route-target
-----------------------------------------------------------------------------------------------

**Minimum user role:** operator

To export routes with the route-target tag:

**Command syntax: export-vpn route-target [export-vpn-route-target]** [, export-vpn-route-target, export-vpn-route-target]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- You can export different multiple route-target tagged routes.

- The route-target can be different from the VFR route-distinguisher.

- The maximum number of route-targets that can be exported is 500.

**Parameter table**

+-------------------------+-----------------------------------------------+-------+---------+
| Parameter               | Description                                   | Range | Default |
+=========================+===============================================+=======+=========+
| export-vpn-route-target | Enable export of routes with route-target tag | \-    | \-      |
+-------------------------+-----------------------------------------------+-------+---------+

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
    dnRouter(cfg-protocols-bgp-afi)# export-vpn route-target 49844:20, 49844:30
    dnRouter(cfg-protocols-bgp-afi)# export-vpn route-target 49844:40


**Removing Configuration**

To stop exporting routes:
::

    dnRouter(cfg-bgp-neighbor-afi)# no export-vpn route-target 49844:40

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
