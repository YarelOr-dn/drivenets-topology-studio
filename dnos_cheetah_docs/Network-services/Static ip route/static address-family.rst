static address-family
---------------------

**Command syntax: address-family [address-family]**

**Description:** Enter static route configuration for an address-family

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)#

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)#

	dnRouter(cfg-netsrv-vrf-protocols-static)# no address-family ipv4-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static)# no address-family ipv6--unicast

**Command mode:** config

**TACACS role:** operator

**Note:**

no commands remove all address-family static routes

**Help line:** static route address family

**Parameter table:**

+----------------+----------------------------+---------------+
| Parameter      | Values                     | Default value |
+================+============================+===============+
| address-family | ipv4-unicast, ipv6-unicast |               |
+----------------+----------------------------+---------------+
