network-services vrf instance protocols bgp neighbor-group address-family nexthop
---------------------------------------------------------------------------------

**Minimum user role:** operator

This command sets the next-hop of the advertised route to be the BGP router's address.

To set the advertised route's next-hop value to be the BGP router's address:

**Command syntax: nexthop [ipv4-address]** force [force]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- Changing the configuration will cause the BGP session to restart.

- For flowspec SAFI, imposing a nexthop change might affect the flowspec action rules. By default, the "nexthop" attribute doesn't change for flowspec NLRI in either eBGP or iBGP sessions.

- For eBGP sessions and any BGP MPLS session, the nexthop value is set to "nexthop self" by default.

- For neighbors within a group, the "no" command reverts the neighbor to the group setting.

- The address type must match the address family.

**Parameter table**

+--------------+-----------------------------------------------------------+--------------+----------+
| Parameter    | Description                                               | Range        | Default  |
+==============+===========================================================+==============+==========+
| ipv4-address | set specific ip address to be used as the nexthop address | A.B.C.D      | \-       |
+--------------+-----------------------------------------------------------+--------------+----------+
| force        | apply nexthop setting even when acting as route reflector | | enabled    | disabled |
|              |                                                           | | disabled   |          |
+--------------+-----------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# nexthop 100.70.1.45

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 5000
    dnRouter(cfg-protocols-bgp-group)# neighbor 2001::66
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-group-neighbor-afi)# nexthop 120.92.1.50

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 65000
    dnRouter(cfg-group-group-afi)# address-family ipv4-unicast
    dnRouter(cfg-group-group-afi)# nexthop 1.1.1.1
    dnRouter(cfg-group-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 2001::66
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-group-neighbor-afi)# nexthop 120.92.1.50

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 65000
    dnRouter(cfg-group-group-afi)# address-family ipv6-unicast
    dnRouter(cfg-group-group-afi)# nexthop 1:1::1:1
    dnRouter(cfg-group-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 2001::66
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-group-neighbor-afi)# nexthop 0:ffff::120

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 1.2.3.4
    dnRouter(cfg-protocols-bgp-neighbor)# address-family flowspec
    dnRouter(cfg-bgp-neighbor-afi)# nexthop 95.70.1.13


**Removing Configuration**

To remove the nexthop settings:
::

    dnRouter(cfg-group-neighbor-afi)# no nexthop

To revert force to the default state:
::

    dnRouter(cfg-bgp-group-afi)# no nexthop self force

**Command History**

+---------+-----------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                          |
+=========+=======================================================================================================================+
| 6.0     | Command introduced                                                                                                    |
+---------+-----------------------------------------------------------------------------------------------------------------------+
| 11.0    | Added option to enter a specific IP address as nexthop Added option to configure nexthop for neighbors within a group |
+---------+-----------------------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for multicast SAFI                                                                                      |
+---------+-----------------------------------------------------------------------------------------------------------------------+
