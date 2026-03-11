protocols bgp address-family l2vpn-evpn label-allocation
--------------------------------------------------------

**Minimum user role:** operator


To configure per-nexthop/per-prefix label allocation for l2vpn-evpn so that we do not allocate a label per MAC address.
BGP label allocation per next-hop mode for IPv4 labeled-unicast and IPv6 labeled-unicast address families has been added. This mode prevents additional lookup in the device's routing table and conserves label space. The label allocation per next-hop feature allows the same label to be used for all the routes advertised from a unique peer device.

- Per-prefix - A unique label is allocated for each bgp advertised MAC address. 

- Per-nexthop - All advertised prefixes, that are locally resolved by the same nexthop, will be assigned the same local label.

**Command syntax: label-allocation [label-allocation-mode]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family l2vpn-evpn

**Parameter table**

+-----------------------+-----------------------------------------------------------------------+-----------------+-------------+
| Parameter             | Description                                                           | Range           | Default     |
+=======================+=======================================================================+=================+=============+
| label-allocation-mode | Configure BGP label allocation mode, either per-prefix or per-nexthop | | per-prefix    | per-nexthop |
|                       |                                                                       | | per-nexthop   |             |
+-----------------------+-----------------------------------------------------------------------+-----------------+-------------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family l2vpn-evpn
    dnRouter(cfg-protocols-bgp-afi)# label-allocation per-prefix

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family l2vpn-evpn
    dnRouter(cfg-protocols-bgp-afi)# label-allocation per-nexthop


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-bgp-afi)# no label-allocation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
