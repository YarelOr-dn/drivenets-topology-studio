protocols rsvp maximum-tunnels threshold
----------------------------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. To set thresholds on RSVP-TE tunnels:

In the above example, the maximum number of RSVP-TE tunnels in the RIB is set to 6,000 and the threshold is set to 70%. This means that when the number of tunnels in the RIB reaches 4,200, a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 6,000.

**Command syntax: maximum-tunnels [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- The thresholds are for generating system-events only. They do not affect in any way the number of installed tunnels.

- The thresholds apply to all tunnel types (primary, bypass, auto-bypass, auto-mesh) and for all tunnel roles (head, transit, tail) combined.

- When the number of tunnels drops below a threshold, a system-event notification is generated.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| maximum   | maximum rsvp-te tunnel limit, exceeding the limit will invoke a periodic warning | 1-29999 | 7000    |
+-----------+----------------------------------------------------------------------------------+---------+---------+
| threshold | maximum rsvp-te tunnel threshold, exceeding the threshold will invoke a warning  | 1-100   | 75      |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# maximum-tunnels 6000 threshold 70


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no maximum-tunnels

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.0    | Command introduced                |
+---------+-----------------------------------+
| 15.0    | Updated max-tunnels default value |
+---------+-----------------------------------+
