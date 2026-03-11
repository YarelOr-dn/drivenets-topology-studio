network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop multiplier
--------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the bfd multiplier:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop
- protocols static address-family ipv6-unicast bfd next-hop

**Parameter table**

+------------+--------------------------+-------+---------+
| Parameter  | Description              | Range | Default |
+============+==========================+=======+=========+
| multiplier | set local BFD multiplier | 2-16  | 3       |
+------------+--------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1::1 single-hop
    dnRouter(cfg-static-ipv6-bfd-nh)# multiplier 5
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
    dnRouter(cfg-static-ipv6-bfd-nh)# multiplier 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-static-ipv6-bfd-nh)# no multiplier

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
