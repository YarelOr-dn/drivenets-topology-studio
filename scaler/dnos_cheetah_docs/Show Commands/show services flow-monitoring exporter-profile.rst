show services flow-monitoring exporter-profile
----------------------------------------------

**Minimum user role:** viewer

The exporter profile includes a single collector destination to which IP flow information is exported.

To show a flow-monitoring exporter-profile configuration:

**Command syntax: show services flow-monitoring exporter-profile[exporter-profile]**

**Command mode:** operational



**Parameter table**

+------------------+-----------------------------------------------+-------+---------+
| Parameter        | Description                                   | Range | Default |
+==================+===============================================+=======+=========+
| exporter-profile | Any existing flow-monitoring exporter-profile |       | \-      |
+------------------+-----------------------------------------------+-------+---------+

**Example**
::

	dnRouter# show services flow-monitoring exporter-profile myExporter
	   Export-profile name: myExporter
	   Version: v9
	   Source IP Address: 200.1.1.20
	   Transport Protocol: udp
	   Packet length: 1468
	   Collector IP Address: 145.10.23.81
	   Collector Transport Port: 30020
	   DSCP value: 0
	   Max-packet size: 1500 Bytes
	   Options:
	       - Interface-table, timeout: 30
	       - Sampler-table, timeout: 30
	   Timeout parameters:
	       - Data Template Timeout: 60 sec
	       - Options Template Timeout: 180 sec
	

.. **Help line:** show flow-monitoring exporter-profile configuration.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


