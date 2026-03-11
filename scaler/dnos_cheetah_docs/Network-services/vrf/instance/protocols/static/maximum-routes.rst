network-services vrf instance protocols static maximum-routes threshold
-----------------------------------------------------------------------

**Minimum user role:** operator

To configure the system maximum static route limit and threshold: The parameters will be used to invoke a system-event when the limit and threshold are crossed.

**Command syntax: maximum-routes [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static
- protocols static

**Note**

- The thresholds are for generating system-events only.

- The thresholds are for IPv4 and IPv6 routes combined.

- When the threshold is cleared, a single system-event notification is generated.

- There is no limitation on the number of static routes that you can configure.

**Parameter table**

+-----------+---------------------------------------+---------+---------+
| Parameter | Description                           | Range   | Default |
+===========+=======================================+=========+=========+
| maximum   | Maximum Number of Static Routes       | 1-65535 | 2000    |
+-----------+---------------------------------------+---------+---------+
| threshold | Threshold Percentage for Static Route | 1-100   | 75      |
+-----------+---------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# maximum-routes 2000 threshold 70
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# maximum-routes 2000 threshold 70


**Removing Configuration**

To revert maximum & threshold to default:
::

    dnRouter(cfg-inst-protocols-static)# no maximum-routes

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
