protocols bgp graceful-restart stalepath-time
---------------------------------------------

**Minimum user role:** operator

Graceful restart enables a BGP router to indicate its ability to preserve its forwarding state during BGP restart. During session initiation, the BGP router informs its peer that it has graceful restart capability. If the BGP session is lost during the restart, the peers mark all the associated routes as stale. However, they do not remove these routes and temporarily continue to use them to make forwarding decisions. Thus, no packets are lost while the BGP process is waiting for convergence of the routing information with the BGP peers.

When the restarting router is back up, the peers wait for the configured amount of time before they delete the stale routes, allowing the router time to converge. When the restarting router sends an end-of-RIB flag notifying its peers that it has converged, or if no end-of-RIB flag is received, but the timer expires, the peers delete any saved stale routes.

To configure the graceful-restart stalepath-time:

**Command syntax: stalepath-time [stale-path-time]**

**Command mode:** config

**Hierarchies**

- protocols bgp graceful-restart
- network-services vrf instance protocols bgp graceful-restart

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter       | Description                                                                      | Range  | Default |
+=================+==================================================================================+========+=========+
| stale-path-time | An upper-bound on the time thate stale routes will be retained by a router after | 1-3600 | 360     |
|                 | a session is restarted. If an End-of-RIB (EOR) marker is received prior to this  |        |         |
|                 | timer expiring stale-routes will be flushed upon its receipt - if no EOR is      |        |         |
|                 | received, then when this timer expires stale paths will be purged. This timer is |        |         |
|                 | referred to as the Selection_Deferral_Timer in RFC4724                           |        |         |
+-----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# graceful-restart
    dnRouter(cfg-protocols-bgp-gr)# stalepath-time 400


**Removing Configuration**

To revert to the default stalepath-time value:
::

    dnRouter(cfg-protocols-bgp-gr)# no stalepath-time

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 6.0     | Command introduced    |
+---------+-----------------------+
| 11.5    | Applied new hierarchy |
+---------+-----------------------+
