static address-family ipv4-unicast route rsvp-tunnel - N/A for this version
---------------------------------------------------------------------------

**Command syntax: route [ip-prefix] rsvp-tunnel [tunnel-name]** admin-distance [admin-distance] tag [tag]

**Description:** Sets a static ip routing entry with primary RSVP tunnel as nexthop

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 rsvp-tunnel TUNNEL_1
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.0/24 rsvp-tunnel TUNNEL_2 admin-distance 5
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 rsvp-tunnel TUNNEL_3 admin-distance 5 tag 100
	
	
	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32 rsvp-tunnel TUNNEL_1
	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

-  Supported only for ipv4-unicast address family

-  Mutually exclusive with any other static route configuration (e.g static route nexthop, static route interface, static route null0).

-  Supported only for primary tunnels, cannot set manual bypass tunnel name or name that starts with "tunnel_bypass" (auto-bypass)

-  If the tunnel doesn't exist or the tunnel is in down state, the static route will be in down state

-  Can set up to 32 static routes to different rsvp-tunnels for a given route (Max ECMP group).

-  the ip static route cannot be:

   -  a limited broadcast address

   -  a multicast address

-  tag - Specifies a tag value that can be used as a match for controlling redistribution using route policies

-  no command removes the static route from RIB

**Parameter table:**

+----------------+---------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| Parameter      | Values        | Default value | notes                                                                                                             |
+================+===============+===============+===================================================================================================================+
| ip-prefix      | A.B.C.D/M,    |               |                                                                                                                   |
+----------------+---------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| tunnel-name    | string        |               |                                                                                                                   |
|                |               |               |                                                                                                                   |
|                | length 1..255 |               |                                                                                                                   |
+----------------+---------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| admin-distance | 1-255         | 1             | An administrative distance of 255 will cause the router to remove the route from the routing table and not use it |
+----------------+---------------+---------------+-------------------------------------------------------------------------------------------------------------------+
| tag            | 1-65535       |               |                                                                                                                   |
+----------------+---------------+---------------+-------------------------------------------------------------------------------------------------------------------+
