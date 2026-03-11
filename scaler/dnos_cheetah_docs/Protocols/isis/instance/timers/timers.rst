protocols isis instance timers
------------------------------

**Minimum user role:** operator

To configure global IS-IS timers, enter the timers configuration level:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# timers
    dnRouter(cfg-isis-inst-timers)#


**Removing Configuration**

To revert all timers to their default value:
::

    dnRouter(cfg-protocols-isis-inst)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
