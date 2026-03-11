ospf capability-opaque- N/A for this version
--------------------------------------------

**Command syntax: capability-opaque [admin-state]**

**Description:** Support Opaque LSA (RFC2370) as fundament for MPLS Traffic Engineering LSA.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ospf
	dnRouter(cfg-protocols-ospf)# capability-opaque disabled
	
	dnRouter(cfg-protocols-ospf)# no capability-opaque
	
**Command mode:** config

**TACACS role:** operator

**Note:**

opaque is enabled by default

no command returns capability-opaque to default state - enabled

**Help line:** Support Opaque LSA

**Parameter table:**

+-------------+-------------------+---------------+
| Parameter   | Values            | Default value |
+=============+===================+===============+
| admin-state | enabled, disabled | enabled       |
+-------------+-------------------+---------------+
