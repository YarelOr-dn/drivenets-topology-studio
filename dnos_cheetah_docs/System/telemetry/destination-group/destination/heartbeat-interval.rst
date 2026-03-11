system telemetry destination-group destination port heartbeat-interval
----------------------------------------------------------------------

**Minimum user role:** operator

To configure the heartbeat-interval for a telemetry destination:

**Command syntax: heartbeat-interval [heartbeat-interval]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group destination port

**Parameter table**

+--------------------+-----------------------------------------------------------------------+---------+---------+
| Parameter          | Description                                                           | Range   | Default |
+====================+=======================================================================+=========+=========+
| heartbeat-interval | Heartbeat interval per destination in seconds (0 means no heartbeat)  | 0-86400 | 0       |
+--------------------+-----------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-destgrp)# destination ip 100.0.0.2 port 5000
    dnRouter(cfg-telemetry-dstgrp-dest)#
    dnRouter(cfg-telemetry-dstgrp-dest)# heartbeat-interval 20


**Removing Configuration**

To revert heartbeat-interval to default:
::

    dnRouter(cfg-system-telemetry-dest-group-dest)# no heartbeat-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
