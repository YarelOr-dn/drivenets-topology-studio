vrf protocols bgp address-family unicast redistribute
-----------------------------------------------------

**Command syntax: redistribute {connected \| static}** metric [metric-value] policy [policy-name]

**Description:** redistribute connected or static routes into BGP in non-default vrf instance

metric - update route metric

policy - filter and update redistributed routes by policy

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-bgp-afi)# redistribute connected

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# address-family ipv6-unicast
	dnRouter(cfg-protocols-bgp-afi)# redistribute static policy My_Policy


	dnRouter(cfg-protocols-bgp-afi)# no redistribute connected
	dnRouter(cfg-protocols-bgp-afi)# no redistribute static
	dnRouter(cfg-protocols-bgp-afi)# no redistribute


**Command mode:** config

**TACACS role:** operator

**Note:**

apply only for unicast sub-address-families

no commands stop route redistribute. use "no redistribute" to stop redistribute of all routes type.

**Help line:** redistribute routes into BGP

**Parameter table:**

+--------------+--------------+---------------+
| Parameter    | Values       | Default value |
+==============+==============+===============+
| metric-value | 0-4294967295 |               |
+--------------+--------------+---------------+
| policy-name  | string       |               |
|              |              |               |
|              | length 1-255 |               |
+--------------+--------------+---------------+
