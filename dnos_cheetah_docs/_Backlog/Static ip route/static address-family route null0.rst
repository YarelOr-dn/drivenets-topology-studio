static address-family route null0
----------------------------------

**Minimum user role:** operator

You can define a null route (blackhole route) by using a null0 interface as gateway. To configure the null0 route, use the following command in either IPv4 or IPv6 configuration mode.

To configure the null0 route for IPv4:


**Command syntax: route [ip-prefix] null0** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- protocols static address-family

**Note**

- Routes designated to null0 cannot have any other static route configuration.

- The IP static route cannot be a limited boradcast address or a multicast address.

..
	**Internal Note**

	-  An IP static route must comply with its address family. e.g, in address family "ipv4-unicast" you can only set ipv4 addresses

	-  when user sets a non /32 ip-prefix, the route installed will be the matching subnet network address. For example if user set route 192.168.1.19  **7**/26 next-hop 10.173.2.65 the configured static route will be 192.168.1.19  **2**/26. The same rule applies for ipv6-prefix.

	-  the ip static route cannot be:

	   -  a limited broadcast address

	   -  a multicast address

	-  route designated to null0 cannot have any other static route configuration.

	-  tag - Specifies a tag value that can be used as a match for controlling redistribution using route policies


**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+
|                   |                                                                                                                                                                                                                                                             |               |             |
| Parameter         | Description                                                                                                                                                                                                                                                 | Range         | Default     |
+===================+=============================================================================================================================================================================================================================================================+===============+=============+
|                   |                                                                                                                                                                                                                                                             |               |             |
| ip-prefix         | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                                        | A.B.C.D/x     | \-          |
|                   |                                                                                                                                                                                                                                                             |               |             |
|                   | In IPv4-unicast configuration mode you can only   set IPv4 destination prefixes and in IPv6-unicast configuration mode you can   only set IPv6 destination prefixes.                                                                                        | x:x::x:x/x    |             |
|                   |                                                                                                                                                                                                                                                             |               |             |
|                   | When setting a non /32 prefix, the route   installed is the matching subnet network address. For example, for route   192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be   192.168.1.192/26. The same applies for IPv6 prefixes.    |               |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+
|                   |                                                                                                                                                                                                                                                             |               |             |
| admin-distance    | The administrative distance for the static route.                                                                                                                                                                                                           | 1..255        | 1           |
|                   |                                                                                                                                                                                                                                                             |               |             |
|                   | An administrative-distance of 255 will cause the   router to remove the route from the routing table.                                                                                                                                                       |               |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 null0
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 null0 admin-distance 20
	dnRouter(cfg-protocols-static-ipv4)# route 192.0.2.1/32 null0

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 null0
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 null0 admin-distance 20
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 null0 admin-distance 20

**Removing Configuration**

To remove the static route from the RIB:
::

	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32 null0

	dnRouter(cfg-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 null0

.. **Help line:** set a null0 static route

**Command History**

+-------------+--------------------------------------------------+
|             |                                                  |
| Release     | Modification                                     |
+=============+==================================================+
|             |                                                  |
| 6.0         | Command introduced                               |
+-------------+--------------------------------------------------+
|             |                                                  |
| 16.1        | Extend tag range to support unit_32 tag value    |
+-------------+--------------------------------------------------+
