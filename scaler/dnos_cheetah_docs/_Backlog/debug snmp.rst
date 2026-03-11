debug snmp 
-----------

**Command syntax: debug snmp** [parameter]

**Description:** Debug SNMP events

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug snmp
	dnRouter(cfg)# debug snmp messages
	dnRouter(cfg)# debug snmp events
	
	dnRouter(cfg)# no debug snmp messages
	dnRouter(cfg)# no debug snmp events
	
	dnRouter# set debug snmp messages
	dnRouter# set debug snmp events
	
	dnRouter#no set debug snmp messages
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  setting "debug snmp" will enable all debug features

**Help line:** Debug SNMP events

**Parameter table:**

+-----------+----------+---------------------+
| Parameter | Values   | description         |
+===========+==========+=====================+
| parameter | messages | Debug SNMP messages |
+-----------+----------+---------------------+
|           | events   | Debug SNMP events   |
+-----------+----------+---------------------+
