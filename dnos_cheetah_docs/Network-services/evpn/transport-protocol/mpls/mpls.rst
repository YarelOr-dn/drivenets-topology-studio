network-services evpn transport-protocol mpls
---------------------------------------------

**Minimum user role:** operator

Define the MPLS Transport and the relevant options - control word and fat-label.

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- network-services evpn transport-protocol

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# transport-protocol
    dnRouter(cfg-netsrv-evpn-tp)# mpls
    dnRouter(cfg-netsrv-evpn-tp-mpls)#


**Removing Configuration**

To remove the mpls definition
::

    dnRouter(cfg-evpn-inst-tp)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.4    | Command introduced |
+---------+--------------------+
