system dns
----------

**Minimum user role:** operator

To configure a DNS for the system:

**Command syntax: dns**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)#


**Removing Configuration**

Removes static DNS configuration:
::

    dnRouter(cfg-system)# no dns

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
