network-services vpws
---------------------

**Minimum user role:** operator

VPWS (Virtual Private Wire Service) is a point-to-point layer2 VPN service that connects a layer-2 interface of one PE with the layer-2 interface of another PE, across the layer-3 core mpls network. The VPWS service uses a Pseudowire (PW) point-to-point tunnel to emulate a physical connection and create an intermediate transport between the two PEs.

To enter the VPWS service configuration mode:

**Command syntax: vpws**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)#


**Removing Configuration**

To remove all VPWS services:
::

    dnRouter(cfg-network-services)# no vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
