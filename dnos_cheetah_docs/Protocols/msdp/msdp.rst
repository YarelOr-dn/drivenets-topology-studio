protocols msdp
--------------

**Minimum user role:** operator

Enters the MSDP configuration hierarchy level.

**Command syntax: msdp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)#


**Removing Configuration**

To disable the MSDP protocol:
::

    dnRouter(cfg-protocols)# no msdp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
