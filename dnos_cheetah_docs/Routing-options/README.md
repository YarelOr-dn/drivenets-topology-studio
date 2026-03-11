# DNOS Routing-options Configuration Reference

This document contains the complete DNOS CLI Routing-options configuration syntax from the official DriveNets documentation.

---

## bgp-vpls-label-block-size
```rst
routing-options bgp-vpls-label-block-size
-----------------------------------------

**Minimum user role:** operator

Configure the BGP-VPLS label block size for BGP-VPLS and BGP-VPWS services:

**Command syntax: bgp-vpls-label-block-size [bgp-vpls-label-block-size]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- When bgp-vpls-label-block-size is set, the requested amount of labels will be allocated from the global mpls label pool.

- By default, BGP-VPLS labels will not be allocated unless the user explicitly configured it.

- If the first label was already allocated in the system, a system restart is required in order for the new configuration to take place.

- If BGP tries to allocate a label from this pool but no contiguous label base exists, the allocation will fail and a system event will be raised.

**Parameter table**

+---------------------------+--------------------------------------------------+------------+---------+
| Parameter                 | Description                                      | Range      | Default |
+===========================+==================================================+============+=========+
| bgp-vpls-label-block-size | Configuration for bgp vpls/vpws label block size | 128-131072 | \-      |
+---------------------------+--------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# bgp-vpls-label-block-size 131072


**Removing Configuration**

To revert the BGP-VPLS label block size to 0
::

    dnRouter(cfg-routing-options)# no bgp-vpls-label-block-size

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
routing-options bmp server admin-state
--------------------------------------

**Minimum user role:** operator

To enable the BMP server to which the BGP neighbor tables information will be sent.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Parameter table**

+-------------+------------------------+--------------+----------+
| Parameter   | Description            | Range        | Default  |
+=============+========================+==============+==========+
| admin-state | bmp server admin-state | | enabled    | disabled |
|             |                        | | disabled   |          |
+-------------+------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# admin-state enabled


**Removing Configuration**

To return the admin-state to the default value:
::

    dnRouter(cfg-routing-option-bmp)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## bmp server
```rst
routing-options bmp server
--------------------------

**Minimum user role:** operator

To configure a BMP server to which the bgp monitoring information will be sent.

**Command syntax: bmp server [server-id]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Up to 5 bmp servers can be configured per neighbor.

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| server-id | bmp server local id | 1-5   | \-      |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-routing-option)# no bmp server 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## class-of-service
```rst
routing-options bmp server class-of-service
-------------------------------------------

**Minimum user role:** operator

To set the DSCP value for outgoing BMP packets.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Parameter table**

+------------------+-------------------------------------+-------+---------+
| Parameter        | Description                         | Range | Default |
+==================+=====================================+=======+=========+
| class-of-service | dscp value for outgoing BMP packets | 0-56  | 16      |
+------------------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# class-of-service 48


**Removing Configuration**

To return the DSCP value to the default value:
::

    dnRouter(cfg-routing-option-bmp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## description
```rst
routing-options bmp server description
--------------------------------------

**Minimum user role:** operator

To set a description for the BMP server.

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Parameter table**

+-------------+------------------------+------------------+---------+
| Parameter   | Description            | Range            | Default |
+=============+========================+==================+=========+
| description | bmp server description | | string         | \-      |
|             |                        | | length 1-255   |         |
+-------------+------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# description "bmp server running on openBMP"


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-routing-option-bmp)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## host
```rst
routing-options bmp server host port
------------------------------------

**Minimum user role:** operator

To set the BMP server IP address and remote port for the BMP TCP session establishment.

**Command syntax: host [ip-address] port [dest-port]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Note**

- The host address and port must be configured for a BMP session to be established.

**Parameter table**

+------------+-------------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                             | Range        | Default |
+============+=========================================================================+==============+=========+
| ip-address | bmp server ip-address                                                   | | A.B.C.D    | \-      |
|            |                                                                         | | X:X::X:X   |         |
+------------+-------------------------------------------------------------------------+--------------+---------+
| dest-port  | destination tcp port to be used for the tcp session with the bmp server | 1-65535      | \-      |
+------------+-------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 2
    dnRouter(cfg-routing-option-bmp)# host 1.1.1.1 port 8000

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# host 1:1::1:1 port 8000


**Removing Configuration**

To remove the ip address and port configuration:
::

    dnRouter(cfg-routing-option-bmp)# no host

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## source-interface
```rst
routing-options bmp server source-interface
-------------------------------------------

**Minimum user role:** operator

To set the interface from which the source IP address for the BMP session will be taken.

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Note**

- The source IP type (IPv4 or IPv6) must match the server IP address-family. If one doesn't exist, the session will not open.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| source-interface | By default , uses the  "system in-band-management source-interface" for the same | | string         | \-      |
|                  | vrf                                                                              | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# source-interface lo0

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 2
    dnRouter(cfg-routing-option-bmp)# source-interface ge100-0/0/0


