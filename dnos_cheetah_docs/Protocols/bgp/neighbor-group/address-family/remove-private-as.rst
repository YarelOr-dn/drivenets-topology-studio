protocols bgp neighbor-group address-family remove-private-as
-------------------------------------------------------------

**Minimum user role:** operator

To remove private AS numbers from the AS path advertised to the neighbor or peer group:

**Command syntax: remove-private-as** all

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Parameter table**

+-----------+--------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                              | Range   | Default |
+===========+==========================================================================+=========+=========+
| all       | remove all private as-numbers regardless if path contains public numbers | Boolean | False   |
+-----------+--------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# remove-private-as
    dnRouter(cfg-protocols-bgp-neighbor)# address-family flowspec
    dnRouter(cfg-bgp-neighbor-afi)# remove-private-as

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-bgp-neighbor-afi)# remove-private-as all

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# remove-private-as


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-bgp-neighbor-afi)# no remove-private-as all

::

    dnRouter(cfg-bgp-group-afi)# no remove-private-as

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
