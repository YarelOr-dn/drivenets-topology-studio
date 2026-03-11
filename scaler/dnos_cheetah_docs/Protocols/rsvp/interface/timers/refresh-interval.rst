protocols rsvp interface timers refresh-interval
------------------------------------------------

**Minimum user role:** operator

An established path remains open as long as the RSVP session is active. The session is maintained by the periodic transmission of messages reporting the state of the session. If the NCR does not receive the state messages for the configured amount of time, it terminates the RSVP session and reroutes the LSP through another active router.
The amount of time that the NCR waits for a state message before terminating the RSVP session = the configured refresh-interval x the configured refresh multiplier.To configure the refresh-interval for the interface:

Say the refresh-interval is set to 60 seconds and the refresh-multiplier is set to 3. The router will expect a state message every 60 seconds. If after 60 seconds from receiving a state message it does not receive another state message, the refresh-multiplier timer enters to action. The router will allow the loss of a state message only 3 times. If after 180 seconds from receiving the last state message it does not receive another state message (i.e. 60 sec x 3), it will terminate the session.
To change the refresh-interval:

**Command syntax: refresh-interval [refresh-interval]**

**Command mode:** config

**Hierarchies**

- protocols rsvp interface timers

**Note**
-  When configuring a new refresh-interval value, the new interval will take effect on the tunnel after the old refresh-interval window has expired. For example, say the tunnel is running with a refresh-interval value of 30 seconds and after 15 seconds from the interval start you change the value to 10 seconds. In this case, the tunnel will wait 15 more seconds for the interval to expire before change its refresh rate to 10 seconds.

.. -  no command returns refresh-interval to its default value

**Parameter table**

+------------------+------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                      | Range   | Default |
+==================+==================================================================+=========+=========+
| refresh-interval | refresh time interval for RSVP interface status refresh messages | 1-65535 | \-      |
+------------------+------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-1
    dnRouter(cfg-protocols-rsvp-if)# timers refresh-interval 100


**Removing Configuration**

To revert to the refresh-interval to its default value:
::

    dnRouter(cfg-protocols-rsvp-if)# no timers refresh-interval

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 10.0    | Command introduced in rsvp interface configuration mode |
+---------+---------------------------------------------------------+
