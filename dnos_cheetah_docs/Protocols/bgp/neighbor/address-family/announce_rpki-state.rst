protocols bgp neighbor address-family announce rpki-state
---------------------------------------------------------

**Minimum user role:** operator

The following command is used to announce the RPKI state information using an Extended Community.

**Command syntax: announce rpki-state**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# announce rpki-state

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP4:all
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# announce
    dnRouter(cfg-bgp-group-afi)# rpki-state


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-group-afi)# no announce

::

    dnRouter(cfg-bgp-neighbor-afi)# no announce rpki-state

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 15.1    | Command introduced                    |
+---------+---------------------------------------+
| 16.1    | Added support for IPv4-multicast SAFI |
+---------+---------------------------------------+
