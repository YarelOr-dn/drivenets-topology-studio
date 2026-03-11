protocols ospfv3 timers throttle spf
------------------------------------

**Minimum user role:** operator

When an OSPFV3 router receives an updated LSA, it doesn’t immediately run SPF but schedules it, in case there is a change in the topology. Because several routers may be affected by the change, it is likely that multiple updated LSAs are received. The router waits for a short while so that it only has to run SPF once for all updated LSAs.
To prevent the router from repeatedly running SPF if the topology change results from a flapping link, the delay in running SPF will keep increasing as long as updated LSAs keep arriving and up to a maximum holdtime interval.
To set the OSPFV3 SPF throttling timers:

**Command syntax: throttle spf {delay [delay], max-holdtime [max-holdtime], min-holdtime [min-holdtime]}**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 timers

**Note**

- The 'no timers throttle spf' reverts SPF throttling timers to thier default value.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter    | Description                                                                      | Range    | Default |
+==============+==================================================================================+==========+=========+
| delay        | Initial SPF schedule delay in milliseconds                                       | 0-600000 | 50      |
+--------------+----------------------------------------------------------------------------------+----------+---------+
| max-holdtime | Maximum wait time between two consecutive SPF calculations Must be lower than    | 0-600000 | 5000    |
|              | max-holdtime                                                                     |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+
| min-holdtime | Minimum hold time between two consecutive SPF calculations must be higher than   | 0-600000 | 200     |
|              | min-holdtime                                                                     |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# timers throttle spf delay 1 min-holdtime 1000 max-holdtime 90000


**Removing Configuration**

The no timers throttle spf command reverts SPF throttling timers to their default values.
::

    dnRouter(cfg-protocols-ospfv3)# no timers throttle spf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
