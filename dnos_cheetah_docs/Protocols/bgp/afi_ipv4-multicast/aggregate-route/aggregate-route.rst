protocols bgp address-family ipv4-multicast aggregate-route
-----------------------------------------------------------

**Minimum user role:** operator

Creates an aggregate (summary) route in a BGP routing table.
An aggregate route will be created if a more specific route exists in the BGP local RIB, and may act as a contributor.
An aggregate route will be installed to the local RIB with nexthop null0 (silent drop).
To create as aggregate route:

**Command syntax: aggregate-route [ip-prefix]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast

**Note**

- This command is only applicable to unicast and multicast sub-address-families.

- You can configure multiple aggregate-address prefixes in an address-family.

- Aggregate-address prefixes will not be advertised in a labeled-unicast safi.

**Parameter table**

+-----------+------------------+-----------+---------+
| Parameter | Description      | Range     | Default |
+===========+==================+===========+=========+
| ip-prefix | aggregate prefix | A.B.C.D/x | \-      |
+-----------+------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 10.108.0.0/16
    dnRouter(cfg-bgp-afi-aggr)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 2001::66/90
    dnRouter(cfg-bgp-afi-aggr)#


**Removing Configuration**

To stop all aggregate-address advertisements:
::

    dnRouter(cfg-protocols-bgp-afi)# no aggregate-address

To stop the advertisement of a specific aggregate-address:
::

    dnRouter(cfg-protocols-bgp-afi)# no aggregate-address 12001::66/90

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
