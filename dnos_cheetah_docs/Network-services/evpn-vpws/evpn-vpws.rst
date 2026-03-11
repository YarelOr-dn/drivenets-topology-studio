network-services evpn-vpws
--------------------------

**Minimum user role:** operator

EVPN-VPWS (Ethernet Virtual Private Network) is a point-to-point layer 2 VPN service that connects one layer 2 interface(s) of
a PE device with one layer 2 interface(s) of another PE device, across the layer 3 core MPLS network. The EVPN service uses
an MPLS or VxLAN transport layer and a BGP control layer.

To enter the EVPN-VPWS service configuration mode:

**Command syntax: evpn-vpws**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws
    dnRouter(cfg-network-services-evpn-vpws)#


**Removing Configuration**

To remove all EVPN VPWS services:
::

    dnRouter(cfg-network-services)# no evpn-vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
