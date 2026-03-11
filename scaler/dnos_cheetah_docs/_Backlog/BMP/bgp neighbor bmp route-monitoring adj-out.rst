bgp neighbor bmp route-monitoring adj-out
-----------------------------------------

**Command syntax: adj-out [admin-state]**

**Description:** Enable exporting bgp neighbor adjacency-out table

Configuration applies for all bgp neighbor address-families

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
	dnRouter(cfg-protocols-bgp-neighbor)# bmp route-monitoring
	dnRouter(cfg-bgp-neighbor-bmp-rm)# adj-out disabled


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# bmp route-monitoring
	dnRouter(cfg-bgp-group-bmp-rm)# adj-out enabled


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
	dnRouter(cfg-protocols-bgp-group)# bmp route-monitoring
	dnRouter(cfg-bgp-group-bmp-rm)# adj-out disabled
	dnRouter(cfg-bgp-group-bmp-rm)# exit
	dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
	dnRouter(cfg-bgp-group-neighbor)# bmp route-monitoring
	dnRouter(cfg-group-neighbor-bmp-rm)# adj-out enabled

	dnRouter(cfg-bgp-neighbor-bmp-rm)# no adj-out
	dnRouter(cfg-bgp-group-bmp-rm)# no adj-out
	dnRouter(cfg-group-neighbor-bmp-rm)# no adj-out

**Command mode:** config

**TACACS role:** operator

**Note:**

- Configuration valid for neighbor, neighbor-group and neighbor within a neighbor group

- For neighbor or group, by default inherit bmp server route-monitoring (per server) behavior

- For neighbor within a group, by default inherit group behavior.

- no command returns admin-state to default values

**Help line:** Enable exporting bgp neighbor adj-out table

**Parameter table:**

+-------------+----------------------+---------------------------------------------------------+
| Parameter   | Values               | Default value                                           |
+=============+======================+=========================================================+
| admin-state | enabled, disabled    | bmp server route-monitoring adj-in post-policy          |
+-------------+----------------------+---------------------------------------------------------+

