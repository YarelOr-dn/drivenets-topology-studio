network-services evpn instance protocols
----------------------------------------

**Minimum user role:** operator

Enter the protocols hierarchy to modify the attributes for this EVPN instance.

**Command syntax: protocols**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# protocols
    dnRouter(cfg-evpn-inst-protocols)#


**Removing Configuration**

To revert the protocols configuration to default:
::

    dnRouter(cfg-netsrv-evpn-inst)# no protocols

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
