qos vrf-redirect vrf-redirect-0 max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The vrf-redirect-0 shaper ensures that the maximum rate of static route vrf redirect traffic, sent through the recycle interface, is limited to the shaper rate.
The limit protects against vrf redirect traffic overwhelming or competing with incoming traffic at each NCP.
To configure the rate of the vrf-redireect-0 traffic:

**Command syntax: vrf-redirect-0 max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos vrf-redirect

**Parameter table**

+---------------------+-------------------------------------------+---------------+---------+
| Parameter           | Description                               | Range         | Default |
+=====================+===========================================+===============+=========+
| max-bandwidth-mbits | Per NCP VRF redirect shaper rate in mbits | 100000-400000 | 100000  |
+---------------------+-------------------------------------------+---------------+---------+
| units               |                                           | | mbps        | mbps    |
|                     |                                           | | gbps        |         |
+---------------------+-------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# vrf-redirect
    dnRouter(cfg-qos-vrf-red)# vrf-redirect-0 max-bandwidth 110 Gbps


**Removing Configuration**

To revert the configured rate to the default value:
::

    dnRouter(cfg-qos)# no vrf-redirect vrf-redirect-0 max-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
