services flow-monitoring exporter-profile options-template-timeout
------------------------------------------------------------------

**Minimum user role:** operator

The options-template is metadata that defines the parameters that are sent for each option and is sent periodically to the collector.

To configure how often the exporter will retransmit the options-template:

**Command syntax: options-template-timeout [options-template-timeout]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter                | Description                                                                      | Range   | Default |
+==========================+==================================================================================+=========+=========+
| options-template-timeout | Sets time after which Options Templates are resent in the UDP Transport Session. | 0-86400 | 1800    |
|                          | Note that the configured lifetime MUST be adapted to the optionsTemplateLifeTime |         |         |
|                          | parameter value at the receiving Collecting Process. Note that this parameter    |         |         |
|                          | corresponds to flow-monitoringTransportSessionOptionsTemplateRefreshTimeout in   |         |         |
|                          | the Flow-monitoring MIB module.                                                  |         |         |
+--------------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# options-template-timeout 60


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no options-template-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
