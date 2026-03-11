static address-family bfd next-hop
----------------------------------

**Command syntax: next-hop [ip-address] [type]** admin-state [admin-state] min-rx [min-rx] min-tx [min-tx] multiplier [multiplier]

**Description:**  Configured BFD for Static route next-hop neighbor.

Once next-hop is used in any of the static routes a BFD session will be formed to that address in order to protect next-hop reachability.

Can configure multiple BFD next-hops, each with it's own bfd session parameters


- type - define next-hop type to define the require BFD session type. A single-hop type is for a directly connected next-hop

- admin-state - Enable a BFD session. For admin-state disabled, bfd session is removed (not kept in admin-down)

- min-tx - set bfd minimum tx interval

- min-rx - set bfd minimum rx interval

- multiplier - set bfd multiplier


**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-vrf-protocols-static-ipv4)# bfd
	dnRouter(cfg-static-ipv4-bfd)# next-hop 10.173.2.65 single-hop admin-state enabled min-rx 100 min-tx 100 multiplier 5
	dnRouter(cfg-static-ipv4-bfd)# next-hop 10.1.3.1 single-hop admin-state enabled min-rx 50 min-tx 50 multiplier 5


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-vrf-protocols-static-ipv6)# bfd
	dnRouter(cfg-static-ipv4-bfd)# next-hop 2001:3::65 single-hop admin-state enabled
	dnRouter(cfg-static-ipv6-bfd)# next-hop 2001:4::13 single-hop admin-state enabled min-rx 50 min-tx 50 multiplier 5



	dnRouter(cfg-static-ipv4-bfd)# no next-hop 10.1.3.1 single-hop
	dnRouter(cfg-static-ipv6-bfd)# no next-hop 2001:3::65 single-hop

**Command mode:** config

**TACACS role:** operator

**Notes:**

-  ״no next-hop 10.1.3.1 single-hop״ remove the bfd configuration of a specific nexthop
-  "next-hop 2001\::3::65 single-hop <bfd parameter>" - return bfd parameter to its default value


**Help line:** static route bfd next-hop configuration

**Parameter table:**

+----------------+---------------------------------+---------------+-----------------------------------------------+
| Parameter      | Values                          | Default value | notes                                         |
+================+=================================+===============+===============================================+
| ip-address     | A.B.C.D,                        |               | must comply with the relative address-family  |
|                |                                 |               |                                               |
|                | {ipv6 address format}           |               |                                               |
+----------------+---------------------------------+---------------+-----------------------------------------------+
| type           | single-hop                      |               |                                               |
+----------------+---------------------------------+---------------+-----------------------------------------------+
| admin-state    | enabled, disabled               | enabled       |                                               |
+----------------+---------------------------------+---------------+-----------------------------------------------+
| min-tx         | 50-1700                         | 300           | miliseconds                                   |
+----------------+---------------------------------+---------------+-----------------------------------------------+
| min-rx         | 50-1700                         | 300           | miliseconds                                   |
+----------------+---------------------------------+---------------+-----------------------------------------------+
| multiplier     | 2-16                            | 3             |                                               |
+----------------+---------------------------------+---------------+-----------------------------------------------+
