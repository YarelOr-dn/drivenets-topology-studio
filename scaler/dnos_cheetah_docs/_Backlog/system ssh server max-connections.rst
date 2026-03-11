system ssh server max-connections
---------------------------------

**Command syntax: server max-connections [max-connections]**

**Description:** configure maximum number of concurrent incoming requests for a new SSH sessions per minute for SSH server.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ssh
	dnRouter(cfg-system-ssh)# server
	dnRouter(cfg-system-ssh-server)# max-connections 30
	
	dnRouter(cfg-system-ssh-server)# no max-connections
	
**Command mode:** config

**TACACS role:** operator

**Note:**

-  no command returns the number of maximum connection request per minute to default

**Help line:**

**Parameter table:**

+-----------------+--------+---------------+
| Parameter       | Values | Default value |
+=================+========+===============+
| max-connections | 1-120  | 60            |
+-----------------+--------+---------------+
