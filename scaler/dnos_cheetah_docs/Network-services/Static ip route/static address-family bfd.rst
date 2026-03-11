static address-family bfd
-------------------------

**Command syntax: bfd**

**Description:**  Enters bfd configuration level for BFD protection of Static route in vrf network service

BFD session is created when bfd-nexthop configured and enabled, and nexthop is used by at least one static route of same type (single-hop/multi-hop)
When Static route nexthop is protected by BFD, static route is valid only when BFD is UP.

BFD session will run in the relevent vrf network service


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
	dnRouter(cfg-static-ipv4-bfd)#


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-vrf-protocols-static-ipv6)# bfd
	dnRouter(cfg-static-ipv6-bfd)#

	dnRouter(cfg-vrf-protocols-static-ipv4)# no bfd
	dnRouter(cfg-vrf-protocols-static-ipv6)# no bfd

**Command mode:** config

**TACACS role:** operator

**Notes:**

-  "no bfd" removes all BFD configuration of the relevant address-family


**Help line:** Enters static route bfd configuration