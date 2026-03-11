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
