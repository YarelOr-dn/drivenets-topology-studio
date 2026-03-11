tracking-policy tracking-group monitor-ipv6-route vrf
-----------------------------------------------------

**Minimum user role:** operator

Configure an ipv6 route to be monitored in the tracking group

**Command syntax: monitor-ipv6-route [ipv6-route] vrf [vrf-instance]** weight [weight]

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+--------------+-------------------------------------------------------+------------+---------+
| Parameter    | Description                                           | Range      | Default |
+==============+=======================================================+============+=========+
| ipv6-route   | route                                                 | X:X::X:X/x | \-      |
+--------------+-------------------------------------------------------+------------+---------+
| vrf-instance | VRF instance to which the route belongs, or 'default' | \-         | \-      |
+--------------+-------------------------------------------------------+------------+---------+
| weight       | Provide an optional weight value                      | 0-65535    | 0       |
+--------------+-------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-ipv6-route 1001:2345::10:23/128
    dnRouter(cfg-trkpl-trkgrp)#
    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-ipv6-route 1001:2345::10:23/128 weight 300
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To remove the route from its association with the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-ipv6-route 1001:2345::10:23/128

To remove the weight value but to leave the route in the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-ipv6-route 1001:2345::10:23/128 weight 300

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
