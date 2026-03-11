protocols bgp graceful-restart purge-time
-----------------------------------------

**Minimum user role:** operator

Graceful restart enables a BGP router to indicate its ability to preserve its forwarding state during BGP restart. During session initiation, the BGP router informs its peer that it has graceful restart capability. If the BGP session is lost during the restart, the peers mark all the associated routes as stale. However, they do not remove these routes and temporarily continue to use them to make forwarding decisions. Thus, no packets are lost while the BGP process is waiting for convergence of the routing information with the BGP peers.

When the restarting router is back up, the peers wait for the configured amount of time before they delete the stale routes, allowing the router time to converge. When the restarting router sends an end-of-RIB flag notifying its peers that it has converged, or if no end-of-RIB flag is received, but the timer expires, the peers delete any saved stale routes.

To configure the graceful-restart purge-time:

**Command syntax: purge-time [purge-time]**

**Command mode:** config

**Hierarchies**

- protocols bgp graceful-restart

**Note**

- The default purge-time is the configured stalepath-time + 60 seconds. When using the default value, reconfiguring the stalepath-time will also update the used purge-time.

**Parameter table**

+------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter  | Description                                                                      | Range  | Default |
+============+==================================================================================+========+=========+
| purge-time | specify the maximum time before stale routes are purged from the routing         | 1-3600 | \-      |
|            | information base (RIB) when the local BGP process restarts                       |        |         |
+------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# graceful-restart
    dnRouter(cfg-protocols-bgp-gr)# purge-time 500


**Removing Configuration**

To revert to the default purge-time value:
::

    dnRouter(cfg-protocols-bgp-gr)# no purge-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
