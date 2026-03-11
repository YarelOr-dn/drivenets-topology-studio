network-services evpn transport-protocol
----------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS or VxLAN

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# transport-protocol
    dnRouter(cfg-netsrv-evpn-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.4    | Command introduced |
+---------+--------------------+
