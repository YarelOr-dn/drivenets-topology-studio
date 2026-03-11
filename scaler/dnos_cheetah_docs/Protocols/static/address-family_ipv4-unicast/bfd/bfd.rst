protocols static address-family ipv4-unicast bfd
------------------------------------------------

**Minimum user role:** operator

You can use the following command to enter the BFD configuration level for BFD protection of a static route. A BFD session is created when bfd-nexthop is configured and enabled, and nexthop is used by at least one static route of the same type (single-hop/multi-hop). When a static route nexthop is protected by BFD, it is valid only when BFD is up.

 To configure BFD protection of a static route:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv4-unicast
- network-services vrf instance protocols static address-family ipv4-unicast

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# bfd
    dnRouter(cfg-static-ipv4-bfd)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# bfd
    dnRouter(cfg-static-ipv4-bfd)#


**Removing Configuration**

To revert to the default configuration:
::

    dnRouter(cfg-protocols-static-ipv4)# no bfd

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
