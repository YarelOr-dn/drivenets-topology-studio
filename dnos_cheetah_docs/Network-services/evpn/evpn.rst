network-services evpn
---------------------

**Minimum user role:** operator

EVPN (Ethernet Virtual Private Network) is a layer 2 VPN service that connects layer2 interface(s) of one PE with the layer 2 interface(s) of other PEs, across the layer 3 core MPLS network. The EVPN service uses an MPLS or VxLAN transport layer and a BGP control layer.

To enter the EVPN service configuration mode:

**Command syntax: evpn**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn
    dnRouter(cfg-network-services-evpn)#


**Removing Configuration**

To remove all EVPN services:
::

    dnRouter(cfg-network-services)# no evpn

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
