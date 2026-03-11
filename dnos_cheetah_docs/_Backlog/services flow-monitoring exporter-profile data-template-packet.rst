services flow-monitoring exporter-profile data-template-packet - deprecated
---------------------------------------------------------------------------

**Command syntax: data-template-packet [packet]**

**Description:** configuring data-template-packet for flow-monitoring exporter. I.e. how many export packets can be sent by flow-exporter without retransmit data-template-set.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# flow-monitoring
	dnRouter(cfg-srv-flow-monitoring)# exporter-profile myExporter
	dnRouter(cfg-srv-flow-monitoring-myExporter)# data-template-packet 10

	dnRouter(cfg-srv-flow-monitoring-myExporter)# no data-template-packet


**Command mode:** config

**TACACS role:** operator

**Note:**

no command remove the template-data-packet configuration.

**Help line:** configure data-template-packet for flow-exporter.

**Parameter table:**

+-----------+---------------------------+---------------+
| Parameter | Values                    | Default value |
+===========+===========================+===============+
| Packet    | 1-4,294,967,295 [packets] |               |
+-----------+---------------------------+---------------+
