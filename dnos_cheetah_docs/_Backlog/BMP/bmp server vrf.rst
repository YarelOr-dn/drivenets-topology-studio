bmp server vrf
--------------

**Command syntax: vrf [vrf-name]**

**Description:** Set vrf network-service in which the bmp server is accessible in


**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# bmp server 1
	dnRouter(cfg-routing-option-bmp)# vrf vrf_1


	dnRouter(cfg-routing-option-bmp)# no vrf

**Command mode:** config

**TACACS role:** operator

**Note:**

- Require auto-complete for all configured vrf on the system, except for mgmt0, mgmt-ncc-0, mgmt-ncc-1

- reconfiguring vrf will result in bmp session reset

- no command return vrf to default value

**Help line:** Set bmp server vrf

**Parameter table:**

+-------------+--------------------------------------------+-----------------------------------+
| Parameter   | Values                                     | Default value                     |
+=============+============================================+===================================+
| vrf         | All existing configured vrf in system      | default                           |
|             | Except mgmt0, mgmt-ncc-0, mgmt-ncc-1       |                                   |
+-------------+--------------------------------------------+-----------------------------------+

