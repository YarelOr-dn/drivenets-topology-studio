qos fabric-multicast ncp-to-fab max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The ncp-to-fab shaper ensures that the rate of unscheduled multicast traffic sent by each NCP core to the fabric is limited to the shaper rate.

To configure the rate of unscheduled multicast traffic:

**Command syntax: ncp-to-fab max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos fabric-multicast

**Parameter table**

+---------------------+------------------------------------------------+-----------+---------+
| Parameter           | Description                                    | Range     | Default |
+=====================+================================================+===========+=========+
| max-bandwidth-mbits | Per core fabric multicast shaper rate in mbits | 50-100000 | 20000   |
+---------------------+------------------------------------------------+-----------+---------+
| units               |                                                | | mbps    | mbps    |
|                     |                                                | | gbps    |         |
+---------------------+------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# fabric-multicast
    dnRouter(cfg-qos-fab-mcast)# ncp-to-fab max-bandwidth 10 Gbps


**Removing Configuration**

To revert the configured rate to the default:
::

    dnRouter(cfg-qos)# no fabric-multicast ncp-to-fab max-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
