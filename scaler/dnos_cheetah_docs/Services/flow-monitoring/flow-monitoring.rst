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
