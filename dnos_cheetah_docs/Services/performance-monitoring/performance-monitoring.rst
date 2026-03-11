services performance-monitoring
-------------------------------

**Minimum user role:** operator

DNOS supports performance monitoring.

**Command syntax: performance-monitoring**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)#


**Removing Configuration**

To remove the performance monitoring configurations:
::

    dnRouter(cfg-srv)# no performance-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
