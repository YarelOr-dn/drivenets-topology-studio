network-services evpn instance mac-handling
-------------------------------------------

**Minimum user role:** operator

Enter the mac-learning hierarchy to modify the mac-learning attributes for this EVPN instance.

**Command syntax: mac-handling**

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
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)#


**Removing Configuration**

To revert the mac-handling configurations to defaults
::

    dnRouter(cfg-evpn-inst)# no mac-handling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
