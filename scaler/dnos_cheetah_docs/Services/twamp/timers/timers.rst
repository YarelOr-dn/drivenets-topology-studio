services twamp timers
---------------------

**Minimum user role:** operator

The server or session timeout parameters enable the system to clear resources, by not allowing inactive control connections or data sessions to remain available indefinitely.

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- services twamp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# timers


**Removing Configuration**

To revert all TWAMP timers to default:
::

    dnRouter(cfg-srv-twamp)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
