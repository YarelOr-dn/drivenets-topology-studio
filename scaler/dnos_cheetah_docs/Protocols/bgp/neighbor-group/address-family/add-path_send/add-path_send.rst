protocols bgp neighbor-group address-family add-path send
---------------------------------------------------------

**Minimum user role:** operator

BGP Additional Paths is a BGP extension that provides the ability to advertise multiple paths for the same prefix without the new paths replacing previous paths. This helps reduce route repetition, and achieve faster re-convergence as an alternative path is available immediately upon failure of a primary path.

To enter add-path send configuration level:

**Command syntax: add-path send**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group neighbor address-family

**Note**

- When all paths share the same next-hop only the single best path will be sent.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# add-path send
    dnRouter(cfg-neighbor-afi-add-path-send)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# add-path send
    dnRouter(cfg-group-afi-add-path-send)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-group-neighbor-afi)# add-path send
    dnRouter(cfg-neighbor-afi-add-path-send)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)# admin-state enabled
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# add-path send
    dnRouter(cfg-group-afi-add-path-send)# admin-state disabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# add-path send
    dnRouter(cfg-neighbor-afi-add-path-send)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-neighbor-afi)# no add-path send

::

    dnRouter(cfg-bgp-group-afi)# no add-path send

::

    dnRouter(cfg-group-neighbor-afi)# no add-path send

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 15.1    | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
