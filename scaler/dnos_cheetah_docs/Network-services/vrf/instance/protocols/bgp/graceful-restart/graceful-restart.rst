network-services vrf instance protocols bgp graceful-restart
------------------------------------------------------------

**Minimum user role:** operator

Graceful restart enables a BGP router to indicate its ability to preserve its forwarding state during BGP restart. During session initiation, the BGP router informs its peer that it has graceful restart capability. If the BGP session is lost during the restart, the peers mark all the associated routes as stale. However, they do not remove these routes and temporarily continue to use them to make forwarding decisions. Thus, no packets are lost while the BGP process is waiting for convergence of the routing information with the BGP peers.

When the restarting router is back up, the peers wait for the configured amount of time before they delete the stale routes, allowing the router time to converge. When the restarting router sends an end-of-RIB flag notifying its peers that it has converged, or if no end-of-RIB flag is received, but the timer expires, the peers delete any saved stale routes.

Graceful restart is enabled by default. To configure the graceful-restart parameters, enter the graceful-restart configuration mode:

**Command syntax: graceful-restart**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# graceful-restart
    dnRouter(cfg-protocols-bgp-gr)#


**Removing Configuration**

To revert all BGP graceful-restart parameters to their default values: 
::

    dnRouter(cfg-protocols-bgp)# no graceful-restart

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 6.0     | Command introduced                  |
+---------+-------------------------------------+
| 10.0    | Added restart-time parameter        |
+---------+-------------------------------------+
| 11.1    | Removed admin-state from the syntax |
+---------+-------------------------------------+
| 11.5    | Applied new hierarchy               |
+---------+-------------------------------------+
