protocols igmp
--------------

**Minimum user role:** operator

To start the IGMP process:

**Command syntax: igmp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# igmp
    dnRouter(cfg-protocols-igmp)#


**Removing Configuration**

To disable the igmp process:
::

    dnRouter(cfg-protocols)# no igmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
