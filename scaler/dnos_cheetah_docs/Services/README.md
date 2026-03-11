# DNOS Services Configuration Reference

This document contains the complete DNOS CLI Services configuration syntax from the official DriveNets documentation.

---

## ethernet-oam
```rst
services ethernet-oam
---------------------

**Minimum user role:** operator

To enter Ethernet OAM configuration mode:

**Command syntax: ethernet-oam**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-protocols)# ethernet-oam
    dnRouter(cfg-services-eoam)#


**Removing Configuration**

To remove the Ethernet OAM services:
::

    dnRouter(cfg-services)# no ethernet-oam

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## cache-events
```rst
services flow-monitoring cache-events limit threshold
-----------------------------------------------------

**Minimum user role:** operator

Exported flows are maintained in a flow-cache table on the NCP's local CPU. The size of the table is limited to 8,000,000 flows. When this table is full, flow entries will be aged out to make room for new flows.

You can set thresholds to generate system events notifying you that the table is about to reach its maximum limit.

To configure thresholds for generating cache system events:

In this example, the flow-cache table is configured to hold a maximum of 50,000 flow entries. When the table reaches 45,000 flows (90%), a system event is generated. When the table reaches 50,000 flows, older flows will be aged out to make room for new flows.

**Command syntax: cache-events limit [cache-events-limit] threshold [cache-events-threshold]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter              | Description                                                                      | Range     | Default |
+========================+==================================================================================+===========+=========+
| cache-events-limit     | The maximum number of allowed flows in the flow-cache table per NCP. When this   | 1-8000000 | 8000000 |
|                        | threshold is crossed, a system event is generated. When the flow-cache table is  |           |         |
|                        | full, flow entries will be aged out to make room for new entries.                |           |         |
+------------------------+----------------------------------------------------------------------------------+-----------+---------+
| cache-events-threshold | A percentage (%) of the limit to give you advance notice that the number of      | 0-100     | 75      |
|                        | flows in the flow-cache table for each NCP is approaching the limit. When this   |           |         |
|                        | threshold is crossed, a system event notification is generated. You will not be  |           |         |
|                        | notified again. If the flow-cache table size reaches 100%, flow entries will be  |           |         |
|                        | aged out to make room for new entries.                                           |           |         |
+------------------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# cache-events limit 50000 threshold 90


**Removing Configuration**

To revert to the default value::
::

    dnRouter(cfg-srv-port-mirroring)# no cache-events

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
```

## cache-rate-limit
```rst
services flow-monitoring cache-rate-limit
-----------------------------------------

**Minimum user role:** operator

You can limit the rate for exporting flow-records from the cache during flush or age-out events.

Any sampled packets beyond 200,000 pps will be disregarded by the control plane and counted as dropped. Note, that this limit is per exporter.

To configure the rate limit:

**Command syntax: cache-rate-limit [cache-rate-limit]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Parameter table**

+------------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter        | Description                                                                      | Range    | Default |
+==================+==================================================================================+==========+=========+
| cache-rate-limit | flow records export rate limit from flow cache table during flush or massive     | 0-200000 | 200000  |
|                  | ageout events                                                                    |          |         |
+------------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# cache-rate-limit 100000


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-port-mirroring)# no cache-rate-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
```

## flow-monitoring
```rst
services flow-monitoring
------------------------

**Minimum user role:** operator

Flow monitoring enables to track all the IP traffic flows in the network using the following main components:

-	**Exporter**: a network element (e.g. a router) that maintains a list of all active IP flows forwarded by the data plane. The exporter samples the data plane #traffic, classifies it based on 10-tuple flow classification which consist of source and destination IP, source and destination ports, protocol, ingress interface, TOS and MPLS labels 1-3. It maintains statistics on each active IP flow and exports them to a remote collector.
	DNOS serves as a flow monitoring exporter, monitoring IPv4 flows, IPv6 flows, IPv4/IPv6 over MPLS by sampling ingress traffic on monitored interfaces. The DNOS Flow Monitoring supports both IPFIX and NetFlow v9.

-	**Collector**: a remote device that maintains a list of all active flows traversing the network. It collects the active IP flow information from all exporters in the network and exposes it to clients for a variety of uses (e.g. DDOS detection and mitigation, monitoring traffic capacity, flows/traffic type mapping, peering reports, troubleshooting, etc.)

Follow these general steps to configure flow monitoring:

#. Enter the flow-monitoring configuration hierarchy.

