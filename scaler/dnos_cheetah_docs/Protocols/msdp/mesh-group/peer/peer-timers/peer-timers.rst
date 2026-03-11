protocols msdp mesh-group peer peer-timers
------------------------------------------

**Minimum user role:** operator

You can use this command to configure the MSDP peer timers hierarchy.

The timers hierarchy also exists under msdp default-peer and msdp mesh-group.

**Command syntax: peer-timers**

**Command mode:** config

**Hierarchies**

- protocols msdp mesh-group peer

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# peer-timers
    dnRouter(cfg-protocols-msdp-peer-timers)#


**Removing Configuration**

To disable the peer-timers process:
::

    dnRouter(cfg-protocols-msdp)# no peer-timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
