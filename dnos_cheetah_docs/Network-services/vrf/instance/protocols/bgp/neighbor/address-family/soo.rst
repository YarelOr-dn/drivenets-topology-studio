network-services vrf instance protocols bgp neighbor address-family soo
-----------------------------------------------------------------------

**Minimum user role:** operator

BGP site of origin (SoO) is a tag that is appended on BGP updates to allow to mark a specific peer as belonging to a particular site. By tagging the route, BGP will check if the peer's site of origin is listed in the community field. If it is then the route will be filtered. If not, then the route will be advertised as normal.

To set the Site-Of-Orgin value for a BGP neighbor or neighbor group:

**Command syntax: soo [site-of-origin]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- Neighbors within a neighbor-group can use the neighbor-group configuration or use a unique setting.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| site-of-origin | Set the Site-Of-Origin value for a BGP neighbor or peer group valid only for     | \-    | \-      |
|                | non-default vrf                                                                  |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance customer_vrf_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# soo 45000:65
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance customer_vrf_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# soo 45000:65
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance customer_vrf_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# 50000:65
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-group-neighbor-afi)# soo 45000:65


**Removing Configuration**

To remove the SoO value for a BGP neighbor:
::

    dnRouter(cfg-bgp-neighbor-afi)# no soo 45000:65

::

    dnRouter(cfg-bgp-group-afi)# no soo 45000:65

::

    dnRouter(cfg-group-neighbor-afi)# no soo 45000:65

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
