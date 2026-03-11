protocols rsvp auto-bandwidth sampling-interval
-----------------------------------------------

**Minimum user role:** operator

The sampling interval is the time-frame in which the average rate of the traffic flowing through the tunnel is calculated. The average rate is calculated as follows: byte/interval.
To configure the sampling interval:

**Command syntax: sampling-interval [sampling-interval]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth

**Note**
- The sampling-interval also defines the sampling rate for which the traffic rate is calculated for the rsvp tunnel statistics.

- Changing the interval configuration will reset the timer.

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter         | Description                                                                      | Range   | Default |
+===================+==================================================================================+=========+=========+
| sampling-interval | the sampling interval over which the average-rate of traffic flowing through a   | 1-10080 | 1       |
|                   | tunnel is calculated                                                             |         |         |
+-------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# sampling-interval 5


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no sampling-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
