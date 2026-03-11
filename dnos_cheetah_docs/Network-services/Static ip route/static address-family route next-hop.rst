static address-family route next-hop
------------------------------------

**Command syntax: route [ip-prefix] next-hop [ip-address]** next-hop-vrf [vrf-name] admin-distance [admin-distance] tag [tag] 

**Description:** Sets a static ip routing entry, matching an ip prefix to its designated gateway.

next-hop-vrf - Set the vrf in which the next-hop ip-address will be resolve. Default behavior is to resolve next-hop in the same vrf of the static-route

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static) address-family ipv4-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 172.16.172.16/32 next-hop 10.173.2.65
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 172.16.172.20/24 next-hop 10.173.2.65 admin-distance 20
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 192.0.2.1/32 next-hop 10.173.2.65 tag 100


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static) address-family ipv6-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 next-hop 2001:3::65
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 next-hop 2001:3::65 admin-distance 20

	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# no route 172.16.172.16/32 next-hop 10.173.2.65
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 next-hop 2001:3::65 admin-distance 20
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 next-hop 2001:3::65
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# no route 172.16.172.16/32

**Command mode:** config

**TACACS role:** operator

**Note:**

-  An IP static route must comply with its address family. e.g, in address family "ipv4 unicast" you can only set ipv4 addresses for route target and route next-hop

-  when user sets a non /32 ip-prefix, the route installed will be the matching subnet network address. For example if user set route 192.168.1.19  **7**/26 next-hop 10.173.2.65 the configured static route will be 192.168.1.19  **2**/26. The same rule applies for ipv6-prefix.

-  next-hop must be a unicast addres

-  nexthop address cannot be a local address within the same vrf

-  nexthop address must be different from the route address

-  next-hop-vrf must be a configured in-band vrf in the system

-  can set multiple next-hop for the same route

-  no command with optional parameter returns parameter to its default values.

-  no command removes the static route from RIB, identified by target network and gateway.

**Help line:** static route configuration

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
| vrf-name       | string                  |               |                                                                                                                   |
|                |                         |               |                                                                                                                   |
|                | any configured in-band  |               |                                                                                                                   |
|                | vrf                     |               |                                                                                                                   |
|                |                         |               |                                                                                                                   |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| ip-address     | A.B.C.D,                |               | must comply with the relative address-family                                                                      |
|                |                         |               |                                                                                                                   |
|                | {ipv6 address format}   |               |                                                                                                                   |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| admin-distance | 1-255                   | 1             | An administrative distance of 255 will cause the router to remove the route from the routing table and not use it |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| tag            | 1-65535                 |               | Specifies a tag value that can be used as a match for controlling redistribution using route policies             |
+----------------+-------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+

..
