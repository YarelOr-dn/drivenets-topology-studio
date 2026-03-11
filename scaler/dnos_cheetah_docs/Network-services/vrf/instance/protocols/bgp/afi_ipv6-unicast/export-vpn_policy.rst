network-services vrf instance protocols bgp address-family ipv6-unicast export-vpn policy
-----------------------------------------------------------------------------------------

**Minimum user role:** operator

To export local routes that comply with the specified policy.
Routes are exported to the matching address-family VPN SAFI in the default BGP VRF.

**Command syntax: export-vpn policy [export-vpn-policy]** [, export-vpn-policy, export-vpn-policy]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- Only the best paths are candidates for export.

**Parameter table**

+-------------------+----------------------------------------------------------------------------+------------------+---------+
| Parameter         | Description                                                                | Range            | Default |
+===================+============================================================================+==================+=========+
| export-vpn-policy | Enable export of excommunity routes which comply with the specified policy | | string         | \-      |
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
    dnRouter(cfg-protocols-bgp-afi)# import-vpn route-target 56335:1
    dnRouter(cfg-protocols-bgp-afi)# export-vpn policy VPN_EXP_POL1, VPN_EXP_POL2


**Removing Configuration**

To stop the export process using the specified policy:
::

    dnRouter(cfg-bgp-neighbor-afi)# no export-vpn policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