#. Set global parameters:

	- Observation domain ID: This ID ensures that all system NCPs’ exported packets to the remote collector are monitored together. See "services flow-monitoring observation-domain-id".

	-	Cache-rate-limit – the rate limit for exporting flow records from the cache during flush or age out events. See "services flow-monitoring cache-rate-limit".

	-	 Cache-events - define thresholds for the flow-cache table, for generating system events. See "services flow-monitoring cache-events".

#. Configure flow-monitoring templates that define how to sample and maintain IP flows on the router. See "services flow-monitoring template".

#. Create exporter profiles that defines how to export IP flow information. See "services flow-monitoring exporter-profile".

#. Create sampler profiles that define how to sample the traffic forwarded to the local CPU. "services flow-monitoring sampler-profile".

#. Attach a flow-monitoring template (or optionally a sampler-profile) to an interface. See "interfaces flow-monitoring".

To enter the flow-monitoring configuration hierarchy:

**Command syntax: flow-monitoring**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)#


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-srv)# no flow-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
```

## observation-domain-id
```rst
services flow-monitoring observation-domain-id
----------------------------------------------

**Minimum user role:** operator

Flows are monitored on specific interfaces where traffic is sampled. In IPFIX, these are termed "observation points". An observation domain is the set of observation points for which traffic is sampled and aggregated for monitoring together. 

In DNOS, the entire "system" is a single “observation domain” and the system's sampled interfaces are the "observation points". By globally configuring an observation-domain ID, the packets exported to the remote collector are identified as belonging to the same observation domain even though each cluster NCP acts as an independent exporter maintaining the IP flow information separately.

The value of the observation-domain ID is configurable per system.

To configure the observation domain ID:

**Command syntax: observation-domain-id [observation-domain-id]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Note**
- Without an observation-domain ID, export packets will not be generated.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter             | Description                                                                      | Range        | Default |
+=======================+==================================================================================+==============+=========+
| observation-domain-id | A 32-bit identifier of the Observation Domain that is locally unique to the      | 1-4294967295 | 1       |
|                       | Exporting Process.  The Exporting Process uses the Observation Domain ID to      |              |         |
|                       | uniquely identify to the Collecting Process the Observation Domain that metered  |              |         |
|                       | the Flows.                                                                       |              |         |
+-----------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# observation-domain-id 560


**Removing Configuration**

To remove the observation-domain ID:
::

    dnRouter(cfg-srv-port-mirroring)# no observation-domain-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
services l2-cross-connect admin-state
-------------------------------------

**Minimum user role:** operator

To enable/disable an L2 cross-connect service:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services l2-cross-connect

**Parameter table**

+-------------+--------------------------------------+--------------+----------+
| Parameter   | Description                          | Range        | Default  |
+=============+======================================+==============+==========+
| admin-state | L2 cross-connect service admin-state | | enabled    | disabled |
|             |                                      | | disabled   |          |
+-------------+--------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-Boston-CRS
    dnRouter(cfg-srv-l2xc)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-srv-l2xc)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## interfaces
```rst
services l2-cross-connect interfaces
------------------------------------

**Minimum user role:** operator

To configure the endpoint members of the xConnect service:

**Command syntax: interfaces [first-interface] [second-interface]**

**Command mode:** config

**Hierarchies**

- services l2-cross-connect

**Note**

- The command is applicable to the following interface types:

	- Physical
  
  - Physical vlan

  - Bundle

	- Bundle vlan

- Only interfaces that are defined as L2-service can be defined as L2-cross-connect member interfaces.

- The same interface cannot be configured twice in the same L2-cross-connect service.

- The same interface cannot be configured twice in two different L2-cross-connect services.

- Replacing a configured L2-cross-connect interface requires configuring both interfaces again.

- Up to 4096 cross connects can be configured on the system collectively.

**Parameter table**

+------------------+--------------------------------+------------------+---------+
| Parameter        | Description                    | Range            | Default |
+==================+================================+==================+=========+
| first-interface  | Cross connect first interface  | | string         | \-      |
|                  |                                | | length 1-255   |         |
+------------------+--------------------------------+------------------+---------+
| second-interface | Cross connect second interface | | string         | \-      |
|                  |                                | | length 1-255   |         |
+------------------+--------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-Boston-CRS
    dnRouter(cfg-srv-l2xc)# interfaces bundle-100.2 bundle-200.3
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-LA-NVP
    dnRouter(cfg-srv-l2xc)# interfaces ge100-0/0/2.32 ge400-0/0/23.93


**Removing Configuration**

To remove the interface endpoints (both interfaces are removed):
::

    dnRouter(cfg-srv-l2xc)# no interfaces

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| TBD     | Extended support for physical and bundle interfaces |
+---------+-----------------------------------------------------+
| 12.0    | Command introduced                                  |
+---------+-----------------------------------------------------+
```

