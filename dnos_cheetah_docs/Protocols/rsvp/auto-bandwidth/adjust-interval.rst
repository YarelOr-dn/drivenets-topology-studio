protocols rsvp auto-bandwidth adjust-interval
---------------------------------------------

**Minimum user role:** operator

The adjust interval is the time-frame in which the samples' calculated average-rates are compared. The highest calculated average-rate within the adjust-interval time-frame will be used in the adjustment threshold decision.
To configure the adjust-interval:

**Command syntax: adjust-interval [adjust-interval]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Note**
.. -  must adjust-interval > sampling-interval

- Changing the interval configuration will reset the timer.

.. -  no command restores adjust-interval to its default value

**Parameter table**

+-----------------+--------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                  | Range   | Default |
+=================+==============================================================+=========+=========+
| adjust-interval | time interval that traffic average-rate samples are gathered | 5-10080 | 1440    |
+-----------------+--------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# adjust-interval 5


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no adjust-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
