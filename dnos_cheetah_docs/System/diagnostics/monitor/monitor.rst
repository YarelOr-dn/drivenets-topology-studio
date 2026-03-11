system diagnostics monitor
--------------------------

**Minimum user role:** operator

To configure monitor:


**Command syntax: monitor**

**Command mode:** config

**Hierarchies**

- system diagnostics

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)# monitor
    dnRouter(cfg-system-diagnostics-monitor)#


**Removing Configuration**

Remove all configured monitor
::

    dnRouter(cfg-system-diagnostics)# no monitor

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
