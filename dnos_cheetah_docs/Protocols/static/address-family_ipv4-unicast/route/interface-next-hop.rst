protocols static address-family ipv4-unicast route next-hop interface
---------------------------------------------------------------------

**Minimum user role:** operator

Use this command to configure a static IP routing entry, matching an IP prefix to its designated gateway. The next-hop must be a connected address of the given interface. To set a static route entry:

**Command syntax: next-hop [ip-address] interface [interface]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- protocols static address-family ipv4-unicast route
- network-services vrf instance protocols static address-family ipv4-unicast route

**Note**

- The interface must match an attached interface in the same VRF.

- A static route IP must match the address family. E.g., in address family "ipv4 unicast" you can only set IPv4 addresses for route target and route next-hop.

- The next-hop address must be different from the route address.

- When configuring a non /32 ip-prefix, the route installed will be the matching subnet network address. For example, when configuring a route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same rule applies for ipv6 prefixes.

- You can set multiple next-hops and interfaces for the same route. A route is unique through the next-hop and interface combination.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                                      | Range            | Default |
+================+==================================================================================+==================+=========+
| ip-address     | target route destination                                                         | A.B.C.D          | \-      |
+----------------+----------------------------------------------------------------------------------+------------------+---------+
| interface      | target route destination                                                         | | string         | \-      |
|                |                                                                                  | | length 1-255   |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+
| admin-distance | administrative-distance for protocol preference when choosing a route for static | 1-255            | 1       |
|                | ip route administrative distance if 1 by default                                 |                  |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32
    dnRouter(cfg-static-ipv4-route)# next-hop 10.173.2.65 interface bundle-2 admin-distance 20
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32
    dnRouter(cfg-static-ipv4-route)# next-hop 10.173.2.65 interface bundle-2 admin-distance 20


**Removing Configuration**

To revert optional parameters to their default values:
::

    dnRouter(cfg-static-ipv4-route)# no next-hop 10.173.2.65 interface bundle-2

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
