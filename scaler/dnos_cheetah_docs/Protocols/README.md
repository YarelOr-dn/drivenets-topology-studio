# DNOS Protocols Configuration Reference

This document contains the complete DNOS CLI protocols configuration syntax:
- BGP
- IS-IS
- OSPF/OSPFv3
- LDP
- MPLS
- LACP
- LLDP
- BFD
- RSVP
- PIM/IGMP
- Static routes
- Segment Routing
- VRRP

---

## address resultion protocol overview
```rst
Address Resolution Protocol (ARP)
---------------------------------

Address resolution is the process of mapping network addresses (IPs) to Media Access Control (MAC) addresses. This process is accomplished using the Address Resolution Protocol (ARP).

Within a single LAN, if an end system A broadcasts an ARP request to learn the MAC address of an end system B, the broadcast is received by all devices on the LAN, but only B replies to the ARP request. The ARP reply contains B's MAC address. A receives the reply and saves B's MAC address in its ARP table. (The ARP table is where network addresses are associated with MAC addresses.) Whenever A needs to communicate with B, it checks the ARP table, finds the MAC address of B, and sends the frame directly, without needing to first use another ARP request.

When the source and destination devices are on different LANs that are interconnected by a router, the source system Y broadcasts an ARP request to learn the MAC address of the destination system Z. The broadcast is received by all devices on the LAN, but it cannot reach Z. To reach Z, we need to manually add it to Y's ARP table.

A dynamically learned record of each mapping between network address and MAC address is kept in the ARP table for a predetermined amount of time (5 min) and then discarded.

You can also add static entries to the ARP table. When IS-IS is available, DNOS takes the IP and MAC addresses from the IS-IS hello messages and periodic messages and pre-installs them in the ARP table.

For ARP-related commands, see:

- interfaces arp
- show arp
- clear arp

For dynamic ARP/NDP synchronization, see:

- Dynamic ARP```

## bgp class-of-service
```rst
protocols bgp class-of-service
------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing BGP packets:

**Command syntax: bgp class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols

**Parameter table**

+------------------+-------------------------------------+-------+---------+
| Parameter        | Description                         | Range | Default |
+==================+=====================================+=======+=========+
| class-of-service | dscp value for outgoing BGP packets | 0-56  | 48      |
+------------------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no bgp class-of-service 48

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## bgp maximum-sessions
```rst
protocols bgp maximum-sessions threshold
----------------------------------------

**Minimum user role:** operator

You can control the maximum number of concurrent BGP sessions by setting thresholds to generate system event notifications. Only established sessions are counted. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary.

- This is a global setting where the thresholds apply to all BGP session types (iBGP and eBGP) and are for all BGP instances combined.

- The thresholds are for generating system-events only. There is no limitation for how many bgp neighbors/groups user can configure. A session will open for every configured peer.

To configure thresholds for BGP sessions:

**Command syntax: bgp maximum-sessions [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- When the number of sessions drops below a threshold, a system-event notification is generated.

- In the above example, the maximum number of sessions is set to 600 and the threshold is set to 70%. This means that when the number of sessions reaches 420 (600x70%), a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of sessions reaches 600.

**Parameter table**

+-----------+---------------------------------------------------------+--------+---------+
| Parameter | Description                                             | Range  | Default |
+===========+=========================================================+========+=========+
| maximum   | maximum session scale, covers all types of bgp sessions | 1-5000 | 2000    |
+-----------+---------------------------------------------------------+--------+---------+
| threshold | threshold as a percentage of system maximum bgp session | 1-100  | 75      |
+-----------+---------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp maximum-sessions 600 threshold 70


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols)# no bgp maximum-sessions

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## bgp nsr
```rst
protocols bgp nsr
-----------------

**Minimum user role:** operator

BGP nonstop routing (NSR) enables a BGP speaker to maintain the BGP session's state while undergoing switchover at the CPU level (e.g. NCC switchover).
Unlike BGP graceful-restart (GR), which requires both BGP ends to support the GR capability and logic, NSR is transparent, and the other end of the BGP session is unaware of the NSR process.
BGP NSR provides a high availability (HA) solution where the neighbor router does not support BGP GR.

The BGP process (bgpd) running on the active NCC, saves all the information required to recover from a BGP failure and provide nonstop routing (including BGP session information for both iBGP and eBGP neighbors, and TCP session information) in the NSR DB (including all BGP acknowledged and unacknowledged packets).
The NSR DBs, located on both active and standby NCC, are regularly synchronized. In the event of a switchover/failover, bgpd starts on the standby NCC and recovers the TCP and BGP session parameters from the NSR-DB in the standby NCC.
BGP NSR does not require the neighbor router to be NSF-capable or NSF-aware, however, it relies on the "route-refresh" capability in order to re-converge after the BGP process recovers.

BGP NSR is applicable to the following address families:

* IPv4-unicast, IPv6-unicast
* IPv4-labeled-unicast, IPv6-labeled-unicast
* IPv4-vpn, IPv6-vpn
* IPv4-rt-constrains
* IPv4-multicast

BGP NSR is supported only on NCEs with external NCCs (i.e. cluster topology).

To enable/disable the BGP NSR feature:

**Command syntax: bgp nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- This is a global BGP configuration that applies to all BGP instances and VRFs.

**Parameter table**

+-----------+---------------------+--------------+---------+
| Parameter | Description         | Range        | Default |
+===========+=====================+==============+=========+
| nsr       | bgp nsr admin-state | | enabled    | enabled |
|           |                     | | disabled   |         |
+-----------+---------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp nsr enabled

    dnRouter(cfg-protocols)# bgp nsr disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no bgp nsr

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 13.0    | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 16.1    | Changed hierarchy for the command to apply to all BGP instances |
+---------+-----------------------------------------------------------------+
```

## neighbor discovery protocol overview
```rst
Neighbor Discovery Protocol Overview
------------------------------------
In IPv6 networks, the neighbor discovery protocol (NDP) is responsible for:

- Router discovery - locating the routers that reside on an attached link
- Prefix discovery - discovering the set of address prefixes that define which destinations are on-link
- Parameter discovery - learning parameters (MTU, hop limit value) to place in outgoing packets
- Address auto-configuration - nodes automatically configure addresses for interfaces
- Neighbor address resolution - determining the link-layer address of an on-link destination given only the destination's IP address
- Next-hop determination - mapping an IP destination address to the IP address of the neighbor to which traffic for the destination should be sent (i.e. the next hop).
- Neighbor reachability verification - determining if the neighbor is reachable
- Duplicate address detection - determining if an address it wants to use is in use by another node
- Redirect - informing a host of a better next-hop node for reaching a specific destination

NDP uses the following ICMPv6 message types to carry out its tasks:

- Router solicitation (type 133) - When an interface becomes enabled, hosts may send out Router Solicitations that request routers to generate Router Advertisements immediately rather than at their next scheduled time.
- Router advertisement (type 134) - IPv6 routers send router advertisement messages periodically or in response to a Router Solicitation message, to inform hosts about the IPv6 prefixes used on the link.
- Neighbor solicitation (type 135) - Sent by a node to determine the link-layer address of a neighbor, or to verify that the neighbor is still reachable. Neighbor solicitation messages are also used for duplicate address detection.
- Neighbor advertisement (type 136) - A response to a Neighbor Solicitation message, or to announce a link-layer address change.
- Redirect (type 137) - Used by routers to inform hosts of a better next hop for a destination.

When IS-IS is available, DNOS takes the IP and MAC addresses from the IS-IS hello messages and periodic messages and pre-installs them entries in the NDP table.

For NDP-related commands, see:

- interfaces ndp

- show ndp

- clear ndp

For dynamic ARP/NDP synchronization, see:

- Dynamic ARP
```

## protocols
```rst
protocols
---------

**Minimum user role:** operator

Enter protocols configuration mode

**Command syntax: protocols**

**Command mode:** config

**Note:**

'no protocols' - remove all protocols configuration

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)#

	dnRouter(cfg)# no protocols

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 11.0    | Command introduced                                              |
+---------+-----------------------------------------------------------------+
```

## vrrp class-of-service
```rst
protocols vrrp class-of-service
-------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing VRRP packets:

**Command syntax: vrrp class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The class-of-service configuration is global and applies to all VRRP instances in any VRF.

**Parameter table**

+------------------+--------------------------------------+-------+---------+
| Parameter        | Description                          | Range | Default |
+==================+======================================+=======+=========+
| class-of-service | DSCP value for outgoing VRRP packets | 0-56  | 48      |
+------------------+--------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no vrrp class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## vrrp startup-delay
```rst
protocols vrrp startup-delay
----------------------------

**Minimum user role:** operator

To set the startup delay to wait before a backup router will attempt preempting the master for the VRRP groups after an interface becomes operational:

**Command syntax: vrrp startup-delay [startup-delay]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The startup-delay configuration is global and applies to all VRRP instances in any VRF.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter     | Description                                                                      | Range  | Default |
+===============+==================================================================================+========+=========+
| startup-delay | Set the delay the higher priority backup router waits before preempting the      | 0-3600 | 30      |
|               | master router after the interfaces becomes operational                           |        |         |
+---------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp startup-delay 600


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no vrrp startup-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
```

# BGP

## admin-distance
```rst
protocols bgp administrative-distance
-------------------------------------

**Minimum user role:** operator

If a router learns of a destination from more than one routing protocol, the administrative distance is compared and the preference is given to the routes with lower administrative distance.

To change the BGP administrative distance for all routes:

**Command syntax: administrative-distance {external [external-route-distance], internal [internal-route-distance], local [local-route-distance]}**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- An administrative-distance of 255 will cause the router to remove the route from the routing table.

**Parameter table**

+-------------------------+----------------------------------------------------------------------+-------+---------+
| Parameter               | Description                                                          | Range | Default |
+=========================+======================================================================+=======+=========+
| external-route-distance | Administrative distance for routes learned from external BGP (eBGP). | 1-255 | 20      |
+-------------------------+----------------------------------------------------------------------+-------+---------+
| internal-route-distance | Administrative distance for routes learned from internal BGP (iBGP). | 1-255 | 200     |
+-------------------------+----------------------------------------------------------------------+-------+---------+
| local-route-distance    | Administrative distance for routes learned from local peers          | 1-255 | 110     |
+-------------------------+----------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# administrative-distance external 120 internal 200 local 150
    dnRouter(cfg-protocols-bgp)# administrative-distance local 60


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-bgp)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-bgp)# no administrative-distance local

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 6.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 15.1    | Updated command syntax from admin to administrative |
+---------+-----------------------------------------------------+
```

## advertise-update-delay
```rst
protocols bgp advertise-update-delay
------------------------------------

**Minimum user role:** operator

You can set the delay time (in seconds) to advertise bgp routes, after bet-path logic finishes. The delay applies to all bgp neighbors and all bgp address-families (does not apply to ipv4-flowspec, ipv6-flowspec and link-state address-families).

When re-configuring advertise-update-delay, the new delay time will apply to all routes ready to be advertised from the reconfig time + old delay timer value.

To set the BGP delay:

**Command syntax: advertise-update-delay [advertise-update-delay]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- A delay value of 0 will not add any additional delay.

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter              | Description                                                                      | Range  | Default |
+========================+==================================================================================+========+=========+
| advertise-update-delay | Set delay time (in seconds) to advertise bgp routes after finishing best-path    | 0-1800 | 240     |
|                        | logic                                                                            |        |         |
+------------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# advertise-update-delay 180


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-bgp)# no advertise-update-delay

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 13.2    | Command introduced            |
+---------+-------------------------------+
| 17.1    | Default changed from 0 to 120 |
+---------+-------------------------------+
```

## always-compare-med
```rst
protocols bgp always-compare-med
--------------------------------

**Minimum user role:** operator

When two or more links exist between autonomous systems, the multi-exit discriminator (MED) values may be set to give preferences to certain routes. When comparing MED values, the lower value is preferred. By default, this function is disabled, and MED values are compared only if two paths have the same neighbor AS.

To configure the BGP process to always compare the MED metric on routes for best path selection, even when received from different ASs:

**Command syntax: always-compare-med**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# always-compare-med


**Removing Configuration**

To disable the always compare MED function:
::

    dnRouter(cfg-protocols-bgp)# no always-compare-med

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## bestpath aigp-ignore
```rst
protocols bgp bestpath aigp-ignore
----------------------------------

**Minimum user role:** operator

By default, the best path selection algorithm considers the AIGP metric as a tie-breaker between paths, and prefers paths with the AIGP attribute over paths without it. This command forces the system to only consider the AIGP attribute in the best path algorithm if both paths have an AIGP attribute.

To set the system to ignore the AIGP metric in best path calculation:

**Command syntax: bestpath aigp-ignore**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- This configuration is applicable to the default VRF only.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-bgp)# bestpath aigp-ignore


**Removing Configuration**

To disable the configuration:
::

    dnRouter(cfg-bgp)# no bestpath aigp-ignore

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 7.0     | Command introduced |
+---------+--------------------+
```

## bestpath as-path
```rst
protocols bgp bestpath as-path
------------------------------

**Minimum user role:** operator

To configure how BGP treats the AS path in best path selection:

**Command syntax: bestpath as-path {confed, multipath-relax, ignore}**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- These parameter options are not mutually exclusive. You may configure all options. These options are disabled by default.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| confed          | specifies that the length of confederation path sets and sequences should be     | Boolean | False   |
|                 | taken into account during the BGP best path decision process                     |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+
| multipath-relax | specifies that BGP decision process should consider paths of equal as-path       | Boolean | False   |
|                 | length candidates for multipath computation. Without the set, the entire as-path |         |         |
|                 | must match for multipath computation                                             |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+
| ignore          | Ignore the AS path length when selecting the best path. The default is to use    | Boolean | False   |
|                 | the AS path length and prefer paths with shorter length.                         |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath as-path confed
    dnRouter(cfg-protocols-bgp)# bestpath as-path multipath-relax
    dnRouter(cfg-protocols-bgp)# bestpath as-path ignore


**Removing Configuration**

To revert the best path AS path instruction to default (disable):
::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path confed

::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path multipath-relax

::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path ignore

::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## bestpath compare-router-id
```rst
protocols bgp bestpath compare-router-id
----------------------------------------

**Minimum user role:** operator

When comparing routes, if all metric stages 1-10 are equal, including local preference, AS-path length, IGP cost, and MED, BGP can select the best path based on router-id (stage 11). This command causes BGP to prefer the route with the lower router-id when all other metrics are equal.

To enable this function:

**Command syntax: bestpath compare-router-id**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- If the route contains route reflector attributes, BGP will use the ORIGINATOR_ID as the ROUTER_ID for comparison. Otherwise, the router-id of the neighbor from which the route was received is used.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath compare-router-id


**Removing Configuration**

To disable the compare-router-id option:
::

    dnRouter(cfg-protocols-bgp)# no bestpath compare-router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## bestpath delay
```rst
protocols bgp bestpath delay
----------------------------

**Minimum user role:** operator

Upon initialization following a restart, the BGP process waits for the configured amount of time before starting to send its updates. During this delay, the router listens to updates coming from the peers without responding. When the peers finish sending updates, or when the timer expires, the BGP calculates the best path for each route and starts advertising to its peers. The best path delay improves convergence because by waiting for all the information before calculating the best paths, less advertisements are required.

The best path delay command sets the maximum time to wait after the first neighbor is established until the BGP starts calculating best paths and sending out advertisements:

**Command syntax: bestpath delay [bestpath-delay]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                                      | Range  | Default |
+================+==================================================================================+========+=========+
| bestpath-delay | Set delay for the first bestpath calculation to all updates to be received from  | 0-3600 | 120     |
|                | all peers                                                                        |        |         |
+----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath delay 10


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no bestpath delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## bestpath deterministic-med
```rst
protocols bgp bestpath deterministic-med
----------------------------------------

**Minimum user role:** operator

When routes are advertised by different peers in the same autonomous system, you can instruct the BGP process to compare the MED variable to select the best path.

To enable this option:

**Command syntax: bestpath deterministic-med**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath deterministic-med


**Removing Configuration**

To disable this configuration:
::

    dnRouter(cfg-protocols-bgp)# no bestpath deterministic-med

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## bestpath med
```rst
protocols bgp bestpath med
--------------------------

**Minimum user role:** operator

The bestpath-med command instructs BGP what to do with the multi-exit discriminator (MED) metrics. By default, routes originating within the same confederation as the router do not have their MED values compared as part of the best-path selection process. Also BGP best-path selection considers a missing MED value to be 0, so routes with missing MED values will be preferred by default.

To change this behavior:

**Command syntax: bestpath med {confed, missing-as-worst}**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- These parameter options may be configured together or individually. When configured individually, the order is not important.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                                      | Range   | Default |
+==================+==================================================================================+=========+=========+
| confed           | MEDs are compared for all paths that consist only of AS_CONFED_SEQUENCE. These   | Boolean | False   |
|                  | paths originated within the local confederation                                  |         |         |
+------------------+----------------------------------------------------------------------------------+---------+---------+
| missing-as-worst | path received with no MED paths are assigned a MED of 4,294,967,294              | Boolean | False   |
+------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath med confed

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath med missing-as-worst

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath med confed missing-as-worst

    dnRouter(cfg-protocols-bgp)# bestpath med missing-as-worst confed


**Removing Configuration**

To disable the bestpath med configuration:
::

    dnRouter(cfg-protocols-bgp)# no bestpath med confed

::

    dnRouter(cfg-protocols-bgp)# no bestpath med missing-as-worst

::

    dnRouter(cfg-protocols-bgp)# no bestpath med

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## bestpath rpki allow-invalid
```rst
protocols bgp bestpath rpki allow-invalid
-----------------------------------------

**Minimum user role:** operator

You can use this command to enable taking routes with invalid RPKI state into consideration for the BGP bestpath calculation.

To configure the RPKI allow-invalid:

**Command syntax: bestpath rpki allow-invalid**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Example**
::

    dnRouter(cfg-protocols-bgp)# bestpath rpki allow-invalid


**Removing Configuration**

To revert to the default value: 
::

    dnRouter(cfg-protocols-bgp)# no bestpath rpki allow-invalid

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 19.3    | Command introduced                 |
+---------+------------------------------------+
| TBD     | Added support for non-default VRFs |
+---------+------------------------------------+
```

## bestpath rpki prefix-validate
```rst
protocols bgp bestpath rpki prefix-validate
-------------------------------------------

**Minimum user role:** operator

You can use this command to enable taking the RPKI validation states of BGP routes and their preference into consideration for the BGP bestpath calculation.

To configure the RPKI prefix-validation:

**Command syntax: bestpath rpki prefix-validate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enables the RPKI validity states of BGP paths to affect the path's preference in | | enabled    | disabled |
|             | the BGP bestpath calculation.                                                    | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter(cfg-protocols-bgp)# bestpath rpki prefix-validate enabled


**Removing Configuration**

To revert to the default value: 
::

    dnRouter(cfg-protocols-bgp)# no bestpath rpki prefix-validate

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 15.1    | Command introduced                        |
+---------+-------------------------------------------+
| 19.3    | Split allow-invalid to a separate command |
+---------+-------------------------------------------+
| TBD     | Added support for non-default VRFs        |
+---------+-------------------------------------------+
```

## bestpath
```rst
protocols bgp bestpath
----------------------

**Minimum user role:** operator

The BGP Best Path Selection Algorithm determines the optimal route to a destination when multiple paths are available. BGP evaluates paths based on several attributes in a predefined order. The goal is to select the most efficient and stable path while maintaining policy control. This process ensures that BGP routers consistently choose and advertise the best available route to their peers.
During best-path selection an Equal-Cost Multi-Path (ECMP) path group may be found so that multiple different paths are installed in the routing table. However, BGP still advertises only a single best path to its peers unless additional features like BGP Add-Path. This distinction ensures stable routing behavior while allowing ECMP for traffic distribution within a router’s local forwarding plane. 


The DNOS best-path selection process for ip routes is as follows:
1.  RPKI state – when the RPKI state is is maintained - meaning only unicast/LU in default VRF.
1.  RPKI validation is done according to RPKI prefix validation configuration.
1.  Path with better RPKI state: valid > not found > unverified > invalid
2.  If “allow invalid” is not set, path with invalid will be chosen only if no other exists 
2.  Path with LLGR-Stale community is less preferred
3.  Highest weight
4.  Highest local preferences 
5.  Originate routes (network, redistribute)
6.  AIGP metric
7.  Shortest AS-path
8.  Lowest origin
9.  Lowest MED
10. Path (eBGP over iBGP)
11. Accept-own
12. Nearest IGP neighbor (IGP-metric)
•   At this stage ECMP group is selected
10. Prefer Labeled-Unicast path over Unicast path (LU and U share same BGP table)
11. Oldest (stable) route (if compare-router-ID is off)
1.  First check if one of the paths compared is already best, and if so, prefers it.
2.  If both are not best, compares the timer in which those were received in seconds - meaning less than a second will be handled as identical.
11. Neighbor with the lowest ID (using the originator attribute, if exists, or the router-ID if not)
12. Shortest cluster list
13. Neighbor with lowest IP
14. Imported path is preferred over local-aggregate

