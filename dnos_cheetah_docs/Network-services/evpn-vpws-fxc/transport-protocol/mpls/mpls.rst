network-services evpn-vpws-fxc transport-protocol mpls
------------------------------------------------------

**Minimum user role:** operator

Define the MPLS Transport and the relevant options - control word and fat-label.

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc transport-protocol

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp)# mpls
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)#


**Removing Configuration**

To remove the mpls definition
::

    dnRouter(cfg-evpn-vpws-fxc-tp)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
