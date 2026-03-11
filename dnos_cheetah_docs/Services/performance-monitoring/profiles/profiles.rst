services performance-monitoring profiles
----------------------------------------

**Minimum user role:** operator

To configure performance monitoring profiles:

**Command syntax: profiles**

**Command mode:** config

**Hierarchies**

- services performance-monitoring

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)#


**Removing Configuration**

To remove the performance monitoring profiles:
::

    dnRouter(cfg-srv-pm)# no profiles

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
