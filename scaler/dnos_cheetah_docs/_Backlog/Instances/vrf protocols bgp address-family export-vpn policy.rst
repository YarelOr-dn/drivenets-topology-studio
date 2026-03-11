vrf protocols bgp address-family export-vpn policy
--------------------------------------------------

**Command syntax: export-vpn policy [policy-name]**

**Description:** Enable export of local routes which comply with the specified policy

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
	dnRouter(cfg-protocols-bgp-afi)# import-vpn route-target 56335:1
	dnRouter(cfg-protocols-bgp-afi)# export-vpn policy VPN_EXP_POL

	dnRouter(cfg-bgp-neighbor-afi)# no export-vpn policy VPN_EXP_POL

**Command mode:** config

**TACACS role:** operator

**Note:**

no command stops exporting by the specified policy

**Help line:** allow export of permitted vpn routes  \*\*\*\* according to policy

**Parameter table:**

+-------------+--------+-------------+
| Parameter   | Values | Description |
+=============+========+=============+
| policy-name | string |             |
+-------------+--------+-------------+
