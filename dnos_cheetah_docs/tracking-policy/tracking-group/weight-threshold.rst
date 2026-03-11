tracking-policy tracking-group weight-threshold
-----------------------------------------------

**Minimum user role:** operator

Define the threshold, such that when the sum of the weights of the failed objects reaches this threshold then
the action shall be applied.
If 'weight-threshold' is configured then 'operation' and 'number-of-failed-objects' cannot be configured.

**Command syntax: weight-threshold [weight-threshold]**

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter        | Description                                                                      | Range        | Default |
+==================+==================================================================================+==============+=========+
| weight-threshold | When the sum of the weights of all the failed objects reaches this threshold     | 1-4294967295 | \-      |
|                  | then the action is performed.                                                    |              |         |
+------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# weight-threshold 500
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To revert the weight-threshold to its default of 0
::

    dnRouter(cfg-trkpl-trkgrp)# no weight-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
