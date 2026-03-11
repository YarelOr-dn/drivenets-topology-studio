services flow-monitoring exporter-profile source-interface
----------------------------------------------------------

**Minimum user role:** operator

Optionally, you can set a source-address for exported packets to be any default VRF interface. If you don't set a source interface or the configured source interface has no IP address, the "system in-band-management source-interface" will be used.

To configure the source-interface:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring exporter-profile

**Note**
- The source-ip is derived from the configured source-interface.

- If the source-interface has multiple IP addresses, a primary address will be used.

**Parameter table**

+------------------+---------------------------------------------------------+-------+---------+
| Parameter        | Description                                             | Range | Default |
+==================+=========================================================+=======+=========+
| source-interface | source interface for sending netflow/IPFIX packets from | \-    | \-      |
+------------------+---------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
    dnRouter(cfg-srv-flow-monitoring-myExporter)# source-interface bundle-0


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myExporter)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
