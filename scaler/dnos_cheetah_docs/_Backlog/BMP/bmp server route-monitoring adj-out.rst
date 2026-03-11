bmp server route-monitoring adj-out
-----------------------------------

**Command syntax: adj-out [admin-state]**

**Description:** Enable exporting bgp neighbor adjencency-out table

Configuration applies for all bgp neighbor address-families

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# bmp server 1
	dnRouter(cfg-routing-option-bmp)# route-monitoring
	dnRouter(cfg-routing-option-bmp-rm)# adj-out enalbed


	dnRouter(cfg-routing-option-bmp)# no adj-out

**Command mode:** config

**TACACS role:** operator

**Note:**

- no command returns admin-state to default value

**Help line:** Enable exporting bgp neighbor adjacency-out table

**Parameter table:**

+-------------+----------------------+-----------------------------------+
| Parameter   | Values               | Default value                     |
+=============+======================+===================================+
| admin-state | enabled, disabled    | disabled                          |
+-------------+----------------------+-----------------------------------+