static address-family route next-hop
------------------------------------

**Minimum user role:** operator

To configure a static route matching an IP prefix to its designated gateway:

To configure an IPv4 static route:

**Command syntax: route [ip-prefix] next-hop [ip-address]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- protocols static address-family

..
	**Internal Note**

	-  An IP static route must comply with its address family. e.g, in address family "ipv4 unicast" you can only set ipv4 addresses for route target and route next-hop

	-  when user sets a non /32 ip-prefix, the route installed will be the matching subnet network address. For example if user set route 192.168.1.19  **7**/26 next-hop 10.173.2.65 the configured static route will be 192.168.1.19  **2**/26. The same rule applies for ipv6-prefix.

	-  next-hop must be a unicast addres

	-  nexthop address must be different from the route addre

	-  can set multiple next-hop for the same route


**Parameter table**

+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                       |                                                                                                                                                                                                                                                             |                         |             |
| Parameter             | Description                                                                                                                                                                                                                                                 | Range                   | Default     |
+=======================+=============================================================================================================================================================================================================================================================+=========================+=============+
|                       |                                                                                                                                                                                                                                                             |                         |             |
| ip-prefix             | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                                        | A.B.C.D/x               | \-          |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | In IPv4-unicast configuration mode you can only   set IPv4 destination prefixes and in IPv6-unicast configuration mode you can   only set IPv6 destination prefixes.                                                                                        | x:x::x:x/x              |             |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | When setting a non /32 prefix, the route installed   is the matching subnet network address. For example, for route   192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be   192.168.1.192/26. The same applies for IPv6 prefixes.    |                         |             |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                       |                                                                                                                                                                                                                                                             |                         |             |
| next-hop              | The gateway IPv4 or IPv6 address for the prefix.                                                                                                                                                                                                            | A.B.C.D                 | \-          |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | In IPv4-unicast configuration mode you can only   set IPv4 next hops and in IPv6-unicast configuration mode you can only set   IPv6 next hops.                                                                                                              | x:x::x:x                |             |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | You can set multiple IP next hops for the same   route.                                                                                                                                                                                                     |                         |             |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | The next-hop address must be different from the   route address.                                                                                                                                                                                            |                         |             |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                       |                                                                                                                                                                                                                                                             |                         |             |
| interface-next-hop    | You can replace the gateway IP address with an   interface name as the next hop.                                                                                                                                                                            | Physical interface      | \-          |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | A route designated to interface-next-hop cannot   have any other static route configuration.                                                                                                                                                                |  Bundle   interface     |             |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | You can set a route to multiple interfaces as   long as they have different admin-distances.                                                                                                                                                                | Bundle sub-interface    |             |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                       |                                                                                                                                                                                                                                                             |                         |             |
| admin-distance        | The administrative distance for the static route.                                                                                                                                                                                                           | 1..255                  | 1           |
|                       |                                                                                                                                                                                                                                                             |                         |             |
|                       | An administrative-distance of 255 will cause the   router to remove the route from the routing table.                                                                                                                                                       |                         |             |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 next-hop 10.173.2.65
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.20/24 next-hop 10.173.2.65 admin-distance 20
	dnRouter(cfg-protocols-static-ipv4)# route 192.0.2.1/32 next-hop 10.173.2.65


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 next-hop 2001:3::65
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 next-hop 2001:3::65 admin-distance 20

**Removing Configuration**

To remove the static route from the RIB:
::

	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32 next-hop 10.173.2.65
	dnRouter(cfg-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 next-hop 2001:3::65
	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32

To revert a parameter to its default value:
::

	dnRouter(cfg-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 next-hop 2001:3::65 admin-distance 20

.. **Help line:** static route configuration

**Command History**

+-------------+--------------------------------------------------+
|             |                                                  |
| Release     | Modification                                     |
+=============+==================================================+
|             |                                                  |
| 6.0         | Command introduced                               |
+-------------+--------------------------------------------------+
|             |                                                  |
| 9.0         | Removed BFD support                              |
+-------------+--------------------------------------------------+
|             |                                                  |
| 16.1        | Extend tag range to support unit_32 tag value    |
+-------------+--------------------------------------------------+
