services flow-monitoring exporter-profile data-template-timeout
---------------------------------------------------------------

**Minimum user role:** operator

The data-template is metadata that defines which parameters are sent for describing IP flows. The data-template-timeout defines how often the flow exporter will retransmit the data-template.

To configure the data-template timeout:

**Command syntax: data-template-timeout [data-template-timeout]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter             | Description                                                                      | Range   | Default |
+=======================+==================================================================================+=========+=========+
| data-template-timeout | Sets time after which Templates are resent in the UDP Transport Session. Note    | 0-86400 | 1800    |
|                       | that the configured lifetime MUST be adapted to the templateLifeTime parameter   |         |         |
|                       | value at the receiving Collecting Process. Note that this parameter corresponds  |         |         |
|                       | to flow-monitoringTransportSessionTemplateRefreshTimeout in the Flow-monitoring  |         |         |
|                       | MIB module.                                                                      |         |         |
+-----------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# data-template-timeout 60


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no data-template-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
