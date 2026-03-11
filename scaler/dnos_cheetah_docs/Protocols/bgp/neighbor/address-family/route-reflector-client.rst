protocols bgp neighbor address-family route-reflector-client
------------------------------------------------------------

**Minimum user role:** operator

To configure a neighbor as a route reflector client:

**Command syntax: route-reflector-client**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family

**Note**

- This command is applicable to iBGP neighbors only.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)#)# route-reflector-client

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# route-reflector-client


**Removing Configuration**

To remove the route-reflector configuration:
::

    dnRouter(cfg-bgp-neighbor-afi)# no route-reflector-client

::

    dnRouter(cfg-bgp-group-afi)# no route-reflector-client

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 15.0    | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
