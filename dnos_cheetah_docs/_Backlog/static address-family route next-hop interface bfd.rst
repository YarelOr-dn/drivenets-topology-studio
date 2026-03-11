static address-family route next-hop interface bfd - supported in v11.1
-----------------------------------------------------------------------

**Command syntax: route [ip-prefix] next-hop [ip-address] interface [interface-name] bfd [admin-state]** min-tx [min-tx] min-rx [min-rx] multiplier [multiplier] admin-distance [admin-distance] tag [tag]

**Description:** Enable BFD for next-hop protection of a static route. Uses single-hop BFD session with egress interface as the specified static route interface

min-tx - set bfd minimum tx interval

min-rx - set bfd minimum rx interval

multiplier - set bfd multiplier

admin-distance - set route administrative distance

tag - tagged the route, which can later be used by a policy

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd enabled
	dnRouter(cfg-protocols-static-ipv4)# route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd enabled min-tx 50 min-rx 50 multiplier 3
	dnRouter(cfg-protocols-static-ipv4)# route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd disabled multiplier 2 admin-distance 20
	
	
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv4)# no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd enabled
	dnRouter(cfg-protocols-static-ipv4)# no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd enabled min-tx 50 min-rx 50 multiplier 3
	dnRouter(cfg-protocols-static-ipv4)# no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd disabled multiplier 2
	
	
	dnRouter(cfg-protocols-static-ipv4)# no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd enabled min-tx 50 min-rx 50 multiplier 3
	dnRouter(cfg-protocols-static-ipv4)# no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd
	
**Command mode:** config

**TACACS role:** operator

**Notes:**

-  An IP static route must comply with its address family. e.g, in address family "ipv4 unicast" you can only set ipv4 addresses for route target and route next-hop

-  nexthop address must be different from the route address

-  can set multiple next-hop and interface for the same route. route is unique by the next-hop and interface combination

-  incase multiple BFD clients register to the same BFD session, a single BFD session is established with the strictest session parameters between all clients

-  'no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd enabled min-tx 50 min-rx 50 multiplier 3' - return bfd session parameters to their default value

-  'no route 192.0.2.1/32 next-hop 10.173.2.65 interface bundle-3 bfd' - return bfd to default admin-state (session parameters remain the same)

**Help line:** static route configuration

**Parameter table:**

+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| Parameter      | Values                          | Default value | notes                                                                                                             |
+================+=================================+===============+===================================================================================================================+
| ip-prefix      | A.B.C.D/M,                      |               | must comply with the relative address-family                                                                      |
|                |                                 |               |                                                                                                                   |
|                | {ipv6 address format}/M         |               | M: 0-32 for ipv4-address                                                                                          |
|                |                                 |               |                                                                                                                   |
|                |                                 |               | M: 0-128 for ipv6-address                                                                                         |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| ip-address     | A.B.C.D,                        |               | must comply with the relative address-family                                                                      |
|                |                                 |               |                                                                                                                   |
|                | {ipv6 address format}           |               |                                                                                                                   |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| interface-name | ge{/10/25/40/100}-X/Y/Z         |               |                                                                                                                   |
|                |                                 |               |                                                                                                                   |
|                | bundle-<bundle-id>              |               |                                                                                                                   |
|                |                                 |               |                                                                                                                   |
|                | bundle-<bundle-id.subinterface> |               |                                                                                                                   |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| admin-state    | enabled, disabled               | disabled      | By default bfd protection is disabled                                                                             |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| min-tx         | 50-255000                       | 300           | miliseconds                                                                                                       |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| min-rx         | 50-255000                       | 300           | miliseconds                                                                                                       |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| multiplier     | 1-255                           | 3             |                                                                                                                   |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| admin-distance | 1-255                           | 1             | An administrative distance of 255 will cause the router to remove the route from the routing table and not use it |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| tag            | 1-65535                         |               | Specifies a tag value that can be used as a match for controlling redistribution using route policies             |
+----------------+---------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------+
