debug grpc - supported in v11.1
-------------------------------

**Command syntax: [parameter]**

**Description:** Debug grpc

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug grpc
	dnRouter(cfg)# debug grpc messages 
	dnRouter(cfg)# debug grpc events
	
	dnRouter(cfg)# no debug grpc messages
	dnRouter(cfg)# no debug grpc events
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  setting "debug grpc" will enable all debug features

**Help line:** Debug gRPC

**Parameter table:**

+-----------+----------+----------------------------+
| Parameter | Values   | description                |
+===========+==========+============================+
| parameter | events   | Debug gRPC events          |
+-----------+----------+----------------------------+
|           | messages | Enter messages debug level |
+-----------+----------+----------------------------+
