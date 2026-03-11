network-services vrf instance protocols bgp neighbor-group address-family
-------------------------------------------------------------------------

**Minimum user role:** operator

The address-family applies to a neighbor, neighbor-group, and a neighbor within a neighbor-group. A neighbor within a neighbor-group inherits all address-families configured for the neighbor-group (a neighbor-group must be configured with at least one address-family, regardless if it has neighbors within it. To configure an address-family to be supported by BGP for the neighbor:

**Command syntax: address-family [neighbor-address-family]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- Changing the configuration will cause the BGP session to restart.

- When FlowSpec SAFI is applied, the received FlowSpec rules are imposed on all FlowSpec enabled interfaces.

- Notice the change in prompt.

**Parameter table**

+-------------------------+---------------+------------------------+---------+
| Parameter               | Description   | Range                  | Default |
+=========================+===============+========================+=========+
| neighbor-address-family | afi-safi type | | ipv4-unicast         | \-      |
|                         |               | | ipv6-unicast         |         |
|                         |               | | ipv4-vpn             |         |
|                         |               | | ipv6-vpn             |         |
|                         |               | | link-state           |         |
|                         |               | | ipv4-flowspec        |         |
|                         |               | | ipv6-flowspec        |         |
|                         |               | | ipv4-rt-constrains   |         |
|                         |               | | ipv4-multicast       |         |
|                         |               | | l2vpn-evpn           |         |
+-------------------------+---------------+------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-group-neighbor-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family link-state
    dnRouter(cfg-group-neighbor-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family link-state
    dnRouter(cfg-group-neighbor-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-flowspec
    dnRouter(cfg-group-neighbor-afi)# exit
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-flowspec
    dnRouter(cfg-group-neighbor-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group FLOWSPEC_V4
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-flowspec
    dnRouter(cfg-group-neighbor-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-flowspec
    dnRouter(cfg-group-neighbor-afi)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-rt-constrains
    dnRouter(cfg-bgp-neighbor-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-bgp-group)# no address-family ipv6-unicast

::

    dnRouter(cfg-protocols-bgp-neighbor)# no address-family ipv4-unicast

::

    dnRouter(cfg-bgp-group-neighbor)# no address-family ipv4-flowspec

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                       |
+=========+====================================================================================================================+
| 6.0     | Command introduced                                                                                                 |
+---------+--------------------------------------------------------------------------------------------------------------------+
| 10.0    | Added support for link-state AFI                                                                                   |
+---------+--------------------------------------------------------------------------------------------------------------------+
| 13.0    | Added support for FlowSpec SAFI                                                                                    |
+---------+--------------------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Route Target Constrain SAFI                                                                 |
+---------+--------------------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI. The command is now supported also under the network-services/vrf hierarchy. |
+---------+--------------------------------------------------------------------------------------------------------------------+
