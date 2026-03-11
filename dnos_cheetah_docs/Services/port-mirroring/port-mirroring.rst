services port-mirroring
-----------------------

**Minimum user role:** operator

Local Port Mirroring, which is also known as Switched Port Analyzer (SPAN), is a method of monitoring network traffic by sending copies of packets from a selected port on a device, or multiple ports, or entire VLAN to another designated local or remote port. The copied network traffic can then be analyzed for performance, troubleshooting, security or other purposes. The port mirroring doesn't affect the traffic flow on the source ports, and allows the mirrored traffic to be sent to a destination port.

To enter the port mirroring configuration hierarchy:

**Command syntax: port-mirroring**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)#


**Removing Configuration**

To revert the port mirroring configuration to the default values:
::

    dnRouter(cfg-srv)# no port-mirroring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
