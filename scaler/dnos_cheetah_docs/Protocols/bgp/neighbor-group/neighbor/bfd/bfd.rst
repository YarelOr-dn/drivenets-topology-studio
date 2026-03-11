protocols bgp neighbor-group neighbor bfd
-----------------------------------------

**Minimum user role:** operator

The command allows enabling BFD for the protection of a session between a single BGP neighbor or neighbor group and allows you to configure the BFD session settings.
The BFD session type (single-hop or multi-hop) is decided according to the BGP session type. The BFD source address is the BGP source address and the BFD destination address is the BGP peer address.

When a BFD session is down, the BGP session will close and all routes from the neighbor will be withdrawn.

The BFD failure detection time is computed out of the negotiated received interval and the remote multiplier configurations.

Detection-time = negotiated-received-interval X received multiplier.
This is the maximum amount of time that can elapse without receiving a BFD control packet before the session is declared down.

BFD neighbor can signal session state down and upon receipt, the local BFD session will immediately switch to DOWN state.

To enable or disable the BFD protocol with a single neighbor or a neighbor group:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor
- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bfd
    dnRouter(cfg-bgp-neighbor-bfd)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# bfd
    dnRouter(cfg-group-neighbor-bfd)#


**Removing Configuration**

To revert the BFD protocol to the default state:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no bfd 

::

    dnRouter(cfg-protocols-bgp-group)# no bfd

::

    dnRouter(cfg-bgp-group-neighbor)# no bfd

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 11.4    | Command reintroduced |
+---------+----------------------+
