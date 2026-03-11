network-services evpn-vpws-fxc
------------------------------

**Minimum user role:** operator

EVPN-VPWS-FXC (Ethernet Virtual Private Network Flexible Cross-connect) is a point-to-point layer 2 VPN service that connects one or more                                                                                                                                                                                                                                                  layer 2 interface(s) of
ACs of a PE device with one or more layer 2 interface(s) of another PE device, across the layer 3 core MPLS network. The EVPN service uses
an MPLS or VxLAN transport layer and a BGP control layer.

To enter the EVPN-VPWS-FXC service configuration mode:

**Command syntax: evpn-vpws-fxc**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws-fxc
    dnRouter(cfg-network-services-evpn-vpws-fxc)#


**Removing Configuration**

To remove all EVPN VPWS FXC services:
::

    dnRouter(cfg-network-services)# no evpn-vpws-fxc

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
