microloop-avoidance
-------------------

**Minimum user role:** operator

To log main events in isis sr microloop-avoidance logic:

**Command syntax: microloop-avoidance**

**Command mode:** config

**Note**

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the ospfd log file for ospf microloop-avoidance and in isisd for isis microloop-avoidance.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# debug
    dnRouter(cfg-debug)# isis
    dnRouter(cfg-debug-isis)# microloop-avoidance


**Removing Configuration**

To disable this debug:
::

    dnRouter(cfg-debug-isis)# no microloop-avoidance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.3    | Command introduced |
+---------+--------------------+
