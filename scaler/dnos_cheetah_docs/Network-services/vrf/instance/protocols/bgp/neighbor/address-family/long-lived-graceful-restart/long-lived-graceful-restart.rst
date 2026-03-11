network-services vrf instance protocols bgp neighbor address-family long-lived-graceful-restart
-----------------------------------------------------------------------------------------------

**Minimum user role:** operator

Long lived graceful restart enables a BGP router to indicate its ability to preserve its forwarding state during BGP restart. During session initiation, the BGP router informs its peer that it has long lived graceful restart capability. If the BGP session is lost during the restart, the peers mark all the associated routes as stale. However, they do not remove these routes and temporarily continue to use them to make forwarding decisions. Thus, no packets are lost while the BGP process is waiting for convergence of the routing information with the BGP peers.

When the restarting router is back up, the peers wait for the configured amount of time before they delete the stale routes, allowing the router time to converge. When the restarting router sends an end-of-RIB flag notifying its peers that it has converged, or if no end-of-RIB flag is received, but the timer expires, the peers delete any saved stale routes.

Long lived graceful restart is disabled by default. To configure the long-lived-graceful-restart parameters, enable the admin-state for a given afi/safi on a neighbor and a global capability flag for a certain BGP

**Command syntax: long-lived-graceful-restart**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# long-lived-graceful-restart
    dnRouter(cfg-neighbor-afi-llgr)#


**Removing Configuration**

To revert to the default long lived graceful restart values:
::

    dnRouter(cfg-bgp-neighbor-afi)# no long-lived-graceful-restart

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19      | Command introduced |
+---------+--------------------+
