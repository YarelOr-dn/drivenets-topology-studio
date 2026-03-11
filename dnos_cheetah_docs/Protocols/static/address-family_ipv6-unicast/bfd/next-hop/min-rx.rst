protocols static address-family ipv6-unicast bfd next-hop min-rx
----------------------------------------------------------------

**Minimum user role:** operator

To set the bfd minimum receive interval (min-rx):

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv6-unicast bfd next-hop
- network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop

**Parameter table**

+-----------+------------------------------------------------------+--------+---------+
| Parameter | Description                                          | Range  | Default |
+===========+======================================================+========+=========+
| min-rx    | set desired minimum receive interval for BFD session | 5-1700 | 300     |
+-----------+------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1::1 single-hop
    dnRouter(cfg-static-ipv6-bfd-nh)# min-rx 50
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
    dnRouter(cfg-static-ipv6-bfd-nh)# min-rx 50


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-static-ipv6-bfd-nh)# no min-rx

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 15.1    | Added support for 5 msec interval               |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
