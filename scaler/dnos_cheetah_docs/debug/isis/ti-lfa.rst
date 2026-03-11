ti-lfa
------

**Minimum user role:** operator

To log main events in isis sr ti-lfa logic:

**Command syntax: ti-lfa**

**Command mode:** config

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# debug
    dnRouter(cfg-debug)# isis
    dnRouter(cfg-debug-isis)# ti-lfa


**Removing Configuration**

To disable this debug:
::

    dnRouter(cfg-debug-isis)# no ti-lfa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
