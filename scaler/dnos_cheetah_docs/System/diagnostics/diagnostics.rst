system diagnostics
------------------

**Minimum user role:** operator

To configure diagnostics:


**Command syntax: diagnostics**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)#


**Removing Configuration**

Remove all configured diagnostics
::

    dnRouter(cfg-system)# no diagnostics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
