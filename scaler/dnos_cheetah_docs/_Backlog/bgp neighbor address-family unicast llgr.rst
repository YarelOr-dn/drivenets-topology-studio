bgp neighbor address-family unicast llgr - N/A for this version
---------------------------------------------------------------

**Command syntax: llgr [admin-state]**

**Description:** BGP persistence, a.k.a long-lived-graceful-restart (LLGR), enables the router to retain routes that it has learnt from the configured neighbor even when the neighbor session is down. It's main goal is to maintain routing information in RIB in case of severe downtime events that may last for hours or even days. LLGR stale routes will only be advertise to LLGR capable neighbor

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
	dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
	dnRouter(cfg-bgp-neighbor-afi)# llgr enabled
	dnRouter(cfg-bgp-neighbor-afi-llgr)#
	
	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
	dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-unicast
	dnRouter(cfg-bgp-neighbor-afi)# llgr enabled
	dnRouter(cfg-neighbor-afi-llgr)#
	
	
	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
	dnRouter(cfg-bgp-group-afi)# llgr enabled
	dnRouter(cfg-group-afi-llgr)#
	
	dnRouter(cfg-bgp-neighbor-afi)# no llgr
	
**Command mode:** config

**TACACS role:** operator

**Note:**

default system behavior is LLGR disabled

apply only for unicast sub-address family

LLGR is supported only with address-family unicast labeled-unicast, both ipv4 and ipv6

apply for default vrf only

for LLGR to be enabled the following must be set:

-  bgp graceful-restart enabled

-  bgp neighbor graceful-restart enabled - for the same neighbor

no command returns LLGR to default state and return all it configuration to default values

**Help line:**

**Parameter table:**

+-------------+-------------------+---------------+
| Parameter   | Values            | Default value |
+=============+===================+===============+
| admin-state | enabled, disabled | disabled      |
+-------------+-------------------+---------------+
