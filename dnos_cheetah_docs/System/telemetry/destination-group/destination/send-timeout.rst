system telemetry destination-group destination port send-timeout
----------------------------------------------------------------

**Minimum user role:** operator

To configure the send-timeout for a telemetry destination:

**Command syntax: send-timeout [send-timeout]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group destination port

**Parameter table**

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter    | Description                                                                                                                                               | Range | Default |
+==============+===========================================================================================================================================================+=======+=========+
| send-timeout | The duration in seconds that the system waits for acknowledgment of a sent packet before considering it lost and retransmitting it. 0 means no timeout.   | 0-30  | 30      |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-destgrp)# destination ip 100.0.0.2 port 5000
    dnRouter(cfg-telemetry-dstgrp-dest)#
    dnRouter(cfg-telemetry-dstgrp-dest)# send-timeout 20


**Removing Configuration**

To revert send-timeout to default:
::

    dnRouter(cfg-system-telemetry-dest-group-dest)# no send-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
