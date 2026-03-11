system telemetry destination-group destination port retry-timer
---------------------------------------------------------------

**Minimum user role:** operator

To configure the retry-timer for a telemetry destination:

**Command syntax: retry-timer [retry-timer]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group destination port

**Parameter table**

+-------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter   | Description                                                                      | Range   | Default |
+=============+==================================================================================+=========+=========+
| retry-timer | Time before another connection is used to the destination after a failure to     | 10-1200 | 30      |
|             | establish the connection.                                                        |         |         |
+-------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-destgrp)# destination ip 100.0.0.2 port 5000
    dnRouter(cfg-telemetry-dstgrp-dest)#
    dnRouter(cfg-telemetry-dstgrp-dest)# retry-timer 20


**Removing Configuration**

To revert retry-timer to default:
::

    dnRouter(cfg-system-telemetry-dest-group-dest)# no retry-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
