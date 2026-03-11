system cprl all-routers
-----------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for all routers:

**Command syntax: all-routers**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# all-routers
    dnRouter(cfg-system-cprl-all-routers)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for all routers:
::

    dnRouter(cfg-system-cprl)# no all-routers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