**Removing Configuration**

To return the source IP address to the default:
::

    dnRouter(cfg-routing-option-bmp)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## fec-statistics
```rst
routing-options fec-statistics
------------------------------

**Minimum user role:** operator

To configure the mpls fec-statistics operation mode:

**Command syntax: fec-statistics [fec-statistics]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Default behavior is to counter per in-label and egress-interface for supported protocols

- Configuration applies to new installed FIB mpls routes only

**Parameter table**

+----------------+------------------------------------------------------------+-------------------------------+---------------------------+
| Parameter      | Description                                                | Range                         | Default                   |
+================+============================================================+===============================+===========================+
| fec-statistics | Configuration for mpls fec-statistics of in-label counters | | in-label-egress-interface   | in-label-egress-interface |
|                |                                                            | | disabled                    |                           |
+----------------+------------------------------------------------------------+-------------------------------+---------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# fec-statistics disabled


**Removing Configuration**

To revert the behavior to its default:
::

    dnRouter(cfg-routing-option)# no fec-statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## flow
```rst
routing-options load-balancing flow
-----------------------------------

**Minimum user role:** operator

To instruct the router which network headers to use to select one of multiple equal-cost paths to the destination for flow-based routing:

**Command syntax: flow [flow]**

**Command mode:** config

**Hierarchies**

- routing-options load-balancing

**Note**

- For fragmented packets, 3-tuple is used regardless of the configuration.

- Ethernet header is ignored in 3-tuple / 5-tuple based load-balancing for L3 interfaces

- no command returns flow to its default state

**Parameter table**

+-----------+-----------------------------------------------------------+---------------------------------------------------+---------+
| Parameter | Description                                               | Range                                             | Default |
+===========+===========================================================+===================================================+=========+
| flow      | The network headers to use for flow-based load-balancing. | | 3-tuple: Ethernet, MPLS, and IP                 | 5-tuple |
|           |                                                           | | 5-tuple: Ethernet, MPLS, IP, TCP/UDP, and GTP   |         |
+-----------+-----------------------------------------------------------+---------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# load-balancing
    dnRouter(cfg-routing-option-lb)# flow 3-tuple


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-routing-option-lb)# no flow

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## load-balancing
```rst
routing-options load-balancing
------------------------------

**Minimum user role:** operator

Load balancing is the ability to spread traffic over multiple paths to a destination. Typically, when the router learns multiple paths to the same network via multiple routing protocols, it installs only one route with the lowest administrative distance in its routing table.
Similarly, when the router learns multiple paths via the same routing protocol (i.e., with the same administrative distance), it selects the path with the lowest cost to the destination. Load balancing can occur when the router is able to install multiple paths with the same administrative distance and cost to the destination.

When there are equal-cost paths to a destination, the router runs a hash algorithm that uses the packet's 3-tuple or 5-tuple (configurable)
to select one of the paths for the packet, thus ensuring flow-based routing.

For the router to distribute the traffic over multiple paths, you need to:

- Configure the protocols' maximum-paths attribute to a value greater than 1. This will allow the protocol to install multiple equal cost paths in the routing table (see bgp address-family maximum-paths and isis instance address-family maximum-paths)
- Configure the flow type (3-tuple or 5-tuple) to be used for path selection (see routing-options load-balancing flow)

To enter load-balancing configuration mode:

**Command syntax: load-balancing**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Unequal cost and per-prefix load balancing are not supported.

- Notice the change in prompt.

- no command returns all load-balancing configurations to their default state

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# load-balancing
    dnRouter(cfg-routing-option-lb)#


**Removing Configuration**

To revert to all load-balancing configurations to their default value:
::

    dnRouter(cfg-routing-option)# no load-balancing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## maximum-routes
```rst
routing-options maximum-routes
------------------------------

**Minimum user role:** operator

When BGP is connected to multiple external peers it is difficult to control what these peers advertise. Routing polices are used to control what is accepted from a peer.
In cases where peers advertise a large amount of prefixes (more than the system can handle), the system is expected to be able to contain this load and once the issue is handled to resume the normal operation.


BGP protection can prevent this on the neighbor level, however if the scale is from multiple neighbors, there is no limitation in BGP and RIB and this scale can overload the whole system.


You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary.


RIB routes are limited in a 1:1 ratio between IPv4 and IPv6, for IGP routes, and a 4:1 ratio between IPv4 and IPv6 for other route types. When setting the maximum-route maximum value to 2,550,000,
the RIB will install up to 2,025,000 IPv4 routes and 525,000 IPv6 routes to the FIB. By default, limits IGP routes to 50,000 and will not install IGP routes above this limit.


To configure RIB size thresholds:

**Command syntax: maximum-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Set the maximum-routes to 0 to disable maximum-routes limitation and system-events.

- The thresholds are for IPv4 and IPv6 combined.

- When the number of routes drops below a threshold, a system-event notification is generated.

