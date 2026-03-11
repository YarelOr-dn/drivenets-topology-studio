protocols lldp timers
---------------------

**Minimum user role:** operator

To adjust the intervals at which LLDP messages are sent:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Example**
::

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# timers


**Removing Configuration**

To return the timers to their default value:
::

    dnRouter(cfg-protocols-lldp)# no timers

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Command reintroduced          |
+---------+-------------------------------+
