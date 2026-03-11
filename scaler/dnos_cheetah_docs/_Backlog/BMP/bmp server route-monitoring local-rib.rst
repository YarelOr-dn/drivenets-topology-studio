bmp server route-monitoring local-rib
-------------------------------------

**Command syntax: local-rib [admin-state]**

**Description:** Enable exporting bgp neighbor local-rib table

Local-rib includes:

* redistributed routes
* advertise network routs
* link-state nlris

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# bmp server 1
	dnRouter(cfg-routing-option-bmp)# route-monitoring
	dnRouter(cfg-routing-option-bmp-rm)# local-rib enabled


	dnRouter(cfg-routing-option-bmp)# no local-rib

**Command mode:** config

**TACACS role:** operator

**Note:**

- no command returns admin-state to default value

**Help line:** Enable exporting bgp neighbor local-rib table

**Parameter table:**

+-------------+----------------------+-----------------------------------+
| Parameter   | Values               | Default value                     |
+=============+======================+===================================+
| admin-state | enabled, disabled    | disabled                          |
+-------------+----------------------+-----------------------------------+