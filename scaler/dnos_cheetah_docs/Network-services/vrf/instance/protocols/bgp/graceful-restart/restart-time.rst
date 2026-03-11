network-services vrf instance protocols bgp graceful-restart restart-time
-------------------------------------------------------------------------

**Minimum user role:** operator

Graceful restart enables a BGP router to indicate its ability to preserve its forwarding state during BGP restart. During session initiation, the BGP router informs its peer that it has graceful restart capability. If the BGP session is lost during the restart, the peers mark all the associated routes as stale. However, they do not remove these routes and temporarily continue to use them to make forwarding decisions. Thus, no packets are lost while the BGP process is waiting for convergence of the routing information with the BGP peers.

When the restarting router is back up, the peers wait for the configured amount of time before they delete the stale routes, allowing the router time to converge. When the restarting router sends an end-of-RIB flag notifying its peers that it has converged, or if no end-of-RIB flag is received, but the timer expires, the peers delete any saved stale routes.

To configure the graceful-restart restart-time:

**Command syntax: restart-time [restart-time]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp graceful-restart
- protocols bgp graceful-restart

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter    | Description                                                                      | Range | Default |
+==============+==================================================================================+=======+=========+
| restart-time | An upper-bound on the time thate stale routes will be retained by a router after | 0-600 | 120     |
|              | a session is restarted. If bgp the restored bgp session didn't reaches establish |       |         |
|              | state prior to this timer expiring stale-routes will be flushed upon its receipt |       |         |
+--------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# graceful-restart
    dnRouter(cfg-protocols-bgp-gr)# restart-time 100


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp-gr)# no restart-time

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 10.0    | Command introduced    |
+---------+-----------------------+
| 11.5    | Applied new hierarchy |
+---------+-----------------------+
