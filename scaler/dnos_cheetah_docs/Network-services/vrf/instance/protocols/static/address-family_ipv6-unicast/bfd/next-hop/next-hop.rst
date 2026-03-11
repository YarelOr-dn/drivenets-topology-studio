network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop
---------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure BFD for Static route next-hop neighbor. Once next-hop is used in any of the static routes a BFD session will be formed to that address in order to protect the next-hop reachability. You can configure multiple BFD next-hops, each with it's own bfd session parameters.

**Command syntax: next-hop [ip-address]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv6-unicast bfd
- protocols static address-family ipv6-unicast bfd

**Parameter table**

+------------+-----------------+----------+---------+
| Parameter  | Description     | Range    | Default |
+============+=================+==========+=========+
| ip-address | nexthop address | X:X::X:X | \-      |
+------------+-----------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1::1
    dnRouter(cfg-static-ipv6-bfd-nh)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1::1
    dnRouter(cfg-static-ipv6-bfd-nh)#


**Removing Configuration**

To remove the BFD configuration of a specific next-hop:
::

    dnRouter(cfg-static-ipv6-bfd)# no next-hop 1::1

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