- Although new routes will still be accepted even if the max-routes limit is reached, you should remove any undesired local routes (e.g. unnecessary static routes), check if all BGP neighbors are justified and verify that the correct policies are used upon receiving a system-event notification that a threshold has been crossed.

- - In the example, the maximum number of routes in the RIB is set to 1,500,000 and the threshold is set to 70%. This means that when the number of routes in the RIB reaches 1,050,000, a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 1,500,000.

- Reconfiguration behavior:

- - when 'maximum' is reconfigured, resulting that current routes number is now below the new maximum value. over-the-limit routes will be installed upto new maximum value.

- - when 'maximum' is reconfigured, resulting that current routes number is now above the new maximum value. only new routes will be blocked from installment. No affect on existing routes that were already installed.

- no command returns maximum & threshold to their default values

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------------+---------+
| Parameter | Description                                                                      | Range              | Default |
+===========+==================================================================================+====================+=========+
| maximum   | The maximum number of routes you want in the RIB.                                | 0, 100000-20000000 | 2550000 |
|           | Set maximum-routes to 0 to disable the maximum-routes limitation and system      |                    |         |
|           | events.                                                                          |                    |         |
+-----------+----------------------------------------------------------------------------------+--------------------+---------+
| threshold | A percentage (%) of max-routes to give you advance notice that the number of     | 1-100              | 75      |
|           | routes in the RIB is reaching the maximum level. When this threshold is crossed, |                    |         |
|           | a system-event notification is generated. You will not be notified again.        |                    |         |
+-----------+----------------------------------------------------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# maximum-routes 2000000

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# maximum-routes 1500000 threshold 70

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# maximum-routes 0


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-routing-option)# no maximum-routes

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 13.2    | Updated command parameter ranges |
+---------+----------------------------------+
```

## ipv4-min-length
```rst
routing-options next-hop-resolution ipv4 min-length
---------------------------------------------------

**Minimum user role:** operator

An operator can set the min-length constraint for the next-hop resolution by RIB. 
A common case is to set a long prefix length to avoid next-hop addresses to be resolved over default-route or summary-route, which may lead to traffic blackholing. 

To configure next-hop-resolution min-length:

**Command syntax: ipv4 min-length [ipv4-min-length]**

**Command mode:** config

**Hierarchies**

- routing-options next-hop-resolution
- network-services vrf instance routing-options next-hop-resolution

**Note**
- For 6PE, mapped IPv6 nexthop addresses ({::ffff:<ipv4-address>}) are handled in RIB as IPv4 address, and will be subjected to IPv4 min-length.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                      | Range | Default |
+=================+==================================================================================+=======+=========+
| ipv4-min-length | Route that resolve a recursive next-hop must comply with the configured prefix   | 1-32  | \-      |
|                 | length minimum value in order to be valid                                        |       |         |
+-----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resolution
    dnRouter(cfg-routing-option-nh-resolution)# ipv4 min-length 30

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# next-hop-resolution
    dnRouter(cfg-inst-routing-option-nh-resolution)# ipv4 min-length 30


**Removing Configuration**

To remove ipv4 min-length configuration:
::

    dnRouter(cfg-routing-option-nh-resolution)# no ipv4 min-length

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.1    | Command introduced |
+---------+--------------------+
```

## ipv6-min-length
```rst
routing-options next-hop-resolution ipv6 min-length
---------------------------------------------------

**Minimum user role:** operator

An operator can set the min-length constraint for next-hop resolution by RIB. 
A common case is to set a long prefix length to avoid next-hop addresses to be resolved over default-route or summary-route, which may lead to traffic blackholing. 

To configure next-hop-resolution min-length:

**Command syntax: ipv6 min-length [ipv6-min-length]**

**Command mode:** config

**Hierarchies**

- routing-options next-hop-resolution
- network-services vrf instance routing-options next-hop-resolution

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                      | Range | Default |
+=================+==================================================================================+=======+=========+
| ipv6-min-length | Route that resolve a recursive next-hop must comply with the configured prefix   | 1-128 | \-      |
|                 | length minimum value in order to be valid                                        |       |         |
+-----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resolution
    dnRouter(cfg-routing-option-nh-resolution)# ipv6 min-length 120

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# next-hop-resolution
    dnRouter(cfg-inst-routing-option-nh-resolution)# ipv6 min-length 120


**Removing Configuration**

To remove ipv6 min-length configuration:
::

    dnRouter(cfg-routing-option-nh-resolution)# no ipv6 min-length

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.1    | Command introduced |
+---------+--------------------+
```

## next-hop-resolution
```rst
routing-options next-hop-resolution
-----------------------------------

**Minimum user role:** operator

