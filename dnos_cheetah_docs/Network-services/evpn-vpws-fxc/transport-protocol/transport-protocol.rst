network-services evpn-vpws-fxc transport-protocol
-------------------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS.

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
