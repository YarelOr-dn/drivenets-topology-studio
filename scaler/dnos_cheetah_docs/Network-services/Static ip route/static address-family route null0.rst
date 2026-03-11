static address-family route null0
----------------------------------

**Command syntax: route [ip-prefix] null0** admin-distance [admin-distance] tag [tag]

**Description:** Sets a static ip route to be discarded (forward to null0)

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static) address-family ipv4-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 172.16.172.16/32 null0
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 172.16.172.16/32 null0 admin-distance 20
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 192.0.2.1/32 null0 tag 100

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static) address-family ipv6-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 null0
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 null0 admin-distance 20
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 null0 admin-distance 20 tag 100

	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# no route 172.16.172.16/32 null0

	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 null0


**Command mode:** config

**TACACS role:** operator

**Note:**

-  An IP static route must comply with its address family. e.g, in address family "ipv4-unicast" you can only set ipv4 addresses

-  when user sets a non /32 ip-prefix, the route installed will be the matching subnet network address. For example if user set route 192.168.1.19  **7**/26 next-hop 10.173.2.65 the configured static route will be 192.168.1.19  **2**/26. The same rule applies for ipv6-prefix.

-  the ip static route cannot be:

   -  a limited broadcast address

   -  a multicast address

-  route designated to null0 cannot have any other static route configuration.

-  tag - Specifies a tag value that can be used as a match for controlling redistribution using route policies

-  no command removes the static route from RIB

**Help line:** set a null0 static route

**Parameter table:**

+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| Parameter      | Values                  | Default value | notes                                                                                                             |
+================+=========================+===============+===================================================================================================================+
| ip-prefix      | A.B.C.D/M,              |               | must comply with the relative address-family                                                                      |
|                |                         |               |                                                                                                                   |
|                | {ipv6 address format}/M |               | M: 0-32 for ipv4-address                                                                                          |
|                |                         |               |                                                                                                                   |
|                |                         |               | M: 0-128 for ipv6-address                                                                                         |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| admin-distance | 1-255                   | 1             | An administrative distance of 255 will cause the router to remove the route from the routing table and not use it |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| tag            | 1-65535                 | 1             |                                                                                                                   |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
