protocols ospf instance seamless-bfd
------------------------------------

**Minimum user role:** operator

To configure OSPF to advertise seamless-BFD reflector discriminators:

**Command syntax: seamless-bfd**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance ospf1
    dnRouter(cfg-protocols-ospf-inst)# seamless-bfd
    dnRouter(cfg-ospf-inst-s_bfd)#


**Removing Configuration**

To stop the ospf process from advertising seamless-bfd relector discriminators
::

    dnRouter(cfg-protocols-ospf-inst)# no seamless-bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
