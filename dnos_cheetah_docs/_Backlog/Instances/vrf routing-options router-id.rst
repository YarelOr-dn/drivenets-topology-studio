vrf routing-options router-id
-----------------------------

**Command syntax: router-id [router-id]**

**Description:** Manually set the router-id to be used by routing protocols under the specified vrf as their default router-id

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# routing-options
	dnRouter(cfg-network-services-vrf-routing-option)# router-id 1.1.1.1


	dnRouter(cfg-network-services-vrf-routing-option)# no router-id

**Command mode:** config

**TACACS role:** operator

**Note:**

-  no command returns router-id to default value

**Help line:**

**Parameter table:**

+-----------+---------+-------------------------------------------------------------+
| Parameter | Values  | Default value                                               |
+===========+=========+=============================================================+
| router-id | A.B.C.D | the highest IPv4 address from any active loopback interface |
+-----------+---------+-------------------------------------------------------------+