**EVPN Bestpath**

The EVPN (and the upcoming VPLS SI) bestpath selection is implemented somewhat differently, primarily due to multihoming scenarios.
The main distinction is that for some route types, the BGP process performs standard or slightly modified bestpath selection but installs all valid routes as ECMP to the EVPN-Manager (which functions as the RIB).
For these routes, the EVPN-Manager calculates the installed ECMP paths based on the information received from BGP.

The bestpath behavior varies by route type:

*Type 3 – Inclusive Multicast (IM) Route*

- Follows standard BGP bestpath selection.
- Only a single route is installed; ECMP is not used for this route.
- No bestpath selection is performed by the EVPN-Manager.

*Type 2 – MAC/IP Route*
- Bestpath logic is applied in both BGP and EVPN-Manager, following this procedure:
- Prefer routes with the MAC Mobility extended community
- Prefer routes with the sticky bit
- Prefer routes with a higher sequence number
- Prefer routes with the lowest IP address

*Type 3 – Auto-Discovery (A/D) Route*
Bestpath logic is present in both BGP and the EVPN-Manager.
- In BGP: Follows standard bestpath selection.
- All valid routes are installed as ECMP from BGP to the EVPN-Manager.
- The EVPN-Manager performs multihoming logic, which differs depending on the service (EVPN/EVPN-VPWS).

The EVPN-Manager’s goal is to determine the valid ECMP paths for each ESI. Some examples:
- If a Type 1 EVI is received without a corresponding Type 1 ESI, the next hop is considered invalid and excluded from ECMP.
- If multiple Type 1 ESI routes are received, they must all belong to the same redundancy mode. In case of a conflict, the entire ESI falls back to single-active mode, and the Designated Forwarder (DF) is calculated accordingly.

*Type 4 – Ethernet Segment (ES) Route*
Bestpath logic is handled only by the BGP process and follows standard BGP bestpath rules.
- This route is used for DF election when a local ESI is present.
- DF election is carried out based on the required type (e.g., MOD or highest preference), as specified in [RFC 7432 – BGP MPLS-Based Ethernet VPN].

*Type 5 – IP Prefix Route*
This route type also goes through the bestpath process within the EVI, but the final bestpath decision is made in the VRF.
In the EVI, a "stitched" route is always preferred over a non-stitched route — meaning the VRF determines the bestpath.

**VPLS Bestpath**

*BGP Process*
- Follows standard BGP bestpath selection (with the VPLS NLRI key being the VE-ID and block offset).
- All routes with the same key are installed as ECMP.

*EVPN-Manager Process*
- Prefer routes without the Down bit
- Prefer routes without the LLGR flag
- Prefer routes with the highest preference
- Prefer routes with the lowest IP address.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.2    | Command introduced |
+---------+--------------------+
```

## bgp
```rst
protocols bgp
-------------

**Minimum user role:** operator

To start the BGP process:

**Command syntax: bgp [as-number]**

**Command mode:** config

**Hierarchies**

- protocols
- network-services vrf instance protocols

**Note**

- The AS-number cannot be changed. To change it, you need to delete the BGP protocol configuration and configure a new process with a different AS-number.

- Notice the change in prompt.

**Parameter table**

+-----------+------------------------+--------------+---------+
| Parameter | Description            | Range        | Default |
+===========+========================+==============+=========+
| as-number | peer-group unique name | 1-4294967295 | \-      |
+-----------+------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)#


**Removing Configuration**

To disable the BGP process:
::

    dnRouter(cfg-protocols)# no bgp

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 6.0     | Command introduced                   |
+---------+--------------------------------------+
| 9.0     | Changed AS-number range to minimum 1 |
+---------+--------------------------------------+
```

## cluster-id
```rst
protocols bgp cluster-id
------------------------

**Minimum user role:** operator

You can use this command to specify a global cluster-id attribute when used as a route-reflector, or per neighbor-group or neighbor if specified explicitly.

Prior to reflecting a route, route reflectors append their cluster-id to the cluster list.

**Command syntax: cluster-id [cluster-id]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor

**Parameter table**

+------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter  | Description                                                                      | Range            | Default |
+============+==================================================================================+==================+=========+
| cluster-id | route-reflector cluster id to use when local router is configured as a route     | | 1-4294967295   | \-      |
|            | reflector.                                                                       | | A.B.C.D        |         |
+------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# cluster-id 65.65.65.65

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65001
    dnRouter(cfg-protocols-bgp)# cluster-id 100

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65001
    dnRouter(cfg-protocols-bgp)# neighbor 1.1.1.1
    dnRouter(cfg-protocols-bgp-neighbor)# cluster-id 101

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# cluster-id 10.0.0.1

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# cluster-id 27081


**Removing Configuration**

To revert all BGP cluster-id to the default value:
::

    dnRouter(cfg-protocols-bgp)# no cluster-id

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 15.1    | Command introduced                                           |
+---------+--------------------------------------------------------------+
| 17.1    | Extended support for neighbor and neighbor-group hierarchies |
+---------+--------------------------------------------------------------+
```

## confederation indentifier
```rst
protocols bgp confederation identifier
--------------------------------------

**Minimum user role:** operator

Because iBGP updates are not passed to other iBGP neighbors, every router within the BGP AS must be fully meshed. In large ASs, the number of iBGP peering sessions required can potentially be enormous. The use of confederations reduces the number of iBGP sessions by allowing to split the AS into smaller sub-ASs.

The AS_PATH attribute within routing updates includes the confederation information. To the outside world (i.e. to BGP peers external to the confederation), your network confederation identified by the AS Confederation Identifier appears as a single AS.

On each router in the AS, you define the confederation identifier and its confederation sub-AS. This breaks up the larger AS into smaller sub-ASs. To enable the confederation sub-ASs to communicate, you need to define the confederation neighbors on each sub-AS border router (see "bgp confederation neighbors").

**Command syntax: confederation identifier [identifier]**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- This command is available to the default VRF instance only.

**Parameter table**

+------------+------------------------------+--------------+---------+
| Parameter  | Description                  | Range        | Default |
+============+==============================+==============+=========+
| identifier | bgp confederation identifier | 1-4294967295 | \-      |
+------------+------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# confederation identifier 8000


**Removing Configuration**

To remove the confederation configuration:
::

    dnRouter(cfg-protocols-bgp)# no confederation identifier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
```

## confederation neighbors
```rst
protocols bgp confederation neighbors
-------------------------------------

**Minimum user role:** operator

When operating in a confederation AS split into multiple sub-ASs, you need to configure the neighbor sub-ASs on the sub-AS border. eBGP sessions will run between the sub-ASs.

To configure the neighbor sub-ASs in the BGP confederation:

**Command syntax: confederation neighbors [neighbors-as]** [, neighbors-as, neighbors-as]

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- This command is available to the default VRF instance only.

- If run another command with different AS-numbers, the new AS-numbers will be added as confederation neighbors. The command does not override existing neighbors.

**Parameter table**

+--------------+------------------------------------+--------------+---------+
| Parameter    | Description                        | Range        | Default |
+==============+====================================+==============+=========+
| neighbors-as | neighbors ASs in BGP confederation | 1-4294967295 | \-      |
+--------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# confederation neighbors 8001, 8002, 8003
    dnRouter(cfg-protocols-bgp)# confederation neighbors 8004, 8005


**Removing Configuration**

To remove all confederation neighbor configuration:
::

    dnRouter(cfg-protocols-bgp)# no confederation neighbors

To remove specific neighbors from the confederation group:
::

    dnRouter(cfg-protocols-bgp)# no confederation neighbors 8002

::

    dnRouter(cfg-protocols-bgp)# no confederation neighbors 8001, 8005

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
```

## default-local-preference
```rst
protocols bgp default local-preference
--------------------------------------

**Minimum user role:** operator

Routers in the same AS exchange the local preference attribute in order to indicate to the AS which path is preferred for exiting the AS and reaching a specific network.

A path with a higher local preference is preferred more.

To configure the default local preference for advertised routes:

**Command syntax: default local-preference [default-local-preference]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Parameter table**

+--------------------------+-------------------------------------------+--------------+---------+
| Parameter                | Description                               | Range        | Default |
+==========================+===========================================+==============+=========+
| default-local-preference | Change the default local preference value | 0-4294967295 | 100     |
+--------------------------+-------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# default local-preference 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no default local-preference

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## dynamic-med-interval
```rst
protocols bgp dynamic-med-interval
----------------------------------

**Minimum user role:** operator

When using an egress policy with 'set med igp-cost', any change in the MED attribute is advertised.
To configure a delay in the advertisement of updates:

**Command syntax: dynamic-med-interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| interval  | Set delay interval for consecutive updates due to MED attribute change when      | 0-15  | 0       |
|           | using set med igp-cost                                                           |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# dynamic-med-interval 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no dynamic-med-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## enforce-first-as
```rst
protocols bgp enforce-first-as
------------------------------

**Minimum user role:** operator

This command forces the BGP router to compare the first AS, in the AS path of eBGP routes received from neighbors, to the configured remote external neighbor AS number. Updates from eBGP neighbors that do not include that AS number as the first item in the AS_PATH attribute will be ignored.

**Command syntax: enforce-first-as**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# enforce-first-as


**Removing Configuration**

To disable the enforcement:
::

    dnRouter(cfg-protocols-bgp)# no enforce-first-as

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## fast-external-failover
```rst
protocols bgp fast-external-failover
------------------------------------

**Minimum user role:** operator

This command instructs the BGP process to immediately terminate external BGP peering sessions of directly adjacent neighbors if the link used to reach these neighbors goes down, without waiting for the hold-down timer to expire:

**Command syntax: fast-external-failover [fast-external-failover]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- This option is enabled by default.

**Parameter table**

+------------------------+---------------------------------------------+--------------+---------+
| Parameter              | Description                                 | Range        | Default |
+========================+=============================================+==============+=========+
| fast-external-failover | fast peer termination for unreachable peers | | enabled    | enabled |
|                        |                                             | | disabled   |         |
+------------------------+---------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# fast-external-failover disabled
    dnRouter(cfg-protocols-bgp)# fast-external-failover enabled


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-protocols-bgp)# no fast-external-failover

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## label-retention
```rst
protocols bgp label-retention
-----------------------------

**Minimum user role:** operator

There are cases where BGP is required to the change the locally allocated labels for the same prefix:

-	For a label per prefix - when the best-path to a prefix has changed from being second-best (bgp-external) to first-best.

-	For a label per nexthop - when the nexthop has changed.

In both cases, to allow for a smooth label transition in the network, bgp will install a new label and retain the previous label installed in FIB for a defined period. This period is the BGP label retention timer.

To configure the label-retention timer:

**Command syntax: label-retention [label-retention-time]**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Parameter table**

+----------------------+-------------+-------+---------+
| Parameter            | Description | Range | Default |
+======================+=============+=======+=========+
| label-retention-time | Munites     | 3-60  | 5       |
+----------------------+-------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# label-retention 10


**Removing Configuration**

To revert BGP label-retention parameter to its default value:
::

    dnRouter(cfg-protocols-bgp)# no label-retention

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## network import-check
```rst
protocols bgp network import-check
----------------------------------

**Minimum user role:** operator

This command instructs the BGP process to validate that the BGP route exists in the routing table (RIB) before injecting it into BGP and advertising it to the BGP neighbors.

**Command syntax: network import-check [network-import-check]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Parameter table**

+----------------------+---------------------------------------+--------------+---------+
| Parameter            | Description                           | Range        | Default |
+======================+=======================================+==============+=========+
| network-import-check | Check BGP network route exists in IGP | | enabled    | enabled |
|                      |                                       | | disabled   |         |
+----------------------+---------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# network import-check disabled


**Removing Configuration**

To revert to the default configuration:
::

    dnRouter(cfg-protocols-bgp)# no network import-check

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 6.0     | Command introduced                         |
+---------+--------------------------------------------+
| 9.0     | Added Enabled/Disabled value to the syntax |
+---------+--------------------------------------------+
```

## nexthop-trigger-delay
```rst
protocols bgp nexthop-trigger-delay
-----------------------------------

**Minimum user role:** operator

If BGP reacts prematurely to IGP updates, traffic may be lost. This command allows you to set a delay in BGP's reaction to IGP updates when IGP convergence is slow.

You can change the delay interval for triggering next-hop calculations when a next-hop address tracking event occurs.

To set the delay:

**Command syntax: nexthop-trigger-delay [nexthop-trigger-delay]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- Setting the delay to 0 disables the delay.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter             | Description                                                                      | Range | Default |
+=======================+==================================================================================+=======+=========+
| nexthop-trigger-delay | Change the delay interval that will trigger the scheduling of next-hop-tracking  | 0-100 | 5       |
|                       | feature                                                                          |       |         |
+-----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# nexthop-trigger-delay 3


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no nexthop-trigger-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
```

## protocols bgp overview
```rst
BGP Overview
-------------

Border Gateway Protocol (BGP) is the main routing protocol for exchanging routing and reachability information among autonomous systems. BGP is also used for routing within an AS. An external BGP (E-BGP) is used to exchange routing information between ASs and internal BGP (I-BGP) is used to distribute learned routes within an AS.

To prevent looping of routing information within an AS, routes learned from an I-BGP peer are not redistributed to other I-BGP peers. Therefore, every I-BGP router in an AS must establish a BGP session with all other I-BGP peers in the AS, creating a full BGP mesh, as shown in the following image.

<INSERT 02_protocols_bgp>

To prevent looping of routing information between ASs, E-BGP peers do not redistribute information received from within their AS. Routes received via I-BGP are not stored in the RIB.

BGP neighbors (peers) are established using manual configuration commands (static peers) and they communicate through a TCP session.

During established BGP sessions, routers exchange update messages about the destinations to which they offer connectivity. The route description includes the destination prefix, prefix length, autonomous systems in the path, the next hop, and information that affects the acceptance policy of the receiving router. Update messages also list destinations to which the router no longer offers connectivity.```

## route-reflection-policy-out-attribute-change
```rst
protocols bgp route-reflection policy-out attribute-change
----------------------------------------------------------

**Minimum user role:** operator

Support modification of the following BGP path attributes by the policy out when acting as a Route-reflector:

NEXT_HOP
AS_PATH
LOCAL_PREF
MED

By default, per RFC4456#10, when acting as a Route-Reflector, for iBGP advertisement, DNOS will not apply any modification for the attributes provided above if the path is an iBGP path. Even if it was explicitly required by the neighbor policy out.
By default, per RFC4456#10, when acting as a Route-Reflector for iBGP advertisement, DNOS will not apply any modification for the attributes provided above if the path is an iBGP path. Even if it was explicitly required by the neighbor policy out.

To enable route-reflector policy-out attribute-change:


**Command syntax: route-reflection policy-out attribute-change [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**
- "Supported for default VRF and non-default VRF"
- "The behavior will apply for any neighbor there is a case of route reflection for and any address-family.
- "Configuration can co-exist with the ‘self-force’ option of policy set ipv4 next-hop / policy set ipv6 next-hop.
-- When the “route-reflector policy-out attribute-change” is enabled, the any next-hop modification option of policy set ipv4 next-hop / policy set ipv6 next-hop is imposed.
-- When the “route-reflector policy-out attribute-change” is disabled (default), only “self-force) the next-hop modification option of policy set ipv4 next-hop / policy set ipv6 next-hop is imposed when the reflecting routes act as the route-reflector.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Support modification of NEXT_HOP, AS_PATH, LOCAL_PREF and MED path attributes by | | enabled    | disabled |
|             | policy out when reflecting paths as Route-reflector                              | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# route-reflection policy-out attribute-change enabled


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-protocols-bgp)# no route-reflection policy-out attribute-change

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## router-id
```rst
protocols bgp router-id
-----------------------

**Minimum user role:** operator

To set the router-ID of the BGP process:

**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- Changing the router-id will cause all BGP sessions to restart.

- When using OSPFv3 or IPv6-based BGP peering within a routing instance, you must explicitly configure a router ID (router-id) for that specific instance. The main routing instance's router ID is not inherited by other instances. Even if only IPv6 protocols are used, a 32-bit router ID is still required, as IPv6 routing protocols rely on it for establishing adjacencies. The router ID must be a non-zero 32-bit (4-octet) unsigned integer. While it's common to use an IPv4 address as the router ID, this is not mandatory - it doesn’t need to be a valid or routable address, just a unique 32-bit value within the routing domain. Failing to configure a router ID in an IPv6 OSPF or BGP instance will result in the protocol defaulting to 0.0.0.0, which is invalid. This will prevent adjacency formation and BGP session establishment.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| router-id | Router id of the router - an unsigned 32-bit integer expressed in dotted quad    | A.B.C.D | \-      |
|           | notation. By default - the ipv4 address of lo0 interface                         |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# router-id 100.70.1.45


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-protocols-bgp)# no router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

# ISIS

## graceful-restart
```rst
protocols isis graceful-restart
-------------------------------

**Minimum user role:** operator

Typically when a router restarts, all its peers detect that the device is not available and update their routing tables accordingly. To avoid routing flaps, graceful restart maintains the data-path behavior for a grace period to allow the device to restart. In this way, graceful restart allows the device to restart with minimal effect on the network. When enabled, the restarting routing device is not removed from the network topology during the restart period and the adjacencies are reestablished after restart is complete.

All graceful restart parameter values must be identical for all IS-IS instances.

To configure graceful restart:

**Command syntax: graceful-restart [admin-state]** grace-interval [grace-interval] helper [helper-state]

**Command mode:** config

**Hierarchies**

- protocols isis

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter      | Description                                                                      | Range        | Default  |
+================+==================================================================================+==============+==========+
| admin-state    | The administrative state of the graceful restart feature.                        | | enabled    | disabled |
|                |                                                                                  | | disabled   |          |
+----------------+----------------------------------------------------------------------------------+--------------+----------+
| grace-interval | Specifies how long (in seconds) the restarting device and its helpers continue   | 5-600        | 120      |
|                | to forward packets without disrupting network performance.                       |              |          |
+----------------+----------------------------------------------------------------------------------+--------------+----------+
| helper-state   | The administrative state of the graceful restart capability on the helper        | | enabled    | enabled  |
|                | device.                                                                          | | disabled   |          |
+----------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# graceful-restart disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# graceful-restart enabled
    dnRouter(cfg-protocols-isis)# graceful-restart enabled grace-interval 500 helper enabled
    dnRouter(cfg-protocols-isis)# graceful-restart enabled helper disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# graceful-restart disabled
    dnRouter(cfg-protocols-isis)# graceful-restart disabled grace-interval 500 helper enabled
    dnRouter(cfg-protocols-isis)# graceful-restart disabled helper disabled


**Removing Configuration**

To revert all graceful restart parameters to their default values:
::

    dnRouter(cfg-protocols-isis)# no graceful-restart

To revert the helper capability to the default state:
::

    dnRouter(cfg-protocols-isis)# no graceful-restart disabled helper

To revert the grace-interval to the default value:
::

    dnRouter(cfg-protocols-isis)# no graceful-restart enabled grace-interval

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 6.0     | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 9.0     | Changed default admin-state and helper-state, changed interval range |
+---------+----------------------------------------------------------------------+
| 10.0    | Removed requirement to specify admin-state in "no" commands          |
+---------+----------------------------------------------------------------------+
```

## isis overview
```rst
Intermediate System to Intermediate System (IS-IS) Overview
-----------------------------------------------------------
The IS-IS routing protocol is a link-state Interior Gateway Protocol (IGP) providing fast convergence, better stability, and more efficient use of bandwidth, memory, and CPU resources. Like other link-state protocols, IS-IS propagates the information required to build a complete network connectivity map on each participating device. This map is then used to calculate the shortest path to destinations.

In large ISIS domains, scaling the number of nodes and links can become a limiting factor due to the LSP database's increased size. Splitting the ISIS domain into levels is an efficient scaling method. Level 1/2 functionality supports route leaking and propagation between the different levels and summarization on level boundaries. DNOS supports pure L2 and L1/L2 border nodes.

**Note**

- RSVP-TE and BGP-LS are supported on L2 only.
```

