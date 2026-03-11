tracking-policy tracking-group monitor-ipv4-route vrf
-----------------------------------------------------

**Minimum user role:** operator

Configure an ipv4 route to be monitored in the tracking group

**Command syntax: monitor-ipv4-route [ipv4-route] vrf [vrf-instance]** weight [weight]

**Command mode:** config

**Hierarchies**

- tracking-policy tracking-group

**Parameter table**

+--------------+-------------------------------------------------------+-----------+---------+
| Parameter    | Description                                           | Range     | Default |
+==============+=======================================================+===========+=========+
| ipv4-route   | route                                                 | A.B.C.D/x | \-      |
+--------------+-------------------------------------------------------+-----------+---------+
| vrf-instance | VRF instance to which the route belongs, or 'default' | \-        | \-      |
+--------------+-------------------------------------------------------+-----------+---------+
| weight       | Provide an optional weight value                      | 0-65535   | 0       |
+--------------+-------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-ipv4-route 192.168.1.1/32
    dnRouter(cfg-trkpl-trkgrp)#
    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-ipv4-route 192.168.1.1/32 vrf vrf-instance1
    dnRouter(cfg-trkpl-trkgrp)#
    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-ipv4-route 192.168.1.1/32 weight 200
    dnRouter(cfg-trkpl-trkgrp)#
    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)# monitor-ipv4-route 192.168.1.1/32 vrf vrf-instance1 weight 200
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To remove the route from its association with the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-ipv4-route 192.168.1.1/32

To restore the vrf to the default-vrf but to leave the route in the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-ipv4-route 192.168.1.1/32 vrf vrf-instance1

To remove the weight value but to leave the route in the tracking group
::

    dnRouter(cfg-trkpl-trkgrp)# no monitor-ipv4-route 192.168.1.1/32 weight 200

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
