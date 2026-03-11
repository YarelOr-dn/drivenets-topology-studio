protocols rsvp optimization interval
------------------------------------

**Minimum user role:** operator

Tunnel optimization runs at fixed intervals (by default every 60 minutes). You may want to change the frequency to more frequent for a better optimized network, or less frequent to save on system resources. To change the optimization frequency:

Say the interval was set to 60 minutes and there are 35 minutes left till the next run when you changed the interval to 100 minutes. The timer will reset to 0 and the next optimization will run after 100 minutes. In this example, the interval between the two periodic runs is 125 minutes because of the timer configuration change.

**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols rsvp optimization

**Note**
- While you can enable optimization per tunnel, the interval is configured globally for all tunnels.

.. -  reconfiguring optimize-timer while timer is running, will reset optimize-timer to new interval value. if optimization was underway, stop current optimization process (even if optimization is due to interface up or user clear triggers).

.. -  Interval 0 will disable periodic optimization.

.. -  'no interval' - return interval to its default value

**Parameter table**

+-----------+------------------------------------------------------+---------+---------+
| Parameter | Description                                          | Range   | Default |
+===========+======================================================+=========+=========+
| interval  | sets how often to run optimization CSPF calculations | 0-65535 | 60      |
+-----------+------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)# interval 30
    dnRouter(cfg-protocols-rsvp-optimization)# interval 0


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-optimization)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
