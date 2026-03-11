system event-manager periodic-policy policy-interval
----------------------------------------------------

**Minimum user role:** admin

To configure the periodic policy reoccuring timeframe.

**Command syntax: policy-interval {periodic [d days hh:mm:ss] \| on-time [hh:mm:ss] every {week_day \| day}}**

**Command mode:** config

**Hierarchies**

- system event-manager periodic-policy


**Note**

- "policy-interval" is a mandatory configuration. The commit will fail if no policy-interval is configured.

- The periodic time interval must be larger than the script-maxruntime.

**Parameter table**

+-------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+---------------+
| Parameter               | Description                                                                                       | Range                                                                | Default       |
+=========================+===================================================================================================+======================================================================+===============+
| periodic                | The day and timeframe the policy is executed repeatedly.                                          | DD HH:MM:SS  (0 00:01:00 - 29 23:59:59)                              | disabled      |
+-------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+---------------+
| on-time                 | The time the policy is executed, either daily or once a week at the specified time.               | HH:MM:SS                                                             | disabled      |
+-------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+---------------+
| every                   | The day of the week the policy is executed.                                                       | week-day: Mon, Tue, Wed, Thu, Fri, Sat, Sun | Day                    | disabled      |
+-------------------------+---------------------------------------------------------------------------------------------------+----------------------------------------------------------------------+---------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# periodic-policy test
    dnRouter(cfg-periodic-policy-test)# policy-interval periodic 0 days 12:00:00
    dnRouter(cfg-periodic-policy-test)# no policy-interval periodic
    dnRouter(cfg-periodic-policy-test)# policy-interval on-time 14:54:03 every Sun


.. **Help line:** configure the periodic policy execution time interval.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

