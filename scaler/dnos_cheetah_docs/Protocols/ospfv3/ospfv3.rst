protocols ospfv3
----------------

**Minimum user role:** operator

Enters the OSPFV3 configuration hierarchy level.

**Command syntax: ospfv3**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The 'no' command will remove the ospf protocol.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)#


**Removing Configuration**

To remove the OSPFv3 protocol
::

    dnRouter(cfg-protocols)# no ospfv3

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
