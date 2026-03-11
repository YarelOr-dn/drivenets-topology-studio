system telemetry
----------------

**Minimum user role:** operator


"Dial-out telemetry enables the transmission of performance monitoring counters and operational state parameters in a real-time and scalable manner. Unlike conventional performance monitoring gathering methods like SNMP polling, dial-out telemetry employs an outbound approach to transport performance monitoring  data from the router, to the PM collector.

With dial-out telemetry, the collector is given the ability to specify precisely which metrics or operational items should be streamed by the device. Furthermore, it allows the determination of a specific destination for data transmission. Dial-out telemetry also caters to the control of connection parameters such as the Virtual Routing and Forwarding (VRF) and the source interface from which data is sent. A multitude of other parameters also exist, which provides granular control over the data transmission and connectivity. To configure dial-out telemetry, enter telemetry configuration mode:"

**Command syntax: telemetry**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)#


**Removing Configuration**

To revert all dial-out telemetry configuration to default:
::

    dnRouter(cfg-system)# no telemetry

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
