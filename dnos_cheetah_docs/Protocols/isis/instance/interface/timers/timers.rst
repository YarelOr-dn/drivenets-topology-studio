protocols isis instance interface timers
----------------------------------------

**Minimum user role:** operator

To configure IS-IS interface timers and enter timers configuration mode:


**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# timers
    dnRouter(cfg-inst-if-timers)#


**Removing Configuration**

To revert all timers to their default value:
::

    dnRouter(cfg-isis-inst-if)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
