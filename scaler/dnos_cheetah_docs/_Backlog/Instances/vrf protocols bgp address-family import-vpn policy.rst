vrf protocols bgp address-family import-vpn policy
--------------------------------------------------

**Command syntax: import-vpn policy [policy-name]**

**Description:** Enable import of BGP routes which comply with the specified policy

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# route-distinguisher 56335:1
	dnRouter(cfg-vrf-protocols-bgp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-bgp-afi)# import-vpn policy VPN_IMP_POL


	dnRouter(cfg-bgp-neighbor-afi)# no import-vpn import-vpn policy VPN_IMP_POL

**Command mode:** config

**TACACS role:** operator

**Note:**

no command stops importing by the specified policy

**Help line:** allow import of permitted vpn routes  \*\*\*\* according to policy

**Parameter table:**

+-------------+--------+-------------+
| Parameter   | Values | Description |
+=============+========+=============+
| policy-name | string |             |
+-------------+--------+-------------+
