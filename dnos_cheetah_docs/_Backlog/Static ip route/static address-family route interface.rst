static address-family route interface
-------------------------------------

**Minimum user role:** operator

To configure a static route matching an ip prefix to its designated interface:

**Command syntax: route [ip-prefix] interface [interface-name]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- protocols static address-family

**Note**

-  A route designated to an interface cannot have any other static route configuration.

-  You can configure a route to multiple interfaces as long as they have different admin-distances.


**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| Parameter         | Description                                                                                                                                                                                                                                                 | Range                   | Default     |
+===================+=============================================================================================================================================================================================================================================================+=========================+=============+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| ip-prefix         | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                                        | A.B.C.D/x               | \-          |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | In IPv4-unicast configuration mode you can only set IPv4 destination prefixes and in IPv6-unicast configuration mode you can only set IPv6 destination prefixes.                                                                                            | x:x::x:x/x              |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | When setting a non /32 prefix, the route installed is the matching subnet network address. For example, for route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same applies for IPv6 prefixes.          |                         |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| interface-name    | The name of the egress interface.                                                                                                                                                                                                                           | Physical interface      | \-          |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | A static route to the mgmt0 and mgmt-ncc interfaces ignore the admin-distance value. All routes to them will be installed.                                                                                                                                  | Physical sub-interface  |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   |                                                                                                                                                                                                                                                             | Bundle interface        |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   |                                                                                                                                                                                                                                                             | Bundle sub-interface    |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| admin-distance    | The administrative distance for the static route.                                                                                                                                                                                                           | 1..255                  | 1           |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | An administrative-distance of 255 will cause the router to remove the route from the routing table.                                                                                                                                                         |                         |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/24 interface bundle-2
	dnRouter(cfg-protocols-static-ipv4)# route 172.30.172.16/16 interface bundle-2 admin-distance 20
	dnRouter(cfg-protocols-static-ipv4)# route 192.0.2.1/32 interface bundle-2


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 interface bundle-2.10
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 interface bundle-2.11 admin-distance 20

**Removing Configuration**

To remove the static route from the RIB:
::

	dnRouter(cfg-protocols-static-ipv4)# no route 172.20.180.16/32

To revert a parameter to its default value:
::

	dnRouter(cfg-protocols-static-ipv4)# no route 172.20.180.16/32 interface bundle-2.10


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
| 16.1        | Extend tag range to support unit_32 tag value    |
+-------------+--------------------------------------------------+
| 17.0        | Command removed                                  |
+-------------+--------------------------------------------------+