Routing protocols leverage RIBs to find out how their route next-hop is resolved. This behavior is done via a next-hop-tracking mechanism. 
When a recursive route is installed, RIB resolves the route next-hop over its table to provide full route solution to FIB.  This behavior is known as PIC
An operator can configure a next-hop resolution constraint that will be enforced by the RIB. When a next-hop-resolution constraint is configured, the RIB will enforce that the resolving route of a protocol route nexthop must match required constraint. 
In case no route is found that can meet desired constraints: 
* RIB will reply to client protocol that no solution was found for next-hop tracking registration
* RIB will not install a Route path to the FIB for a nexthop with no valid solution.
To enter the mpls-nh-ipv6 routing table configuration level:

**Command syntax: next-hop-resolution**

**Command mode:** config

**Hierarchies**

- routing-options
- network-services vrf instance routing-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resolution
    dnRouter(cfg-routing-option-nh-resolution)#

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# next-hop-resolution
    dnRouter(cfg-inst-routing-option-nh-resolution)#


**Removing Configuration**

To revert all next-hop-resolution configurations to default:
::

    dnRouter(cfg-routing-option)# no next-hop-resolution

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.1    | Command introduced |
+---------+--------------------+
```

## next-hop-resources
```rst
routing-options next-hop-resources
----------------------------------

**Minimum user role:** operator

To configure the warning threshold for the next-hop resources in use:

**Command syntax: next-hop-resources**

**Command mode:** config

**Hierarchies**

- routing-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resources threshold 80
    dnRouter(cfg-routing-option)#


**Removing Configuration**

To revert the threshold to its default: 75%
::

    dnRouter(cfg-routing-option)# no next-hop-resources threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## next-hop-resources
```rst
routing-options next-hop-resources threshold
--------------------------------------------

**Minimum user role:** operator

To configure the warning threshold for the next-hop resources in use:

**Command syntax: next-hop-resources threshold [threshold]**

**Command mode:** config

**Hierarchies**

- routing-options

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| threshold | percent of max scale for which a syslog event will be sent when crossing         | 0, 50-100 | 75      |
|           | threshold                                                                        |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resources threshold 80
    dnRouter(cfg-routing-option)#


**Removing Configuration**

To revert the threshold to its default: 75%
::

    dnRouter(cfg-routing-option)# no next-hop-resources threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## threshold
```rst
routing-options next-hop-resources threshold
--------------------------------------------

**Minimum user role:** operator

To configure the warning threshold for the next-hop resources in use:

**Command syntax: threshold [threshold]**

**Command mode:** config

**Hierarchies**

- routing-options next-hop-resources

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| threshold | percent of max scale for which a syslog event will be sent when crossing         | 0, 50-100 | 75      |
|           | threshold                                                                        |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# next-hop-resources
    dnRouter(cfg-routing-option-nh-resources)# threshold 80
    dnRouter(cfg-routing-option-nh-resources)#


**Removing Configuration**

To revert the threshold to its default: 75%
::

    dnRouter(cfg-routing-option-nh-resources)# no threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## qppb-per-vrf
```rst
routing-options qppb-per-vrf
----------------------------

**Minimum user role:** operator

An operator can select that all IP traffic forwarded in the default vrf will be subjected to qppb match, regardless of the traffic ingress interface.
To enable per vrf qppb:

**Command syntax: qppb-per-vrf**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- When qppb-per-vrf is set for a given vrf, interfaces that belong to that vrf cannot have a qppb configuration. The user will not be able have either 'qppb enabled' or 'qppb disabled' for interfaces in vrf which has qppb-per-ver.

- Traffic redirected to the default vrf is subjected to qppb logic

- VPN traffic terminated in non-default vrf is not subjected to qppb logic, unless explicitly configured for the vrf instance

- When qppb-per-vrf is set, qppb statistics are provided per qppb rule level without interface granularity.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# qppb-per-vrf enabled


**Removing Configuration**

To revert the behavior to its default:
::

    dnRouter(cfg-routing-option)# no qppb-per-vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.1    | Command introduced |
+---------+--------------------+
```

## router-id
```rst
routing-options router-id
-------------------------

**Minimum user role:** operator

To manually set the router-id to be used by the routing protocols:

**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- used in default vrf

- no command returns router-id to default value

- When using OSPFv3 or IPv6-based BGP peering within a routing instance, you must explicitly configure a router ID (router-id) for that specific instance.

The main routing instance's router ID is not inherited by other instances. Even if only IPv6 protocols are used, a 32-bit router ID is still required, as IPv6 routing protocols rely on it for establishing adjacencies. The router ID must be a non-zero 32-bit (4-octet) unsigned integer. While it's common to use an IPv4 address as the router ID, this is not mandatory - it doesn’t need to be a valid or routable address, just a unique 32-bit value within the routing domain.

Failing to configure a router ID in an IPv6 OSPF or BGP instance will result in the protocol defaulting to 0.0.0.0, which is invalid. This will prevent adjacency formation and BGP session establishment.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+-------------------------------------------------------------+
| Parameter | Description                                                                      | Range   | Default                                                     |
+===========+==================================================================================+=========+=============================================================+
| router-id | Set the network unique router ID. This ID will serve as the default ID for all   | A.B.C.D | The highest IPv4 address from any active loopback interface |
|           | routing protocols, unless otherwise specified.                                   |         |                                                             |
+-----------+----------------------------------------------------------------------------------+---------+-------------------------------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# router-id 1.1.1.1


**Removing Configuration**

To remove the router-id configuration:
::

    dnRouter(cfg-routing-option)# no router-id

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 6.0     | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 11.0    | Moved from the Protocols hierarchy to the Routing-options hierarchy. |
+---------+----------------------------------------------------------------------+
```

