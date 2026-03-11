protocols static address-family ipv4-unicast bfd next-hop single-hop
--------------------------------------------------------------------

**Minimum user role:** operator

To define the next-hop type for the required BFD session type. A single-hop type is for a directly connected next-hop.

**Command syntax: single-hop**

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv4-unicast bfd next-hop
- network-services vrf instance protocols static address-family ipv4-unicast bfd next-hop

**Note**

- BFD type is a mandatory setting.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# bfd
    dnRouter(cfg-static-ipv4-bfd)# next-hop 1.1.1.1
    dnRouter(cfg-static-ipv4-bfd-nh)# single-hop
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# bfd
    dnRouter(cfg-static-ipv4-bfd)# next-hop 1.1.1.1
    dnRouter(cfg-static-ipv4-bfd-nh)# single-hop


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-static-ipv4-bfd-nh)# no single-hop

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
