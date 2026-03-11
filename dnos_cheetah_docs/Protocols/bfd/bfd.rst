protocols bfd
-------------

**Minimum user role:** operator

To enter the BFD configuration hierarchy.

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bfd
    dnRouter(cfg-protocols-bfd)#


**Removing Configuration**

To disable the BFD process:
::

    dnRouter(cfg-protocols)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
