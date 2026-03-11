debug system 
-------------

**Command syntax: debug system** [parameters]

**Description:** Debug system NCE events

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug system ncp
	dnRouter(cfg)# debug system ncf
	dnRouter(cfg)# debug system ncm
	dnRouter(cfg)# debug system 
	
	
	dnRouter(cfg)# no debug system ncp
	dnRouter(cfg)# no debug system ncf
	dnRouter(cfg)# no debug system ncm
	dnRouter(cfg)# no debug system 
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  setting "debug system" will enable all debug features, including all sub debug levels

-  the debug messages are written to /var/log/dn/system.log file

**Help line:** Debug OSPF events

**Parameter table:**

+-----------+--------+------------------------------------------------------+
| Parameter | Values | description                                          |
+===========+========+======================================================+
| parameter | ncc    | debug information of discovery/status change for ncc |
+-----------+--------+------------------------------------------------------+
|           | ncp    | debug information of discovery/status change for ncp |
+-----------+--------+------------------------------------------------------+
|           | ncf    | debug information of discovery/status change for ncf |
+-----------+--------+------------------------------------------------------+
|           | ncm    | debug information of discovery/status change for ncm |
+-----------+--------+------------------------------------------------------+
