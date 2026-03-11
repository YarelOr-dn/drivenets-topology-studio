network-services evpn-vpws transport-protocol mpls
--------------------------------------------------

**Minimum user role:** operator

Define the MPLS Transport and the relevant options - control word and fat-label.

**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws transport-protocol

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-tp)# mpls
    dnRouter(cfg-netsrv-evpn-vpws-tp-mpls)#


**Removing Configuration**

To remove the mpls definition
::

    dnRouter(cfg-evpn-vpws-tp)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
