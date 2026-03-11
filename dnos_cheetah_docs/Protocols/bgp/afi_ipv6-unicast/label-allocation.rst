protocols bgp address-family ipv6-unicast label-allocation
----------------------------------------------------------

**Minimum user role:** operator

BGP label allocation per next-hop mode for IPv4 labeled-unicast and IPv6 labeled-unicast address families has been added. This mode prevents additional lookup in the device's routing table and conserves label space. The label allocation per next-hop feature allows the same label to be used for all the routes advertised from a unique peer device.

- Per-prefix - A unique label is allocated for each bgp advertise labeled prefix . Local prefixes will share the same php/explicit-null label.

- Per-nexthop - All advertised prefixes, that are locally resolved by the same nexthop, will be assigned the same local label.

To configure per-nexthop/per-prefix label allocation:

**Command syntax: label-allocation [label-allocation-mode]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv4-vpn
- protocols bgp address-family ipv6-vpn

**Note**

- This command is only applicable to unicast sub-address-families.

- The nexthop prefix includes all route resolution variations, including ecmp, egress labels and alternate paths.

**Parameter table**

+-----------------------+-----------------------------------------------------------------------+-----------------+------------+
| Parameter             | Description                                                           | Range           | Default    |
+=======================+=======================================================================+=================+============+
| label-allocation-mode | Configure BGP label allocation mode, either per-prefix or per-nexthop | | per-prefix    | per-prefix |
|                       |                                                                       | | per-nexthop   |            |
+-----------------------+-----------------------------------------------------------------------+-----------------+------------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# label-allocation per-prefix

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# label-allocation per-nexthop


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-bgp-afi)# no label-allocation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