## isis
```rst
protocols isis
--------------

**Minimum user role:** operator

The IS-IS routing protocol is a link-state Interior Gateway Protocol (IGP) providing fast convergence, better stability, and more efficient use of bandwidth, memory, and CPU resources. Like other link-state protocols, IS-IS propagates the information required to build a complete network connectivity map on each participating device. This map is then used to calculate the shortest path to destinations.

In large IS-IS domains, scaling the number of nodes and links can become a limiting factor due to the LSP database's increased size. Splitting the IS-IS domain into levels is an efficient scaling method. Level 1/2 functionality supports route leaking and propagation between the different levels and summarization on level boundaries. DNOS supports pure L2 and L1/L2 border nodes.

To enter the IS-IS global configuration level:

**Command syntax: isis**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- RSVP-TE and BGP-LS are supported on L2 only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)#


**Removing Configuration**

To remove all IS-IS instances and return all global IS-IS configuration to the default values:
::

    dnRouter(cfg-protocols)# no isis

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## lsp-fingerprint
```rst
protocols isis lsp-fingerprint
------------------------------

**Minimum user role:** operator

Enable advertisement of fingerprint TLV (Type 15) according to rfc8196.
Fingerprint TLV will hold unique system identifiers.
Fingerprint TLV is used to detect duplicating nodes in the network. The detection will result only in a system event, no other corrective action is automatically taken.
To enable LSP fingerprint TLV generation:

**Command syntax: lsp-fingerprint [lsp-fingerprint]**

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- Configuration applies for all ISIS instances and for all levels ISIS is enabled on for a given instance.

- Fingerprint TLV is advertised under the LSP first fragment.

- Fingerprint TLV is advertised with S, A flags unset. Support of fingerprint TLV does not reflect system support for autoconfiguration.

- The system event will comply with DNOS syslog suppression, such as a single syslog notification that is sent every 30sec as long as duplication is recognized by repeatedly getting the conflicting LSP.

- The fingerprint will not be signaled in any other type of packet, but LSP.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter       | Description                                                                      | Range        | Default  |
+=================+==================================================================================+==============+==========+
| lsp-fingerprint | Enable advertisement of fingerprint tlv (Type 15) according to rfc8196.          | | enabled    | disabled |
|                 | Fingerprint tlv will hold system unique identifier. Fingerprint tlv is used to   | | disabled   |          |
|                 | detect duplicating nodes in the network                                          |              |          |
+-----------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# lsp-fingerprint enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-isis)# no lsp-fingerprint

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## maximum-adjacencies
```rst
protocols isis maximum-adjacencies
----------------------------------

**Minimum user role:** operator

You can control the number of IS-IS adjacencies allowed. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. The thresholds are for generating system-events only. There is no strict limit on the number of IS-IS adjacencies that can be formed.

To limit the number of IS-IS adjacencies:

**Command syntax: maximum-adjacencies [max-adjacencies]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- There is no strict limitation on the number of IS-IS adjacencies that can be formed.

- When a threshold is crossed (max-adjacencies or threshold), a single system-event notification is generated.

- When a threshold is cleared (max-adjacencies or threshold), a single system-event notification is generated.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| max-adjacencies | The maximum number of IS-IS adjacencies allowed. When this threshold is crossed, | 1-65535 | 50      |
|                 | a system-event notification is generated every 30 seconds until the number of    |         |         |
|                 | adjacencies drops below the maximum.                                             |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+
| threshold       | A percentage (%) of max-adjacencies to give you advance notice that the number   | 1-100   | 75      |
|                 | of adjacencies is reaching the maximum level. When this threshold is crossed, a  |         |         |
|                 | single system-event notification is generated.                                   |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# maximum-adjacencies 50 threshold 80

In the above example, the maximum number of IS-IS adjacencies is set to 50 and the threshold is set to 80%. This means that when the number of adjacencies reaches 40, a system-event notification will be generated that the 80% threshold has been crossed. If you do nothing, you will not receive another notification until the number of adjacencies reaches 50.


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-isis)# no maximum-adjacencies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## maximum-routes
```rst
protocols isis maximum-routes
-----------------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. The scale is aggregated across all isis instances and address-families.

To set thresholds on IS-IS routes:

**Command syntax: maximum-routes [max-routes]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- There is no strict limitation on the number of IS-IS adjacencies that can be formed.

- When a threshold is crossed (max-routes or threshold), a single system-event notification is generated.

- When a threshold is cleared (max-routes or threshold), a single system-event notification is generated.

**Parameter table**

+------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                                      | Range        | Default |
+============+==================================================================================+==============+=========+
| max-routes | The maximum number of IS-IS routes you want in the RIB. When this threshold is   | 1-4294967295 | 32000   |
|            | crossed, a single system-event notification is generated. You will not be        |              |         |
|            | notified again.                                                                  |              |         |
|            | 0 means no limit; a system-event will not be generated.                          |              |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+
| threshold  | A percentage (%) of max-routes to give you advance notice that the number of     | 1-100        | 75      |
|            | IS-IS routes in the RIB is reaching the maximum level. When this threshold is    |              |         |
|            | crossed, a system-event notification is generated. You will not be notified      |              |         |
|            | again.                                                                           |              |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# maximum-routes 15000 threshold 80

In the above example, the maximum number of IS-IS routes in the RIB is set to 15,000 and the threshold is set to 80%. This means that when the number of IS-IS routes in the RIB reaches 12,000, a system-event notification will be generated that the 80% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 15,000.


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-isis)# no maximum-routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## nsr
```rst
protocols isis nsr
------------------

**Minimum user role:** operator

IS-IS nonstop routing (NSR) enables an IS-IS speaker to maintain IS-IS adjacencies, state and database, while undergoing a switchover at the CPU level (e.g. NCC switchover).
Unlike IS-IS graceful-restart (GR), which requires support from an IS-IS neighbor as GR helper, NSR recovery is transparent to the network and connected neighbors.

IS-IS NSR is supported for cluster (external NCC) and stand-alone setups.

To enable/disable isis NSR:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- NSR is mutually exclusive with GR support. IS-IS nsr and IS-IS graceful restart cannot be enabled at the same time.

**Parameter table**

+-----------+----------------------------+--------------+---------+
| Parameter | Description                | Range        | Default |
+===========+============================+==============+=========+
| nsr       | Set IS-IS Non Stop Routing | | enabled    | enabled |
|           |                            | | disabled   |         |
+-----------+----------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# nsr enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-isis)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

# OSPF

## maximum-adjacencies
```rst
protocols ospf maximum-adjacencies
----------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPF maximum adjacencies and threshold limit.

**Command syntax: maximum-adjacencies [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospf

**Note**

- When the threshold is crossed, a single system-event OSPF_MAXIMUM_ADJACENCIES_THRESHOLD_EXCEEDED notification is generated.

- When the threshold is cleared, a single system-event OSPF_MAXIMUM_ADJACENCIES_THRESHOLD_CLEARED notification is generated.

- When the maximum threshold is crossed, a system-event OSPF_MAXIMUM_ADJACENCIES_LIMIT_REACHED notification is generated.

- When the maximum threshold is cleared, a single system-event OSPF_MAXIMUM_ADJACENCIES_LIMIT_CLEARED notification is generated.

**Parameter table**

+-----------+-----------------------------------------------------------+---------+---------+
| Parameter | Description                                               | Range   | Default |
+===========+===========================================================+=========+=========+
| maximum   | maximum number of adjacencies.                            | 1-65535 | 500     |
+-----------+-----------------------------------------------------------+---------+---------+
| threshold | threshold as a percentage of maximum allowed adjacencies. | 1-100   | 75      |
+-----------+-----------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# maximum-adjacencies 433
    dnRouter(cfg-protocols-ospf)# maximum-adjacencies 433 threshold 65


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospf)# no maximum-adjacencies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
```

## maximum-routes
```rst
protocols ospf maximum-routes
-----------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPF maximum routes and threshold limit.

**Command syntax: maximum-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospf

**Note**

- The 'no maximum-routes' returns the maximum and threshold to their default values.

**Parameter table**

+-----------+------------------------------------------------------+--------------+---------+
| Parameter | Description                                          | Range        | Default |
+===========+======================================================+==============+=========+
| maximum   | maximum number of routes.                            | 1-4294967295 | 32000   |
+-----------+------------------------------------------------------+--------------+---------+
| threshold | threshold as a percentage of maximum allowed routes. | 1-100        | 75      |
+-----------+------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# maximum-routes 90000
    dnRouter(cfg-protocols-ospf)# maximum-routes 90000 threshold 80


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospf)# no maximum-routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
```

## nsr
```rst
protocols ospf nsr
------------------

**Minimum user role:** operator

OSPF nonstop routing (NSR) enables an OSPF speaker to maintain OSPF adjacencies, state and database, while undergoing a switchover at the CPU level (e.g. NCC switchover). Unlike OSPF graceful-restart (GR), which requires support from an OSPF neighbor as GR helper, NSR recovery is transparent to the network and connected neighbors.
OSPF NSR is supported for cluster (external NCC) and stand-alone setups.
Configuration applies for all OSPFv2 instances in all VRFs.
To enable/disable OSPF NSR:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols ospf

**Note**

- NSR is mutually exclusive with GR support. OSPF NSR and OSPF graceful restart in restarting mode cannot be enabled at the same time.

**Parameter table**

+-----------+---------------------------+--------------+---------+
| Parameter | Description               | Range        | Default |
+===========+===========================+==============+=========+
| nsr       | Set OSPF Non Stop Routing | | enabled    | enabled |
|           |                           | | disabled   |         |
+-----------+---------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# nsr enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospf)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
```

## ospf overview
```rst
Open Shortest Path First (OSPF) Overview
----------------------------------------
Open Shortest Path First (OSPF) is a link-state routing protocol that operates within a single autonomous system. Each OSPF router maintains an identical database describing the routers' topology. Each router communicates its topology to other routers using link state advertisements (LSA). A topology of the area is constructed from these LSAs and is stored in the database. From this database, each router constructs a tree of shortest paths with itself as a root, giving the route to each destination in the autonomous system. OSPF recalculates routes quickly and dynamically in the face of topological changes, utilizing a minimum of routing protocol traffic.

The OSPF protocol is enabled with equal-cost multi-path routing (ECMP) so that packet forwarding to a single destination can spread across multiple next-hops as opposed to a single “best”.

The following commands are common to OSPFv2 (IPv4 OSPF version) and OSPFv3 (IPv6 OSPF version).

The following table maps the commands available per OSPF version:

+-------------------------------------------------------+------+--------+
| Command                                               | OSPF | OSPFv3 |
+-------------------------------------------------------+------+--------+
| clear ospf statistics                                 | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf routes                                     | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf process                                    | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf database                                   | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf interfaces                                 | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface hello-interval                    | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf auto-cost reference-bandwidth                    | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf class-of-service                                 | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf default-originate                                | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd admin-state                             | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd min-rx                                  | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd min-tx                                  | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd multiplier                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd                                         | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf max-metric router-lsa-administrative             | v    |        |
+-------------------------------------------------------+------+--------+
| ospf max-metric router-lsa on-startup                 | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd                               | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd admin-state                   | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd min-rx                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd min-tx                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd multiplier                    | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf maximum-ecmp-paths                               | v    |        |
+-------------------------------------------------------+------+--------+
| ospf maximum-redistributed-prefixes                   | v    |        |
+-------------------------------------------------------+------+--------+
| ospf redistribute                                     | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf redistribute-metric                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf timers refresh                                   | v    |        |
+-------------------------------------------------------+------+--------+
| ospf timers throttle lsa all                          | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf timers lsa-arrival                               | v    |        |
+-------------------------------------------------------+------+--------+
| ospf timers throttle spf                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf administrative distance                          | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface cost                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface dead-interval                     | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface mtu-ignore                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface network                           | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface passive                           | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface                                   | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area                                             | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf log-adjacency-changes                            | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf router-id                                        | v    | v      |
+-------------------------------------------------------+------+--------+
| protocols ospf                                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf mpls ldp-sync                                    | v    |        |
+-------------------------------------------------------+------+--------+
| ospf graceful-restart                                 | v    |        |
+-------------------------------------------------------+------+--------+
| ospf fast-reroute                                     | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area network                                     | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area authentication                              | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area filter-list in/out                          | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication                    | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication-key authentication | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication-key md5            | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface fast-reroute-candidate            | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface cost-mirroring                    | v    |        |
+-------------------------------------------------------+------+--------+```

## ospf
```rst
protocols ospf
--------------

**Minimum user role:** operator

Enters the OSPF configuration hierarchy level.

**Command syntax: ospf**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The no command will remove the ospf protocol.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)#


**Removing Configuration**

To remove the OSPF protocol
::

    dnRouter(cfg-protocols)# no ospf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

# OSPFV3

## administrative-distance-external
```rst
protocols ospfv3 administrative-distance external
-------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance external [administrative-distance-external]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+----------------------------------+----------------------------------------------------------+-------+---------+
| Parameter                        | Description                                              | Range | Default |
+==================================+==========================================================+=======+=========+
| administrative-distance-external | Set the administrative distance for ospf external routes | 1-255 | \-      |
+----------------------------------+----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance external 120


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance external

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## administrative-distance-inter
```rst
protocols ospfv3 administrative-distance inter-area
---------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance inter-area [administrative-distance-inter-area]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+------------------------------------+------------------------------------------------------------+-------+---------+
| Parameter                          | Description                                                | Range | Default |
+====================================+============================================================+=======+=========+
| administrative-distance-inter-area | Set the administrative distance for ospf inter-area routes | 1-255 | \-      |
+------------------------------------+------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance inter-area 200


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance inter-area

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## administrative-distance-intra
```rst
protocols ospfv3 administrative-distance intra-area
---------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance intra-area [administrative-distance-intra-area]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+------------------------------------+------------------------------------------------------------+-------+---------+
| Parameter                          | Description                                                | Range | Default |
+====================================+============================================================+=======+=========+
| administrative-distance-intra-area | Set the administrative distance for ospf intra-area routes | 1-255 | \-      |
+------------------------------------+------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance intra-area 150


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance intra-area

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## administrative-distance
```rst
protocols ospfv3 administrative-distance
----------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.
To configure the administrative distance for ospfv3:

**Command syntax: administrative-distance [administrative-distance]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- An admin-distance of 255 will cause the router to remove the route from the forwarding table and not use it.

**Parameter table**

+-------------------------+------------------------------------------+-------+---------+
| Parameter               | Description                              | Range | Default |
+=========================+==========================================+=======+=========+
| administrative-distance | Set the administrative distance for ospf | 1-255 | 110     |
+-------------------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# administrative-distance 20
    dnRouter(cfg-protocols-ospfv3)# administrative-distance external 22
    dnRouter(cfg-protocols-ospfv3)# administrative-distance inter-area 25
    dnRouter(cfg-protocols-ospfv3)# administrative-distance intra-area 30


**Removing Configuration**

To revert administrative distances to the default value:
::

    dnRouter(cfg-protocols-ospfv3)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## auto-cost
```rst
protocols ospfv3 auto-cost reference-bandwidth
----------------------------------------------

**Minimum user role:** operator

You can set the reference bandwidth for cost calculations, where this bandwidth is considered equivalent to an OSPFv3 cost of 1 (specified in Mbps). The default is 100 Mbps (i.e. a link of bandwidth 100 Mbps or higher will have a cost of 1. Cost of lower bandwidth links will be scaled with reference to this cost. 
To configure the reference bandwidth:

**Command syntax: auto-cost reference-bandwidth [auto-cost-reference-bandwidth]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Parameter table**

+-------------------------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter                     | Description                                                                      | Range     | Default |
+===============================+==================================================================================+===========+=========+
| auto-cost-reference-bandwidth | This sets the reference bandwidth for cost calculations, where this bandwidth is | 1-4294967 | 100     |
|                               | considered equivalent to an OSPF cost of 1, specified in Mbits/s. The default is |           |         |
|                               | 100Mbit/s (i.e. a link of bandwidth 100Mbit/s or higher will have a cost of 1.   |           |         |
|                               | Cost of lower bandwidth links will be scaled with reference to this cost).       |           |         |
+-------------------------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# auto-cost reference-bandwidth 100000


**Removing Configuration**

To return the reference bandwidth to its default value: 
::

    dnRouter(cfg-protocols-ospfv3)# no auto-cost reference-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## class-of-service
```rst
protocols ospfv3 class-of-service
---------------------------------

**Minimum user role:** operator

Set dscp value for outgoing OSPFv3 packets. 
IPP is set accordingly. i.e DSCP 48 is mapped to 6.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- No command returns dscp-value to default

**Parameter table**

+------------------+--------------------------------------+-------+---------+
| Parameter        | Description                          | Range | Default |
+==================+======================================+=======+=========+
| class-of-service | dscp value for outgoing OSPF packets | 0-56  | 48      |
+------------------+--------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospfv3)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## default-originate
```rst
protocols ospfv3 default-originate
----------------------------------

**Minimum user role:** operator

To force the router to generate an OSPFv3 AS-External (type-5) LSA, describing a default route into all external-routing capable areas, of the specified metric and metric type:

**Command syntax: default-originate** always metric [metric] metric-type [metric-type] policy [policy-name]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- default-originate is disabled by default.

- no default-originate - disables default-information originate.

- no default-originate [attribute] - return attribute to default state.

- If always is set, the default-route is originated with default metric 0. The Metric can be modified by a user configuration or policy logic.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| always      | when true, the default is always advertised, even when there is no default       | Boolean          | False   |
|             | present in the routing table                                                     |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| metric      | Used for generating the default route, this parameter specifies the cost for     | 0-16777214       | \-      |
|             | reaching the rest of the world through this route.                               |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-type | Specifies how the cost of a neighbor metric is determined                        | | 1              | 2       |
|             |                                                                                  | | 2              |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| policy-name | set routing policy                                                               | | string         | \-      |
|             |                                                                                  | | length 1-255   |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# default-originate
    dnRouter(cfg-protocols-ospfv3)# default-originate metric 10000
    dnRouter(cfg-protocols-ospfv3)# default-originate metric 10000 metric-type 2
    dnRouter(cfg-protocols-ospfv3)# default-originate metric 10000 metric-type 2 policy MY_POL
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# default-originate always
    dnRouter(cfg-protocols-ospfv3)# default-originate always metric 10000
    dnRouter(cfg-protocols-ospfv3)# default-originate always metric 10000 metric-type 2
    dnRouter(cfg-protocols-ospfv3)# default-originate metric-type 2 metric 3000 always
    dnRouter(cfg-protocols-ospfv3)# default-originate always metric 10000 metric-type 2 policy MY_POL  - dnRouter# configure


**Removing Configuration**

default-originate is disabled by default
::

    no default-originate - disables default-information originate

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 11.6    | Command introduced                                |
+---------+---------------------------------------------------+
| 13.1    | Added support for OSPFv3                          |
+---------+---------------------------------------------------+
| 25.0    | Expected metric behavior note under 'always' knob |
+---------+---------------------------------------------------+
```

## maximum-adjacencies
```rst
protocols ospfv3 maximum-adjacencies
------------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPFV3 maximum adjacencies and threshold limit.

**Command syntax: maximum-adjacencies [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- When the threshold is crossed, a single system-event OSPFV3_MAXIMUM_ADJACENCIES_THRESHOLD_EXCEEDED notification is generated.

- When the threshold is cleared, a single system-event OSPFV3_MAXIMUM_ADJACENCIES_THRESHOLD_CLEARED notification is generated.

- When the maximum threshold is crossed, a system-event OSPFV3_MAXIMUM_ADJACENCIES_LIMIT_REACHED notification is generated.

- When the maximum threshold is cleared, a single system-event OSPFV3_MAXIMUM_ADJACENCIES_LIMIT_CLEARED notification is generated.

**Parameter table**

+-----------+-----------------------------------------------------------+---------+---------+
| Parameter | Description                                               | Range   | Default |
+===========+===========================================================+=========+=========+
| maximum   | maximum number of adjacencies.                            | 1-65535 | 500     |
+-----------+-----------------------------------------------------------+---------+---------+
| threshold | threshold as a percentage of maximum allowed adjacencies. | 1-100   | 75      |
+-----------+-----------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# maximum-adjacencies 433
    dnRouter(cfg-protocols-ospfv3)# maximum-adjacencies 433 threshold 65


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospfv3)# no maximum-adjacencies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
```