## l2-cross-connect
```rst
services l2-cross-connect
-------------------------

**Minimum user role:** operator


Circuit cross-connect allows to configure transparent connections between two circuits for the exchange of L2 data from one circuit to the other, and between two interfaces of the same type on the same router. This local switching connection works like a bridge domain with two bridge ports, where traffic enters from one endpoint of the local connection and leaves through the other.

To configure the l2 cross-connect:

#. Create an L2 cross-connect service.

#. Configure the two endpoints for the xConnect service. See "services l2-cross-connect interfaces".

#. Enable the xConnect service. See "services l2-cross-connect admin-state".

To create an L2 cross-connect service:

**Command syntax: l2-cross-connect [l2-cross-connect]**

**Command mode:** config

**Hierarchies**

- services

**Note**

- You can create up to 4096 xConnect services per system.

**Parameter table**

+------------------+---------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                   | Range            | Default |
+==================+===============================================================+==================+=========+
| l2-cross-connect | Enters the context of L2 cross connect service configuration. | | string         | \-      |
|                  |                                                               | | length 1-255   |         |
+------------------+---------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-Boston-CRS
    dnRouter(cfg-srv-l2xc)#


**Removing Configuration**

To delete a certain l2-cross-connect:
::

    dnRouter(cfg-srv)# no l2-cross-connect XC-To-Boston-CRS

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
```

## mpls-oam
```rst
services mpls-oam
-----------------

**Minimum user role:** operator


MPLS Operations, Administration, and Maintenance (OAM) is used for detecting failures in the datapath (e.g. black holes and misrouting). MPLS OAM provides proactive and on-demand troubleshooting tools for MPLS Networks and services by measuring the MPLS network and diagnosing defects that cannot otherwise be detected.

In addition to detecting operational failures, MPLS OAM can also be used for accounting and performance measurement of the MPLS network.

While Internet Control Message Protocol (ICMP) ping and traceroute can assist in diagnosing the root cause of a forwarding failure, they might not detect LSP failures because an ICMP packet can be forwarded via an IP path to the destination when an LSP breakage occurs.

MPLS LSP ping and traceroute are better suited for identifying LSP breakages because:

-	An MPLS echo request packet cannot be forwarded via an IP path because its IP Time to Live (TTL) is set to 1 and its IP destination address field is set to a 127.x.y.z/8 address.

-	The Forwarding Equivalence Class (FEC) being checked is not stored in the IP destination address field (as is the case of ICMP).

-	An LSP can take multiple paths from ingress to egress. This particularly occurs with Equal Cost Multipath (ECMP). The LSP traceroute command can trace all possible paths to an LSP node.

The MPLS OAM includes the following set of protocols for effectively detecting problems in the MPLS network:

-	MPLS LSP ping - checks connectivity of LSPs: An MPLS echo packet is sent through an LSP to validate it. When the packet reaches the end of the path, it is sent to the control plane of the egress LSR. The egress LSR then verifies whether it is indeed an egress for the FEC. 

-	MPLS traceroute - used for hop-by-hop fault localization and/or path tracing: A packet is sent to the control plane of each transit LSR. The transit LSR performs various checks to confirm that it is indeed a transit LSR for this path; this LSR also returns additional information that helps check the control plane against the data plane.

To configure MPLS OAM, enter the services OAM configuration hierarchy:

**Command syntax: mpls-oam**

**Command mode:** config

**Hierarchies**

- services

**Note**

- MPLS OAM supports RSVP tunnels and BGP-LU LSPs only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-protocols)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)#


**Removing Configuration**

To revert all MPLS-OAM parameters to their default values and remove all configured profiles:
::

    dnRouter(cfg-srv)# no mpls-oam

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## performance-monitoring
```rst
services performance-monitoring
-------------------------------

**Minimum user role:** operator

DNOS supports performance monitoring.

**Command syntax: performance-monitoring**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)#


**Removing Configuration**

To remove the performance monitoring configurations:
::

    dnRouter(cfg-srv)# no performance-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

## port-mirroring
```rst
services port-mirroring
-----------------------

**Minimum user role:** operator

Local Port Mirroring, which is also known as Switched Port Analyzer (SPAN), is a method of monitoring network traffic by sending copies of packets from a selected port on a device, or multiple ports, or entire VLAN to another designated local or remote port. The copied network traffic can then be analyzed for performance, troubleshooting, security or other purposes. The port mirroring doesn't affect the traffic flow on the source ports, and allows the mirrored traffic to be sent to a destination port.

To enter the port mirroring configuration hierarchy:

**Command syntax: port-mirroring**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)#


**Removing Configuration**

To revert the port mirroring configuration to the default values:
::

    dnRouter(cfg-srv)# no port-mirroring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## service-activation-testing
```rst
services service-activation-testing
-----------------------------------

