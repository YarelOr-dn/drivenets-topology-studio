protocols isis instance seamless-bfd
------------------------------------

**Minimum user role:** operator

To configure IS-IS to advertise seamless-bfd reflector discriminators:

**Command syntax: seamless-bfd**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# seamless-bfd
    dnRouter(cfg-isis-inst-s_bfd)#


**Removing Configuration**

To stop the isis process from advertising seamless-bfd relector discriminators
::

    dnRouter(cfg-protocols-isis-inst)# no seamless-bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