## maximum-ecmp-paths
```rst
protocols ospfv3 maximum-ecmp-paths
-----------------------------------

**Minimum user role:** operator

To configure the OSPFV3 maximum ECMP path limit:

**Command syntax: maximum-ecmp-paths [maximum-ecmp-paths]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- On-startup and On-shutdown may be configured simultaneously and are mutually exclusive with "administrative".

**Parameter table**

+--------------------+-------------------------------------------+-------+---------+
| Parameter          | Description                               | Range | Default |
+====================+===========================================+=======+=========+
| maximum-ecmp-paths | Maximum ECMP paths that OSPF can support. | 1-32  | 32      |
+--------------------+-------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# maximum-ecmp-paths 20


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospfv3)# no maximum-ecmp-paths

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 11.6    | Command introduced        |
+---------+---------------------------+
| 13.1    | Added support for OSPFv3  |
+---------+---------------------------+
```

## maximum-redistributed-prefixes
```rst
protocols ospfv3 maximum-redistributed-prefixes
-----------------------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPFV3 maximum redistributed prefixes limit and threshold limit. Scale is aggregated across all address-families. A single system-event notification is generated in the following cases:
•	When the threshold is crossed
•	When the threshold is cleared
•	When the maximum is reached (no further prefixes are redistributed and a system-event notification is generated)
•	When the redistributed prefixes decreases below the maximum.

**Command syntax: maximum-redistributed-prefixes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**
The 'no maximum-redistributed-prefixes' returns the maximum and threshold to their default values.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| maximum   | maximum allowed number prefixes redistribute below which no more prefixes are    | 1-32000 | 10000   |
|           | allowed.                                                                         |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+
| threshold | threshold as a percentage of system maximum allowed redistributed prefixes.      | 1-100   | 75      |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# maximum-redistributed-prefixes 30000
    dnRouter(cfg-protocols-ospfv3)# maximum-redistributed-prefixes 30000 threshold 80


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospfv3)# no maximum-redistributed-prefixes

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 13.1    | Added support for OSPFv3 |
+---------+--------------------------+
```

## maximum-routes
```rst
protocols ospfv3 maximum-routes
-------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPFV3 maximum routes and threshold limit.

**Command syntax: maximum-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'no maximum-routes' returns the maximum and threshold to their default values.

**Parameter table**

+-----------+------------------------------------------------------+--------------+---------+
| Parameter | Description                                          | Range        | Default |
+===========+======================================================+==============+=========+
| maximum   | maximum number of routes.                            | 1-4294967295 | 9000    |
+-----------+------------------------------------------------------+--------------+---------+
| threshold | threshold as a percentage of maximum allowed routes. | 1-100        | 75      |
+-----------+------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# maximum-routes 90000
    dnRouter(cfg-protocols-ospfv3)# maximum-routes 90000 threshold 80


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospfv3)# no maximum-routes

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 13.1    | Command introduced                                    |
+---------+-------------------------------------------------------+
| TBD     | Add default values for maximum routes and adjacencies |
+---------+-------------------------------------------------------+
```

## max-metric-router-lsa-administrative-external-lsa
```rst
protocols ospfv3 max-metric router-lsa administrative external-lsa
------------------------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.

To change the OSPF administrative distance for all routes:

**Command syntax: max-metric router-lsa administrative external-lsa** external-lsa-metric [external-lsa-metric]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'external-lsa' option is used to override the external-LSA metric with the max-metric value or with the [external-lsa] metric value.

**Parameter table**

+---------------------+---------------------------------------+------------+----------+
| Parameter           | Description                           | Range      | Default  |
+=====================+=======================================+============+==========+
| external-lsa-metric | The external-lsa metric to advertise. | 1-16777215 | 16711680 |
+---------------------+---------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa administrative external-lsa external-lsa-metric 120000


**Removing Configuration**

To stop the automatic max-metric advertisement:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa administrative external-lsa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## max-metric-router-lsa-administrative-include-stub
```rst
protocols ospfv3 max-metric router-lsa administrative include-stub
------------------------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa administrative include-stub**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'include-stub' option is used to advertise stub-links in router-LSA with the max-metric value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa administrative include-stub


**Removing Configuration**

To stop the automatic max-metric advertisement:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa administrative

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## max-metric-router-lsa-administrative
```rst
protocols ospfv3 max-metric router-lsa administrative
-----------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa administrative**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- This option is disabled by default.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa administrative
    dnRouter(cfg-protocols-ospfv3-mm-admin)#


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa administrative

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## max-metric-router-lsa-on-startup-external-lsa
```rst
protocols ospfv3 max-metric router-lsa on-startup external-lsa
--------------------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.

To change the OSPF administrative distance for all routes:

**Command syntax: max-metric router-lsa on-startup external-lsa** external-lsa-metric [external-lsa-metric]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'external-lsa' option is used to override the external-LSA metric with the max-metric value or with the [external-lsa] metric value.

**Parameter table**

+---------------------+---------------------------------------+------------+----------+
| Parameter           | Description                           | Range      | Default  |
+=====================+=======================================+============+==========+
| external-lsa-metric | The external-lsa metric to advertise. | 1-16777215 | 16711680 |
+---------------------+---------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup external-lsa external-lsa-metric 120000


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa on-startup external-lsa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## max-metric-router-lsa-on-startup-include-stub
```rst
protocols ospfv3 max-metric router-lsa on-startup include-stub
--------------------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa on-startup include-stub**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'include-stub' option is used to advertise stub-links in router-LSA with the max-metric value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup
    dnRouter(cfg-protocols-ospfv3-mm-startup)# include-stub


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa on-startup

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## max-metric-router-lsa-on-startup-interval
```rst
protocols ospfv3 max-metric router-lsa on-startup interval
----------------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa on-startup interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Parameter table**

+-----------+------------------------------------------+---------+---------+
| Parameter | Description                              | Range   | Default |
+===========+==========================================+=========+=========+
| interval  | time in seconds for advertise on startup | 5-86400 | 600     |
+-----------+------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup
    dnRouter(cfg-protocols-ospfv3-mm-startup)# interval 3600


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa on-startup

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## max-metric-router-lsa-on-startup
```rst
protocols ospfv3 max-metric router-lsa on-startup
-------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa on-startup**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- This option is disabled by default.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup
    dnRouter(cfg-protocols-ospfv3-mm-startup)#


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa on-startup

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## nsr
```rst
protocols ospfv3 nsr
--------------------

**Minimum user role:** operator

OSPFv3 nonstop routing (NSR) enables an OSPFv3 speaker to maintain OSPFv3 adjacencies, state and database, while undergoing a switchover at the CPU level (e.g. NCC switchover). Unlike OSPFv3 graceful-restart (GR), which requires support from an OSPFv3 neighbor as GR helper, NSR recovery is transparent to the network and connected neighbors.
OSPFv3 NSR is supported for cluster (external NCC) and stand-alone setups.
Configuration applies for all OSPFv3 instances in all VRFs.
To enable/disable OSPFv3 NSR:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- NSR is mutually exclusive with GR support. OSPFv3 NSR and OSPFv3 graceful restart in restarting mode cannot be enabled at the same time.

**Parameter table**

+-----------+-----------------------------+--------------+---------+
| Parameter | Description                 | Range        | Default |
+===========+=============================+==============+=========+
| nsr       | Set OSPFv3 Non Stop Routing | | enabled    | enabled |
|           |                             | | disabled   |         |
+-----------+-----------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# nsr enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospfv3)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.0    | Command introduced |
+---------+--------------------+
```

## ospfv3 overview
```rst
Open Shortest Path First (OSPFv3) Overview
------------------------------------------

Open Shortest Path First (OSPFv3) is a link-state routing protocol that operates within a single autonomous system. Each OSPF router maintains an identical database describing the routers' topology. Each router communicates its topology to other routers using link state advertisements (LSA). A topology of the area is constructed from these LSAs and is stored in the database. From this database, each router constructs a tree of shortest paths with itself as a root, giving the route to each destination in the autonomous system. OSPF recalculates routes quickly and dynamically in the face of topological changes, utilizing a minimum of routing protocol traffic.

The OSPF protocol is enabled with equal-cost multi-path routing (ECMP) so that packet forwarding to a single destination can spread across multiple next-hops as opposed to a single “best”.

The following commands are common to OSPFv2 (IPv4 OSPF version) and OSPFv3 (IPv6 OSPF version).

The following table maps the commands available per OSPF version:

+-------------------------------------------------------+------+--------+
| Command                                               | OSPF | OSPFv3 |
+-------------------------------------------------------+------+--------+
| clear ospf statistics                                 | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf routes                                     | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf process                                    | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf database                                   | v    | v      |
+-------------------------------------------------------+------+--------+
| clear ospf interfaces                                 | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface hello-interval                    | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf auto-cost reference-bandwidth                    | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf class-of-service                                 | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf default-originate                                | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd admin-state                             | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd min-rx                                  | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd min-tx                                  | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd multiplier                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area bfd                                         | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf max-metric router-lsa-administrative             | v    |        |
+-------------------------------------------------------+------+--------+
| ospf max-metric router-lsa on-startup                 | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd                               | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd admin-state                   | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd min-rx                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd min-tx                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd multiplier                    | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf maximum-ecmp-paths                               | v    |        |
+-------------------------------------------------------+------+--------+
| ospf maximum-redistributed-prefixes                   | v    |        |
+-------------------------------------------------------+------+--------+
| ospf redistribute                                     | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf redistribute-metric                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf timers refresh                                   | v    |        |
+-------------------------------------------------------+------+--------+
| ospf timers throttle lsa all                          | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf timers lsa-arrival                               | v    |        |
+-------------------------------------------------------+------+--------+
| ospf timers throttle spf                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf administrative distance                          | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface cost                              | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface dead-interval                     | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface mtu-ignore                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface network                           | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface passive                           | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area interface                                   | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf area                                             | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf log-adjacency-changes                            | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf router-id                                        | v    | v      |
+-------------------------------------------------------+------+--------+
| protocols ospf                                        | v    | v      |
+-------------------------------------------------------+------+--------+
| ospf mpls ldp-sync                                    | v    |        |
+-------------------------------------------------------+------+--------+
| ospf graceful-restart                                 | v    |        |
+-------------------------------------------------------+------+--------+
| ospf fast-reroute                                     | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area network                                     | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area authentication                              | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area filter-list in/out                          | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication                    | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication-key authentication | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication-key md5            | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface fast-reroute-candidate            | v    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface cost-mirroring                    | v    |        |
+-------------------------------------------------------+------+--------+
```

## ospfv3
```rst
protocols ospfv3
----------------

**Minimum user role:** operator

Enters the OSPFV3 configuration hierarchy level.

**Command syntax: ospfv3**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The 'no' command will remove the ospf protocol.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)#


**Removing Configuration**

To remove the OSPFv3 protocol
::

    dnRouter(cfg-protocols)# no ospfv3

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## redistribute bgp
```rst
protocols ospfv3 redistribute bgp
---------------------------------

**Minimum user role:** operator

You can use the following command to redistribute OSPFV3 routes of the specified protocol or kind into OSPF/OSPFv3, with the metric type and metric set if specified, and filtering the routes using the given policy (if specified).
If indicated, you can add the specified tag:

**Command syntax: redistribute bgp** metric [metric] metric-type [metric-type] policy [redistribute-policy] tag [tag]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- By default no redistribution is done.

- The metric default value is set by `redistribute-metric <#ospfv3 redistribute-metric>` configuration.

- no redistribute [protocol] - stops redistribution of a given protocols.

- no redistribute [protocol] [attribute] - return attribute to default state.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter           | Description                                                                      | Range            | Default |
+=====================+==================================================================================+==================+=========+
| metric              | sets metric value for the redistributed route                                    | 0-16777214       | \-      |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-type         | sets metric-type for the redistributed route                                     | | 1              | 2       |
|                     |                                                                                  | | 2              |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| redistribute-policy | policy (route-map) for filtering the routes                                      | | string         | \-      |
|                     |                                                                                  | | length 1-255   |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| tag                 | The tag value. Tag zero means no tagging is done. If, for example, a static      | 0-4294967295     | \-      |
|                     | route has tag and it is redistributed tag 0 means it is kept with the same tag   |                  |         |
|                     | on the redistributed tag. A non zero tag should override the original static     |                  |         |
|                     | route tag,                                                                       |                  |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# redistribute bgp
    dnRouter(cfg-protocols-ospfv3)# redistribute bgp metric 1 metric-type 2 policy MY_POL tag 2341


**Removing Configuration**

To return the attribute to the default state:
::

    dnRouter(cfg-protocols-ospfv3)# no redistribute bgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## redistribute connected
```rst
protocols ospfv3 redistribute connected
---------------------------------------

**Minimum user role:** operator

You can use the following command to redistribute OSPFV3 routes of the specified protocol or kind into OSPF/OSPFv3, with the metric type and metric set if specified, and filtering the routes using the given policy (if specified).
If indicated, you can add the specified tag:

**Command syntax: redistribute connected** metric [metric] metric-type [metric-type] policy [redistribute-policy] tag [tag]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- By default no redistribution is done.

- The metric default value is set by `redistribute-metric <#ospfv3 redistribute-metric>` configuration.

- no redistribute [protocol] - stops redistribution of a given protocols.

- no redistribute [protocol] [attribute] - return attribute to default state.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter           | Description                                                                      | Range            | Default |
+=====================+==================================================================================+==================+=========+
| metric              | sets metric value for the redistributed route                                    | 0-16777214       | \-      |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-type         | sets metric-type for the redistributed route                                     | | 1              | 2       |
|                     |                                                                                  | | 2              |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| redistribute-policy | policy (route-map) for filtering the routes                                      | | string         | \-      |
|                     |                                                                                  | | length 1-255   |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| tag                 | The tag value. Tag zero means no tagging is done. If, for example, a static      | 0-4294967295     | \-      |
|                     | route has tag and it is redistributed tag 0 means it is kept with the same tag   |                  |         |
|                     | on the redistributed tag. A non zero tag should override the original static     |                  |         |
|                     | route tag,                                                                       |                  |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# redistribute static
    dnRouter(cfg-protocols-ospfv3)# redistribute static metric 1 metric-type 2 policy MY_POL tag 2341


**Removing Configuration**

To return the attribute to the default state:
::

    dnRouter(cfg-protocols-ospfv3)# no redistribute connected

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## redistribute-metric
```rst
protocols ospfv3 redistribute-metric
------------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPFV3 maximum redistributed prefixes limit and threshold limit. Scale is aggregated across all address-families. A single system-event notification is generated in the following cases:

•	When the threshold is crossed
•	When the threshold is cleared
•	When the maximum is reached (no further prefixes are redistributed and a system-event notification is generated)
•	When the redistributed prefixes decreases below the maximum.

**Command syntax: redistribute-metric [redistribute-metric]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- No command returns metric to its default value.

**Parameter table**

+---------------------+-------------------------------------------------------------------------+------------+---------+
| Parameter           | Description                                                             | Range      | Default |
+=====================+=========================================================================+============+=========+
| redistribute-metric | Sets the default metric value for the OSPFv2 or OSPFv3 routing protocol | 0-16777214 | \-      |
+---------------------+-------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# redistribute-metric 1


**Removing Configuration**

To return the metric to its default value: 
::

    dnRouter(cfg-protocols-ospfv3)# no redistribute-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## redistribute static
```rst
protocols ospfv3 redistribute static
------------------------------------

**Minimum user role:** operator

You can use the following command to redistribute OSPFV3 routes of the specified protocol or kind into OSPF/OSPFv3, with the metric type and metric set if specified, and filtering the routes using the given policy (if specified).
If indicated, you can add the specified tag:

**Command syntax: redistribute static** metric [metric] metric-type [metric-type] policy [redistribute-policy] tag [tag]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- By default no redistribution is done.

- The metric default value is set by `redistribute-metric <#ospfv3 redistribute-metric>` configuration.

- no redistribute [protocol] - stops redistribution of a given protocols.

- no redistribute [protocol] [attribute] - return attribute to default state.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter           | Description                                                                      | Range            | Default |
+=====================+==================================================================================+==================+=========+
| metric              | sets metric value for the redistributed route                                    | 0-16777214       | \-      |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-type         | sets metric-type for the redistributed route                                     | | 1              | 2       |
|                     |                                                                                  | | 2              |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| redistribute-policy | policy (route-map) for filtering the routes                                      | | string         | \-      |
|                     |                                                                                  | | length 1-255   |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| tag                 | The tag value. Tag zero means no tagging is done. If, for example, a static      | 0-4294967295     | \-      |
|                     | route has tag and it is redistributed tag 0 means it is kept with the same tag   |                  |         |
|                     | on the redistributed tag. A non zero tag should override the original static     |                  |         |
|                     | route tag,                                                                       |                  |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# redistribute static
    dnRouter(cfg-protocols-ospfv3)# redistribute static metric 1 metric-type 2 policy MY_POL tag 2341


**Removing Configuration**

To return the attribute to the default state:
::

    dnRouter(cfg-protocols-ospfv3)# no redistribute static

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

## router-id
```rst
protocols ospfv3 router-id
--------------------------

**Minimum user role:** operator

Use the following command to set the OSPFV3 router-id as the network unique router ID:

**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'no router-id' command will restore the ospfv3 router-id to its default value.

- When changing the router-id, the OSPFv3 process will restart with the current configuration.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| router-id | A 32-bit number represented as a dotted quad assigned to each router running the | A.B.C.D | \-      |
|           | OSPFv2 protocol. This number should be unique within the autonomous system. the  |         |         |
|           | default value should be the highest IP address on the lowest routers Loopback    |         |         |
|           | Interfaces. If there is no Loopback Interfaces configured, then highest IP       |         |         |
|           | address on its active interfaces                                                 |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# router-id 100.70.1.45


**Removing Configuration**

To restore the ospfv3 router-id to its default value:
::

    no router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
```

# LDP

## administrative-distance
```rst
protocols ldp administrative-distance
-------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.

To configure the administrative-distance for LDP:

**Command syntax: administrative-distance [admin-distance]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- When reconfiguring the administrative-distance, run clear ldp neighbor.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| admin-distance | Sets the administrative distance for LDP. A value of 255 will cause the router   | 1-255 | 105     |
|                | to remove the route from the forwarding table.                                   |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# administrative-distance 130


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ldp)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
protocols ldp admin-state
-------------------------

**Minimum user role:** operator

Setting the LDP protocol to disable mode. LDP will not send or receive LDP packets.

To set the LDP protocol to disable mode:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Parameter table**

+-------------+------------------------------------+--------------+---------+
| Parameter   | Description                        | Range        | Default |
+=============+====================================+==============+=========+
| admin-state | Administratively set the LDP state | | enabled    | enabled |
|             |                                    | | disabled   |         |
+-------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-ldp)# no admin-state disabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## authentication
```rst
protocols ldp authentication password
-------------------------------------

**Minimum user role:** operator

To set the MD5 authentication password for all LDP neighbors.
Changing the authentication configuration will cause all LDP sessions to restart unless they have a per-neighbor authentication configuration, which will override this setting.

**Command syntax: authentication [type] password [enc-password]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- If a password is not provided with the command, you will be prompted to enter a clear-text password. The clear-text password is 1-80 charachters long.

- When authentication password is specified authentication is set on TCP sessions by default.

- When typing a clear text password, the password and retyping won't be displayed in the CLI terminal

- Clear text password length is 1-80 charachters

- enc-password must be a valid dnRouter encrypted password

- changing authentication configuration will cause all LDP sessions to restart unless they have an overriding per neighbor configuration for authentication

- password is saved encrypted, and always displayed as secret

- The 'no authentication' command disables authentication as default configuration. This results in restarting LDP neighbor sessions, for which there is no override authentication configuration.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter    | Description                                                                      | Range | Default |
+==============+==================================================================================+=======+=========+
| type         | authentication type                                                              | md5   | \-      |
+--------------+----------------------------------------------------------------------------------+-------+---------+
| enc-password | set a default password for authentication encrypted secret password string for   | \-    | \-      |
|              | the LDP neighbor. if the user enters a clear-text password, the password is then |       |         |
|              | encrypted by the system and saved in secret argument. if user specified 'secret' |       |         |
|              | save string in secret                                                            |       |         |
+--------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# authentication md5 password
    Enter password:
    Enter password for verification:

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# authentication md5 password enc-!344fGVkX1+


**Removing Configuration**

To disable the authentication:
::

    dnRouter(cfg-protocols-ldp)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
```

## class-of-service
```rst
protocols ldp class-of-service
------------------------------

**Minimum user role:** operator

