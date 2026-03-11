lacp interface force-up
-----------------------

**Command syntax: interface [interface-name]** force-up [force-up]

**Description:**

When configured enabled, feature forcing LACP to up state on a bundle in case a neighbor device is undergoing a change which may impact LACP session.

i.e, neighbor device is undergoing SW upgrade or configuration change.

configured interface is onlybundle interfacetype

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# lacp
	
	dnRouter(cfg-protocols-lacp)# interface bundle-2
	dnRouter(cfg-protocols-lacp-if)# force-up enabled
	
	dnRouter(cfg-protocols-lacp)# interface bundle-1
	dnRouter(cfg-protocols-lacp-if)# force-up disabled
	
	dnRouter(cfg-protocols-lacp-if)# no force-up
	
**Command mode:** config

**TACACS role:** operator

**Note:** no command removes the force-up value from the configuration.

**Help line:** Configure force-up feature on an interface

**Parameter table:**

+----------------+--------------------+---------------+
| Parameter      | Values             | Default value |
+================+====================+===============+
| Interface-name | bundle-<bundle id> |               |
+----------------+--------------------+---------------+
| Force-up       | enabled            | disabled      |
|                |                    |               |
|                | disabled           |               |
+----------------+--------------------+---------------+
