vrf protocols static
--------------------

**Command syntax: static**

**Description:** Enters static ip routing configuration under the vrf instance.

Configuration are the same as "  `static ip route <#STATIC IP ROUTE>`__  ", only uses a non-default vrf

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# static
	dnRouter(cfg-vrf-protocols-static)#

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_2
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# static
	dnRouter(cfg-vrf-protocols-static)#

	dnRouter(cfg-network-services-vrf-protocols)# no static

**Command mode:** config

**TACACS role:** operator

**Note:**

no command remove all static route configurations under the vrf instance

**Help line:** static ip routing configuration under the vrf instance

**Configuration examples:**

dnRouter#

dnRouter# configure

dnRouter(cfg)# network-services

dnRouter(cfg-network-services)# vrf customer_vrf_2

dnRouter(cfg-network-services-vrf)# protocols

dnRouter(cfg-network-services-vrf-protocols)# static

dnRouter(cfg-vrf-protocols-static)# address-family ipv4-unicast

dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32 10.173.2.65

dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.16/32 10.173.2.65

dnRouter#

dnRouter# configure

dnRouter(cfg)# network-services

dnRouter(cfg-network-services)# vrf customer_vrf_1

dnRouter(cfg-network-services-vrf)# protocols

dnRouter(cfg-network-services-vrf-protocols)# static

dnRouter(cfg- vrf-protocols-static)# address-family ipv6-unicast

dnRouter(cfg-protocols-static-ipv6)# route ::ffff:172.16.172.16/128 2001:3::65

dnRouter(cfg-protocols-static-ipv6)# no route ::ffff:172.16.172.16/128 2001:3::65