To set the DSCP value for outgoing LDP packets:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- IPP is set accordingly, i.e. a DSCP value of 48 is mapped to 6.

**Parameter table**

+------------------+------------------------------------------+-------+---------+
| Parameter        | Description                              | Range | Default |
+==================+==========================================+=======+=========+
| class-of-service | LDP UDP and TCP packets class of service | 0-56  | 48      |
+------------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# class-of-service 50


**Removing Configuration**

To revert the dscp-value to the default value:
::

    dnRouter(cfg-protocols-ldp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
```

## ldp overview
```rst
Label Distribution Protocol (LDP) Overview
------------------------------------------
Label Distribution Protocol (LDP) enables peer label switch routers (LSRs) to exchange label information for supporting hop-by-hop forwarding in a Multi-Protocol Label Switching (MPLS) network.

With IP forwarding, when a packet arrives at a router, the router looks at the destination address in the IP header, performs a route lookup, and forwards the packet to the next hop. With MPLS forwarding, when a packet arrives at a router, the router looks at the incoming label, looks up the label in a table, and forwards the packet to the next hop.

Each router has a unique LSR ID. When you enable LDP, LSRs send out discovery messages ("Hello" messages) to announce their presence in the network. The discovery messages are transmitted periodically as multicast UDP packets to all directly connected routers on the subnet. If a neighbor LSR responds to the message, the two routers can establish an LDP session. Within the "hello" packet, the router advertises its LSR ID and also a transport IP address, which is used to build the TCP connection with the neighbor LSR. The LSRs can then exchange label information.

DNOS supports downstream-unsolicited label distribution method with ordered label control and liberal label retention.

**Downstream-unsolicited** means that as soon as the LSR learns a route, it sends a FEC-to-label binding for that route to all peer LSRs, both upstream and downstream and does not wait for a request from an upstream device.

**Ordered** label control means that an LSR does not advertise a label for a FEC unless it is the egress LSR for the FEC (i.e. when the FEC is its directly attached interface or when MPLS is not configured on the next-hop interface) or until it has received a label for the FEC from its downstream peer. This prevents early data mapping from occurring on the first LSR in the path.

**Liberal** label retention means that any label mapping that may ever be used as a next hop is retained. Should a topology change occur, the labels to use in the new topology are already in place.

The mappings distributed by the LDP protocol are used to build a Label Information Base (LIB) - a data structure representing the mapping of each prefix to a label for each neighboring LDP peer. The LIBs are then used to construct the Label Forwarding Information Base (LFIB), which is the actual table used by the data path to take the forwarding decision.

The MPLS LDP-IGP synchronization feature provides a means to synchronize LDP and IGPs to minimize MPLS packet loss. When an IGP adjacency is established on a link but LDP IGP synchronization is not yet achieved or is lost, the IGP advertises the max-metric on that link. LDP-sync is always enabled in LDP. Also, all OSPF interfaces (except loopbacks) are enabled for LDP sync. See Configuring LDP Sync.```

## ldp
```rst
protocols ldp
-------------

**Minimum user role:** operator

To start the process, enter LDP configuration hierarchy using the following command:

**Command syntax: ldp**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- You can only configure LDP for the default VRF.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)#


**Removing Configuration**

To remove the LDP protocol configuration:
::

    dnRouter(cfg-protocols)# no protocols ldp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## ldp-sync on-session-delay
```rst
protocols ldp ldp-sync on-session-delay
---------------------------------------

**Minimum user role:** operator

The MPLS LDP-IGP synchronization feature provides a means to synchronize LDP and IGPs to minimize MPLS packet loss.
When an IGP adjacency is established on a link but LDP IGP synchronization is not yet achieved or is lost, the IGP advertises the max-metric on that link. 
LDP-sync is always enabled in LDP. Also, all OSPF interfaces (except loopbacks) are enabled for LDP sync.

To configure LDP-IGP synchronization:

**Command syntax: ldp-sync on-session-delay [on-session-delay]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- LDP sync is always enabled in LDP either with no delay or with configured delay.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                      | Range | Default |
+==================+==================================================================================+=======+=========+
| on-session-delay | The amount of time to wait (in seconds) before notifying if the LDP interface is | 5-300 | 15      |
|                  | synchronized                                                                     |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# ldp-sync on-session-delay 50


**Removing Configuration**

To revert the delay configuraiton to default:
::

    dnRouter(cfg-protocols-ldp)# no ldp-sync on-session-delay

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 6.0     | Command introduced                                |
+---------+---------------------------------------------------+
| 13.0    | Command syntax changed from on-proc to on-session |
+---------+---------------------------------------------------+
```

## nsr
```rst
protocols ldp nsr
-----------------

**Minimum user role:** operator

LDP nonstop routing (NSR) enables an LDP speaker to maintain the LDP session's state while undergoing switchover at the CPU level (e.g. NCC switchover).
Unlike LDP graceful-restart (GR), which requires both LDP ends to support the GR capability and logic, NSR is transparent, and the other end of the LDP session is unaware of the NSR process.

While LDP works with NSR, LDP continue to support as a helper for neighbor GR.

The LDP process (ldpd) running on the active NCC, saves (in the NSR DB) all the information required for recovering from an LDP failure and for providing nonstop routing (including LDP TCP session information and any advertised and received prefix<->label).
The NSR DBs, located on both active and standby NCCs, are regularly synchronized. In the event of a switchover/failover, ldpd starts on the standby NCC and recovers the TCP and LDP session parameters from the NSR-DB in the standby NCC.

To enable/disable the LDP NSR feature:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- LDP NSR cannot be enabled together with LDP Graceful-Restart.

**Parameter table**

+-----------+-----------------------------------------+--------------+---------+
| Parameter | Description                             | Range        | Default |
+===========+=========================================+==============+=========+
| nsr       | The admin-state of LDP non-stop-routing | | enabled    | enabled |
|           |                                         | | disabled   |         |
+-----------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# nsr enabled

    dnRouter(cfg-protocols-ldp)# nsr disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ldp)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## rcv-addr-withdraw-delay
```rst
protocols ldp rcv-addr-withdraw-delay
-------------------------------------

**Minimum user role:** operator

Use this command to delay the LDP reaction for an address-withdraw message received from a neighbor. 
Multiple address-withdraw messages, that are received during the delay period, will be treated together as soon as the delay timer expires.

**Command syntax: rcv-addr-withdraw-delay [delay]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- A value of 0 means there is no delay and LDP will react immediately to any received address-withdraw.

**Parameter table**

+-----------+-------------------------------+-------+---------+
| Parameter | Description                   | Range | Default |
+===========+===============================+=======+=========+
| delay     | The delay period (in seconds) | 0-120 | 0       |
+-----------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# rcv-addr-withdraw-delay 10


**Removing Configuration**

To return the delay timer to the default value:
::

    dnRouter(cfg-protocols-ldp)# no rcv-addr-withdraw-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## router-id
```rst
protocols ldp router-id
-----------------------

**Minimum user role:** operator

To configure the LDP router ID:

**Command syntax: router-id [ipv4-address]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- To configure LDP a router-id must be configured. If one is not configured, the default router-id is the router-options router-id. If the router-options router-id is not configured, the highest IPv4 address of any loopback interface will be used.

**Parameter table**

+--------------+--------------------------------------------+---------+---------+
| Parameter    | Description                                | Range   | Default |
+==============+============================================+=========+=========+
| ipv4-address | The network ipv4 address of the LDP router | A.B.C.D | \-      |
+--------------+--------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# router-id 100.70.1.45


**Removing Configuration**

To remove configuration:
::

    dnRouter(cfg-protocols-ldp)# no router-id

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 6.0     | Command introduced                                    |
+---------+-------------------------------------------------------+
| 13.0    | Command syntax changed from router-id to ipv4-address |
+---------+-------------------------------------------------------+
```

# MPLS

## mpls overview
```rst
Multiprotocol Label Switching (MPLS) Overview
---------------------------------------------
MPLS is a packet-forwarding technology that uses labels in order to make data forwarding decisions. With MPLS, the Layer 3 header analysis is done just once, when the packet enters the MPLS domain. Subsequent packet forwarding is done by inspecting the label, without examining the packet.

These labels describe how to forward an incoming packet on an MPLS-enabled router. MPLS-labeled packets are switched to a destination via a specific path rather than being routed to a destination based on the routing table.
```

## mpls
```rst
protocols mpls
--------------

**Minimum user role:** operator

To configure MPLS, enter MPLS configuration mode:

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)#


**Removing Configuration**

To remove the MPLS protocol configuration:
::

    dnRouter(cfg-protocols)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## ttl-propagate
```rst
protocols mpls ttl-propagate
----------------------------

**Minimum user role:** operator

MPLS TTL propagation allows disabling the default TTL propagation in the IP-MPLS architecture. 
When the admin-state is enabled (default), TTL propagation works in uniform mode. Ingress LSR copies the IP TTL to the MPLS header and decrements it by 1. Each transit LSR performing a swap operation decrements the MPLS TTL value in the MPLS header of the packet by 1. MPLS to IP behavior depends on TTL propagation mode and performed operation. When the IP header value reaches 0, the packet is dropped. When the admin-state is disabled, then TTL propagation works in pipe mode, ingress LSR sets the MPLS TTL to 255, and each transit LSR performing a swap operation decrements the MPLS TTL value by 1. MPLS to IP behavior depends on TTL propagation mode and operation performed.
By default, IP MPLS TTL propagation is enabled. To disable it, use the following command in MPLS configuration mode:

**Command syntax: ttl-propagate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls

**Parameter table**

+-------------+------------------------------------------------------+----------------------------+-----------------------+
| Parameter   | Description                                          | Range                      | Default               |
+=============+======================================================+============================+=======================+
| admin-state | Sets the administrative state of the TTL propagation | | consts.OPTION_ENABLED    | consts.OPTION_ENABLED |
|             |                                                      | | consts.OPTION_DISABLED   |                       |
+-------------+------------------------------------------------------+----------------------------+-----------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# ttl-propagate enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# ttl-propagate disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-mpls)# no ttl-propagate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

# LACP

## lacp overview
```rst
Link Aggregation Control Protocol (LACP) Overview
-------------------------------------------------

The Link Aggregation Control Protocol (LACP) is used for dynamically exchanging information between two bundle partner systems to automatically maintain the links within the bundle. A partner actively sends out a LACP protocol data unit (PDU) to a remote partner containing information about its state, its ports and links, and any information it knows about the remote partner.

A partner can either be an active or passive participant in LACP. An active partner periodically initiates LACPDUs to its remote partner. A passive partner only responds to LACPDUs.

**Note**
-	The ports at both ends must be of the same speed and duplex.

The LACP feature provides a mechanism for automatic link failover within the bundle interface.

**LACP Configuration**

LACP exchanges are made between actors (the transmitting link) and partners (the receiving link). The LACP mode can be either active or passive.

To configure LACP on a predefined bundle interface with associated physical interfaces (ports):

 1. Enter LACP mode. See protocols lacp.

 2. Configure the LACP system identifier. The system identifier is the concatenation of the system priority value and the system ID value.
    a. Configure the system priority. See lacp system-priority.
    b. Configure the system ID. See lacp system-id.
 3. Configure the LACP parameters, using the following general command:

**Example**

::

    dnRouter(cfg-protocols)# lacp interface [interface-name] parameter [parameter-value]


**The parameters are:**

+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Parameter      | Description                                                                                              | Reference             |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Interface-name | The name of the interface on which to configure LACP.                                                    | -                     |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Mode           | The mode for exchanging LACP packets between interfaces.                                                 | lacp interface mode   |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Period         | The frequency of sending LACPDUs.                                                                        | lacp interface period |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Min-links      | The minimum number of interface members that must be active for the aggregate interface to be available. | interfaces min-links  |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+

 4. Configure the bundle's members' port priority. See interfaces port-priority.
```

## lacp
```rst
protocols lacp
--------------

**Minimum user role:** operator

To start the LACP process:

**Command syntax: lacp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)#


**Removing Configuration**

To remove the lacp protocol:
::

    dnRouter(cfg-protocols)# no lacp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## system-id
```rst
protocols lacp system-id
------------------------

**Minimum user role:** operator

The LACP system ID is formed by combining the LACP system-priority with the system's ID. The system ID is the least significant part of the LACP system unique identifier, in the form of a MAC address. The system MAC address is randomly selected from a pool of addresses, whose first 3 bytes have a fixed value (84:40:76) and last 3 bytes are randomized on first start-up. The ID assignment is performed once after deployment and persists after reset. You can optionally change the system-id.
To change the LACP system ID:

**Command syntax: system-id [system-id]**

**Command mode:** config

**Hierarchies**

- protocols lacp

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| system-id | The MAC address portion of the node's System ID. This is combined with the       | \-    | \-      |
|           | system priority to construct the 8-octet system-id                               |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# system-id 11:22:33:44:55:66


**Removing Configuration**

To revert to the default system-id:
::

    dnRouter(cfg-protocols-lacp)# no system-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## system-priority
```rst
protocols lacp system-priority
------------------------------

**Minimum user role:** operator

The significant Part of LACP system identifier (2 bytes), Priority for the system.
A lower value is higher priority.

The actor with the higher priority is the master after negotiation with other systems.

**Command syntax: system-priority [system-priority]**

**Command mode:** config

**Hierarchies**

- protocols lacp

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| system-priority | Sytem priority used by the node on this LAG interface. Lower value is higher     | 0-65535 | 1       |
|                 | priority for determining which node is the controlling system.                   |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# system-priority 10


**Removing Configuration**

To revert the priority to the default value:
::

    dnRouter(cfg-protocols-lacp)# no system-priority

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 6.0     | Command introduced       |
+---------+--------------------------+
| 9.0     | Updated priority default |
+---------+--------------------------+
```

# LLDP

## admin-state
```rst
protocols lldp admin-state
--------------------------

**Minimum user role:** operator

To enable LLDP admin-state (LLDP admin-state is disabled by default):

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Parameter table**

+-------------+-----------------------------------------+--------------+---------+
| Parameter   | Description                             | Range        | Default |
+=============+=========================================+==============+=========+
| admin-state | System level state of the LLDP protocol | | enabled    | enabled |
|             |                                         | | disabled   |         |
+-------------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# admin-state enabled


**Removing Configuration**

To return LLDP admin-state to its default value:
::

    dnRouter(cfg-protocols-lldp)# no admin-state

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 7.0     | Command introduced                                         |
+---------+------------------------------------------------------------+
| 9.0     | Not supported in this version                              |
+---------+------------------------------------------------------------+
| 10.0    | Command reintroduced with admin-state "enabled" by default |
+---------+------------------------------------------------------------+
| 16.1    | Updated command with admin-state "disabled" by default     |
+---------+------------------------------------------------------------+
```

## chassis-id-mac-address
```rst
protocols lldp chassis-id-mac-address
-------------------------------------

**Minimum user role:** operator

Configure lldp mandatory Chassis ID tlv information. 
When advertising Chassis ID with type mac-address (default system behavior), this configuration defines which system mac address is to be advertised
* system-id - (default behavior) Signal the system-id mac address. A locally randomized mac address from DRIVENETS MAC pool, unique per router deployment
* chassis-mac - Advertise the router platform base mac address as chassis-id. Option is valid for Stand-Alone systems only.

**Command syntax: chassis-id-mac-address [chassis-id-mac-address]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+-----------------+-----------+
| Parameter              | Description                                                                      | Range           | Default   |
+========================+==================================================================================+=================+===========+
| chassis-id-mac-address | The Chassis ID is a mandatory TLV which identifies the chassis component of the  | | system-id     | system-id |
|                        | endpoint identifier associated with the transmitting LLDP agent.                 | | chassis-mac   |           |
|                        | chassis-id-mac-address defines which system mac is to be advertised when chassis |                 |           |
|                        | id type is mac-address                                                           |                 |           |
+------------------------+----------------------------------------------------------------------------------+-----------------+-----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# chassis-id-mac-address chassis-mac

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# chassis-id-mac-address system-d


**Removing Configuration**

To return chassis-id-mac-address to default value:
::

    dnRouter(cfg-protocols-lldp)# no chassis-id-mac-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## lldp overview
```rst
Link Layer Discovery Protocol (LLDP) Overview
---------------------------------------------

LLDP is a neighbor discovery protocol that is used for network devices to advertise information about themselves to other devices on the network and learn about each other. The information gathered with LLDP is stored in the device and can be queried. The topology of an LLDP-enabled network can be discovered by crawling the hosts and querying this database.

The information that can be retrieved include:

- System name and description
- Port name and description
- IP management address
- System capabilities (switching, routing, etc.)

LLDP information is sent by the devices from each of their interfaces at fixed interval in the form of an Ethernet frame. Each frame contains one LLDP data unit (LLDPDU), which is a sequence of type, length, and value (TLV) attributes carrying configuration information, device capabilities, and device identity.

For transmitted LLDPDU, the interfaces from which LLDP information is collected are:

- Physical interfaces with admin-state "enabled"
- Interfaces with LLDP admin-state "enabled"
- LLDP Tx per interface is "enabled"

For received LLDPDU, the interfaces from which LLDP information is collected are:

- Physical interfaces with admin-state "enabled"
- Interfaces with LLDP admin-state "enabled"
- LLDP Rx per interface is "enabled"

Tx and Rx states per interface are independent. Each interface can send without receiving or receive without sending LLDPDUs.

The Ethernet frame used in LLDP includes:

- The destination MAC address - typically set to a special multicast address that 802.1D -compliant bridges do not forward
- The EtherType field set to 0x88cc
- Mandatory TLV attributes:

   - Chassis ID
   - Port ID
   - Time to Live

- Optional TLV attributes
- End of LLDPDU TLV - with type and length fields set to 0

+-------------------------------------------------+-------------------+-----------+----------------+-------------+------------------+---------------+----------------------+
| Destination MAC                                 | Source MAC        | EtherType | Chassis ID TLV | Port ID TLV | Time to live TLV | Optional TLVs | End of LLDPDU TLV    |
+-------------------------------------------------+-------------------+-----------+----------------+-------------+------------------+---------------+----------------------+
| 01:80:c2:00:00:0e (we send) or (can receive)    | Station's address | 0x88cc    | Type = 1       | Type = 2    | Type = 3         | Zero or more  | Type = 0. Length = 0 |
| 01:80:c2:00:00:03 or 01:80:c2:00:00:00          |                   |           |                |             |                  | complete TLVs |                      |
+-------------------------------------------------+-------------------+-----------+----------------+-------------+------------------+---------------+----------------------+

Each TLV component has the following basic structure:

+--------+--------+--------------+
| Type   | Length | Value        |
+--------+--------+--------------+
| 7 bits | 9 bits | 0-511 octets |
+--------+--------+--------------+

DNOS supports the following TLVs:

