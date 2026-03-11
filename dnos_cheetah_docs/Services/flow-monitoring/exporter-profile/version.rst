services flow-monitoring exporter-profile version
-------------------------------------------------

**Minimum user role:** operator

Exported records are encapsulated and exported as either Netflow v9 or IPFix format.

To configure the version (i.e. encapsulation format):

**Command syntax: version [version]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Parameter table**

+-----------+-------------------------+-----------+---------+
| Parameter | Description             | Range     | Default |
+===========+=========================+===========+=========+
| version   | Export protocol version | | v9      | ipfix   |
|           |                         | | ipfix   |         |
+-----------+-------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# version ipfix


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no version

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
