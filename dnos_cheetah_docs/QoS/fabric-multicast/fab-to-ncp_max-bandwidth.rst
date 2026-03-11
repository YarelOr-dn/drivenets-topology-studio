qos fabric-multicast fab-to-ncp max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The fab-to-ncp shaper ensures that the maximum rate of multicast traffic sent from the fabric to each NCP, through the recycle interface, is limited to the shaper rate. The limit protects against aggregate multicast traffic overwhelming or competing with incoming traffic on the egress NCP.

To configure the rate of the fabric multicast traffic:

**Command syntax: fab-to-ncp max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos fabric-multicast

**Note**

- The recycle port interface and calendar shaper are always set to 120 Gbps.

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
    dnRouter(cfg-qos-fab-mcast)# fab-to-ncp max-bandwidth 10 Gbps


**Removing Configuration**

To revert the configured rate to the default:
::

    dnRouter(cfg-qos)# no fabric-multicast fab-to-ncp max-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
