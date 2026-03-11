system grpc
-----------

**Minimum user role:** operator

RPC-based telemetry streaming allows to export performance monitor counters and operational state parameters in a flexible and scalable way. Unlike traditional PM collection methods such as SNMP walk, gRPC based telemetry uses push method for delivering PM data from the router to the PM collector.

The gRPC network management interface (gNMI) allows gRPC-based telemetry collectors to manage gRPC-based telemetry exporters (e.g. routers). Specifically it allows the collector to specify which counters or operation items should be streamed by the router, at which mode (e.g. sampling, on-change) and with which DSCP marking.

To configure gRPC, enter gRPC configuration mode:

**Command syntax: grpc**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc
    dnRouter(cfg-system-grpc)#


**Removing Configuration**

To revert all gRPC configuration to default:
::

    dnRouter(cfg-system)# no grpc

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
