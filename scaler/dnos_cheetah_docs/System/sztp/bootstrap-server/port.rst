system sztp bootstrap-server port
---------------------------------

**Minimum user role:** admin

To configure the port on which the bootstrap server listens to bootstrap information requests and progress updates from the client.

**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system sztp bootstrap-server

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| port      | The port number the bootstrap server listens on.  If no port is specified, the   | 0-65535 | 443     |
|           | IANA-assigned port for 'https' (443) is used.                                    |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# bootstrap-server ::1
    dnRouter(cfg-system-sztp-bootsrv)# port 9339


**Removing Configuration**

To revert port to default:
::

    dnRouter(cfg-system-sztp-bootsrv)# no port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
