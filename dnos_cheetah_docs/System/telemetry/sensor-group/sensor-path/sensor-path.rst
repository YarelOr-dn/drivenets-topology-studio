system telemetry sensor-group sensor-path
-----------------------------------------

**Minimum user role:** operator

This command configures a sensor-path to collect data from the system.

**Command syntax: sensor-path [sensor-path]**

**Command mode:** config

**Hierarchies**

- system telemetry sensor-group

**Note**

- Up to 16 sensor paths can be configured in a sensor group.

- The YANG path can point to a container, list, or leaf node.

- The YANG path can target specific elements, such as "/drivenets-top/interfaces/interface[name='bundle-1']/oper-items/counters/forwarding-counters", pinpointing an individual interface forwarding counters.

- Wildcards ("\*") can be used to select multiple elements that match a pattern, such as "/drivenets-top/interfaces/interface[name='bundle-\*']", to monitor all interfaces with names starting with "bundle".

- It is recommended to select specific, granular YANG paths for the sensor group to ensure minimal and relevant telemetry data is monitored. Avoid high-level hierarchy selections to prevent excess data transmission and maintain system performance.

**Parameter table**

+-------------+---------------------------+-------+---------+
| Parameter   | Description               | Range | Default |
+=============+===========================+=======+=========+
| sensor-path | The YANG path to a sensor | \-    | \-      |
+-------------+---------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# sensor-group default
    dnRouter(cfg-system-telemetry-snsrgrp)# sensor-path "/drivenets-top/interface/interface[name='bundle*'']/oper-items/counters/forwarding-counters"
    dnRouter(cfg-telemetry-snsrgrp-snsrpth)#
    dnRouter(cfg-system-telemetry-snsrgrp)# sensor-path "/drivenets-top/interface/interface[name='ge100-0/0/1']/oper-items/counters/ethernet-counters/rx-octets"
    dnRouter(cfg-telemetry-snsrgrp-snsrpth)#
    dnRouter(cfg-system-telemetry-snsrgrp)# sensor-path "/drivenets-top/interface/interface[name='ge100-0/0/1']"
    dnRouter(cfg-telemetry-snsrgrp-snsrpth)#


**Removing Configuration**

To delete sensor path from sensor group:
::

    dnRouter(cfg-system-telemetry)# no sensor-path "/drivenets-top/interface/interface[name='ge100-0/0/1']"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
