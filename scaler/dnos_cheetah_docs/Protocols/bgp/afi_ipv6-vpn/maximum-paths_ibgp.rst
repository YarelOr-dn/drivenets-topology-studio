protocols bgp address-family ipv6-vpn maximum-paths ibgp
--------------------------------------------------------

**Minimum user role:** operator

To configure BGP to install multiple paths in the routing table:

**Command syntax: maximum-paths ibgp [ibgp-maximum-paths]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-vpn
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-vpn
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast
- network-services evpn instance protocols bgp
- network-services evpn-vpws instance protocols bgp

**Note**

- This command is relevant only to unicast and multicast sub-address-families, including label-unicast.

- To view the installed routes, use the various show route commands: "show route", "show route forwarding-table", "show mpls route", and "show mpls forwarding-table".

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                                      | Range | Default |
+====================+==================================================================================+=======+=========+
| ibgp-maximum-paths | Maximum number of parallel paths to consider when using iBGP multipath. The      | 1-32  | 1       |
|                    | default is to use a single path                                                  |       |         |
+--------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# maximum-paths ibgp 5

    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# maximum-paths ibgp 3


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast

::

    dnRouter(cfg-protocols-bgp-afi)# no maximum-paths ibgp

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 6.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 13.1    | Updated maximum-paths value to 32                   |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
