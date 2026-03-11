protocols bgp address-family ipv6-unicast labeled-unicast prefix-sid
--------------------------------------------------------------------

**Minimum user role:** operator

BGP Prefix-SID Redistribution allows advertising IPv4 and IPv6 BGP Prefix-SID for SR-MPLS IPv4/IPv6-based networks. 
It is possible for BGP to carry the association of an SR-MPLS Node-SID index with an IPv4/IPv6 prefix. 
This is achieved by attaching a prefix-SID BGP path attribute containing the label-index value to an IPv4/IPv6 route belonging to either an IPv4-LU or IPv6-LU address family.
To enable support for the BGP Prefix-SID (RFC 8669) for the labeled-unicast sub-address-family, the BGP local label allocation will assign a label from the Segment-Routing Global Block according to the prefix Label-Index attribute.

**Command syntax: prefix-sid [prefix-sid]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-unicast labeled-unicast
- protocols bgp address-family ipv4-unicast labeled-unicast

**Note**

- This command only supports Labeled-Unicast routes.

- When working with a prefix-sid, the label-allocation-mode must be per prefix.

- When working with a prefix-sid, for ipv6 labled-unicast, the label-mode must no be all-explicit-null.

**Parameter table**

+------------+-------------------------------------------------------------------------------+--------------+----------+
| Parameter  | Description                                                                   | Range        | Default  |
+============+===============================================================================+==============+==========+
| prefix-sid | Support bgp segment-routing prefix-sid under labled-unicast safi per RFC 8669 | | enabled    | disabled |
|            |                                                                               | | disabled   |          |
+------------+-------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# labeled-unicast
    dnRouter(cfg-bgp-afi-lu)# prefix-sid enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# labeled-unicast
    dnRouter(cfg-bgp-afi-lu)# prefix-sid enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-afi-lu)# no prefix-sid

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
