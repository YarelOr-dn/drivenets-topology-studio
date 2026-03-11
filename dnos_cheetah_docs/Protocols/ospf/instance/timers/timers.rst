protocols ospf instance timers
------------------------------

**Minimum user role:** operator

Configure timers

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# timers
    dnRouter(cfg-protocols-ospf-timers)#


**Removing Configuration**

To revert all timers parameters to their default values: 
::

    dnRouter(cfg-protocols-ospf)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
