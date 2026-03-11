network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop admin-state
---------------------------------------------------------------------------------------------------

**Minimum user role:** operator

You can enable BFD for next-hop protection of a single hop static route. The static route will be valid for FIB installation only when BFD is UP.

When next-hop is used in any of the static routes, a BFD session will be formed to that address in order to protect the next-hop reachability. You can configure multiple BFD next-hops, each with its own BFD session parameters.

When admin-state is disabled, the BFD session is removed.

To enable/disable BFD for next-hop protection:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop
- protocols static address-family ipv6-unicast bfd next-hop

**Parameter table**

+-------------+--------------------------------------+--------------+---------+
| Parameter   | Description                          | Range        | Default |
+=============+======================================+==============+=========+
| admin-state | set whether bfd protection is in use | | enabled    | enabled |
|             |                                      | | disabled   |         |
+-------------+--------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1::1 single-hop
    dnRouter(cfg-static-ipv6-bfd-nh)# admin-state disabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1.1.1.1 single-hop
    dnRouter(cfg-static-ipv6-bfd-nh)# admin-state disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-static-ipv6-bfd-nh)# no admin-state

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
