vrf protocols bgp address-family import-leak
--------------------------------------------

**Command syntax: import-leak policy [policy-name]**

**Description:** Performs leakage of routes from the default VRF to non-default VRF. Leakage is filtered using a routing-policy

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)#  address-family ipv4-unicast
	dnRouter(cfg-protocols-bgp-afi)# import-leak policy POL_NAME

	dnRouter(cfg-protocols-bgp-afi)# no import-leak policy

**Command mode:** config

**TACACS role:** operator

**Note:**

no command disable import

**Help line:** Import-leak policy on routes sent from default VRF to the local VPN

**Parameter table:**

+-------------+--------------+---------------+
| Parameter   | Values       | Default value |
+=============+==============+===============+
| policy-name | string       |               |
|             |              |               |
|             | length 1-255 |               |
+-------------+--------------+---------------+
