network-services vrf instance protocols bgp neighbor-group address-family maximum-prefix restart-interval
---------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

Defines the restart interval when an exceed-action value is set to 'restart'.

**Command syntax: restart-interval [restart-interval]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family maximum-prefix
- protocols bgp neighbor address-family maximum-prefix
- protocols bgp neighbor-group address-family maximum-prefix
- protocols bgp neighbor-group neighbor address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group neighbor address-family maximum-prefix

**Note**
When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+------------------+-------------+---------+---------+
| Parameter        | Description | Range   | Default |
+==================+=============+=========+=========+
| restart-interval | minutes     | 1-65535 | \-      |
+------------------+-------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# maximum-prefix
    dnRouter(cfg-neighbor-afi-maximum-prefix)# restart-interval 100


**Removing Configuration**

To remove the restart interval:
::

    dnRouter(cfg-neighbor-afi-maximum-prefix)# no restart-interval

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
