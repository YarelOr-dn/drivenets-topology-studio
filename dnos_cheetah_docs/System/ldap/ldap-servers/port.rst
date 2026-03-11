system ldap ldap-server priority port
-------------------------------------

**Minimum user role:** admin

To define the port that is used by the server: If the port is not configured, the server uses port 636.

**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-server priority

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| port      | The port on which the server uses. If the port is not configured, the server     | 0..65535| 636     |
|           | uses port 636                                                                    |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-server priority 3
    dnRouter(cfg-system-ldap-server)# port 630


**Removing Configuration**

To revert the port to the default:
::

    dnRouter(cfg-system-ldap-server)# no port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
