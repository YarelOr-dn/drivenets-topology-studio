network-services vrf instance protocols bgp address-family ipv6-unicast import-vpn policy
-----------------------------------------------------------------------------------------

**Minimum user role:** operator

To import local BGP routes that comply with the specified policy:

**Command syntax: import-vpn policy [import-vpn-policy]** [, import-vpn-policy, import-vpn-policy]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- All paths in the VPN SAFI are candidates for import. Filter by route-target and then by import-vpn policy.

**Parameter table**

+-------------------+----------------------------------------------------------------------------+------------------+---------+
| Parameter         | Description                                                                | Range            | Default |
+===================+============================================================================+==================+=========+
| import-vpn-policy | Enable import of excommunity routes which comply with the specified policy | | string         | \-      |
|                   |                                                                            | | length 1-255   |         |
+-------------------+----------------------------------------------------------------------------+------------------+---------+

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
    dnRouter(cfg-protocols-bgp-afi)# import-vpn policy VPN_IMP_POL1, VPN_IMP_POL2


**Removing Configuration**

To stop the import process using the specified policy:
::

    dnRouter(cfg-bgp-neighbor-afi)# no import-vpn import-vpn policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
