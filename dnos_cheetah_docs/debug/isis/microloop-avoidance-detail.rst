microloop-avoidance-detail
--------------------------

**Minimum user role:** operator

To log all events in isis sr microloop-avoidance logic:

**Command syntax: microloop-avoidance**

**Command mode:** config

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# debug
    dnRouter(cfg-debug)# isis
    dnRouter(cfg-debug-isis)# microloop-avoidance-detail


**Removing Configuration**

To disable this debug:
::

    dnRouter(cfg-debug-isis)# no microloop-avoidance-detail

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.3    | Command introduced |
+---------+--------------------+
