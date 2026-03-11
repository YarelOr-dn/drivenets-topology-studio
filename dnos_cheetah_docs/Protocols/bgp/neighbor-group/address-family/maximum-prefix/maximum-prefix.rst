protocols bgp neighbor-group address-family maximum-prefix
----------------------------------------------------------

**Minimum user role:** operator

By setting the maximum-prefix attribute, you control the number of prefixes that can be received from a neighbor. This is useful when a router starts receiving more routes than its memory can take.

To limit the number of routes that can be learned from the neighbor, peer group, or neighbor in a peer group:

**Command syntax: maximum-prefix**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**
When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# maximum-prefix
    dnRouter(cfg-neighbor-afi-maximum-prefix)#


**Removing Configuration**

To revert to the default maximum-prefixes:
::

    dnRouter(cfg-bgp-neighbor-afi)# no maximum-prefix

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
