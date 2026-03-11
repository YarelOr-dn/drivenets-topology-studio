system sztp bootstrap-server priority
-------------------------------------

**Minimum user role:** admin

The configure priority of the bootstrap server. The priority is used to determine the order in which the bootstrap server is used by the client. The lower the priority, the first the bootstrap server is used by the client. If priority is equal, the client will use the bootstrap server with the lowest IP address.

**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- system sztp bootstrap-server

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| priority  | bootstrap server priority. When multiple servers are set, DNOS accesses          | 1-255 | 255     |
|           | bootstrap servers according to their priority. I.e. first DNOS will attempt      |       |         |
|           | bootstrap server with lowest priority                                            |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# bootstrap-server ::1
    dnRouter(cfg-system-sztp-bootsrv)# priority 2


**Removing Configuration**

To revert priority to default:
::

    dnRouter(cfg-system-sztp-bootsrv)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
