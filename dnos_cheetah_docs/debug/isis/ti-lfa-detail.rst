ti-lfa-detail
-------------

**Minimum user role:** operator

To log all events in isis sr ti-lfa logic:

**Command syntax: ti-lfa-detail**

**Command mode:** config

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# debug
    dnRouter(cfg-debug)# isis
    dnRouter(cfg-debug-isis)# ti-lfa-detail


**Removing Configuration**

To disable this debug:
::

    dnRouter(cfg-debug-isis)# no ti-lfa-detail

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+

