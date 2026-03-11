system telemetry destination-group destination port compression
---------------------------------------------------------------

**Minimum user role:** operator

To configure telemetry compression to a destination:

**Command syntax: compression [compression]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group destination port

**Parameter table**

+-------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter   | Description                                                                      | Range    | Default |
+=============+==================================================================================+==========+=========+
| compression | The compression type to use on the data. If no value is entered, no compression  | | none   | none    |
|             | is used.                                                                         | | gzip   |         |
+-------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-destgrp)# destination ip 100.0.0.2 port 5000
    dnRouter(cfg-telemetry-dstgrp-dest)#
    dnRouter(cfg-telemetry-dstgrp-dest)# compression gzip
    dnRouter(cfg-telemetry-dstgrp-dest)# compression none


**Removing Configuration**

To revert compression to default:
::

    dnRouter(cfg-telemetry-dstgrp-dest)# no compression

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
