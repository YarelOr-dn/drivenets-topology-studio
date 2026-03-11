tracking-policy tracking-group delay
------------------------------------

**Minimum user role:** operator

Configure the Delay value to be applied, when the conditions have been met and before performing the action.

**Command syntax: delay [delay]**

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+-----------+-----------------------------------------------------------------+---------+---------+
| Parameter | Description                                                     | Range   | Default |
+===========+=================================================================+=========+=========+
| delay     | the delay (seconds) to be applied before performing the action. | 0-65535 | 0       |
+-----------+-----------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# delay 300
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-trkpl-trkgrp)# no delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
