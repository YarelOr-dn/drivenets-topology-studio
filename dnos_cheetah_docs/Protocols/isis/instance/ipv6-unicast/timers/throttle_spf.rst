protocols isis instance address-family ipv6-unicast timers throttle spf
-----------------------------------------------------------------------

**Minimum user role:** operator

When an IS-IS router receives an updated LSP, it doesn’t immediately run SPF but schedules it, in case there is a change in the topology. Because several routers may be affected by the change, it is likely that multiple updated LSPs are received. The router waits for a short while so that it only has to run SPF once for all updated LSPs.

To prevent the router from repeatedly running SPF if the topology change results from a flapping link, the delay in running SPF will keep increasing as long as updated LSPs keep arriving and up to the maximum holdtime interval.

The configuration applies to a specific IS-IS address-family topology and to all IS-IS levels.

To set the SPF timers:


**Command syntax: throttle spf {delay [delay], min-holdtime [min-holdtime], max-holdtime [max-holdtime]}**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast timers

**Note**
- At least one optional parameter must be configured.
- When working with a single topology, SPF for IPv6-unicast address-family won't run.


**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter    | Description                                                                      | Range    | Default |
+==============+==================================================================================+==========+=========+
| delay        | The minimum amount of time (in seconds) from first change received (e.g.         | 0-600000 | 0       |
|              | receiving an LSP packet) till SPF calculation. The value must be ≤ max-holdtime  |          |         |
|              | and ≤ min-holdtime.                                                              |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+
| min-holdtime | The minimum interval (in seconds) between consecutive SPF calculations. The      | 0-600000 | 5       |
|              | value Must be ≤ max-holdtime.                                                    |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+
| max-holdtime | The maximum interval (in seconds) between consecutive SPF calculations. The      | 0-600000 | 5000    |
|              | value must be ≥ delay and min-holdtime.                                          |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# timers
    dnRouter(cfg-inst-afi-timers)# throttle spf max-holdtime 6600 delay 12
    dnRouter(cfg-inst-afi-timers)# throttle spf min-holdtime 20
    dnRouter(cfg-inst-afi-timers)# throttle spf delay 12 min-holdtime 5 max-holdtime 6600

In the last example, the delay is set to 12 sec, the min-holdtime is set to the default 5 sec and the max-holdtime to 6600 sec. Hence, when an LSP first arrives, the router delays the SPF calculation according to the delay timer (12 sec). 12 seconds after receiving the LSP it will perform the SPF calculation. When a subsequent LSP arrives, it will delay the calculation by min-hold time (5 sec). For every subsequent LSP, the calculation delay will be double the previous delay, until the max-holdtime (6600 sec) is reached.


**Removing Configuration**

To revert all timers to their default value:
::

    dnRouter(cfg-isis-inst-timers)# no throttle spf

To revert a timer to its default value:
::

    dnRouter(cfg-isis-inst-timers)# no throttle spf max-holdtime
    dnRouter(cfg-isis-inst-timers)# no throttle spf delay min-holdtime

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 6.0     | Command introduced                                           |
+---------+--------------------------------------------------------------+
| 9.0     | Applied new hierarchy, removed level-1 and level-1-2 routing |
+---------+--------------------------------------------------------------+