## routing-options
```rst
routing-options
---------------

**Minimum user role:** operator

The routing options configuration hierarchy allows you to filter out routes that are installed in the routing tables based on policies.This is done per routing table.To apply a policy to the routing table follow this general procedure:

Enter the routing-options configuration hierarchy (see below).
Enter the configuration hierarchy for the specific routing table. See routing-options table.
Select the policy to apply to the table. See routing-options table install-policy.
To enter the routing options configuration mode:

**Command syntax: routing-options**

**Command mode:** config

**Note**

- Notice the change in prompt.

- no command returns all routing-options configurations to their default state

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)#


**Removing Configuration**

To revert all routing-options configurations to their default state:
::

    dnRouter(cfg)# no routing-options

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
routing-options rpki server admin-state
---------------------------------------

**Minimum user role:** operator

To set the administrative state of the RPKI cache-server:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-------------+-------------------------------+--------------+---------+
| Parameter   | Description                   | Range        | Default |
+=============+===============================+==============+=========+
| admin-state | RPKI cache server admin-state | | enabled    | enabled |
|             |                               | | disabled   |         |
+-------------+-------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# admin-state disabled


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-routing-options-rpki)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## expire-interval
```rst
routing-options rpki server expire-interval
-------------------------------------------

**Minimum user role:** operator

To set the expire-interval value for the RTR session with the BGP RPKI cache server:

**Command syntax: expire-interval [expire-interval]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter       | Description                                                                      | Range      | Default |
+=================+==================================================================================+============+=========+
| expire-interval | Configures the time BGP waits to keep routes from a cache after the cache        | 360-172800 | 7200    |
|                 | session drops. Set expire-interval in seconds.                                   |            |         |
+-----------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# expire-interval 7200


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no expire-interval

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 15.1    | Command introduced                       |
+---------+------------------------------------------+
| 16.1    | Modified the expire-interval lower bound |
+---------+------------------------------------------+
```

## refresh-interval
```rst
routing-options rpki server refresh-interval
--------------------------------------------

**Minimum user role:** operator

To set the refresh-interval value for the RTR session with the BGP RPKI cache server.

**Command syntax: refresh-interval [refresh-interval]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                                      | Range   | Default |
+==================+==================================================================================+=========+=========+
| refresh-interval | Configures the time BGP waits in before next periodic attempt to poll the cache  | 1-86400 | 3600    |
|                  | and between subsequent attempts. Set refresh-interval in seconds.                |         |         |
+------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# refresh-interval 3600


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no refresh-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## retry-interval
```rst
routing-options rpki server retry-interval
------------------------------------------

**Minimum user role:** operator

To set the retry-interval value for the RTR session with the BGP RPKI cache server.

**Command syntax: retry-interval [retry-interval]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                                      | Range  | Default |
+================+==================================================================================+========+=========+
| retry-interval | Configures the time BGP waits for a response after sending a serial or reset     | 1-7200 | 600     |
|                | query. Set retry-interval in seconds.                                            |        |         |
+----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# retry-interval 600


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no retry-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## rpki server
```rst
routing-options rpki server
---------------------------

**Minimum user role:** operator

To configure a BGP RPKI cache server and its remote address.

**Command syntax: rpki server [server-address]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Multiple RPKI cache-servers can be configured for redundancy.

- Sessions are established simultaneously with all the configured RPKI cache-servers.

**Parameter table**

+----------------+------------------------------------------+-------+---------+
| Parameter      | Description                              | Range | Default |
+================+==========================================+=======+=========+
| server-address | RPKI cache server IP address or hotsname | \-    | \-      |
+----------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)#

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 2001:125:125::1
    dnRouter(cfg-routing-options-rpki)#

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)#


**Removing Configuration**

To revert all RPKI cache-server's configuration to the default values:
::

    dnRouter(cfg-routing-options)# no rpki server 1.1.1.1

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 15.1    | Command introduced                                   |
+---------+------------------------------------------------------+
| 16.2    | Replaced server identifier with the server's address |
+---------+------------------------------------------------------+
```

## source-interface
```rst
routing-options rpki server source-interface
--------------------------------------------

**Minimum user role:** operator

To set the interface from which the source IP address for the RTR session with a BGP RPKI cache server will be taken.

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**

