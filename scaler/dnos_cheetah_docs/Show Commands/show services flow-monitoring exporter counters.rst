show services flow-monitoring exporter counters
-----------------------------------------------

**Minimum user role:** viewer

To display counters for flow-monitoring exported flows:



**Command syntax: show services flow-monitoring exporter counters ncp [ncp-id]** exporter-profile [exporter-profile]

**Command mode:** operational

.. 
	**Internal Note**

	- "show services flow-monitoring exporter counters ncp" without expoert-profile parameter, shows exporter counters for all exporters on the specifi NCPs.

**Parameter table**

+------------------+---------------------------------------------------+-----------------------+---------+
| Parameter        | Description                                       | Range                 | Default |
+==================+===================================================+=======================+=========+
| ncp              | Any existing ncp-id                               |                       | \-      |
+------------------+---------------------------------------------------+-----------------------+---------+
| exporter-profile | The ID number of the exported information element | According to RFC 7011 |         |
+------------------+---------------------------------------------------+-----------------------+---------+

The output parameters include the following:

+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Parameter                  | Description                                                                                                             |
+============================+=========================================================================================================================+
| Collector                  | Destination IP address and L4 port of the export packets that are sent by the exporter                                  |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Used by template           | List of flow-monitoring templates that use this exporter                                                                |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Source                     | Source IP address and L4 port of the export packets that are sent by exporter                                           |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Version                    | Flow records exporting protocol: v9 (netflow) / ipfix                                                                   |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported IPv4 Flows        | Number of exported flow records that describe IPv4 flows                                                                |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported IPv6 Flows        | Number of exported flow records that describe IPv6 flows                                                                |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported IPv4oMPLS Flows   | Number of exported flow records that describe IPv4oMPLS flows                                                           |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported IPv6oMPLS Flows   | Number of exported flow records that describe IPv6oMPLS flows                                                           |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported Data Templates    | Number of exported data templates                                                                                       |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported Option Templates  | Number of exported option templates                                                                                     |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exported Packets           | Total number of exported packets (including flow records, data and option templates)                                    |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Average export flow rate   | Average export rate of flow records per second                                                                          |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Average export packet rate | Average export rate of packets per second (including flow records, data and option templates)                           |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Average export bit rate    | Average export rate of bits per second (including flow records, data and option templates)                              |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Discarded Flows            | Number of flow records that were discarded since they cannot be exported due to exceeded export rate (cache-rate-limit) |
+----------------------------+-------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show services flow-monitoring exporter counters ncp 5
	Flow export statistics for myExporter1
	  Collector: 121.43.11.201, port 4739
	  Used by Templates: myTemplateIPv4, myTemplateIPv6, myTemplateIPv4oMPLS
	  Source: 10.1.1.1, port 21042
	  Version 9 flow records
	  Exported IPv4 Flows: 0 
	  Exported IPv6 Flows: 0 
	  Exported IPv4oMPLS Flows: 0 
	  Exported IPv6oMPLS Flows: 0 
	  Exported Data Templates: 0
	  Exported Option Templates: 0 
	  Exported Packets: 0 (0 Bytes)
	  Average export rate: 0 flows per second, 0 packets per second, 0 bps
	  Discarded Flows: 0
	  
	Flow export statistics for myExporter2  
	  Collector: 121.43.11.201, port 4739
	  Used by Templates: myTemplateIPv4, myTemplateIPv6, myTemplateIPv4oMPLS
	  Source: 10.1.1.1, port 21042
	  Version 9 flow records
	  Exported IPv4 Flows: 0 
	  Exported IPv6 Flows: 0 
	  Exported IPv4oMPLS Flows: 0 
	  Exported IPv6oMPLS Flows: 0 
	  Exported Data Templates: 0
	  Exported Option Templates: 0 
	  Exported Packets: 0 (0 Bytes)
	  Average export rate: 0 flows per second, 0 packets per second, 0 bps
	  Discarded Flows: 0
	
	dnRouter# show services flow-monitoring exporter counters ncp 2 exporter-profile myExporter3 
	Flow export statistics for myExporter3
	  Collector: 121.43.11.201, port 4739
	  Used by Templates: myTemplateIPv4, myTemplateIPv6, myTemplateIPv4oMPLS
	  Source: 10.1.1.1, port 21042
	  Version 9 flow records
	  Exported IPv4 Flows: 0 
	  Exported IPv6 Flows: 0 
	  Exported IPv4oMPLS Flows: 0 
	  Exported IPv6oMPLS Flows: 0 
	  Exported Data Templates: 0
	  Exported Option Templates: 0 
	  Exported Packets: 0 (0 Bytes)
	  Average export rate: 0 flows per second, 0 packets per second, 0 bps
	  Discarded Flows: 0
	

.. **Help line:** show counters for exported flows by flow-monitoring.

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 11.4    | Command introduced                            |
+---------+-----------------------------------------------+
| 13.0    | Updated parameter and parameter output tables |
+---------+-----------------------------------------------+


