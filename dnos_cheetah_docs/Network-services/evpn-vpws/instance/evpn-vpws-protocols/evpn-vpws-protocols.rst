network-services evpn-vpws instance protocols
---------------------------------------------

**Minimum user role:** operator

Enter the protocols hierarchy to modify the attributes for this EVPN-VPWS instance.

**Command syntax: protocols**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# protocols
    dnRouter(cfg-evpn-vpws-inst-protocols)#


**Removing Configuration**

To revert the protocols configuration to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no protocols

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
