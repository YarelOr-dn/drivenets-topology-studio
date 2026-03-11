protocols ospf
--------------

**Minimum user role:** operator

Enters the OSPF configuration hierarchy level.

**Command syntax: ospf**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The no command will remove the ospf protocol.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)#


**Removing Configuration**

To remove the OSPF protocol
::

    dnRouter(cfg-protocols)# no ospf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
