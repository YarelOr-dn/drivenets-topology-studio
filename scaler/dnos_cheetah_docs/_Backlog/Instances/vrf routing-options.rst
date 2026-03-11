vrf routing-options
-------------------

**Command syntax: routing-options**

**Description:** enters routing-options configuration level

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# routing-options
	dnRouter(cfg-netsrv-vrf-routing-options)# 
	
	
	dnRouter(cfg-netsrv-vrf)# no routing-options
	
**Command mode:** config

**TACACS role:** operator

**Note:**

-  no command returns all routing-options configurations to their default state

**Help line:**
