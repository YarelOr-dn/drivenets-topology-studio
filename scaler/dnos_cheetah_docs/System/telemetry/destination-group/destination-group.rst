system telemetry destination-group
----------------------------------

**Minimum user role:** operator

To configure a destination group:

**Command syntax: destination-group [destination-group]**

**Command mode:** config

**Hierarchies**

- system telemetry

**Note**

- Up to 32 destination groups can be configured.

**Parameter table**

+-------------------+--------------------------------+------------------+---------+
| Parameter         | Description                    | Range            | Default |
+===================+================================+==================+=========+
| destination-group | Name of the destination group. | | string         | \-      |
|                   |                                | | length 1-255   |         |
+-------------------+--------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-dstgrp)#
    dnRouter(cfg-system)# telemetry destination-group production
    dnRouter(cfg-system-telemetry-dstgrp)#
    dnRouter(cfg-system)# telemetry destination-group staging
    dnRouter(cfg-system-telemetry-dstgrp)#


**Removing Configuration**

To delete the configuration under destination-group group:
::

    dnRouter(cfg-system-telemetry)# no destination-group lab

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