+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| TLV Type | TLV Name            | Values and Origin                                                                                   | YANG Path                                                                        |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 1        | Chassis ID          | Chassis ID Subtype: MAC address (val = 4)                                                           | Chassis_id: dn-top:drivenets-top/dn-proto:protocols/                             |
|          |                     | Chassis ID: Station's_MAC_address (MAC Address pattern)                                             | dn-lacp:lacp/dn-lacp:config-items/dn-lacp-private:actual-system-id               |
|          |                     | This value is identical for all interfaces in the cluster and is                                    |                                                                                  |
|          |                     | taken from the system-id defined in LAG control - LACP (in the private yang)                        |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 2        | Port ID             | Port ID Subtype: Interface name (val = 5)                                                           | Interface_name: dn-if:interfaces/dn-if:interface*/dn-if:oper-items/dn-if:name    |
|          |                     | Port ID: Interface_name (string)                                                                    |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 3        | Time To Live        | Seconds: hold_time (uint_16)                                                                        | Hold_time: dn-top:drivenets-top/dn-proto:protocols/dn-lldp:lldp/dn-lldp:         |
|          |                     |                                                                                                     | oper-items/dn-lldp:timers/dn-lldp:hold-time                                      |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 4        | Port description    | Port Description: Interface_description (string) If value not configured,                           | Interface_description: dn-top:drivenets-top/dn-if:interfaces/dn-if:              |
|          |                     | this TLV type not sent                                                                              | interface*/dn-if:oper-items/dn-if:description                                    |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 5        | System name         | System Name: System_name (string)                                                                   | System_name: dn-top: drivenets-top/dn-sys:system/dn-sys:oper-items/dn-sys:name   |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 6        | System description  | System Description: DRIVENETS                                                                       | System_description: dn-top:drivenets-top/dn-sys:system/dn-sys:oper-items/dn-sys: |
|          |                     | LTD. System_description, DNOS_version (string) Concatenated string of fixed                         | system-info/dn-sys:description                                                   |
|          |                     | and configurable values                                                                             |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 7        | System capabilities | Capabilities:                                                                                       | dn-top:drivenets-top/dn-proto:protocols/dn-lldp:lldp/dn-lldp:oper-items/dn-      |
|          |                     |                                                                                                     |                                                                                  |
|          |                     |     - Other: Not capable (0)                                                                        | lldp:capabilities/dn-lldp:capability*                                            |
|          |                     |     - Repeater: Not capable (0)                                                                     |                                                                                  |
|          |                     |     - Bridge: Capable (1)                                                                           |                                                                                  |
|          |                     |     - WLAN access point: Not capable (0)                                                            |                                                                                  |
|          |                     |     - Router: Capable (1)                                                                           |                                                                                  |
|          |                     |     - Telephone: Not capable (0)                                                                    |                                                                                  |
|          |                     |     - DOCSIS cable device: Not capable (0)                                                          |                                                                                  |
|          |                     |     - Station only: Not capable (0)                                                                 |                                                                                  |
|          |                     |                                                                                                     |                                                                                  |
|          |                     |  Enabled Capabilities:                                                                              |                                                                                  |
|          |                     |     - Other: Not capable (0)                                                                        |                                                                                  |
|          |                     |     - Repeater: Not capable (0)                                                                     |                                                                                  |
|          |                     |     - Bridge: Capable (1)                                                                           |                                                                                  |
|          |                     |     - WLAN access point: Not capable (0)                                                            |                                                                                  |
|          |                     |     - Router: Capable (1)                                                                           |                                                                                  |
|          |                     |     - Telephone: Not capable (0)                                                                    |                                                                                  |
|          |                     |     - DOCSIS cable device: Not capable (0)                                                          |                                                                                  |
|          |                     |     - Station only: Not capable (0)                                                                 |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 8        | Management address  |     - Address String Length: len(Address Subtype) + len(Management Address)                         | Inband-management source-interface: dn-top:drivenets-top/dn-sys:system/dn-sys:   |
|          |                     |     - Address Subtype: IPv4 (1) / IPv6 (2)                                                          | oper-items/dn-sys:inband-management/dn-sys:source-interface                      |
|          |                     |     - Management Address: ipv4_address / ipv6_address                                               |                                                                                  |
|          |                     |     - Interface Subtype: ifIndex (2)                                                                | IPv4 Management Address: dn-top:drivenets-top/dn-if:interfaces/dn-if:            |
|          |                     |     - Interface Number: ifindex                                                                     | interface*/dn-ip:ipv4/dn-ip:addresses/dn-ip:address*/dn-ip:oper-items/dn-ip:ip   |
|          |                     |     - OID String Length: 0                                                                          |                                                                                  |
|          |                     |                                                                                                     |                                                                                  |   
|          |                     |      By default for DP interfaces, the management address will be taken                             | IPv6 Management Address: dn-top:drivenets-top/dn-if:interfaces/dn-if:            |
|          |                     |      from the in-band-management source-interface configuration to be advertised.                   | interface*/dn-ip:ipv6/dn-ip:addresses/dn-ip:address*/dn-ip:oper-items/dn-ip:ip   |
|          |                     |      By default for mgmt interfaces, the management address will be taken from the                  |                                                                                  |
|          |                     |      configured interface address.                                                                  | Interface_ifindex: dn-top:drivenets-top/dn-if:interfaces/dn-if:interface*/dn-    |
|          |                     |      If there is no any address configuration, this TLV type will be sent with                      | if:oper-items/dn-if:if-index                                                     |
|          |                     |      the following values:                                                                          |                                                                                  |
|          |                     |      - Address String Length: len(Address Subtype) + len(Management Address)                        | Station's_MAC_address: dn-top:drivenets-top/dn-if:interfaces/dn-if:interface*/dn-|
|          |                     |      - Address Subtype: 802 (includes all 802 media plus Ethernet "canonical format") (value - 6)   | eth:ethernet/dn-eth:oper-items/dn-eth:mac-address                                |
|          |                     |      - Management Address: Station's_MAC_address (MAC Address pattern)                              |                                                                                  |
|          |                     |      - Interface Subtype: ifIndex (2)                                                               |                                                                                  |
|          |                     |      - Interface Number: ifindex                                                                    |                                                                                  |
|          |                     |      - OID String Length: 0                                                                         |                                                                                  |
|          |                     |                                                                                                     |                                                                                  |   
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 0        | End of LLDPDU       | 0x0000                                                                                              | N/A                                                                              |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+




The parsing of the TLV is handled separately for each received LLDP packet.

- TLV types that are not supported, are discarded. They are counted as unrecognized TLVs.
- Supported TLV types that are malformed are discarded. They are counted as discarded TLVs.
- When duplicate TLV types are received in the same packet, the last received TLV overrides any previous TLV.

Each Network Cloud node (NCP, NCF, NCC) includes a container with the node_manager process running the LLDP protocol on that node. This process is responsible for sending and receiving LLDP TLVs per node interface:

**NCP:**

- Data Path interfaces (UNI/NNI) - geX-Y.Z.W
- Management interfaces for OOB - mgmt-ncc/0/0 mgmt-ncp/x/y
- Control interfaces for cluster connectivity- ctrl-ncp/x/y

**NCF:**

- Management interfaces for OOB - mgmt-ncf/x/y
- Control interfaces for cluster connectivity- ctrl-ncf/x/y

**NCC:**

- Management interfaces for OOB - mgmt-ncc/x/y
- Control interfaces for cluster connectivity- ctrl-ncc/x/y

All gathered LLDP information is sent to the NCC (Centralized functionality). All LLDP configuration is maintained in the NCC, which distributes it to all cluster nodes.

To manage the internal cluster link detection before container deployment, the host OS contains an LLDP process (lldpd-os) only for the internal management interfaces:

**NCP:**

- Management interfaces for OOB - mgmt-ncp/x/y
- Control interfaces for cluster connectivity- ctrl-ncp/x/y

**NCF:**

- Management interfaces for OOB - mgmt-ncf/x/y
- Control interfaces for cluster connectivity- ctrl-ncf/x/y

**NCC:**

- Management interfaces for OOB - mgmt-ncc/x/y
- Control interfaces for cluster connectivity- ctrl-ncc/x/y

The lldpd-os process performs "hand-out" to the custom node_manager process when deployed.

The collected LLDP information is stored in the database in case of NCC switchover or reset. Due to performance considerations, up to 10 simultaneous active neighbors are supported per LLDP interface.

**LLDP Configuration**


To configure LLDP follow these general steps:

1. Enter LLDP configuration mode. See protocols lldp.
2. Enable/Disable LLDP globally. See lldp admin-state.
3. Enable/Disable LLDP on an interface. See lldp interface.
4. Configure LLDP timers. See lldp timers.
```

## lldp
```rst
protocols lldp
--------------

**Minimum user role:** operator

To enter LLDP configuration mode:"

**Command syntax: lldp**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The lldp protocol is applicable for default vrf only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)#


**Removing Configuration**

To remove the LLDP protocol
::

    dnRouter(cfg-protocols)# no lldp

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Command reintroduced          |
+---------+-------------------------------+
```

## management source-interface
```rst
protocols lldp management source-interface
------------------------------------------

**Minimum user role:** operator


To configure the source interface from which the management address will be taken for lldp management tlv advertisements:

**Command syntax: management source-interface [management source-address]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Note**

- The source-interface can belong to any vrf in the system

- In case source-interface has no ip address, or in state down, lldp will fallback to advertise mac address of the provided interface.'

**Parameter table**

+---------------------------+--------------------------------------------------------------------------------+------------------+---------+
| Parameter                 | Description                                                                    | Range            | Default |
+===========================+================================================================================+==================+=========+
| management source-address | source interface for management address to be advertised under management tlv. | | string         | \-      |
|                           |                                                                                | | length 1-255   |         |
+---------------------------+--------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# management-source-interface bundle-1.127

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# management-source-interface irb5


**Removing Configuration**

To revert to default management address behavior:
::

    dnRouter(cfg-protocols-lldp-if)# no management-source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## tlv-filter
```rst
protocols lldp tlv-filter
-------------------------

**Minimum user role:** operator

This command allows LLDP to disable non-mandatory TLV messages so that sensitive information about a network is not disclosed. To filter optional LLDP TLVs to be sent to peers:

**Command syntax: tlv-filter [optional-TLV-name]** [, optional-TLV-name, optional-TLV-name]

**Command mode:** config

**Hierarchies**

- protocols lldp

**Note**

- Multiple TLVs can be specified at once (separated by commas).

**Parameter table**

+-------------------+------------------------------------------------+-------------------------+---------+
| Parameter         | Description                                    | Range                   | Default |
+===================+================================================+=========================+=========+
| optional-TLV-name | Filter optional LLDP TLVs to be sent to peers. | | management-address    | \-      |
|                   |                                                | | port-description      |         |
|                   |                                                | | system-capabilities   |         |
|                   |                                                | | system-description    |         |
|                   |                                                | | system-name           |         |
+-------------------+------------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# tlv-filter management-address

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# tlv-filter management-address, system-capabilities


**Removing Configuration**

To remove specific optional TLVs from the LLDP TLV filter:
::

    dnRouter(cfg-protocols-lldp)# no tlv-filter management-address

::

    dnRouter(cfg-protocols-lldp)# no tlv-filter management-address, system-description

To remove the entire LLDP TLV filter:
::

    dnRouter(cfg-protocols-lldp)# no tlv-filter

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

# BFD

## bfd
```rst
protocols bfd
-------------

**Minimum user role:** operator

To start the BFD process and enter BFD configuration mode:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The BFD protocol is only relevant for default vrf

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bfd
    dnRouter(cfg-protocols-bfd)#


**Removing Configuration**

To disable the BFD protocol:
::

    dnRouter(cfg-protocols)# no bfd

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 9.0     | Command removed      |
+---------+----------------------+
| 11.2    | Command reintroduced |
+---------+----------------------+
```

## class-of-service
```rst
protocols bfd class-of-service
------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different 
traffic so that when congestion occurs, you can control which packets receive priority.

To configure the DSCP value for all locally generated BFD packets:

**Command syntax: class-of-service [dscp]**

**Command mode:** config

**Hierarchies**

- protocols bfd

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| dscp      | The DSCP value that is used in the BFD packet to classify it and give it a       | 0-63  | 48      |
|           | priority.                                                                        |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bfd
    dnRouter(cfg-protocols-bfd)# class-of-service 16


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bfd)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## maximum-sessions
```rst
protocols bfd maximum-sessions threshold
----------------------------------------

**Minimum user role:** operator

You can control the number of concurrent BFD sessions by setting thresholds to generate system event notifications. 
Only established sessions are counted. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. 
Micro-BFD sessions are excluded from this count. System supports micro-BFD sessions on every system port.
Once the threshold is crossed, a warning system-event will be sent (every 30 seconds).

To configure thresholds for BFD sessions:

**Command syntax: maximum-sessions [max-sessions] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols bfd

**Parameter table**

+--------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter    | Description                                                                      | Range   | Default |
+==============+==================================================================================+=========+=========+
| max-sessions | The maximum number of concurrent BFD sessions. When the maximum number of        | 0-65535 | 2000    |
|              | sessions threshold is crossed, a system-event notification is generated every 30 |         |         |
|              | seconds.                                                                         |         |         |
|              | A value of 0 means no limit.                                                     |         |         |
+--------------+----------------------------------------------------------------------------------+---------+---------+
| threshold    | A percentage (%) of max-sessions to give you advance notice that the number of   | 1-100   | 75      |
|              | BFD sessions is reaching the maximum level.                                      |         |         |
|              | When this threshold is crossed, a system event notification is generated.        |         |         |
+--------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bfd
    dnRouter(cfg-protocols-bfd)# maximum-sessions 500 threshold 75

    In the above example, the maximum number of sessions is set to 500 and the threshold is set to 75%.
 This means that when the number of sessions reaches 375 (500x75%), a system-event notification will be generated that the 75% threshold has been crossed.
 If you do nothing, you will not receive another notification until the number of sessions reaches 500. At this point, a system-event notification will start to be generated every 30 seconds.

**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bfd)# no maximum-sessions

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 11.2    | Command introduced                      |
+---------+-----------------------------------------+
| 15.1    | Added support for 2000 maximum sessions |
+---------+-----------------------------------------+
```

# RSVP

## admin-group exclude-all
```rst
protocols rsvp admin-group exclude-all
--------------------------------------

**Minimum user role:** operator

After configuring the administrative group, you can either exclude, include, or ignore links of that color in the traffic engineering database:

- If you exclude a specific color, all segments with an administrative group of that color are excluded from CSPF path selection.

- If you include a specific color, only those segments with the appropriate color are selected.

- If you neither exclude nor include the color, the metrics associated with the administrative groups and applied on the specific segments determine the path cost for that segment.

The LSP with the lowest total path cost is selected into the traffic engineering database. To define global link exclude admin-group attributes for all tunnels:

**Command syntax: admin-group exclude-all**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- You cannot set the same admin-group-name in both an exclude and include constraint.

- The tunnel admin-group exclude configuration overrides the global setting.

.. -  default system behavior is to ignore admin-groups constraints in path calculation

.. -  can either set exclude or exclude-all

.. -  cannot be set together with admin-group include

.. -  'no admin-group exclude [admin-group-name]'' - remove the specified admin-group from the admin-groups list

.. -  'no admin-group exclude', 'no admin-group exclude-all' - remove all admin-groups from the admin-groups list

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group exclude-any RED, GREEN

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group exclude-all


**Removing Configuration**

To remove a specific admin-group-name from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group exclude RED

To remove all admin-groups from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group exclude-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## admin-group exclude
```rst
protocols rsvp admin-group
--------------------------

**Minimum user role:** operator

After configuring the administrative group, you can either exclude, include, or ignore links of that color in the traffic engineering database:

- If you exclude a specific color, all segments with an administrative group of that color are excluded from CSPF path selection.

- If you include a specific color, only those segments with the appropriate color are selected.

- If you neither exclude nor include the color, the metrics associated with the administrative groups and applied on the specific segments determine the path cost for that segment.

The LSP with the lowest total path cost is selected into the traffic engineering database. To define global link exclude admin-group attributes for all tunnels:

**Command syntax: admin-group [exclude-type] [admin-group-name]** [, admin-group-name, admin-group-name]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- You cannot set the same admin-group-name in both an exclude and include constraint.

- The tunnel admin-group exclude configuration overrides the global setting.

.. -  default system behavior is to ignore admin-groups constraints in path calculation

.. -  can either set exclude or exclude-all

.. -  cannot be set together with admin-group include

.. -  'no admin-group exclude [admin-group-name]'' - remove the specified admin-group from the admin-groups list

.. -  'no admin-group exclude', 'no admin-group exclude-all' - remove all admin-groups from the admin-groups list

**Parameter table**

+------------------+------------------------------------+--------------------+---------+
| Parameter        | Description                        | Range              | Default |
+==================+====================================+====================+=========+
| exclude-type     | exclude options                    | | exclude-any      | \-      |
|                  |                                    | | exclude-strict   |         |
+------------------+------------------------------------+--------------------+---------+
| admin-group-name | Admin groups (separated by commas) | | string           | \-      |
|                  |                                    | | length 1-255     |         |
+------------------+------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group exclude-any RED, GREEN

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group exclude-all


**Removing Configuration**

To remove a specific admin-group-name from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group exclude RED

To remove all admin-groups from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group exclude-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## admin-group include
```rst
protocols rsvp admin-group
--------------------------

**Minimum user role:** operator

After configuring the administrative group, you can either exclude, include, or ignore links of that color in the traffic engineering database:

- If you exclude a specific color, all segments with an administrative group of that color are excluded from CSPF path selection.

- If you include a specific color, only those segments with the appropriate color are selected.

- If you neither exclude nor include the color, the metrics associated with the administrative groups and applied on the specific segments determine the path cost for that segment.

The LSP with the lowest total path cost is selected into the traffic engineering database. By default, admin-group constraints are ignored in path calculation.
To define global link include admin-group attributes for all tunnels:

**Command syntax: admin-group [include-type] [admin-group-name]** [, admin-group-name, admin-group-name]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- You cannot set the same admin-group-name in both an exclude and include constraint.

.. -  default system behavior is to ignore admin-groups constraints in path calculation

.. -  can either set include-all or include-any or include-strict admin-group list

.. -  cannot be set together with admin-group exclude

.. -  'no admin-group include-all [admin-group-name]', 'no admin-group include-strict [admin-group-name]' - remove the specified admin-group from the admin-groups list

.. -  'no admin-group include-any', 'no admin-group include-strict' - remove all admin-groups from the admin-groups list

**Parameter table**

+------------------+------------------------------------+--------------------+---------+
| Parameter        | Description                        | Range              | Default |
+==================+====================================+====================+=========+
| include-type     | rsvp global admin groups           | | include-all      | \-      |
|                  |                                    | | include-any      |         |
|                  |                                    | | include-strict   |         |
+------------------+------------------------------------+--------------------+---------+
| admin-group-name | Admin groups (separated by commas) | | string           | \-      |
|                  |                                    | | length 1-255     |         |
+------------------+------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group include-all RED, GREEN

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group include-strict BLUE


**Removing Configuration**

To remove a specific admin-group-name from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group include-any RED

To remove all admin-groups from the admin group list:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group include-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## administrative-distance
```rst
protocols rsvp administrative-distance
--------------------------------------

**Minimum user role:** operator

The command sets the RSVP administrative-distance. This allows you to control the way RSVP tunnels take preference over other protocols (for example, LDP) in RIB tables.
To define the RSVP administrative-distance:

**Command syntax: administrative-distance [administrative-distance]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
-  An administrative distance of 255 will cause the route to be removed from the forwarding table and will not be used.

.. -  When reconfiguring administrative-distance, user should run clear rsvp tunnel, new administrative-distance values will only apply to new rsvp tunnels installed in RIB

.. - no command return to default value

**Parameter table**

+-------------------------+----------------------------------+-------+---------+
| Parameter               | Description                      | Range | Default |
+=========================+==================================+=======+=========+
| administrative-distance | administrative distance for RSVP | 1-255 | 100     |
+-------------------------+----------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# administrative-distance 90


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## class-of-service
```rst
protocols rsvp class-of-service
-------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.
To configure a CoS for all outgoing RSVP packets:

**Command syntax: class-of-service [class-of-service-dscp]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+-----------------------+------------------------------------------+-------+---------+
| Parameter             | Description                              | Range | Default |
+=======================+==========================================+=======+=========+
| class-of-service-dscp | set dscp value for outgoing RSVP packets | 0-56  | 48      |
+-----------------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## cspf-calculation
```rst
protocols rsvp cspf-calculation
-------------------------------

**Minimum user role:** operator

RSVP uses the Constrained Shortest Path First (CSPF) algorithm to calculate traffic paths that are subject to the following constraints:

- LSP attributes - Administrative groups such as link coloring, bandwidth requirements, and EROs

- Link attributes - Colors on a particular link and available bandwidth

These constraints are maintained in the traffic engineering database. The database provides CSPF with up-to-date topology information, the current reservable bandwidth of links, and the link colors. You can configure whether or not CSPF is used for path calculation. When disabled, the tunnel path must be explicitly set in order for the tunnel to be established. When enabled, CSPF calculates the available bandwidth ratio along each valid candidate tunnel path (where a valid candidate tunnel path is an equal cost shortest path that satisfies the path constraints). The available bandwidth ratio is calculated as: available-bandwidth/max-reservable-bandwidth across all path links.  
Use the equal-cost mode to define how the available bandwidth ratio is considered for path selection:

- Least-fill - the path with the highest available-bandwidth-ratio is selected

- Most-fill - the path with the lowest available-bandwidth-ratio is selected

- Random - randomly selects a path from all valid path candidates

To enable/disable CSPF path calculation:

**Command syntax: cspf-calculation [cspf-calculation]** equal-cost [equal-cost]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
-  max-reservable-bandwidth is the configured traffic-engineering class-type 0 bandwidth for the TE interface.

.. -  'no cspf-calculation enabled equal-cost' return equal-cost to default value

.. -  'no cspf-calculation' command returns cspf-calculation & equal-cost to default values

**Parameter table**

