debug twamp - supported in v11.1
--------------------------------

**Command syntax: [parameter]**

**Description:** Debug TWAMP events

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug twamp
	dnRouter(cfg)# debug twamp messages 
	dnRouter(cfg)# debug twamp messages data
	dnRouter(cfg)# debug twamp messages control
	dnRouter(cfg)# debug twamp events
	
	dnRouter(cfg)# no debug twamp messages
	dnRouter(cfg)# no debug twamp events
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  setting "debug twamp" will enable all debug features

**Help line:** Debug TWAMP events

**Parameter table:**

+-----------+----------+----------------------------+
| Parameter | Values   | description                |
+===========+==========+============================+
| parameter | events   | Debug TWAMP events         |
+-----------+----------+----------------------------+
|           | messages | Enter messages debug level |
+-----------+----------+----------------------------+
