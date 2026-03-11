protocols bfd seamless-bfd
--------------------------

**Minimum user role:** operator

To enter the Seamless BFD configuration hierarchy.

**Command syntax: seamless-bfd**

**Command mode:** config

**Hierarchies**

- protocols bfd

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)#


**Removing Configuration**

To disable the Seamless BFD process:
::

    dnRouter(cfg-protocols)# no seamless-bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
