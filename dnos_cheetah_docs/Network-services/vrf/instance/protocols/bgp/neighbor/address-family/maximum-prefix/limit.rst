network-services vrf instance protocols bgp neighbor address-family maximum-prefix limit
----------------------------------------------------------------------------------------

**Minimum user role:** operator

"Specifies the maximum number of IP network prefixes (routes) that can be learned from a specified neighbor or neighbor group."

**Command syntax: limit [maximum-prefix-number]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor address-family maximum-prefix
- protocols bgp neighbor address-family maximum-prefix
- protocols bgp neighbor-group address-family maximum-prefix
- protocols bgp neighbor-group neighbor address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group neighbor address-family maximum-prefix

**Note**
Neighbors within a neighbor-group derive the neighbor-group configuration or can have a unique setting from the group.

**Parameter table**

+-----------------------+----------------------+--------------+---------+
| Parameter             | Description          | Range        | Default |
+=======================+======================+==============+=========+
| maximum-prefix-number | 0 used for unlimited | 0-4294967295 | 0       |
+-----------------------+----------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# maximum-prefix
    dnRouter(cfg-neighbor-afi-maximum-prefix)# limit 1000000000


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-neighbor-afi-maximum-prefix)# no limit

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
