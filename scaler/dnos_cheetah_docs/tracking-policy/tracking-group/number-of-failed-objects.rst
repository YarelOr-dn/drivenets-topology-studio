tracking-policy tracking-group number-of-failed-objects
-------------------------------------------------------

**Minimum user role:** operator

Define the number of failed objects, such that when the number of failed objects reaches this value then the action shall be applied. If the 'number-of-failed-objects' is configured then the 'operation' and 'weight-threshold'' cannot be configured.

**Command syntax: number-of-failed-objects [number-of-failed-objects]**

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter                | Description                                                                      | Range   | Default |
+==========================+==================================================================================+=========+=========+
| number-of-failed-objects | When the number of failed objects reaches this value, then the action will be    | 1-65535 | \-      |
|                          | applied.                                                                         |         |         |
+--------------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# number-of-failed-objects 5
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To revert the number-of-failed-objects to its default of 1
::

    dnRouter(cfg-trkpl-trkgrp)# no number-of-failed-objects

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
