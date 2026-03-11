services flow-monitoring exporter-profile collector ip-address
--------------------------------------------------------------

**Minimum user role:** operator

The collector is a remote device that maintains a list of all active flows traversing the network. It collects the active IP flow information from all exporters in the network and exposes it to clients for a variety of uses (e.g. DDOS detection and mitigation, monitoring traffic capacity, flows/traffic type mapping, peering reports, troubleshooting, etc.).

You can configure only one collector per exporter profile.

To configure a collector to which to export flow records:

**Command syntax: collector ip-address [destination-address]** transport [transport] port [destination-port] class-of-service [class-of-service] ttl [ttl]

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter           | Description                                                                      | Range        | Default |
+=====================+==================================================================================+==============+=========+
| destination-address | IP address of the Collection Process to which Flow-monitoring Messages are sent. | | A.B.C.D    | \-      |
|                     |                                                                                  | | X:X::X:X   |         |
+---------------------+----------------------------------------------------------------------------------+--------------+---------+
| transport           | L4 trasport protocol for export packets                                          | udp          | udp     |
+---------------------+----------------------------------------------------------------------------------+--------------+---------+
| destination-port    | If not configured by the user, the Monitoring Device uses the default port       | 1024-65535   | 4739    |
|                     | number for Flow-monitoring, which is 4739 without TLS or DTLS.                   |              |         |
+---------------------+----------------------------------------------------------------------------------+--------------+---------+
| class-of-service    | This parameter specifies the dscp of IP packets sent to the Collector.           | 0-56         | 0       |
+---------------------+----------------------------------------------------------------------------------+--------------+---------+
| ttl                 | TTL value for generated export packet                                            | 1-255        | 255     |
+---------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# collector ip-address 212.51.8.17 transport udp port 2055 class-of-service 16 ttl 1


**Removing Configuration**

To remove the collector configuration:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no collector

To revert an optional parameter to its default value:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no collector ip-address 212.51.8.17 class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
