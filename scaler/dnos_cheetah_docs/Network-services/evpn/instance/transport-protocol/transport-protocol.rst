network-services evpn instance transport-protocol
-------------------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS or VxLAN

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Example**
::

    dnRouter#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# transport-protocol
    dnRouter(cfg-evpn-inst-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn-inst)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
