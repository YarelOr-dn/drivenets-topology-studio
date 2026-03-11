vrf protocols bgp
-----------------

**Command syntax: bgp [as-number]**

**Description:** Enters bgp configuration under the vrf instance.

Configuration are the same as "  `BGP <#BGP>`__  ", only uses a non-default vrf

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)#

	dnRouter(cfg-network-services-vrf-protocols)# no protocol bgp

**Command mode:** config

**TACACS role:** operator

**Note:**

bgp as-number must be the same for all bgp instance vrf including default vrf

no command removes all bgp configurations under the vrf instance

**Help line:** bgp configuration under the vrf instance

**Parameter table:**

+-----------+--------------+---------------+----------+
| Parameter | Values       | Default value | comments |
+===========+==============+===============+==========+
| as-number | 0-4294967295 |               |          |
+-----------+--------------+---------------+----------+

****

**BGP configuration under instance-vrf - configuration example:**

dnRouter#

dnRouter# configure

dnRouter(cfg)# network-services

dnRouter(cfg-network-services)# vrf customer_vrf_1

dnRouter(cfg-network-services-vrf)# protocols

dnRouter(cfg-network-services-vrf-protocols)# bgp 65000

dnRouter(cfg-vrf-protocols-bgp)# route-distinguisher 56335:1

dnRouter(cfg-vrf-protocols-bgp)# address-family ipv4-unicast

dnRouter(cfg-protocols-bgp-afi)# redistribute connected

dnRouter(cfg-vrf-protocols-bgp)# neighbor 12.170.4.1

dnRouter(cfg-protocols-bgp-neighbor)# remote-as 5000

dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-unicast
