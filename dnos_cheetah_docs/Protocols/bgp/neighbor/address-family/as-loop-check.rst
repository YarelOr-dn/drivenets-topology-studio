protocols bgp neighbor address-family as-loop-check
---------------------------------------------------

**Minimum user role:** operator

When BGP updates travel through different Autonomous Systems (AS), each eBGP router prepends its AS number to the AS PATH attribute of the BGP update message. If a router receives an update that includes its own AS number in the AS PATH attribute, it will discard it by default to prevent loops. However, In some cases, you may want to allow such updates.

**Command syntax: as-loop-check [as-loop-check]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- allow-as-in must be enabled on the receiving end of the BGP update, otherwise it will drop any update that contains its own AS number. See "bgp neighbor address-family allow-as-in".

- This command applies only to eBGP neighbors.

- If both as-loop-check and as-override are enabled for the same neighbor, as-loop-check will be ignored as the neighbor AS is expected to be replaced.

**Parameter table**

+---------------+---------------------------------------------------------------------------+--------------+---------+
| Parameter     | Description                                                               | Range        | Default |
+===============+===========================================================================+==============+=========+
| as-loop-check | do not advertise route if neighbor as number is part of the route as-path | | enabled    | enabled |
|               |                                                                           | | disabled   |         |
+---------------+---------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# as-loop-check disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# as-loop-check disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# as-loop-check disabled
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-group-neighbor-afi)# as-loop-check enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-group-afi)# no as-loop-check

::

    dnRouter(cfg-bgp-neighbor-afi)# no as-loop-check

::

    dnRouter(cfg-group-neighbor-afi)# no as-loop-check

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
