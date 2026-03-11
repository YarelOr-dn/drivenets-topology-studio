protocols lacp
--------------

**Minimum user role:** operator

To start the LACP process:

**Command syntax: lacp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)#


**Removing Configuration**

To remove the lacp protocol:
::

    dnRouter(cfg-protocols)# no lacp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
