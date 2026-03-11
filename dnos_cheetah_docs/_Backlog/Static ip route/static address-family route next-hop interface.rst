static address-family route next-hop interface
----------------------------------------------

**Minimum user role:** operator

To configure a static route matching an ip prefix to its designated gateway:

**Command syntax: route [ip-prefix] next-hop [ip-address] interface [interface-name]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- protocols static address-family

**Note**

- You can set multiple next-hop and interface for the same route; the route is made unique through the next-hop and interface combination.

**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| Parameter         | Description                                                                                                                                                                                                                                                 | Range                   | Default     |
+===================+=============================================================================================================================================================================================================================================================+=========================+=============+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| ip-prefix         | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                                        | A.B.C.D/x               | \-          |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | In IPv4-unicast configuration mode you can only   set IPv4 destination prefixes and in IPv6-unicast configuration mode you can   only set IPv6 destination prefixes.                                                                                        | x:x::x:x/x              |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | When setting a non /32 prefix, the route installed   is the matching subnet network address. For example, for route   192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be   192.168.1.192/26. The same applies for IPv6 prefixes.    |                         |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| next-hop          | The gateway IPv4 or IPv6 address for the prefix.                                                                                                                                                                                                            | A.B.C.D                 | \-          |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | In IPv4-unicast configuration mode you can only   set IPv4 next hops and in IPv6-unicast configuration mode you can only set   IPv6 next hops.                                                                                                              | x:x::x:x                |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | You can set multiple IP next hops for the same   route, but the route must   be a unique next-hop and interface combination.                                                                                                                                |                         |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | The next-hop address must be different from the   route address.                                                                                                                                                                                            |                         |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| interface-name    | The name of the egress interface.                                                                                                                                                                                                                           | Physical interface      | \-          |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | A static route to the mgmt0 and mgmt-ncc   interfaces ignore the admin-distance value. All routes to them will be installed.                                                                                                                                | Physical sub-interface  |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   |                                                                                                                                                                                                                                                             | Bundle   interface      |             |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   |                                                                                                                                                                                                                                                             | Bundle sub-interface    |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                   |                                                                                                                                                                                                                                                             |                         |             |
| admin-distance    | The administrative distance for the static route.                                                                                                                                                                                                           | 1..255                  | 1           |
|                   |                                                                                                                                                                                                                                                             |                         |             |
|                   | An administrative-distance of 255 will cause the   router to remove the route from the routing table.                                                                                                                                                       |                         |             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 next-hop 10.173.2.65 interface bundle-2
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.20/24 next-hop 10.173.2.65 interface bundle-2 admin-distance 20


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 next-hop 2001:3::65 interface bundle-2
	dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 next-hop 2001:3::65 interface bundle-3 admin-distance 20

**Removing Configuration**

To remove the static route from the RIB:
::

	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32 next-hop 10.173.2.65 interface bundle-2
	dnRouter(cfg-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 next-hop 2001:3::65 interface bundle-3
	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32

To revert a parameter to its default value:
::

	dnRouter(cfg-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 next-hop 2001:3::65 interface bundle-2 admin-distance 20

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
