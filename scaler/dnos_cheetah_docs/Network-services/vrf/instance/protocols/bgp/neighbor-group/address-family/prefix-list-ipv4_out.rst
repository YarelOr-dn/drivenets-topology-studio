network-services vrf instance protocols bgp neighbor-group address-family prefix-list-ipv4 out
----------------------------------------------------------------------------------------------

**Minimum user role:** operator

The following command filters the route updates for a BGP neighbor or peer group according to IP address and mask length.

**Command syntax: prefix-list-ipv4 [ipv4-prefix-list-out] out**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family

**Parameter table**

+----------------------+---------------------------------------+------------------+---------+
| Parameter            | Description                           | Range            | Default |
+======================+=======================================+==================+=========+
| ipv4-prefix-list-out | applies the filter in outgoing routes | | string         | \-      |
|                      |                                       | | length 1-255   |         |
+----------------------+---------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# prefix-list-ipv4 PL4_OUT out

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-vpn
    dnRouter(cfg-bgp-group-afi)# prefix-list PL4_OUT out


**Removing Configuration**

To disable filtering:
::

    dnRouter(cfg-bgp-group-afi)# no prefix-list-ipv4 PL_OUT out"

::

    dnRouter(cfg-bgp-neighbor-afi)# no prefix-list-ipv4 PL_OUT out"

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