- The source IP address type (IPv4 or IPv6) needs to match the IP address-family of the configured server. If such an address doesn't exist, the session will not open.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| source-interface | By default the 'system in-band-management source-interface' for the same VRF is  | | string         | \-      |
|                  | used. If both are not configured, then egress-forwarding resolution shall        | | length 1-255   |         |
|                  | determine the interface and source IP address                                    |                  |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# source-interface lo0

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# source-interface ge100-0/0/0


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## transport ssh password
```rst
routing-options rpki server transport ssh password
--------------------------------------------------

**Minimum user role:** operator

To configure the password for the SSH transport session with the BGP RPKI cache-server.

**Command syntax: transport ssh password [ssh-session-password]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**

- There's no remove option for the SSH password as it is a mandatory config for the RPKI server when transport SSH is used. The user can only change the assigned SSH password.


- If the authentication secret is not entered with the command, then the user will be prompted to enter a password. The maximum length of this password is 80 characters. It shall then be encrypted and stored into the system.


- The maximum length of the encrypted password stored into the system is 255, as shown in the parameter table below.


**Parameter table**

+----------------------+---------------------------------------------------------------+------------------+---------+
| Parameter            | Description                                                   | Range            | Default |
+======================+===============================================================+==================+=========+
| ssh-session-password | Set a password for the SSH session with the RPKI cache-server | | string         | \-      |
|                      |                                                               | | length 1-255   |         |
+----------------------+---------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport ssh password EncryptedPassword

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# transport ssh password
    Enter password:
    Enter password for verification:

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# transport ssh password
    Enter password:
    Enter password for verification:
    {'ERROR': 'Invalid secret length!'}
    (Max encrypted length 255 Min secret length 1 Max Clear length 80).


**Removing Configuration**

To remove the configured SSH password:
::

    The SSH password is mandatory when transport SSH is used. You can only change it, not remove it.

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 15.1    | Command introduced                    |
+---------+---------------------------------------+
| 15.2    | Removed MD5 from the command's syntax |
+---------+---------------------------------------+
```

## transport ssh port
```rst
routing-options rpki server transport ssh port
----------------------------------------------

**Minimum user role:** operator

To configure the port for the SSH transport session with the BGP RPKI cache-server.

**Command syntax: transport ssh port [ssh-port]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**
- There's no remove option for the SSH port as it is a mandatory config for the RPKI server when transport SSH is used. The user can only change the assigned SSH port.


**Parameter table**

+-----------+------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                            | Range   | Default |
+===========+========================================================================+=========+=========+
| ssh-port  | Destination port to be used for the session with the RPKI cache server | 1-65535 | \-      |
+-----------+------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport ssh port 323


**Removing Configuration**

To remove the configured SSH port:
::

    The SSH port is mandatory when transport SSH is used. You can only change it, not remove it.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## transport ssh username
```rst
routing-options rpki server transport ssh username
--------------------------------------------------

**Minimum user role:** operator

To configure the username for the SSH transport session with the BGP RPKI cache-server.

**Command syntax: transport ssh username [ssh-username]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**
- There's no remove option for the SSH username as it is a mandatory config for the RPKI server when transport SSH is used. The user can only change the assigned SSH username.


**Parameter table**

+--------------+-------------------------------------------------+------------------+---------+
| Parameter    | Description                                     | Range            | Default |
+==============+=================================================+==================+=========+
| ssh-username | Username for SSH session with RPKI cache server | | string         | \-      |
|              |                                                 | | length 1-255   |         |
+--------------+-------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport ssh username RPKIValidator


**Removing Configuration**

To remove the configured SSH username:
::

    The SSH username is mandatory when transport SSH is used. You can only change it, not remove it.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## transport tcp port
```rst
routing-options rpki server transport tcp port
----------------------------------------------

**Minimum user role:** operator

To configure the port for the TCP transport session with the BGP RPKI cache-server.

**Command syntax: transport tcp port [tcp-port]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**
- There's no remove option for the TCP port as it is a mandatory config for the RPKI server when transport TCP is used. The user can only change the assigned TCP port.


**Parameter table**

+-----------+------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                            | Range   | Default |
+===========+========================================================================+=========+=========+
| tcp-port  | Destination port to be used for the session with the RPKI cache server | 1-65535 | \-      |
+-----------+------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport tcp port 323


**Removing Configuration**

To remove the configured TCP port:
::

    The TCP port is mandatory when transport TCP is used. You can only change it, not remove it.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## vrf
```rst
routing-options rpki server vrf
-------------------------------

**Minimum user role:** operator

To set vrf instance from which RPKI cache-server is accessible:

**Command syntax: vrf [vrf]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-----------+---------------------+------------------+---------+
| Parameter | Description         | Range            | Default |
+===========+=====================+==================+=========+
| vrf       | The name of the vrf | | string         | default |
|           |                     | | length 1-255   |         |
+-----------+---------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# vrf IN_BAND_MGMT


**Removing Configuration**

To return the vrf to its default value:
::

    dnRouter(cfg-routing-options-rpki)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## global-block
