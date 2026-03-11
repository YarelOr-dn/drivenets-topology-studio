system telemetry sensor-group
-----------------------------

**Minimum user role:** operator

A sensor group enables targeted monitoring of specific YANG model elements. It allows users to specify which portions of the YANG model are of interest and should be included in the telemetry subscription. A sensor group can encompass a range of YANG paths representing containers, lists, or leaf nodes.

**Command syntax: sensor-group [sensor-group]**

**Command mode:** config

**Hierarchies**

- system telemetry

**Note**

- Up to 512 sensor-groups groups can be configured.

**Parameter table**

+--------------+--------------------------+------------------+---------+
| Parameter    | Description              | Range            | Default |
+==============+==========================+==================+=========+
| sensor-group | Name of the sensor group | | string         | \-      |
|              |                          | | length 1-255   |         |
+--------------+--------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# sensor-group default
    dnRouter(cfg-system-telemetry-snsrgrp)#
    dnRouter(cfg-system-telemetry)# sensor-group bundle-collection
    dnRouter(cfg-system-telemetry-snsrgrp)#


**Removing Configuration**

To delete the configuration under sensor group:
::

    dnRouter(cfg-system-telemetry)# no sensor-group bundle-collection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
