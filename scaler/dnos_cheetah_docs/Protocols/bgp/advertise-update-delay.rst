protocols bgp advertise-update-delay
------------------------------------

**Minimum user role:** operator

You can set the delay time (in seconds) to advertise bgp routes, after bet-path logic finishes. The delay applies to all bgp neighbors and all bgp address-families (does not apply to ipv4-flowspec, ipv6-flowspec and link-state address-families).

When re-configuring advertise-update-delay, the new delay time will apply to all routes ready to be advertised from the reconfig time + old delay timer value.

To set the BGP delay:

**Command syntax: advertise-update-delay [advertise-update-delay]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- A delay value of 0 will not add any additional delay.

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter              | Description                                                                      | Range  | Default |
+========================+==================================================================================+========+=========+
| advertise-update-delay | Set delay time (in seconds) to advertise bgp routes after finishing best-path    | 0-1800 | 240     |
|                        | logic                                                                            |        |         |
+------------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# advertise-update-delay 180


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-bgp)# no advertise-update-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
