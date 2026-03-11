services flow-monitoring template exporter-profile
--------------------------------------------------

**Minimum user role:** operator

The exporter profile includes a single collector destination to which IP flow information is exported. The flow-monitoring template references up to 3 existing exporter profiles.

To configure the exporter profile:

**Command syntax: exporter-profile [export-profile]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring template

**Parameter table**

+----------------+------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                            | Range            | Default |
+================+========================================================================+==================+=========+
| export-profile | defines the list of exporters for the flows collected by the template. | | string         | \-      |
|                |                                                                        | | length 1-255   |         |
+----------------+------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# template myTemplate
    dnRouter(cfg-srv-flow-monitoring-myTemplate)# exporter-profile myExporter,myExporter2


**Removing Configuration**

To remove all exporter profiles from the template:
::

    dnRouter(cfg-srv-flow-monitoring-myTemplate)# no exporter-profile

To remove a specific profile from the template:
::

    dnRouter(cfg-srv-flow-monitoring-myTemplate)# no exporter-profile myExporter

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
