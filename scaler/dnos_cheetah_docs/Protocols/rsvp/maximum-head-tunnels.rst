protocols rsvp maximum-head-tunnels
-----------------------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. To set thresholds on RSVP-TE head tunnels:

**Command syntax: maximum-head-tunnels [maximum]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  there is no limitation for how many rsvp head tunnels user can configure, or how many rsvp head tunnel can be created

- The thresholds are for generating system-events only. They do not affect in any way the number of installed tunnels.

- The thresholds apply to all tunnel types (primary, bypass, auto-bypass, auto-mesh).

**Parameter table**

+-----------+----------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                | Range   | Default |
+===========+============================================================================+=========+=========+
| maximum   | maximum rsvp-te head tunnel limit, exceeding the limit will invoke warning | 1-29999 | 500     |
+-----------+----------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# maximum-head-tunnels 150


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no maximum-head-tunnels

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.2    | Command introduced                |
+---------+-----------------------------------+
| 15.0    | Updated max-tunnels default value |
+---------+-----------------------------------+
