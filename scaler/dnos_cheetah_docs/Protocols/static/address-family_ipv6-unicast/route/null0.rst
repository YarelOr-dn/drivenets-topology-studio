protocols static address-family ipv6-unicast route null0
--------------------------------------------------------

**Minimum user role:** operator

Sets a static ip routing entry, matching an ip prefix to its designated gateway.

**Command syntax: null0** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv6-unicast route
- network-services vrf instance protocols static address-family ipv6-unicast route

**Note**

- A static route IP must match the address family. E.g., in address family "ipv4-unicast" you can only set ipv4 addresses.

- When configuring a non /32 ip-prefix, the route installed will be the matching subnet network address. For example, when configuring a route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same rule applies for ipv6 prefixes.

- The static route IP cannot be a limited broadcast address or a multicast address.

- A route designated to null0 cannot have any other static route configuration.

- tag - specifies a tag value that can be used as a match for controlling redistribution using route policies.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| admin-distance | administrative-distance for protocol preference when choosing a route for static | 1-255 | 1       |
|                | ip route administrative distance if 1 by default                                 |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128
    dnRouter(cfg-static-ipv6-route)# null0 admin-distance 20
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128
    dnRouter(cfg-static-ipv6-route)# null0 admin-distance 20


**Removing Configuration**

To revert the static route from RIB to default:
::

    dnRouter(cfg-static-ipv6-route)# no null0

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
