network-services vrf instance protocols bgp neighbor-group neighbor address-family nexthop self
-----------------------------------------------------------------------------------------------

**Minimum user role:** operator

This command sets the next-hop of the advertised route to be the BGP router's address.

To set the advertised route's next-hop value to be the BGP router's address:

**Command syntax: nexthop self** force [force]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group neighbor address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Note**

- Changing the configuration will cause the BGP session to restart.

- For flowspec SAFI, imposing a nexthop change might affect the flowspec action rules. By default, the "nexthop" attribute doesn't change for flowspec NLRI in either eBGP or iBGP sessions.

- For eBGP sessions and any BGP MPLS session, the nexthop value is set to "nexthop self" by default.

- For neighbors within a group, the "no" command reverts the neighbor to the group setting.

- self uses the BGP session source address:

- For IPv4 over IPv6 sessions - the BGP router-id is used

- For IPv6 over IPv4 sessions - ::ffff:<session-ipv4-source-address> is used

- For BGP 6PE (IPv6 labeled-unicast), ::ffff:<session-ipv4-source-address> is used.

**Parameter table**

+-----------+-----------------------------------------------------------+--------------+---------+
| Parameter | Description                                               | Range        | Default |
+===========+===========================================================+==============+=========+
| force     | apply nexthop setting even when acting as route reflector | | enabled    | \-      |
|           |                                                           | | disabled   |         |
+-----------+-----------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 5000
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# nexthop self

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 65000
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)#)# route-reflector-client
    dnRouter(cfg-bgp-group-afi)# nexthop self force enabled


**Removing Configuration**

To remove the nexthop settings:
::

    dnRouter(cfg-group-neighbor-afi)# no nexthop

To revert force to the default state:
::

    dnRouter(cfg-bgp-group-afi)# no nexthop self force

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 6.0     | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 11.0    | Added option to configure nexthop for neighbors within a group |
+---------+----------------------------------------------------------------+
