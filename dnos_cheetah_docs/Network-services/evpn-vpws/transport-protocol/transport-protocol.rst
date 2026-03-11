network-services evpn-vpws transport-protocol
---------------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS.

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn-vpws)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