+------------------+----------------------------------------------------------------------------------+----------------+------------+
| Parameter        | Description                                                                      | Range          | Default    |
+==================+==================================================================================+================+============+
| cspf-calculation | Globally set whether Constraint Shortest Path Forwarding is used for path        | | enabled      | enabled    |
|                  | calculation                                                                      | | disabled     |            |
+------------------+----------------------------------------------------------------------------------+----------------+------------+
| equal-cost       | choose how available-bandwidth-ratio is considered for path selection            | | least-fill   | least-fill |
|                  |                                                                                  | | most-fill    |            |
|                  |                                                                                  | | random       |            |
+------------------+----------------------------------------------------------------------------------+----------------+------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# cspf-calculation disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# cspf-calculation enabled equal-cost random


**Removing Configuration**

To revert equal-cost to default mode:
::

    dnRouter(cfg-protocols-rsvp)# no cspf-calculation enabled equal-cost

To revert cspf-calculation and equal-cost mode to their default values:
::

    dnRouter(cfg-protocols-rsvp)# no cspf-calculation

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 10.0    | Command introduced                                            |
+---------+---------------------------------------------------------------+
| 11.0    | Added "most-fill" and "random" selection of equal cost paths. |
+---------+---------------------------------------------------------------+
```

## explicit-null
```rst
protocols rsvp explicit-null
----------------------------

**Minimum user role:** operator

This command sets explicit-null behavior for the LSP. When enabled, the last LSR in the LSP will advertise label 0 to indicate to the penultimate router to push label 0 instead of popping the last label.

When disabled, the egress LSR advertises an implicit null label (label 3) to indicate to the penultimate router to remove (pop) the tunnel's label. When the packet arrives to the egress LSR, the egress LSR only needs to perform IP lookup, saving it from doing a label lookup first.
Although implicit-null is more efficient, explicit-null is useful for maintaining class of service (CoS). When a packet or Ethernet frame is encapsulated in MPLS, you can you can set the EXP bits independently, so that the LSP CoS is different than the payload CoS. In this case, if you use implicit-null, the LSP CoS will be lost when the penultimate LSR pops the label and the packet will be queued on the outgoing interface according to the CoS behavior of the underlying payload. With explicit-null, however, the MPLS header is preserved until the packet reaches the egress, preserving the LSP CoS behavior across the entire LSP.
To enable/disable explicit-null behavior for the LSP:

**Command syntax: explicit-null [explicit-null]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  default system behavior is implicit-null were penultimate-hop router removes the tunnel label

-  Changing the explicit-null admin-state will only affect new tunnels.

.. -  no command returns explicit-null to default value

**Parameter table**

+---------------+----------------------------------------+--------------+----------+
| Parameter     | Description                            | Range        | Default  |
+===============+========================================+==============+==========+
| explicit-null | Set explicit-null behavior for the LSP | | enabled    | disabled |
|               |                                        | | disabled   |          |
+---------------+----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# explicit-null enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp)# no explicit-null

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## ldp-sync
```rst
protocols rsvp ldp-sync
-----------------------

**Minimum user role:** operator

Enable ldp sync for all tunnels set with ldp-tunneling. When enabled, rsvp tunnel is excluded to be used for ldp tunneling, by either shortcut of forwarding-adjecency, if targeted LDP peer is missing.

**Command syntax: ldp-sync [ldp-sync]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+-----------+-----------------------+--------------+----------+
| Parameter | Description           | Range        | Default  |
+===========+=======================+==============+==========+
| ldp-sync  | Set shortcut ldp sync | | enabled    | disabled |
|           |                       | | disabled   |          |
+-----------+-----------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# ldp-sync enabled


**Removing Configuration**

To return the ldp-sync to the default:
::

    dnRouter(cfg-protocols-rsvp)# no ldp-sync

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
```

## maximum-head-tunnels
```rst
protocols rsvp maximum-head-tunnels
-----------------------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. To set thresholds on RSVP-TE head tunnels:

**Command syntax: maximum-head-tunnels [maximum]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  there is no limitation for how many rsvp head tunnels user can configure, or how many rsvp head tunnel can be created

- The thresholds are for generating system-events only. They do not affect in any way the number of installed tunnels.

- The thresholds apply to all tunnel types (primary, bypass, auto-bypass, auto-mesh).

**Parameter table**

+-----------+----------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                | Range   | Default |
+===========+============================================================================+=========+=========+
| maximum   | maximum rsvp-te head tunnel limit, exceeding the limit will invoke warning | 1-29999 | 500     |
+-----------+----------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# maximum-head-tunnels 150


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no maximum-head-tunnels

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.2    | Command introduced                |
+---------+-----------------------------------+
| 15.0    | Updated max-tunnels default value |
+---------+-----------------------------------+
```

## maximum-tunnels
```rst
protocols rsvp maximum-tunnels threshold
----------------------------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. To set thresholds on RSVP-TE tunnels:

In the above example, the maximum number of RSVP-TE tunnels in the RIB is set to 6,000 and the threshold is set to 70%. This means that when the number of tunnels in the RIB reaches 4,200, a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 6,000.

**Command syntax: maximum-tunnels [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- The thresholds are for generating system-events only. They do not affect in any way the number of installed tunnels.

- The thresholds apply to all tunnel types (primary, bypass, auto-bypass, auto-mesh) and for all tunnel roles (head, transit, tail) combined.

- When the number of tunnels drops below a threshold, a system-event notification is generated.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| maximum   | maximum rsvp-te tunnel limit, exceeding the limit will invoke a periodic warning | 1-29999 | 7000    |
+-----------+----------------------------------------------------------------------------------+---------+---------+
| threshold | maximum rsvp-te tunnel threshold, exceeding the threshold will invoke a warning  | 1-100   | 75      |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# maximum-tunnels 6000 threshold 70


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no maximum-tunnels

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.0    | Command introduced                |
+---------+-----------------------------------+
| 15.0    | Updated max-tunnels default value |
+---------+-----------------------------------+
```

## path-selection
```rst
protocols rsvp path-selection
-----------------------------

**Minimum user role:** operator

This command sets the type of metric cspf should consider when finding an LSP path. The metric types are:

•	te-metric - The interface traffic-engineering metric, signaled as part of the traffic-engineering information by the igp protocol

•	igp-metric - The interface igp-metric.

To configure the metric-type:

**Command syntax: path-selection [path-selection]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+----------------+-------------------------------------------------------------+----------------+-----------+
| Parameter      | Description                                                 | Range          | Default   |
+================+=============================================================+================+===========+
| path-selection | Set which metric should cspf consider whan finding lsp path | | te-metric    | te-metric |
|                |                                                             | | igp-metric   |           |
+----------------+-------------------------------------------------------------+----------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# path-selection igp-metric


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no path-selection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## pcep delegation
```rst
protocols rsvp pcep delegation
------------------------------

**Minimum user role:** operator

PCEP delegation enables to configure the use of PCEP to delegate tunnel settings to a remote PCE. See additional information on PCE and PCEP in "mpls traffic-engineering pcep”.
When a new LSP is established for a tunnel, the path computation client (PCC) revokes the PCE's explicit route object (ERO) constraint. This may result in a new path with a different ERO for the tunnel. To prevent this behavior, use the sticky-ero attribute. With sticky-ero enabled, the following behavior is observed:

- The path computation client (PCC) keeps the last successfully established ERO received from the PCE for new established LSPs for the tunnel. All other LSP parameters (e.g. bandwidth, admin-groups, etc.) remain unchanged.

- When the user applies a new path configuration (ERO) to the tunnel, the tunnel will continue using the ERO provided by the PCE. The new path will be used when the tunnel is no longer delegated or RSVP has restarted.

To configure PCEP delegation globally:

**Command syntax: pcep delegation [admin-state]** sticky-ero [sticky-ero]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  'delegation disable' - disable delegation. sticky-ero-admin-state configuration remain unchanged

.. -  'no pcep delegation [delegation-admin-state] sticky-ero', 'no pcep delegation [delegation-admin-state] sticky-ero [sticky-ero-admin-state]' - return sticky-ero-admin-state to default settings

.. -  'no pcep delegation', 'no pcep delegation [delegation-admin-state]' - return both delegation-admin-state and sticky-ero-admin-state to default values

- When PCEP delegation is enabled, you still have control over tunnel configuration.

**Parameter table**

+-------------+-------------------------+--------------+----------+
| Parameter   | Description             | Range        | Default  |
+=============+=========================+==============+==========+
| admin-state | default delegation mode | | enabled    | disabled |
|             |                         | | disabled   |          |
+-------------+-------------------------+--------------+----------+
| sticky-ero  | default delegation mode | | enabled    | enabled  |
|             |                         | | disabled   |          |
+-------------+-------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# pcep delegation enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# pcep delegation enabled sticky-ero enabled


**Removing Configuration**

To revert to the default sticky-ero state:
::

    dnRouter(cfg-protocols-rsvp)# no pcep delegation enabled sticky-ero

To revert to the default delegation state and sticky-ero-admin-state:
::

    dnRouter(cfg-protocols-rsvp)# no pcep delegation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## preemption hard
```rst
protocols rsvp preemption hard
------------------------------

**Minimum user role:** operator

When bandwidth is insufficient to handle all RSVP tunnels (for example when a new tunnel with bandwidth reservation needs to be installed, or one of the members of a bundle interface fails), you can control the preemption of one or more existing RSVP bandwidth reservations to accommodate a higher priority reservation. The preemption will occur in make-before-break fashion, such that the lower priority tunnel is maintained until the alternative higher priority tunnel is successfully established.
You can choose between two preemption types:

- Hard: the device tears down a preempted LSP first, signals a new path, and then reestablishes the LSP over the new path. In the interval between the time that the LSP is taken down and the new LSP is established, any traffic attempting to use the LSP is lost.

- Soft: the device first attempts to find a new path for the preempted LSP before tearing down the old path to prevent traffic loss. During soft preemption, the two LSPs with their corresponding bandwidth requirements are used until the original path is torn down. 

When enabled, tunnel changes will be applied only if the new tunnel is created successfully. When preemption is required, the least number of tunnels will be preempted in order to satisfy the new bandwidth requirement.

To configure preemption:

**Command syntax: preemption hard**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -timeout - can only be set for type 'soft'

.. -'no preemption soft timeout' - return timeout to default value

.. -'no preemption' - return to default preemption settings (soft) with default timeout value

- Preemption affects transit routers.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# preemption soft timeout 40

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# preemption hard


**Removing Configuration**

To revert to the default timeout value:
::

    dnRouter(cfg-protocols-rsvp-mmb)# no preemption soft timeout

To revert to the default preemption type (and reverts the timeout to default):
::

    dnRouter(cfg-protocols-rsvp-mmb)# no preemption

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## preemption soft
```rst
protocols rsvp preemption soft
------------------------------

**Minimum user role:** operator

When bandwidth is insufficient to handle all RSVP tunnels (for example when a new tunnel with bandwidth reservation needs to be installed, or one of the members of a bundle interface fails), you can control the preemption of one or more existing RSVP bandwidth reservations to accommodate a higher priority reservation. The preemption will occur in make-before-break fashion, such that the lower priority tunnel is maintained until the alternative higher priority tunnel is successfully established.
You can choose between two preemption types:

- Hard: the device tears down a preempted LSP first, signals a new path, and then reestablishes the LSP over the new path. In the interval between the time that the LSP is taken down and the new LSP is established, any traffic attempting to use the LSP is lost.

- Soft: the device first attempts to find a new path for the preempted LSP before tearing down the old path to prevent traffic loss. During soft preemption, the two LSPs with their corresponding bandwidth requirements are used until the original path is torn down. 

When enabled, tunnel changes will be applied only if the new tunnel is created successfully. When preemption is required, the least number of tunnels will be preempted in order to satisfy the new bandwidth requirement.

To configure preemption:

**Command syntax: preemption soft** timeout [timeout]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -timeout - can only be set for type 'soft'

.. -'no preemption soft timeout' - return timeout to default value

.. -'no preemption' - return to default preemption settings (soft) with default timeout value

- Preemption affects transit routers.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                      | Range  | Default |
+===========+==================================================================================+========+=========+
| timeout   | maximum time for trying to establish alternate tunnel before primary tunnel is   | 30-300 | 30      |
|           | preempted                                                                        |        |         |
+-----------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# preemption soft timeout 40

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# preemption hard


**Removing Configuration**

To revert to the default timeout value:
::

    dnRouter(cfg-protocols-rsvp-mmb)# no preemption soft timeout

To revert to the default preemption type (and reverts the timeout to default):
::

    dnRouter(cfg-protocols-rsvp-mmb)# no preemption

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## priority
```rst
protocols rsvp priority setup hold
----------------------------------

**Minimum user role:** operator

Preemption of an existing LSP is used when there is insufficient bandwidth. Priority determines whether an LSP can be preempted or can preempt another LSP using the following properties:

- Setup priority - determines which tunnels can be preempted. For preemption to occur, the setup priority of the new tunnel must be higher than the setup priority of the existing tunnel.

- Hold priority - determines which LSP should be preempted by other LSPs. A high hold priority means that the LSP is less likely to be preempted (that is, it is less likely to give up its reservation).

To prevent preemption loops (i.e. when two LSPs are allowed to preempt each other), the hold priority must be greater than or equal to the setup priority.
By default, an LSP has a setup priority of 7 (meaning it cannot preempt any other LSP) and a hold priority of 0 (meaning it cannot be preempted by other LSPs), so that preemption does not happen.
To globally configure the tunnels' reservation priority:

**Command syntax: priority setup [setup] hold [hold]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- Hold-priority must be ≥ setup priority to prevent preemption loops.

.. -  must comply [hold-priority] <= [setup-priority]

.. -  no command returns to default priority settings.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| setup     | priority used when signaling an LSP for this tunnel to determine which existing  | 0-7   | 7       |
|           | tunnels can be preempted                                                         |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+
| hold      | priority associated with an LSP for this tunnel to determine if it should be     | 0-7   | 0       |
|           | preempted by other LSPs that are being signaled                                  |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# priority setup 3 hold 3


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## protection
```rst
protocols rsvp protection
-------------------------

**Minimum user role:** operator

Fast reroute protection enables to divert a tunnel passing through a failed interface by encapsulating it in a different tunnel carrying the traffic to a merge point behind the network failure.
There are two types of traffic protection for RSVP-signaled LSPs:

- Link protection - where a bypass tunnel encapsulates the traffic through an LSP skipping the potential damaged link and forwards it towards the protected tunnel's next-hop.

- Node protection - where a bypass tunnel encapsulates the traffic through an LSP skipping the potential damaged node and forwards it towards the protected tunnel's next next-hop.

The bypass-tunnel can have any length LSP (limited by the configured “hop-limit”).

When protection is needed and a bypass tunnel that can provide it (i.e. it has the required destination and matches the required protection type) is available, the bypass tunnel will be used regardless of any conflict with the Primary tunnel's attributes, such as admin-group.
When there are multiple possible bypass-tunnels available for protection, the bypass tunnel that will be used is the “least used” bypass-tunnel, i.e the tunnel that protects the least number of primary tunnels. 

The bypass tunnel protection type supported is facility-backup. A single bypass-tunnel provides protection to multiple primary tunnels. If several (2 or more) primary tunnels are protected by a single protection Bypass (of the same type) and a new protection bypass (of the same type) is created – the bypasses are reselected for protection of the primary tunnels to ensure equal usage of bypass tunnels among the primary tunnels.
You can configure up to 5 manual bypass-tunnels per interface. There is no limit to the number of auto bypass-tunnels established through an interface.
When checking the scale of tunnels in the system, bypass-tunnels (auto and manual) are regarded as any other tunnel and are counted in the system's total tunnel scale limit.

When enabled, all the nodes are informed that the LSP is protected against link and/or node failure. Bypass tunnels that match the protection request are set as protection tunnels. If there are no eligible bypass tunnels and auto-bypass is enabled, an auto-bypass tunnel will be created.

To globally enable/disable fast-reroute tunnel protection:

**Command syntax: protection [protection]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+------------+----------------------------------------------------+---------------------+----------+
| Parameter  | Description                                        | Range               | Default  |
+============+====================================================+=====================+==========+
| protection | global configuration for tunnel protection setting | | disabled          | disabled |
|            |                                                    | | link-protection   |          |
|            |                                                    | | node-protection   |          |
+------------+----------------------------------------------------+---------------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# protection link-protection

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# protection node-protection

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# protection disabled


**Removing Configuration**

To revert protection to the default state:
::

    dnRouter(cfg-protocols-rsvp)# no protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## rib-unicast-install
```rst
protocols rsvp rib-unicast-install
----------------------------------

**Minimum user role:** operator

With the rib-unicast-install command, you can install RSVP tunnel destinations in the RIB IPv4-unicast table as directly reachable through the tunnel.
To enable/disable the ability to install the tunnel destinations in the RIB:

**Command syntax: rib-unicast-install [rib-unicast-install]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- This configuration is applicable to all primary tunnel types (regular and auto-mesh), except bypass tunnels.

.. - RSVP administrative-distance is 100 by default

.. - 'no rib-unicast-install'- return rib-unicast-install to default state

**Parameter table**

+---------------------+-----------------------------------------------------------------------------+--------------+----------+
| Parameter           | Description                                                                 | Range        | Default  |
+=====================+=============================================================================+==============+==========+
| rib-unicast-install | state if tunnel destination will be installed in the rib ipv4-unicast table | | enabled    | disabled |
|                     |                                                                             | | disabled   |          |
+---------------------+-----------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# rib-unicast-install enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# rib-unicast-install enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# rib-unicast-install disabled
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# rib-unicast-install enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# rib-unicast-install enabled
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# rib-unicast-install disabled


**Removing Configuration**

To return the rib-unicast-install to the default:
::

    dnRouter(cfg-protocols-rsvp)# no rib-unicast-install

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
```

## rsvp
```rst
protocols rsvp
--------------

**Minimum user role:** operator

Enters the RSVP configuration hierarchy level.

**Command syntax: rsvp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)#


**Removing Configuration**

To remove all RSVP configuration:
::

    dnRouter(cfg-protocols)# no rsvp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
```

## source-address
```rst
protocols rsvp source-address
-----------------------------

**Minimum user role:** operator

To configure the RSVP IP source address to be used in tunnel signaling:

**Command syntax: source-address [source-address]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+----------------+------------------------------------------------------+---------+---------+
| Parameter      | Description                                          | Range   | Default |
+================+======================================================+=========+=========+
| source-address | rsvp ip source address to be use in tunnel signaling | A.B.C.D | \-      |
+----------------+------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# source-address 10.10.10.10


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no source-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

# PIM

## asm-override
```rst
protocols pim asm-override
--------------------------

**Minimum user role:** operator

When sub-ranges from SSM group ranges are statically or dynamically mapped to RPs, enable ASM override.

To enable the ASM override for SSM group ranges:

