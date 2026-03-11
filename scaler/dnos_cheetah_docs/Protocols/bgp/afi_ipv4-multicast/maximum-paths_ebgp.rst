protocols bgp address-family ipv4-multicast maximum-paths ebgp
--------------------------------------------------------------

**Minimum user role:** operator

To configure BGP to install multiple equal cost paths in the routing table, when some paths are ebgp and others are ibgp:

**Command syntax: maximum-paths ebgp [ebgp-maximum-paths]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-vpn
- protocols bgp address-family ipv6-vpn
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast

**Note**

- BGP will only advertise one best path to its eBGP neighbors.

- This command is relevant only to unicast and multicast sub-address-families, including label-unicast.

- To view the installed routes, use the various show route commands: "show route", "show route forwarding-table", "show mpls route", and "show mpls forwarding-table".

- ECMP between ebgp and ibgp paths are only possible if all paths are imported from other vrfs.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                                      | Range | Default |
+====================+==================================================================================+=======+=========+
| ebgp-maximum-paths | Maximum number of parallel paths to consider when using BGP multipath. The       | 1-32  | 1       |
|                    | default is use a single path.                                                    |       |         |
+--------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# maximum-paths ebgp 5

    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# maximum-paths ebgp 3


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast

::

    dnRouter(cfg-protocols-bgp-afi)# no maximum-paths ebgp

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
