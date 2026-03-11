static maximum-routes
---------------------

**Command syntax: maximum-routes [maximum] threshold [threshold]**

**Description:** configure system maximum static route limit and threshold for a specific vrf.

The parameters will be used to invoke a system-event when limit & threshold are crossed

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# maximum-routes 1000 threshold 70

	dnRouter(cfg-netsrv-vrf-protocols-static)# no maximum-routes

**Command mode:** config

**TACACS role:** operator

**Note:**

-  there is no limitation for how many static routes user can configure

-  no command returns maximum & threshold to their default values

**Help line:**

**Parameter table:**

+-----------+----------+---------------+
| Parameter | Values   | Default value |
+===========+==========+===============+
| maximum   | 1..65535 | 2000          |
+-----------+----------+---------------+
| threshold | 1..100   | 75            |
+-----------+----------+---------------+