```rst
routing-options segment-routing mpls global-block
-------------------------------------------------

**Minimum user role:** operator

The segment routing global block (SRGB) is a set of labels that are reserved for segment routing and have global significance in the routing protocol domain.
The configured label block is reserved even if not used by any of the segment-routing capable protocols.
By default, the segment-routing capable protocols use the SRGB/SRLB range configured under the routing-options hierarchy level, unless a specific block is configured under the protocol level.

To configure the segment routing global block (SRGB) used by the router:

**Command syntax: global-block [lower-bound] [range]**

**Command mode:** config

**Hierarchies**

- routing-options segment-routing mpls

**Note**

- When changing the configuration, the new block will only apply on the next system restart. To view the configured labels blocks and the currently in used label blocks, use the show mpls label-allocation tables command.

- The base and range together define the block size (i.e. the number of labels in the block) and must be identical for all instances, even if segment-routing is disabled.

- SRGB and SRLB blocks must not overlap.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter   | Description                                                                      | Range       | Default |
+=============+==================================================================================+=============+=========+
| lower-bound | Lower bound of the global label block. The block is defined to include this      | 256-1036384 | 16000   |
|             | label.                                                                           |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+
| range       | Define the srgb block size. for size of 1, only the lower-bound label exist in   | 1-1000000   | 8000    |
|             | block                                                                            |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# segment-routing mpls
    dnRouter(cfg-routing-option-sr)# global-block 32000 16000


**Removing Configuration**

To revert to the default values: 
::

    dnRouter(cfg-routing-option-sr)# no global-block

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 14      | Command introduced                                         |
+---------+------------------------------------------------------------+
| 16.2    | Extened base maximum range to 1036384                      |
+---------+------------------------------------------------------------+
| 18.2    | Increase SRGB range to 400000                              |
+---------+------------------------------------------------------------+
| 18.3    | Increase SRGB lower-bound options and max range to 1000000 |
+---------+------------------------------------------------------------+
```

## local-block
```rst
routing-options segment-routing mpls local-block
------------------------------------------------

**Minimum user role:** operator

The segment routing local block (SRLB) is a set of labels that have local significance only.
By default, the segment-routing capable protocols use the SRGB/SRLB range configured under the routing-options hierarchy level, unless a specific block is configured under the protocol level.
To configure the segment routing local block (SRLB) used by the router:

**Command syntax: local-block [lower-bound] [range]**

**Command mode:** config

**Hierarchies**

- routing-options segment-routing mpls

**Note**

- When changing the configuration, the new block will only apply on the next system restart. To view the configured labels blocks and the currently in used label blocks, use the show mpls label-allocation tables command.

- SRGB and SRLB blocks must be identical for all instances and must not overlap.

- SRGB and SRLB blocks must not overlap

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter   | Description                                                                      | Range       | Default |
+=============+==================================================================================+=============+=========+
| lower-bound | Lower bound of the local label block.                                            | 256-1040383 | 8000    |
+-------------+----------------------------------------------------------------------------------+-------------+---------+
| range       | Define the SRLB block size. For size of 1, only the lower bound label exist in   | 1-1000000   | 8000    |
|             | block                                                                            |             |         |
+-------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# segment-routing mpls
    dnRouter(cfg-routing-option-sr)# local-block 8000 1000


**Removing Configuration**

To revert to the default values: 
::

    dnRouter(cfg-routing-option-sr)# no local-block

**Command History**

+---------+-------------------------------------------------------------------+
| Release | Modification                                                      |
+=========+===================================================================+
| 14      | Command introduced                                                |
+---------+-------------------------------------------------------------------+
| 15      | Updated lower-bound from min 16 to min 256                        |
+---------+-------------------------------------------------------------------+
| 18.3    | Updated lower-bound parameter range and added range configuration |
+---------+-------------------------------------------------------------------+
| TBD     | Updated maximum supported range                                   |
+---------+-------------------------------------------------------------------+
```

## segment-routing
```rst
routing-options segment-routing mpls
------------------------------------

**Minimum user role:** operator

Segment routing is a mechanism for source-based packet forwarding, where the source router pre-selects a path to the destination and encodes it
in the packet header as an ordered list of segments. A segment is an instruction consisting of a flat unsigned 20-bit identifier (the segment ID - SID) and is encoded as an MPLS label.

The interior gateway protocol (IGP) distributes two types of segments: prefix SIDs and adjacency SIDs.
The segment routing configuration level allows you to configure the segment routing global block (SRGB) and local block (SRLB) that will be used by the router.
Every node in the domain will receive a node SID from the global block, and every adjacency formed by each router receives a SID from the router's local block.

To enter the global segment routing configuration level:

**Command syntax: segment-routing mpls**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- The SRGB and SRLB ranges affect the label pools assigned to other MPLS protocols such as RSVP, BGP, and LDP label pools.

- Notice the change in prompt.

- no command returns all segment-routing mpls configurations to their default state

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# segment-routing mpls
    dnRouter(cfg-routing-option-sr)#


**Removing Configuration**

To revert all segment-routing configurations to the default values:
::

    dnRouter(cfg-routing-option)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
```

