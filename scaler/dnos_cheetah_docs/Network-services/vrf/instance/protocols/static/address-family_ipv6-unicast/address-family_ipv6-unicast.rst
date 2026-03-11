network-services vrf instance protocols static address-family ipv6-unicast
--------------------------------------------------------------------------

**Minimum user role:** operator

To enter static route configuration for an address-family:

**Command syntax: address-family ipv6-unicast**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static
- protocols static

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)#


**Removing Configuration**

To remove all address-family static routes:
::

    dnRouter(cfg-inst-protocols-static)# no address-family ipv6-unicast

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
