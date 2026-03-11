vrf protocols bgp address-family
--------------------------------

**Command syntax: address-family [address-family-type]**

**Description:** Configure an address-family to be supported by bgp and enters its configuration.

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-bgp-afi)#

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
	dnRouter(cfg-vrf-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
	dnRouter(cfg-bgp-group-afi)#

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
	dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
	dnRouter(cfg-group-neighbor-afi)#


	dnRouter(network-services-vrf-bgp)# no address-family ipv4-unicast
	dnRouter(cfg-protocols-bgp-group)# no address-family ipv6-unicast
	dnRouter(cfg-protocols-bgp-neighbor)# no address-family ipv4-unicast
	dnRouter(cfg-bgp-group-neighbor)# no address-family ipv4-unicast

**Command mode:** config

**TACACS role:** operator

**Note:**

only unicast sub-address-family is supported under non-default vrf

ipv4-unicast address family **is not the default setting**.

address-family configuration outside a neighbor-group or a neighbor, are global configuration for all address-families

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