## install-policy
```rst
routing-options table mpls-nh install-policy
--------------------------------------------

**Minimum user role:** operator

The install-policy enables to filter out destinations from being installed in the MPLS-NH table according to a predefined prefix-list using a policy. This prevents specific recursive routes from entering the tunnel, regardless of the originating protocol.
To set an import policy to apply on routes being installed in the routing table:

**Command syntax: install-policy [policy-name]**

**Command mode:** config

**Hierarchies**

- routing-options table mpls-nh

**Note**

- policy only support the following action: match ipv4|ipv6 prefix [prefix-list-name]

- policy rule apply regardless of originating protocol (RSVP, LDP, IGP-Shortcuts)

- no command removes the import policy

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| policy-name | The name of the policy that you want applied to installed routes.                | | string         | \-      |
|             | The policy only supports the following action: match ipv4|ipv6 prefix            | | length 1-255   |         |
|             | [prefix-list-name]. See policy match ip prefix.                                  |                  |         |
|             | The policy rule applies regardless of the originating protocol (RSVP, LDP,       |                  |         |
|             | IGP-shortcuts).                                                                  |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# table mpls-nh
    dnRouter(cfg-routing-option-mpls-nh)# install-policy MPLS_NH_IN


**Removing Configuration**

To remove the policy import:
::

    dnRouter(cfg-routing-option-mpls-nh)# no install-policy MPLS_NH_IN

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## install-policy
```rst
routing-options table mpls-nh-ipv6 install-policy
-------------------------------------------------

**Minimum user role:** operator

To set the import policy to apply on routes being installed in the routing table:


**Command syntax: install-policy [install-policy]**

**Command mode:** config

**Hierarchies**

- routing-options table mpls-nh-ipv6

**Note**

- policy only support the following action: match ipv4|ipv6 prefix [prefix-list-name]

- policy rule apply regardless of originating protocol

**Parameter table**

+----------------+---------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                               | Range            | Default |
+================+===========================================================================+==================+=========+
| install-policy | Set import policy to apply on routes being installed in the routing table | | string         | \-      |
|                |                                                                           | | length 1-255   |         |
+----------------+---------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# table mpls-nh-ipv6
    dnRouter(cfg-routing-option-mpls-nh-ipv6)# install-policy MPLS_NH_IPv6_POL


**Removing Configuration**

To remove the import policy:
::

    dnRouter(cfg-routing-option-mpls-nh-ipv6)# no install-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## table mpls-nh-ipv6
```rst
routing-options table mpls-nh-ipv6
----------------------------------

**Minimum user role:** operator

To enter the mpls-nh-ipv6 routing table configuration level:


**Command syntax: table mpls-nh-ipv6**

**Command mode:** config

**Hierarchies**

- routing-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# table mpls-nh-ipv6
    dnRouter(cfg-routing-option-mpls-nh-ipv6)#


**Removing Configuration**

To revert all table configurations to default:
::

    dnRouter(cfg-routing-option)# no table mpls-nh-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## table mpls-nh
```rst
routing-options table mpls-nh
-----------------------------

**Minimum user role:** operator

To enter configuration mode for the routing table to which you want to apply a policy (see explanation in routing-options):

**Command syntax: table mpls-nh**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Notice the change in prompt.

- no command returns all table configurations to their default state

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# table mpls-nh
    dnRouter(cfg-routing-option-mpls-nh)#


**Removing Configuration**

To revert all table configuration to the default values:
::

    dnRouter(cfg-routing-option)# no table mpls-nh

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
```

## throttle-link-state-changes
```rst
routing-options throttle-link-state-changes min-delay max-delay
---------------------------------------------------------------

**Minimum user role:** operator

Use this command to aggregate multiple different interface state-changes to a single event. The routing protocols will treat all state changes as if they occurred at once.

**Command syntax: throttle-link-state-changes min-delay [min-delay] max-delay [max-delay]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Require max-delay > min-delay

- Reconfiguring throttle-link-state-changes timers will immediately invoke any aggregated events. Any following interface state change will be delayed and aggregated according to new timers.

- no command min-delay & max-delay to their default values

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| min-delay | The minimal delay to be added for any interface state-change.                    | 0-5000  | 0       |
|           | A value of 0 will result in no aggregation taking place and the protocol will    |         |         |
|           | react immediately upon interface state change.                                   |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+
| max-delay | The maximum delay allowed for any interface state change.                        | 1-60000 | 2000    |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# throttle-link-state-changes min-delay 100 max-delay 2000
    dnRouter(cfg-routing-option)#


**Removing Configuration**

To revert min-delay and max-delay to their default value:
::

    dnRouter(cfg-routing-option)# no throttle-link-state-changes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

