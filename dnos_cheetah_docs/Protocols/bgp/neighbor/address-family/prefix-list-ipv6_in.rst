protocols bgp neighbor address-family prefix-list-ipv6 in
---------------------------------------------------------

**Minimum user role:** operator

The following command filters the route updates for a BGP neighbor or peer group according to IP address and mask length.

**Command syntax: prefix-list-ipv6 [ipv6-prefix-list-in] in**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Parameter table**

+---------------------+---------------------------------------+------------------+---------+
| Parameter           | Description                           | Range            | Default |
+=====================+=======================================+==================+=========+
| ipv6-prefix-list-in | applies the filter in incoming routes | | string         | \-      |
|                     |                                       | | length 1-255   |         |
+---------------------+---------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-bgp-neighbor-afi)# prefix-list-ipv6 PL6_IN in

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# prefix-list-ipv6 PL6_IN in


**Removing Configuration**

To disable filtering:
::

    dnRouter(cfg-bgp-group-afi)# no prefix-list-ipv6 PL_IN in"

::

    dnRouter(cfg-bgp-neighbor-afi)# no prefix-list-ipv6 PL_IN in"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
