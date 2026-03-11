services flow-monitoring exporter-profile
-----------------------------------------

**Minimum user role:** operator

The exporter profile includes a single collector destination to which IP flow information is exported. The profile includes a list of parameters defining how to export flow records. You can configure up to 4 exporter profiles per system.

To create an exporter profile and enter its configuration hierarchy:

**Command syntax: exporter-profile [export-profile]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Parameter table**

+----------------+--------------------------------------------------------+------------------+---------+
| Parameter      | Description                                            | Range            | Default |
+================+========================================================+==================+=========+
| export-profile | Reference to the configured name of the export-profile | | string         | \-      |
|                |                                                        | | length 1-255   |         |
+----------------+--------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)#


**Removing Configuration**

You cannot delete an exporter profile if it is used by a flow-monitoring template. Remove the profile from the template before deleting the profile.
::

    dnRouter(cfg-srv-flow-monitoring)# no exporter-profile myExporter

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.4    | Command introduced                                 |
+---------+----------------------------------------------------+
| 13.1    | Increased support of exporter profiles from 3 to 4 |
+---------+----------------------------------------------------+
