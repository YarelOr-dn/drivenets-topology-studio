services flow-monitoring exporter-profile packet-length
-------------------------------------------------------

**Minimum user role:** operator

Set the maximum IP packet size for the export packet sent towards the collector.

To configure the exporter packet length:

**Command syntax: packet-length [packet-length]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Note**

- The packet-length is L3 MTU including the IPv4/IPv6 header.

- If the packet size exceeds the egress interface MTU size, the flow monitoring exported traffic will be dropped.

**Parameter table**

+---------------+-----------------------------+----------+---------+
| Parameter     | Description                 | Range    | Default |
+===============+=============================+==========+=========+
| packet-length | Export packets maximum size | 522-9286 | 1468    |
+---------------+-----------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# packet-length 1000


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no packet-length

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
