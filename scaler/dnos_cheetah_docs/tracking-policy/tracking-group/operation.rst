tracking-policy tracking-group operation
----------------------------------------

**Minimum user role:** operator

If the 'and' operation is configured then only when all the monitored objects fail will the action be applied. If the 'or' operation is configured then as soon as one of the monitored objects fails the action will be applied. If the 'operation' is configured then the 'weight-threshold' and 'number-of-failed-objects' cannot be configured.

**Command syntax: operation [tp-operation]**

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+--------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter    | Description                                                                      | Range   | Default |
+==============+==================================================================================+=========+=========+
| tp-operation | Apply 'and' or 'or' operation to the monitored objects 'and' implies that all    | | and   | \-      |
|              | objects must fail; while 'or' implies that one object has failed before          | | or    |         |
|              | performing the action                                                            |         |         |
+--------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# operation and
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To revert the invert-monitoring configuration to its default of disabled.
::

    dnRouter(cfg-trkpl-trkgrp)# no operation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
