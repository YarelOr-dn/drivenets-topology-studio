protocols rsvp timers protection-distribution
---------------------------------------------

**Minimum user role:** operator

Sets the periodic protection-distribution timer. With protection-distribution, bypass tunnels that are protecting the same interface and the same destination will need to balance which primary lsps they protect, in order to balance the aggregated protected-bw between bypasses,
When set to 0, no protection-distribution is performed.
To configure the protection distribution:

**Command syntax: protection-distribution [protection-distribution]**

**Command mode:** config

**Hierarchies**

- protocols rsvp timers

**Note**
- If the interval is reconfigured while the timer is running, the timer will be reset to the new interval value. if balancing is underway, current balancing process should be stopped.

.. -  Interval 0 will disable periodic optimization.

**Parameter table**

+-------------------------+------------------------------------------------+----------+---------+
| Parameter               | Description                                    | Range    | Default |
+=========================+================================================+==========+=========+
| protection-distribution | Set the periodic protection-distribution timer | 0, 5-180 | 0       |
+-------------------------+------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)# protection-distribution 10


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp-timers)# no protection-distribution

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
