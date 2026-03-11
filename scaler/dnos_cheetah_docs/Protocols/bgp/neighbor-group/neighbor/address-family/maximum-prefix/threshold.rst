protocols bgp neighbor-group neighbor address-family maximum-prefix threshold
-----------------------------------------------------------------------------

**Minimum user role:** operator

Specifies the percentage of the value specified by *maximum-prefix-number* that causes a log message to be generated.

**Command syntax: threshold [syslog-threshold]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor address-family maximum-prefix
- protocols bgp neighbor address-family maximum-prefix
- protocols bgp neighbor-group address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group neighbor address-family maximum-prefix

**Note**
When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+------------------+-------------+-------+---------+
| Parameter        | Description | Range | Default |
+==================+=============+=======+=========+
| syslog-threshold | percentage  | 1-100 | 100     |
+------------------+-------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# maximum-prefix
    dnRouter(cfg-neighbor-afi-maximum-prefix)# threshold 75


**Removing Configuration**

To revert to the default maximum-prefixes:
::

    dnRouter(cfg-neighbor-afi-maximum-prefix)# no threshold

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
