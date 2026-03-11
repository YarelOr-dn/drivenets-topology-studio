system telemetry destination-group destination port
---------------------------------------------------

**Minimum user role:** operator

To configure the destination address where dial-out telemetry data is transmitted:

**Command syntax: destination [ip] port [port]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group

**Note**

- Up to 4 destinations can be configured in destination group.

**Parameter table**

+-----------+-----------------------+--------------+---------+
| Parameter | Description           | Range        | Default |
+===========+=======================+==============+=========+
| ip        | IPv4 or IPv6 address. | | A.B.C.D    | \-      |
|           |                       | | X:X::X:X   |         |
+-----------+-----------------------+--------------+---------+
| port      | Port number.          | 0-65535      | \-      |
+-----------+-----------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-destgrp)# destination 100.0.0.2 port 5000
    dnRouter(cfg-telemetry-dstgrp-dest)#
    {'dnRouter(cfg-system-telemetry-destgrp)# destination a1b:2c:2f4c:1:': 'port 7503'}
    dnRouter(cfg-telemetry-dstgrp-dest)#


**Removing Configuration**

To remove destination from destination group:
::

    dnRouter(cfg-system-telemetry-destgrp)# # no destination ip a1b:2c:2f4c:1:: port 7503

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
