system sztp security
--------------------

**Minimum user role:** admin

SZTP requires security configuration of the client, both for mutal authentication of the server and traffic encryption. 

To configure global security parameters, enter the SZTP security configuration mode:

**Command syntax: security**

**Command mode:** config

**Hierarchies**

- system sztp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# security


**Removing Configuration**

To remove all global security configuration for SZTP:
::

    dnRouter(cfg-system-sztp)# no security

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
