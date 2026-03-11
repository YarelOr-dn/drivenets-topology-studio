services flow-monitoring exporter-profile options timeout
---------------------------------------------------------

**Minimum user role:** operator

Options enable to send additional metadata to the collector. These are:

-	Sampler-table - a list of the configured sample profiles configured

-	Interface-table - a list of the router interfaces

-	VRF-table - a list of the configured VRFs

The options are sent periodically in a metadata collection on the exported IP flows.

To configure the options-template:

According to the above example, the exporter will send the sampler-table every 60 seconds and the interface-table every 50 seconds, regardless of whether or not there are any statistics information on the forwarded IP-flows.

**Command syntax: options [option] timeout [options-timeout]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------------------+---------+
| Parameter       | Description                                                                      | Range               | Default |
+=================+==================================================================================+=====================+=========+
| option          | Reference to configured name of the option                                       | | sampler-table     | \-      |
|                 |                                                                                  | | interface-table   |         |
|                 |                                                                                  | | vrf-table         |         |
+-----------------+----------------------------------------------------------------------------------+---------------------+---------+
| options-timeout | Time interval for periodic export of the options data.  If set to zero, the      | 0-86400             | 1800    |
|                 | export is triggered when the options data has changed.                           |                     |         |
+-----------------+----------------------------------------------------------------------------------+---------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# options sampler-table timeout 60
    dnRouter(cfg-srv-flow-monitoring-myExporter)# options interface-table timeout 50


**Removing Configuration**

To remove the flow-export options:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no options

To remove a specific option from the options-template:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no options sampler-table

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
