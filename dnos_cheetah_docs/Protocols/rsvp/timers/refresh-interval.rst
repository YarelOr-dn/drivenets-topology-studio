protocols rsvp timers refresh-interval
--------------------------------------

**Minimum user role:** operator

An established path remains open as long as the RSVP session is active. The session is maintained by the periodic transmission of messages reporting the state of the session. If the NCR does not receive the state messages for the configured amount of time, it terminates the RSVP session and reroutes the LSP through another active router.

The amount of time that the NCR waits for a state message before terminating the RSVP session = the configured refresh-interval x the configured refresh multiplier (see "rsvp timers refresh-multiplier")

When configuring a new refresh-interval value, the new interval will take effect on the tunnel after the old refresh-interval window has expired. For example, say the tunnel is running with a refresh-interval value of 30 seconds and after 15 seconds from the interval start you change the value to 10 seconds. In this case, the tunnel will wait 15 more seconds for the interval to expire before change its refresh rate to 10 seconds.

To configure the refresh-interval:

**Command syntax: refresh-interval [refresh-interval]**

**Command mode:** config

**Hierarchies**

- protocols rsvp timers

**Note**
- If the interval is reconfigured while the timer is running, the timer will be reset to the new interval value. if balancing is underway, current balancing process should be stopped.

..  -  when setting a new refresh-interval value, the new interval will take effect on the tunnel once the old refresh-interval window has expired. e.g if tunnel is running with refresh-interval of 30seconds and while there are 15 seconds left to next refresh, user configured an interval of 10seconds. only after the 15 seconds window will expire, will the tunnel change its refresh rate to every 10 seconds

**Parameter table**

+------------------+----------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                          | Range   | Default |
+==================+======================================================================+=========+=========+
| refresh-interval | set refresh time interval for RSVP interface status refresh messages | 1-65535 | 45      |
+------------------+----------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)# refresh-interval 100


**Removing Configuration**

To revert to the refresh-interval to its default value:
::

    dnRouter(cfg-protocols-rsvp-timers)# no refresh-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
