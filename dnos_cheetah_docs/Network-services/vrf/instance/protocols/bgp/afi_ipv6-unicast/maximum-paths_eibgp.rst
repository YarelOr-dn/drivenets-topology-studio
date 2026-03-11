network-services vrf instance protocols bgp address-family ipv6-unicast maximum-paths eibgp
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

Multipath between eBGP and iBGP paths is possible only when both paths are imported paths into a non-default vrf table.

To configure BGP multi-path between eBGP paths and iBGP paths for a non-default vrf unicast table:

**Command syntax: maximum-paths eibgp [eibgp-maximum-paths]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- When eiBGP is configured, eBGP paths are preferred over iBGP paths.

**Parameter table**

+---------------------+---------------------------------------------------------------------------+-------+---------+
| Parameter           | Description                                                               | Range | Default |
+=====================+===========================================================================+=======+=========+
| eibgp-maximum-paths | Maximum number of parallel paths to consider when using EI-BGP multipath. | 1-32  | 1       |
+---------------------+---------------------------------------------------------------------------+-------+---------+

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
    dnRouter(cfg-inst-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# maximum-paths eibgp 5

    dnRouter(cfg-inst-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# maximum-paths eibgp 7


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp-afi)# no maximum-paths eibgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
