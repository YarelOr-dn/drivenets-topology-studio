vrf routing-options maximum-routes
----------------------------------

**Command syntax: maximum-routes [maximum] threshold [threshold]**

**Description:** configure RIB maximum scale and threshold limit for the specified vrf

Scale is for both IPv4 & IPv6

Scale figures will only be used to generate system-events warnings (no effect on number of installed routes).

-  when threshold is crossed - a single system-event notification is generated

-  when threshold is cleared - a single system-event notification is generated

-  when maximum is crossed - a system-event notification is generated

-  when maximum is cleared - a single system-event notification is generated

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# routing-options
	dnRouter(cfg-netsrv-vrf-routing-options)# maximum-routes 500000 threshold 70
	
	
	dnRouter(cfg-netsrv-vrf-routing-options)# no maximum-routes
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

-  0 value means no limit. No system-events will be generated

-  no command returns maximum & threshold to their default values

**Help line:**

**Parameter table:**

+-----------+---------------+---------------+
| Parameter | Values        | Default value |
+===========+===============+===============+
| maximum   | 0..4294967295 | 50000         |
+-----------+---------------+---------------+
| threshold | 1..100        | 75            |
+-----------+---------------+---------------+
