network-services evpn-vpws instance transport-protocol mpls
-----------------------------------------------------------

**Minimum user role:** operator

Enter the MPLS Transport hierarchy to configure the relevant options - control word and fat-label.

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance transport-protocol

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# transport-protocol
    dnRouter(cfg-evpn-vpws-inst-tp)# mpls
    dnRouter(cfg-inst-tp-mpls)#


**Removing Configuration**

To remove the mpls definition
::

    dnRouter(cfg-evpn-vpws-inst-tp)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
