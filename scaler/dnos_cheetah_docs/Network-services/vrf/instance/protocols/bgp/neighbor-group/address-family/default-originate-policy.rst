network-services vrf instance protocols bgp neighbor-group address-family default-originate
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable a BGP router to forward the default route 0.0.0.0 to a BGP neighbor or a BGP peer group:

**Command syntax: default-originate** policy [policy]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family

**Note**

- This command is only applicable to unicast sub-address-families.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                      | Range            | Default |
+===========+==================================================================================+==================+=========+
| policy    | Optionally injects the default route conditionally, depending on the match       | | string         | \-      |
|           | conditions in the route map                                                      | | length 1-255   |         |
+-----------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# default-originate

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# default-originate policy POL_NAME

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-rt-constrains
    dnRouter(cfg-bgp-neighbor-afi)# default-originate


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-bgp-group-afi)# no default-originate

::

    dnRouter(cfg-bgp-neighbor-afi)# no default-originate

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 6.0     | Command introduced                                 |
+---------+----------------------------------------------------+
| 16.1    | Added support for IPv4 Route Target Constrain SAFI |
+---------+----------------------------------------------------+
