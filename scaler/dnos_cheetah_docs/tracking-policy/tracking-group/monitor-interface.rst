tracking-policy tracking-group monitor-interface
------------------------------------------------

**Minimum user role:** operator

Configure an interface to be monitored in the tracking group

**Command syntax: monitor-interface [name]** weight [weight]

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Note**

- support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y/irbX>

**Parameter table**

+-----------+----------------------------------+------------------+---------+
| Parameter | Description                      | Range            | Default |
+===========+==================================+==================+=========+
| name      | interface name                   | | string         | \-      |
|           |                                  | | length 1-255   |         |
+-----------+----------------------------------+------------------+---------+
| weight    | Provide an optional weight value | 0-65535          | 0       |
+-----------+----------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-interface ge100-0/0/1.10
    dnRouter(cfg-trkpl-trkgrp)#
    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-interface ge100-0/0/1.10 weight 100
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To remove the interface from its association with the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-interface ge100-0/0/1.10

To remove the weight value but to leave the interface in the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-interface ge100-0/0/1.10 weight 100

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
