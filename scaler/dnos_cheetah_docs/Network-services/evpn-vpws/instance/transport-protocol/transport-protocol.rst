network-services evpn-vpws instance transport-protocol
------------------------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS.

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Example**
::

    dnRouter#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# transport-protocol
    dnRouter(cfg-evpn-vpws-inst-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting them to their default values.
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
