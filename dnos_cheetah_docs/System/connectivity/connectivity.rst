system connectivity
-------------------

**Minimum user role:** operator

DNOS cluster connectivity pairings,
defines connections between smartNICs to WBOXes.

**Command syntax: connectivity**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-sys)# connectivity
    dnRouter(cfg-sys-conn)#


**Removing Configuration**

To remove entire cluster connnectivity pairings:
::

    dnRouter(cfg-srv)# no connectivity

**Command History**

+----------+--------------------+
| Release  | Modification       |
+==========+====================+
| 18.0.11  | Command introduced |
+----------+--------------------+
