services xconnect fallback admin-state- N/A for this version
------------------------------------------------------------

**Command syntax: fallback [xc-fb-id] admin-state [admin-state]**

**Description:** configure xconnect fallback service administrative state for each xconnect fallback id

Each xconnect fallback id has its own administrative state

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# xconnect
	dnRouter(cfg-srv-xc)# fallback 1 admin-state enabled
	dnRouter(cfg-srv-xc)# fallback 5 admin-state disabled
	
	dnRouter(cfg-srv-xc)# no fallback 1 admin-state
	dnRouter(cfg-srv-xc)# no fallback 5 admin-state
	
**Command mode:** operational

**TACACS role:** operator

**Note:** no command returns the xconnect fallback service administrative state to its default value.

**Help line:** configure xconnect fallback admin-state

**Parameter table:**

+-------------+------------------+---------------+
| Parameter   | Values           | Default value |
+=============+==================+===============+
| xc-fb-id    | 1-255            |               |
+-------------+------------------+---------------+
| admin-state | enabled/disabled | disabled      |
+-------------+------------------+---------------+
