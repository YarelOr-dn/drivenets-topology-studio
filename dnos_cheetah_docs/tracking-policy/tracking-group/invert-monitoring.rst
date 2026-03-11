tracking-policy tracking-group invert-monitoring
------------------------------------------------

**Minimum user role:** operator

This setting defines whether invert-monitoring is enabled.
By default it is disabled and when the monitored objects fail the action is applied.
If invert-monitoring is enabled, when the monitored objects are available then the action is applied.

**Command syntax: invert-monitoring [invert-monitoring]**

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+-------------------+-----------------------------------------------------------------------------+--------------+----------+
| Parameter         | Description                                                                 | Range        | Default  |
+===================+=============================================================================+==============+==========+
| invert-monitoring | Invert the monitoring - perform action when monitored objects are available | | enabled    | disabled |
|                   |                                                                             | | disabled   |          |
+-------------------+-----------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# invert-monitoring enabled
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To revert the invert-monitoring configuration to its default of disabled.
::

    dnRouter(cfg-trkpl-trkgrp)# no invert-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
