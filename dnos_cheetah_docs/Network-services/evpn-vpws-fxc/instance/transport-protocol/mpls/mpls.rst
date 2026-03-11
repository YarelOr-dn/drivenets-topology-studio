network-services evpn-vpws-fxc instance transport-protocol mpls
---------------------------------------------------------------

**Minimum user role:** operator

Enter the MPLS Transport hierarchy to configure the relevant options - control word and fat-label.

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance transport-protocol

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# transport-protocol
    dnRouter(cfg-evpn-vpws-fxc-inst-tp)# mpls
    dnRouter(cfg-inst-tp-mpls)#


**Removing Configuration**

To remove the mpls definition
::

    dnRouter(cfg-evpn-vpws-fxc-inst-tp)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
