protocols static
-----------------

**Command syntax: static**

**Description:** Enters the menu hierarchy of protocols static for a specific vrf

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)#

	dnRouter(cfg-netsrv-vrf-protocols)## no static

**Command mode:** config

**TACACS role:** operator

**Note:**

no command removes a all static route configurations for a specific VRF

**Help line:** static route configuration