**Command syntax: asm-override [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Note**
- PIM register and MSDP SA messages are not accepted, generated, or forwarded for group addresses within the SSM range, unless asm-override is enabled and SSM group sub-ranges are mapped to RPs.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | When enabled the PIM SSM ranges should also be allowed for ASM and Join(\*,G)    | | enabled    | disabled |
|             | for G in the SSM ranges shall be accpeted                                        | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# asm-override enabled
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no asm-override

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 12.0    | Command introduced        |
+---------+---------------------------+
| TBD     | Parameter applies per-VRF |
+---------+---------------------------+
```

## class-of-service
```rst
protocols pim class-of-service
------------------------------

**Minimum user role:** operator

The class-of-service parameter configures the Differentiated Services Code Point (DSCP) value used for all outgoing PIM protocol packets, which affects how these packets are prioritized in the network.

This is a global parameter that applies to all VRFs (both default and non-default).

To set the DSCP value for outgoing PIM packets:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**
- The IPP is set accordingly. I.e DSCP 48 is mapped to 6.

**Parameter table**

+------------------+------------------------------+-------+---------+
| Parameter        | Description                  | Range | Default |
+==================+==============================+=======+=========+
| class-of-service | PIM packets class of service | 0-56  | 48      |
+------------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# class-of-service 48
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no class-of-service

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 12.0    | Command introduced                     |
+---------+----------------------------------------+
| TBD     | Parameter applies globally to all VRFs |
+---------+----------------------------------------+
```

## graceful-restart-timer
```rst
protocols pim graceful-restart-timer
------------------------------------

**Minimum user role:** operator

The graceful restart time is the time limit to maintain stale PIM-originated multicast forwarding entries before they are cleared. Multicast forwarding entries become stale following a PIM process restart (for example, following a restart of the routing engine or a cluster NCC failover event). After the grace time, all stale PIM join/prune states are discarded and the related multicast RIB and FIB entries are removed.

To configure the PIM graceful restart timeout:

**Command syntax: graceful-restart-timer [graceful-restart-timer]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Note**
- The graceful restart time must be lower than the hello-holdtime, or lower than the maximum interface hello-interval times 3.5 seconds to ensure non-stop routing with all peer PIM neighbors.

- In the event that PIM NSR is enabled, its timer shall be used instead of the configured PIM graceful restart time.

- The graceful-restart-timer value must be the same across all VRFs. If different values are configured, the configuration will be rejected.

**Parameter table**

+------------------------+----------------------------------------------+---------+---------+
| Parameter              | Description                                  | Range   | Default |
+========================+==============================================+=========+=========+
| graceful-restart-timer | Maximum time for graceful restart to finish. | 30-3600 | 180     |
+------------------------+----------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# graceful-restart-time 100
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no graceful-restart-time

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 12.0    | Command introduced                                      |
+---------+---------------------------------------------------------+
| 18.1    | Changed graceful-restart-time to graceful-restart-timer |
+---------+---------------------------------------------------------+
| TBD     | Parameter applies per-VRF                               |
+---------+---------------------------------------------------------+
```

## hello-interval
```rst
protocols pim hello-interval
----------------------------

**Minimum user role:** operator

The hello interval is the periodic interval at which PIM Hello messages are sent to maintain neighbor relationships and exchange PIM protocol information.

To configure the hello interval:

**Command syntax: hello-interval [hello-interval]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Note**
- Any change in the pim hello interval will take effect immediately if the new value is lower than the previous value. Otherwise, it will only take effect after the derived timers, such as PIM hello hold-time, are updated and sent to peer routers at least once.

- The derived hello hold-time is 3.5 x hello-interval and it must be greater than the graceful-restart-time.

**Parameter table**

+----------------+--------------------------------------+--------+---------+
| Parameter      | Description                          | Range  | Default |
+================+======================================+========+=========+
| hello-interval | Periodic interval for Hello messages | 1-3600 | 30      |
+----------------+--------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# hello-interval 100
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no hello-interval

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 12.0    | Command introduced        |
+---------+---------------------------+
| TBD     | Parameter applies per-VRF |
+---------+---------------------------+
```

## join-prune-interval
```rst
protocols pim join-prune-interval
---------------------------------

**Minimum user role:** operator

To set the join-prune-interval value for outgoing PIM packets:

**Command syntax: join-prune-interval [join-prune-interval]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter           | Description                                                                      | Range  | Default |
+=====================+==================================================================================+========+=========+
| join-prune-interval | Periodic interval between Join/Prune messages. The hold-time associated with the | 10-600 | 60      |
|                     | PIM-Join message is 3.5 times the pim join-prune-interval                        |        |         |
+---------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# join-prune-interval 180
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no join-prune-interval

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 18.1    | Command introduced        |
+---------+---------------------------+
| TBD     | Parameter applies per-VRF |
+---------+---------------------------+
```

## load-split
```rst
protocols pim load-split admin-state
------------------------------------

**Minimum user role:** operator

To take advantage of multiple paths throughout the network, traffic from a multicast source or sources is load split across ECMP paths.

To enable/disable PIM's load-split:

**Command syntax: load-split admin-state [load-split-admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Parameter table**

+------------------------+--------------------------------+--------------+---------+
| Parameter              | Description                    | Range        | Default |
+========================+================================+==============+=========+
| load-split-admin-state | The PIM Load Split admin state | | enabled    | enabled |
|                        |                                | | disabled   |         |
+------------------------+--------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# load-split admin-state disabled
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no load-split admin-state

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 12.0    | Command introduced        |
+---------+---------------------------+
| TBD     | Parameter applies per-VRF |
+---------+---------------------------+
```

## maximum-mfib-routes
```rst
protocols pim maximum-mfib-routes
---------------------------------

**Minimum user role:** operator

The maximum-mfib-routes parameter sets the system-wide limit for the number of Multicast Forwarding Information Base (MFIB) routes that PIM can create.

This is a global parameter that applies to all VRFs (both default and non-default).

To configure the PIM maximum MFIB routes limit:

**Command syntax: maximum-mfib-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols pim

**Parameter table**

+-----------+----------------------------------+---------+---------+
| Parameter | Description                      | Range   | Default |
+===========+==================================+=========+=========+
| maximum   | maximum limit of PIM MFIB routes | 1-60000 | 60000   |
+-----------+----------------------------------+---------+---------+
| threshold | percentage of maximum limit      | 1-100   | 75      |
+-----------+----------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# maximum-mfib-routes 50000
    dnRouter(cfg-protocols-pim)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# maximum-mfib-routes 40000 threshold 90
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no maximum-mfib-routes

**Command History**

+---------+---------------------------------------------------------------------------+
| Release | Modification                                                              |
+=========+===========================================================================+
| 12.0    | Command introduced                                                        |
+---------+---------------------------------------------------------------------------+
| 18.2.1  | Renamed the command                                                       |
+---------+---------------------------------------------------------------------------+
| TBD     | Parameter now applies globally to all VRFs (both default and non-default) |
+---------+---------------------------------------------------------------------------+
```

## maximum-mfib-routes-vrf
```rst
protocols pim maximum-mfib-routes-vrf
-------------------------------------

**Minimum user role:** operator

The maximum-mfib-routes-vrf parameter sets the per-VRF limit for the number of Multicast Forwarding Information Base (MFIB) routes that PIM can create for this specific VRF.

This is a per-VRF parameter that applies only to the current VRF instance. The per-VRF maximum must be less than or equal to the global maximum configured at the system level.

To configure the PIM maximum MFIB routes limit for a VRF:

**Command syntax: maximum-mfib-routes-vrf [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Parameter table**

+-----------+-----------------------------------------------+---------+---------+
| Parameter | Description                                   | Range   | Default |
+===========+===============================================+=========+=========+
| maximum   | Maximum limit of PIM MFIB routes for this VRF | 1-60000 | 60000   |
+-----------+-----------------------------------------------+---------+---------+
| threshold | Percentage of maximum limit for this VRF      | 1-100   | 75      |
+-----------+-----------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# maximum-mfib-routes-vrf 30000
    dnRouter(cfg-protocols-pim)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# maximum-mfib-routes-vrf 25000 threshold 80
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value (default VRF context):
::

    dnRouter(cfg-protocols-pim)# no maximum-mfib-routes-vrf

To revert to the default value (non-default VRF context):
::

    dnRouter(cfg-network-services-vrf-instance-protocols-pim)# no maximum-mfib-routes-vrf

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| TBD     | Command introduced for per-VRF PIM MFIB routes configuration |
+---------+--------------------------------------------------------------+
```

## nsr
```rst
protocols pim nsr
-----------------

**Minimum user role:** operator

PIM Non-Stop Routing (NSR) allows PIM to maintain forwarding state during routing engine restarts or cluster NCC failover events.
To enable or disable PIM NSR:

**Command syntax: nsr [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Note**

- By default, PIM NSR is enabled.

- The NSR configuration (enabled/disabled state) must be the same across all VRFs. If different values are configured, the configuration will be rejected.

**Parameter table**

+-------------+-------------------------+--------------+---------+
| Parameter   | Description             | Range        | Default |
+=============+=========================+==============+=========+
| admin-state | The PIM NSR admin state | | enabled    | enabled |
|             |                         | | disabled   |         |
+-------------+-------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# nsr enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# nsr disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim


**Removing Configuration**

To revert PIM NSR to the default value:
::

    dnRouter(cfg-protocols-pim)# no nsr

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 16.1    | Command introduced        |
+---------+---------------------------+
| TBD     | Parameter applies per-VRF |
+---------+---------------------------+
```

## pim
```rst
protocols pim
-------------

**Minimum user role:** operator

Protocol Independent Multicast (PIM) is a collection of protocols used in a multicast environment. The main PIM protocols are: PIM Sparse Mode (PIM-SM) and PIM Dense Mode (PIM-DM). A combination of the two (PIM Sparse-Dense mode) is also sometimes used.

In PIM-SM, routers need to explicitly announce that they want to receive multicast messages from multicast groups, while PIM-DM protocols assumes that all routers want to receive multicast messages unless they state otherwise.
PIM-SM is the method used to route multicast packets from a source to multicast groups. It is used when only some of the recipients want to receive the multicast packet. In PIM-SM, a Rendezvous Point (RP) is used to receive multicast packets from the source and deliver them to the recipient.

Each domain in PIM-SM has a set of routers acting as RPs, which can be viewed as an exchange point where the source and recipients meet. First-hop routers are responsible for registering the sources to the RP and the latter is responsible for building a shortest path tree (SPT) to the source once it receives traffic from the source, thus creating a (S,G) entry between the router and the source. Last-hop routers are responsible for registering the recipients to the RP by creating a (\*,G) entry between the recipient and the RP. When a source transmits multicast data, the traffic flows to the RP and then to the recipients.

Enters the PIM configuration hierarchy level:

**Command syntax: pim**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To remove all PIM configuration:
::

    dnRouter(cfg-protocols)# no pim

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
| TBD     | Add VRF support    |
+---------+--------------------+
```

## ssm-ranges
```rst
protocols pim ssm-ranges
------------------------

**Minimum user role:** operator

Use the following command to configure the PIM-SSM group ranges:

**Command syntax: ssm-ranges [range-policy-prefix-list]**

**Command mode:** config

**Hierarchies**

- protocols pim
- network-services vrf instance protocols pim

**Note**
- PIM register and MSDP SA messages are not accepted, generated, or forwarded for group addresses within the SSM range, unless asm-override is enabled and SSM group sub-ranges are mapped to RPs.

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter                | Description                                                                      | Range            | Default |
+==========================+==================================================================================+==================+=========+
| range-policy-prefix-list | The prefix-list name which uniquely identify a policy that contains one or more  | | string         | \-      |
|                          | policy rules used to accept or reject certain multicast groups. The groups       | | length 1-255   |         |
|                          | accepted by this policy define the multicast group rang used by SSM. If a policy |                  |         |
|                          | is not specified, the default SSM multicast group rang is used. The default SSM  |                  |         |
|                          | multicast group range is 232.0.0.0/8 for IPv4                                    |                  |         |
+--------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# ssm-ranges SSM-Ranges-Pref-List


**Removing Configuration**

To revert PIM maximum-mfib-routes to default value:
::

    dnRouter(cfg-protocols-pim)# no ssm-ranges

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 12.0    | Command introduced        |
+---------+---------------------------+
| TBD     | Parameter applies per-VRF |
+---------+---------------------------+
```

# IGMP

## class-of-service
```rst
protocols igmp class-of-service
-------------------------------

**Minimum user role:** operator

You can use the following command to set the DSCP value for outgoing IGMP Mtrace packets class of service.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols igmp

**Note**
- IPP is set according to the DSCP value for outgoing packets, for example, DSCP 48 is mapped to 6.

**Parameter table**

+------------------+-------------------------------+-------+---------+
| Parameter        | Description                   | Range | Default |
+==================+===============================+=======+=========+
| class-of-service | IGMP packets class of service | 0-56  | 48      |
+------------------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# igmp
    dnRouter(cfg-protocols-igmp)# class-of-service 50


**Removing Configuration**

To return the dscp-value to the default:
::

    dnRouter(cfg-protocols-igmp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## igmp
```rst
protocols igmp
--------------

**Minimum user role:** operator

To start the IGMP process:

**Command syntax: igmp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# igmp
    dnRouter(cfg-protocols-igmp)#


**Removing Configuration**

To disable the igmp process:
::

    dnRouter(cfg-protocols)# no igmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

# DHCP

## class-of-service
```rst
protocols dhcp class-of-service
-------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure the DSCP value for all locally generated DHCP packets:

**Command syntax: class-of-service [dscp]**

**Command mode:** config

**Hierarchies**

- protocols dhcp

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| dscp      | The DSCP value that is used in the DHCP packet to classify it and give it a      | 0-56  | 48      |
|           | priority.                                                                        |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# dhcp
    dnRouter(cfg-protocols-dhcp)# class-of-service 16


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-dhcp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## dhcp
```rst
protocols dhcp
--------------

**Minimum user role:** operator

To configure the DHCP process and enter DHCP configuration mode:

**Command syntax: dhcp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# dhcp
    dnRouter(cfg-protocols-dhcp)#


**Removing Configuration**

To revert to the default configuration of the DHCP protocol:
::

    dnRouter(cfg-protocols)# no dhcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.2    | Command introduced |
+---------+--------------------+
```

# STATIC

## maximum-routes
```rst
protocols static maximum-routes threshold
-----------------------------------------

**Minimum user role:** operator

To configure the system maximum static route limit and threshold: The parameters will be used to invoke a system-event when the limit and threshold are crossed.

**Command syntax: maximum-routes [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols static
- network-services vrf instance protocols static

**Note**

- The thresholds are for generating system-events only.

- The thresholds are for IPv4 and IPv6 routes combined.

- When the threshold is cleared, a single system-event notification is generated.

- There is no limitation on the number of static routes that you can configure.

**Parameter table**

+-----------+---------------------------------------+---------+---------+
| Parameter | Description                           | Range   | Default |
+===========+=======================================+=========+=========+
| maximum   | Maximum Number of Static Routes       | 1-65535 | 16000   |
+-----------+---------------------------------------+---------+---------+
| threshold | Threshold Percentage for Static Route | 1-100   | 75      |
+-----------+---------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# maximum-routes 2000 threshold 70
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# maximum-routes 2000 threshold 70


**Removing Configuration**

To revert maximum & threshold to default:
::

    dnRouter(cfg-inst-protocols-static)# no maximum-routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## static routes overview
```rst
Static Routes Overview
----------------------
Routers forward packets using either route information from route table entries that you manually configure or the route information that is calculated using dynamic routing algorithms. You can supplement dynamic routes with static routes where appropriate. Static routes are useful in environments where network traffic is predictable and where the network design is simple and for specifying a gateway of last resort (a default router to which all unroutable packets are sent).
```

## static
```rst
protocols static
----------------

**Minimum user role:** operator

Routers forward packets using either route information from route table entries that you manually configure or the route information that is calculated using dynamic routing algorithms. You can supplement dynamic routes with static routes where appropriate. Static routes are useful in environments where network traffic is predictable and where the network design is simple and for specifying a gateway of last resort (a default router to which all unroutable packets are sent).
To configure static routes, enter the static configuration hierarchy:

**Command syntax: static**

**Command mode:** config

**Hierarchies**

- protocols
- network-services vrf instance protocols

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)#


**Removing Configuration**

To remove all static config per vrf instance:
::

    dnRouter(cfg-vrf-inst-protocols)# no static

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

# SEGMENT-ROUTING

## segment-routing
```rst
protocols segment-routing
-------------------------

**Minimum user role:** operator

To enter the segment-routing configuration hierarchy:

**Command syntax: segment-routing**

**Command mode:** config

**Hierarchies**

- protocols

**Note**
- no command remove all segment-routing configurations

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)#


**Removing Configuration**

To remove the segment-routing configuration:
::

    dnRouter(cfg-protocols)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

# VRRP

## vrrp
```rst
protocols vrrp interface
------------------------

**Minimum user role:** operator

To enable VRRP on an interface and enter interface configuration mode:


**Command syntax: vrrp interface [interface-name]**

**Command mode:** config

**Hierarchies**

- protocols
- network-services vrf instance protocols

**Parameter table**

+----------------+-----------------------------------------------------+----------------------------------------+---------+
| Parameter      | Description                                         | Range                                  | Default |
+================+=====================================================+========================================+=========+
| interface-name | The name of the interface on which VRRP is enabled. | | geX-<f>/<n>/<p>                      | \-      |
|                |                                                     | | geX-<f>/<n>/<p>.<sub-interface-id>   |         |
|                |                                                     | | bundle-<bundle-id>                   |         |
|                |                                                     | | bundle-<bundle-id.sub-bundle-id>     |         |
|                |                                                     | | irb<0-65535>                         |         |
+----------------+-----------------------------------------------------+----------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)#

    dnRouter(cfg-protocols)# vrrp interface bundle-2.1012
    dnRouter(cfg-protocols-vrrp-bundle-2.1012)#


**Removing Configuration**

To disable the VRRP process on an interface:
::

    dnRouter(cfg-protocols)# no vrrp interface ge100-0/0/0

To remove all VRRP configuration:
::

    dnRouter(cfg-protocols)# no vrrp

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 17.2    | Command introduced                     |
+---------+----------------------------------------+
| 18.0    | Added IRB support to tracked-interface |
+---------+----------------------------------------+
| 19.3    | Add no vrrp command                    |
+---------+----------------------------------------+
```

# MSDP

## class-of-service
```rst
protocols msdp class-of-service
-------------------------------

**Minimum user role:** operator

You can use the following command to set the DSCP value for outgoing MSDP Mtrace packets class of service.

The class-of-service set for the packet determines how the packet is treated through the network.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
IPP is set accordingly. i.e DSCP 48 is mapped to 6.

**Parameter table**

+------------------+-------------------------------+-------+---------+
| Parameter        | Description                   | Range | Default |
+==================+===============================+=======+=========+
| class-of-service | MSDP packets class of service | 0-56  | 48      |
+------------------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# class-of-service 50


**Removing Configuration**

To return the dscp-value to the default:
::

    dnRouter(cfg-protocols-msdp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## maximum-sa-states
```rst
protocols msdp maximum-sa-states
--------------------------------

**Minimum user role:** operator

When a PIM Register (S,G) message is received from the RPF, an SA state is created.

You can use the following command to configure the maximum number of SA states.

**Command syntax: maximum-sa-states [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- Threshold - the percentage of the value specified by **maximum**

- 'no maximum-sa-states' command reverts back both the maximum-sa-states and threshold to their default values.

**Parameter table**

+-----------+-----------------------------+---------+---------+
| Parameter | Description                 | Range   | Default |
+===========+=============================+=========+=========+
| maximum   | maximum limit of SA states  | 1-60000 | 60000   |
+-----------+-----------------------------+---------+---------+
| threshold | percentage of maximum limit | 1-100   | 75      |
+-----------+-----------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# maximum-sa-states 18000
    dnRouter(cfg-protocols-msdp)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# maximum-sa-states 20000 threshold 90
    dnRouter(cfg-protocols-msdp)#


**Removing Configuration**

To return the maximum-sa-states to the default value:
::

    dnRouter(cfg-protocols-msdp)# no maximum-sa-states

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## msdp
```rst
protocols msdp
--------------

**Minimum user role:** operator

Enters the MSDP configuration hierarchy level.

**Command syntax: msdp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)#


**Removing Configuration**

To disable the MSDP protocol:
::

    dnRouter(cfg-protocols)# no msdp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## originator-rp
```rst
protocols msdp originator-rp
----------------------------

**Minimum user role:** operator

You can use this command to enable setting the IP address or specify the interface to be the RP address of the MSDP SA messages originated by the local MSDP router.

**Command syntax: originator-rp {source-address [source-address], interface [interface-name]}**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- The originator-rp must have default or be configured. If it is not configured, the default originator-rp will be the router-id.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                                      | Range            | Default |
+================+==================================================================================+==================+=========+
| source-address | specify the originator ID source address to use for the MSDP session to this     | A.B.C.D          | \-      |
|                | peer                                                                             |                  |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+
| interface-name | Specify the interface name from which the MSDP originator RP IP address shall be | | string         | \-      |
|                | taken                                                                            | | length 1-255   |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# originator-rp interface lo0
    dnRouter(cfg-protocols-msdp)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# originator-rp source-address 1.1.1.1
    dnRouter(cfg-protocols-msdp)#


**Removing Configuration**

To return the originator-rp setting to its default value:
::

    dnRouter(cfg-protocols-msdp)# no originator-rp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## sa-hold-time
```rst
protocols msdp sa-hold-time
---------------------------

**Minimum user role:** operator

When a new MSDP SA TLV is accepted, the router caches the entry and sets its hold timer to sa-hold-time. If the MSDP SA TLV with the same (S,G,RP) is revived before the timer expires, its hold time is reset to sa-hold-time. In any other case, the entry is removed from the cache.

**Command syntax: sa-hold-time [sa-hold-time]**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- The hold-time timer must be greater than the keep-alive timer. The user is warned in case the keep-alive timer is greater or equal to hold-time.

**Parameter table**

+--------------+--------------------------------------------+----------+---------+
| Parameter    | Description                                | Range    | Default |
+==============+============================================+==========+=========+
| sa-hold-time | Sets the MSDP received SA state hold time. | 150-3600 | 150     |
+--------------+--------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# sa-hold-time 250


**Removing Configuration**

To revert the sa-hold-time to its default value:
::

    dnRouter(cfg-protocols-msdp)# no sa-hold-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

