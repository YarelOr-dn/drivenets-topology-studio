system grpc listen-port - supported in v11.1
--------------------------------------------

**Command syntax: listen-port [port]**

**Description:** configure listen port for gRPC server.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# grpc
	dnRouter(cfg-system-grpc)# listen-port 60000
	
	dnRouter(cfg-sysetm-grpc)# no listen-port 
	
**Command mode:** config

**TACACS role:** operator

**Note:**

no command change listen-port to the default.

**Help line:** configure listen port for gRPC server.

**Parameter table:**

+-----------+------------+---------------+
| Parameter | Values     | Default value |
+===========+============+===============+
| port      | 1024-65535 | 50051         |
+-----------+------------+---------------+
