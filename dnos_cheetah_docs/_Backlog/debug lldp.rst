debug lldp 
-----------

**Command syntax: debug lldp** [parameter]

**Description:** Debug LLDP events

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug lldp messages
	dnRouter(cfg)# debug lldp neighbors
	dnRouter(cfg)# debug lldp
	
	
	dnRouter(cfg)# no debug ldp messages
	dnRouter(cfg)# no debug ldp neighbors
	dnRouter(cfg)# no debug lldp
	
	dnRouter# set debug lldp messages
	dnRouter# set debug lldp neighbors
	dnRouter# set debug lldp
	
	dnRouter# no set debug ldp neighbors
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  setting "debug lldp" will enable all debug features

**Help line:** Debug LLDP events

**Parameter table:**

+-----------+-----------+----------------------+
| Parameter | Values    | description          |
+===========+===========+======================+
| parameter | messages  | Debug LLDP messages  |
+-----------+-----------+----------------------+
|           | neighbors | Debug LLDP neighbors |
+-----------+-----------+----------------------+
