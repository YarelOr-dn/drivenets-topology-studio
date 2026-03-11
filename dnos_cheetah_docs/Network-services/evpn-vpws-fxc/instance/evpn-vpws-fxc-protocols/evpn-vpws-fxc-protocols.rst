network-services evpn-vpws-fxc instance protocols
-------------------------------------------------

**Minimum user role:** operator

Enter the protocols hierarchy to modify the attributes for this EVPN-VPWS-FXC instance.

**Command syntax: protocols**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)#


**Removing Configuration**

To revert the protocols configuration to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no protocols

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
