system sztp security verify-hostname
------------------------------------

**Minimum user role:** admin

To enable/disable verification of hostname in the bootstrap-server certificate

**Command syntax: verify-hostname [verify-hostname]**

**Command mode:** config

**Hierarchies**

- system sztp security

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter       | Description                                                                      | Range        | Default  |
+=================+==================================================================================+==============+==========+
| verify-hostname | Indicates whether the hostname in the certificate received by the bootstrap      | | enabled    | disabled |
|                 | server is checked for a match against the known hostname. If this is set as      | | disabled   |          |
|                 | 'enabled', the server's hostname in the received server certificate will be      |              |          |
|                 | compared against known hostname during the SZTP process. Setting it as           |              |          |
|                 | 'disabled' will skip this check.                                                 |              |          |
+-----------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# security
    dnRouter(cfg-system-sztp-security)# verify-hostname enabled


**Removing Configuration**

To revert verify-hostname to default:
::

    dnRouter(cfg-system-sztp-security)# no verify-hostname

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
