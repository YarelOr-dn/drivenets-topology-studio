protocols ospfv3 timers
-----------------------

**Minimum user role:** operator

Configure timers

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# timers
    dnRouter(cfg-protocols-ospfv3-timers)#


**Removing Configuration**

To revert all timers parameters to their default values: 
::

    dnRouter(cfg-protocols-ospfv3)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
