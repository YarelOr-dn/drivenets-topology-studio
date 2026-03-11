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
