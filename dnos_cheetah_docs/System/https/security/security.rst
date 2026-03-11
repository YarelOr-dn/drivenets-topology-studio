system https security
---------------------

**Minimum user role:** operator

HTTPS server might require the security configuration of the client.

To configure the security configuration of the client, enter the HTTPS security configuration mode:

**Command syntax: security**

**Command mode:** config

**Hierarchies**

- system https

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# https
    dnRouter(cfg-system-https)# security


**Removing Configuration**

To remove all global security configuration for HTTPS:
::

    dnRouter(cfg-system-https)# no security

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
