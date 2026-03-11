network-services vrf instance protocols static address-family ipv6-unicast route
--------------------------------------------------------------------------------

**Minimum user role:** operator

To configure a static route matching an IP prefix to its designated gateway:

**Command syntax: route [ip-prefix]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv6-unicast
- protocols static address-family ipv6-unicast

**Note**

- An static route IP must match the address family. E.g, in address family 'ipv4 unicast' you can only set ipv4 addresses for route target and route next-hop.

- When a non /32 ip-prefix is configured, the installed route will be the matching subnet network address. For example, when configuring a route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same rule applies for ipv6 prefixes.

- The next-hop must be a unicast address.

- The nexthop address must be different from the route address.

- You can set multiple next-hops for the same route.

**Parameter table**

+-----------+--------------------------+------------+---------+
| Parameter | Description              | Range      | Default |
+===========+==========================+============+=========+
| ip-prefix | target route destination | X:X::X:X/x | \-      |
+-----------+--------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route 1::/64
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route 1::/64


**Removing Configuration**

To remove a specific next-hop:
::

    dnRouter(cfg-inst-protocols-static)# no route route 1::/64

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
