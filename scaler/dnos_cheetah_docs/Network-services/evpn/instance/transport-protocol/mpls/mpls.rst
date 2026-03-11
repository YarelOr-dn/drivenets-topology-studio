network-services evpn instance transport-protocol mpls
------------------------------------------------------

**Minimum user role:** operator

Enter the MPLS Transport hierarchy to configure the relevant options - control word and fat-label.

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- network-services evpn instance transport-protocol

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# transport-protocol
    dnRouter(cfg-evpn-inst-tp)# mpls
    dnRouter(cfg-inst-tp-mpls)#


**Removing Configuration**

To remove the mpls definition
::

    dnRouter(cfg-evpn-inst-tp)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
