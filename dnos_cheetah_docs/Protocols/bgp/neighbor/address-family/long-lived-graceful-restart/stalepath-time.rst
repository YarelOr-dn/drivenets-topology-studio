protocols bgp neighbor address-family long-lived-graceful-restart stalepath-time units
--------------------------------------------------------------------------------------

**Minimum user role:** operator

Long lived graceful restart enables a BGP router to indicate its ability to preserve its forwarding state during BGP restart. During session initiation, the BGP router informs its peer that it has long lived graceful restart capability. If the BGP session is lost during the restart, the peers mark all the associated routes as stale. However, they do not remove these routes and temporarily continue to use them to make forwarding decisions. Thus, no packets are lost while the BGP process is waiting for convergence of the routing information with the BGP peers.

When the restarting router is back up, the peers wait for the configured amount of time before they delete the stale routes, allowing the router time to converge. When the restarting router sends an end-of-RIB flag notifying its peers that it has converged, or if no end-of-RIB flag is received, but the timer expires, the peers delete any saved stale routes.

To configure the graceful-restart stalepath-time:

**Command syntax: stalepath-time [time] units [units]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family long-lived-graceful-restart

**Parameter table**

+-----------+---------------------------------------------------------------------------------+-------------+---------+
| Parameter | Description                                                                     | Range       | Default |
+===========+=================================================================================+=============+=========+
| time      | 1..16777215 for seconds 1..279620 for minutes 1..4660 for hours 1..194 for days | 1-16777215  | 1       |
+-----------+---------------------------------------------------------------------------------+-------------+---------+
| units     | time resolution                                                                 | | seconds   | hours   |
|           |                                                                                 | | minutes   |         |
|           |                                                                                 | | hours     |         |
|           |                                                                                 | | days      |         |
+-----------+---------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# long-lived-graceful-restart
    dnRouter(cfg-neighbor-afi-llgr)# stalepath-time 400 units seconds


**Removing Configuration**

To revert to the default stalepath-time value:
::

    dnRouter(cfg-neighbor-afi-llgr)# no stalepath-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19      | Command introduced |
+---------+--------------------+
