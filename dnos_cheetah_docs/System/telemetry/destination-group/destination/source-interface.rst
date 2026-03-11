system telemetry destination-group destination port source-interface
--------------------------------------------------------------------

**Minimum user role:** operator

To configure a source-interface for a telemetry destination:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system telemetry destination-group destination port

**Note**
- "This command is applicable to the following interfaces: physical interfaces, logical interfaces (sub-interfaces), bundle interfaces, bundle sub-interfaces, and loopback interfaces."
- "The source-interface must have an IP address configured as the packets sent include the source-interface IP address."
- "By default, the global configuration for the source interface uses "system inband source-interface" for VRF default and "network-services vrf management-plane source-interface" for non-default in-band management VRFs."
- "If the source-interface under destination is specified it overrides the global VRF source-interface configuration for that server."
- "The source-interface must be associated with the same VRF as the destination."
- "You cannot modify source-interfaces for mgmt0 VRFs."


**Parameter table**

+------------------+--------------------------------------------+------------------+---------+
| Parameter        | Description                                | Range            | Default |
+==================+============================================+==================+=========+
| source-interface | The source interface for the subscription. | | string         | \-      |
|                  |                                            | | length 1-255   |         |
+------------------+--------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry destination-group lab
    dnRouter(cfg-system-telemetry-destgrp)# destination ip 100.0.0.2 port 5000
    dnRouter(cfg-telemetry-dstgrp-dest)# source-interface bundle-1.1


**Removing Configuration**

To revert source-interface to default:
::

    dnRouter(cfg-telemetry-dstgrp-dest)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
