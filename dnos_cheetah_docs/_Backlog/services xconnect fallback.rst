services xconnect fallback- N/A for this version
------------------------------------------------

**Command syntax: fallback [xc-fb-id] interfaces [interface-1] [interface-2]**

**Description:** configure xconnect fallback service

Only single physical ports (non-bundles) can be configured for xconnect services

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# xconnect
	dnRouter(cfg-srv-xc)# fallback 1 interfaces ge100-1/2/1 ge100-1/2/2
	dnRouter(cfg-srv-xc)# fallback 5 interfaces ge100-5/4/1 ge100-5/4/2
	
	dnRouter(cfg-srv)# no xconnect
	
	dnRouter(cfg-srv-xc)# no fallback 1
	
**Command mode:** operational

**TACACS role:** operator

**Note:** no command removes the xconnect fallback service configuration

Validation:

A user cannot configure the same interface under a single xconnect service

A user cannot configure the same interface twice across all xconnect services

**Help line:** configure xconnect fallback interfaces

**Parameter table:**

+-------------+-------------------+---------------+
| Parameter   | Values            | Default value |
+=============+===================+===============+
| xc-fb-id    | 1-255             |               |
+-------------+-------------------+---------------+
| Interface-1 | ge100-<f>/<n>/<p> |               |
+-------------+-------------------+---------------+
| Interface-2 | ge100-<f>/<n>/<p> |               |
+-------------+-------------------+---------------+
