vrf protocols bgp neighbor address-family
-----------------------------------------

**Command syntax: address-family [address-family-type]**

**Description:** Configure an address-family to share with bgp peer and enters its configuration.

**CLI example:**
::


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# neighbor 12.170.4.1
	dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
	dnRouter(cfg-bgp-neighbor-afi)#

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)#  neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
	dnRouter(cfg-bgp-group-afi)#

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)#  neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
	dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
	dnRouter(cfg-group-neighbor-afi)#



	dnRouter(cfg-protocols-bgp-group)# no address-family ipv6-unicast
	dnRouter(cfg-protocols-bgp-neighbor)# no address-family ipv4-unicast
	dnRouter(cfg-bgp-group-neighbor)# no address-family ipv4-flowspec

**Command mode:** config

**TACACS role:** operator

**Note:**

only unicast sub-address-families supported for neighbors in non default vrf

"address-family" applies for both neighbor and neighbor-group and neighbor within a neighbor-group

A neighbor not within a neighbor-group, must be configured with at least one address-family

A neighbor within a neighbor-group inherit all address families configured for the neighbor-group

A neighbor-group, must be configured with at least one address-family. Regardless if it has neighbors within it

A neighbor within a neighbor-group can't be configured with an address-family that isn't configured for the neighbor-group

changing address-family configuration will cause bgp session o restart

no commands remove the address-family

**Help line:** Configure an address-family

**Parameter table:**

+---------------------+---------------+---------------+
| Parameter           | Values        | Default value |
+=====================+===============+===============+
| address-family-type | ipv4-unicast, |               |
|                     |               |               |
|                     | ipv6-unicast, |               |
+---------------------+---------------+---------------+
