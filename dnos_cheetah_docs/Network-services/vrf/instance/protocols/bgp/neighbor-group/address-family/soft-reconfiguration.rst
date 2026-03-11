network-services vrf instance protocols bgp neighbor-group address-family soft-reconfiguration inbound
------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set address-family prefixes to be saved in the adj-RIB-in table to support soft rest:

**Command syntax: soft-reconfiguration inbound**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# soft-reconfiguration inbound
    dnRouter(cfg-protocols-bgp-neighbor)# address-family flowspec
    dnRouter(cfg-bgp-neighbor-afi)# soft-reconfiguration inbound

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-vpn
    dnRouter(cfg-bgp-group-afi)# soft-reconfiguration inbound


**Removing Configuration**

To stop the routes from being saved in the adj-RIB-in table for the neighbor address-family:
::

    dnRouter(cfg-bgp-group-afi)# no soft-reconfiguration inbound

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 10.0    | Command not supported            |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
