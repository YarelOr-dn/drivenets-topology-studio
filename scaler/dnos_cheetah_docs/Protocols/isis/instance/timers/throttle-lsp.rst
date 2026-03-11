protocols isis instance timers throttle lsp
-------------------------------------------

**Minimum user role:** operator

In the NCR, local LSPs are generated as a result of interface status change, e.g interface going up/down, or change in neighbor adjacency. Repeated recalculations of LSPs can cause increased CPU load on the local router. Also, the flooding of these recalculated LSPs to other IS-IS routers in the network causes increased traffic and prolonged route calculations. A solution is to delay the LSP updates to reduce the number of recalculations. However, such delays impact convergence time.

This command gives you control over LSP generation timers to decide on the optimal trade-off between convergence time and LSP flooding.

This command sets the minimum intervals at which LSPs are sent on an IS-IS interface to control the flooding pace to neighboring routing devices and prevent overloading them.

The throttle algorithm exponentially increases the holdtime between LSP generations as long as LSP generation triggering events keep coming. If for two max-holdtime durations no LSP generation triggering event is received, the min-holdtime reverts to its original value.

To set throttle LSP timers:

**Command syntax: throttle lsp {delay [delay], max-holdtime [max-holdtime], min-holdtime [min-holdtime]}**

**Command mode:** config

**Hierarchies**

- protocols isis instance timers

**Note**
- The configuration applies to all IS-IS levels
- You can set each parameter individually in any order
- The parameters' values must be: delay <= min-holdtime <= max-holdtime.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter    | Description                                                                      | Range    | Default |
+==============+==================================================================================+==========+=========+
| delay        | The minimum amount of time (in msec) from first change received till SPF         | 0-600000 | 50      |
|              | calculation.                                                                     |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+
| max-holdtime | The minimum hold time (in msec) between consecutive SPF calculations.            | 0-600000 | 5000    |
|              | Must be lower than max-holdtime.                                                 |          |         |
|              | The min-holdtime is doubled after every LSP calculation, until max-holdtime is   |          |         |
|              | reached. If after 2 max-holdtime durations no LSP generation triggering event    |          |         |
|              | occurs, the min-holdtime reverts to its original configured value.               |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+
| min-holdtime | The maximum holdtime (in msec) between consecutive LSP calculations.             | 0-600000 | 200     |
|              | Must be higher than min-holdtime.                                                |          |         |
|              | 2 x max-holdtime must be lower than the set lsp-refresh. See "isis instance      |          |         |
|              | timers lsp-refresh".                                                             |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# timers
    dnRouter(cfg-isis-inst-timers)# throttle lsp max-holdtime 5000 delay 5
    dnRouter(cfg-isis-inst-timers)# throttle lsp min-holdtime 20
    dnRouter(cfg-isis-inst-timers)# throttle lsp delay 200 min-holdtime 400 max-holdtime 10000

In the last example, the delay is set to 200ms, the min-holdtime is set to 400 ms and the max-holdtime to 10s. Hence, when an LSA first arrives, the router delays the SPF calculation according to the delay timer (200 msec). 200 msec after receiving the LSA it will perform the SPF calculation. When a subsequent LSA arrives, it will delay the calculation by min-hold time (400 msec). For every subsequent LSA, the calculation delay will be double the previous delay, until the max-holdtime (10s) is reached.


**Removing Configuration**

To revert a timer to its default value:
::

    dnRouter(cfg-isis-inst-timers)# no throttle lsp max-holdtime
    dnRouter(cfg-isis-inst-timers)# no throttle lsp delay min-holdtime

To revert all timers to their default value:
::

    dnRouter(cfg-isis-inst-timers)# no throttle lsp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
