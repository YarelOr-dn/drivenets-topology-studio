system https
------------

**Minimum user role:** operator

Configure HTTPS.

To configure HTTPS, enter the HTTPS configuration mode:

**Command syntax: https**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# https
    dnRouter(cfg-system-https)#


**Removing Configuration**

To revert all HTTPS configuration to default:
::

    dnRouter(cfg-system)# no https

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
