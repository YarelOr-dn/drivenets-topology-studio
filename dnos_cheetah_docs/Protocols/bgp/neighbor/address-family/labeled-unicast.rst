protocols bgp neighbor address-family labeled-unicast
-----------------------------------------------------

**Minimum user role:** operator

The following command enables MPLS labeled-unicast sessions (IPv4/IPv6) with a neighbor to generate a local BGP label and add it to the route.

To configure this for a neighbor or a group:

**Command syntax: labeled-unicast**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family

**Note**

- This command is only applicable to unicast sub-address-families.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# labeled-unicast

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# labeled-unicast


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-bgp-neighbor-afi)# no labeled-unicast

::

    dnRouter(cfg-bgp-group-afi)# no labeled-unicast

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 6.0     | Command introduced                     |
+---------+----------------------------------------+
| 15.0    | Added support for IPv6 labeled-unicast |
+---------+----------------------------------------+