**Minimum user role:** operator

To enter the service-activation-testing configuration hierarchy:

**Command syntax: service-activation-testing**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)#


**Removing Configuration**

To revert all service-activation-testing configuration to default:
::

    dnRouter(cfg-srv)# no service-activation-testing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## services overview
```rst
Services Overview
-----------------
To enter services configuration mode:

::

	dnRouter(cfg)# services
	dnRouter(cfg-srv)#

**Command mode:** services configuration

**Note**

- Notice the change in prompt from dnRouter(cfg)# to dnRouter(cfg-srv)# (services configuration mode).

You can configure the following services:

Two Way Active Measurement Protocol (TWAMP)

services mpls-oam

Flow Monitoring

Local Port Mirroring

services l2-cross-connect```

## services
```rst
services
--------

**Minimum user role:** operator

Enter the services configuration hierarchy.

**Command syntax: services**

**Command mode:** config

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)#


**Removing Configuration**

To remove services:
::

    dnRouter(cfg)# no services

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
```

## simple-twamp
```rst
services simple-twamp
---------------------

**Minimum user role:** operator

The Simple Two Way Active Measurement Protocol (STAMP) is an open protocol. An open protocol allows different vendor equipment to work together without any additional proprietary equipment. STAMP is used as a lightweight implementation of the TWAMP protocol to measure network performance between two devices that support the TWAMP-Test protocol by sending probe/data test packets between a session sender and a session reflector, without the need for TWAMP-Control protocol which makes it more scalable.

Unlike standard track TWAMP, Simple TWAMP - Test protocol - sends packets between two devices. This runs between session sender and session reflector

The Simple TWAMP protocol sessions require two end-points with the following roles:

	-	Session-sender - creates TWAMP test packets which are sent to the session-reflector and collects and analyzes packets received.

	-	Session-reflector - returns a test packet when a packet is received from a session-sender. No information is stored but sent back to the session-sender.

DriveNets Simple TWAMP implementation supports both roles of Session-Sender and Session-Reflector:

- As a Session-Reflector DriveNets devices only responds to sessions. This means no result or history information such as statistics are retained other than the counter which displays the reflected packets. The counters can be seen by running the command show services performance-monitoring sessions.

- As a Session-Sender DriveNets aggregates all of the received measurement packets from all configured devices and analyzes the results for quality of data sessions, delay, jitter, or packet loss.

Simple TWAMP features include:

-	DSCP Marking - supports Class-of-Service (CoS) in two modes, either the DSCP value of reflected packets is remarked per configuration or it can be reflected with the same DSCP value received by the Session-Sender.

-	Timestamps - Two timestamps are included in the reply message. The first is the time the packet is received on the ingress interface on the NCP and the second time-stamp refers to the time the packet leaves the NCP on the egress interface. In a standalone scheme the reply is transmitted from the same NCP, but in a cluster , the reply could be transmitted from another NCP within the cluster. The timestamps use the internal NTP clock within the system.

-	Scale - support up to 2K simultaneous test sessions, which can be from the same Session-Sender or different Session-Senders.


To enter the Simple TWAMP configuration hierarchy:

**Command syntax: simple-twamp**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)#


**Removing Configuration**

To revert all Simple TWAMP configuration to default:
::

    dnRouter(cfg-srv)# no simple-twamp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
services twamp admin-state
--------------------------

**Minimum user role:** operator

To enable or disable the TWAMP service:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services twamp

**Parameter table**

+-------------+-----------------------------------------+--------------+----------+
| Parameter   | Description                             | Range        | Default  |
+=============+=========================================+==============+==========+
| admin-state | The desired state of the TWAMP service. | | enabled    | disabled |
|             |                                         | | disabled   |          |
+-------------+-----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# admin-state enabled
    dnRouter(cfg-srv-twamp)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-twamp)# no admin-state

**Command History**

+---------+-------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                    |
+=========+=================================================================================================+
| 5.1.0   | Command introduced                                                                              |
+---------+-------------------------------------------------------------------------------------------------+
| 6.0     | Updated command services TWAMP mode changed to services TWAMP admin-state Applied new hierarchy |
+---------+-------------------------------------------------------------------------------------------------+
| 9.0     | TWAMP not supported                                                                             |
+---------+-------------------------------------------------------------------------------------------------+
| 11.2    | Command re-introduced                                                                           |
+---------+-------------------------------------------------------------------------------------------------+
```

