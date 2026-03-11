protocols rsvp timers
---------------------

**Minimum user role:** operator

You can set timers to:

- Terminate the RSVP session if refresh messages are not received (determined by "rsvp timers refresh-interval" and "rsvp timers refresh-multiplier")

- Reset the tunnel when the router is unable to establish a tunnel (determined by "rsvp timers retry")

To configure RSVP timers, enter timers configuration mode:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)#


**Removing Configuration**

To revert all timers to their default values:
::

    dnRouter(cfg-protocols-rsvp)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
