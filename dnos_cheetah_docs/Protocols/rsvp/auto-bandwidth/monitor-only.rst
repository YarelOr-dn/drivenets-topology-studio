protocols rsvp auto-bandwidth monitor-only
------------------------------------------

**Minimum user role:** operator

This command instructs RSVP to do all the auto-bandwidth calculations according to the configuration and record them, but without actually performing any changes. The recorded information is available in show commands.
To enable/disable monitoring-only:

**Command syntax: monitor-only [monitor-only]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Note**
.. -  'no monitor-only' - return to disabled state

-  No adjustments will be made even if you explicitly run the "run rsvp auto-bandwidth adjust" command.

**Parameter table**

+--------------+------------------------------------------------------------------------------+--------------+----------+
| Parameter    | Description                                                                  | Range        | Default  |
+==============+==============================================================================+==============+==========+
| monitor-only | maximum sampled traffic rate is monitored but doesnt effect tunnel bandwidth | | enabled    | disabled |
|              |                                                                              | | disabled   |          |
+--------------+------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# monitor-only enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no monitor-only

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