## data-destination-port
```rst
services twamp data-destination-port
------------------------------------

**Minimum user role:** operator

The destination port is the incoming UDP port that the data connection uses to send data packets to the TWAMP server.

By default, the UDP data destination port range is between 10000-20000. You can configure a smaller port range within this range.

To configure the destination port range:

**Command syntax: data-destination-port [data-dst-ports]**

**Command mode:** config

**Hierarchies**

- services twamp

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                      | Range       | Default |
+================+==================================================================================+=============+=========+
| data-dst-ports | Minimal value of the UDP destination port range. Maximal value of the UDP        | 10000-20000 | 10000   |
|                | destination port range.                                                          |             |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# data-destination-port 10000-11000
    dnRouter(cfg-srv-twamp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-twamp)# no data-destination-port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## data-source-port
```rst
services twamp data-source-port
-------------------------------

**Minimum user role:** operator

The source port is the incoming UDP port that the data connection uses to send data packets to the TWAMP server.

By default, the UDP data source port range is between 10000-20000. You can configure a smaller port range within this range.

To configure the source port range:

**Command syntax: data-source-port [data-src-ports]**

**Command mode:** config

**Hierarchies**

- services twamp

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                      | Range       | Default |
+================+==================================================================================+=============+=========+
| data-src-ports | Minimal value of the UDP source port range. Maximal value of the UDP source port | 10000-20000 | 10000   |
|                | range.                                                                           |             |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# data-source-port 10000-11000
    dnRouter(cfg-srv-twamp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-twamp)# no data-source-port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## twamp
```rst
services twamp
--------------

**Minimum user role:** operator

Two Way Active Measurement Protocol (TWAMP) is an open protocol. An open protocol allows different vendor equipment to work together without any additional proprietary equipment. TWAMP is used to measure network performance between two devices that support the TWAMP protocol by sending probe/data test packets between the devices. TWAMP uses a client-server architecture. There are two protocols used within TWAMP:

-	TWAMP-Control protocol - starts and ends test sessions. This runs between client and server

-	TWAMP - Test protocol - sends packets between two devices. This runs between session sender and session reflector

The TWAMP protocol sessions require two end-points with the following roles:

-	TWAMP client (typically used also as a session-sender)

	-	Control-client initiates, starts, and stops the TWAMP test sessions towards the TWAMP server.

	-	Session-sender creates TWAMP test packets which are sent to the session-reflector (TWAMP server) and collects and analyzes packets received.

-	TWAMP server, each NCE (typically used also as a session-reflector)

	-	Session-reflector returns a test packet when a packet is received from a session-sender. No information is stored but sent back to the client.

	-	Server manages one or more sessions with the TWAMP control-client and listens for control messages on a known TCP port.

DriveNets TWAMP implementation supports TWAMP clients, with the DriveNets NCE as the TWAMP server and Session-Reflector. As DriveNets TWAMP is in server mode, it only responds to sessions. This means no result or history information such as statistics are retained other than the counters which display the RX and TX packets. The counters can be seen by running the command show services twamp sessions in configuration mode. The TWAMP client aggregates all of the received measurement packets from all configured devices and analyzes the results for quality of control traffic, data sessions, jitter, or packet loss. TWAMP features include:

-	Test Packet Frequency - DriveNets TWAMP has a test packet frequency of 100 milliseconds continuously. The statistical distribution packets have an average inter-arrival delay of 3.3 milliseconds.

-	 DSCP Marking - supports, Class-of-Service (CoS), the DSCP value is the same as received by the client messages. This applies to both control packets and data packets.

-	Timestamps - Two timestamps are included in the reply message. The first is the time the packet is received on the ingress interface on the NCP and the second time-stamp refers to the time the packet leaves the NCP on the egress interface. In a standalone scheme the reply is transmitted from the same NCP, but in a cluster , the reply could be transmitted from another NCP within the cluster. The timestamps use the internal NTP clock within the system.

-	Scale- support up to ten simultaneous control sessions, which can be from the same client or different clients. Each control session can support up to ten simultaneous data sessions. This means that in total there can be up to 100 simultaneous data sessions.

To configure the the TWAMP responder (session-reflector) parameters, enter TWAMP configuration hierarchy:

**Command syntax: twamp**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)#


**Removing Configuration**

To revert all TWAMP configuration to default:
::

    dnRouter(cfg-srv)# no twamp

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 11.2    | Command introduced     |
+---------+------------------------+
| 17.0    | Added support for IPv6 |
+---------+------------------------+
```

