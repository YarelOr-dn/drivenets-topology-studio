network-services evpn instance e-tree-leaf
------------------------------------------

**Minimum user role:** operator

An e-tree-leaf is not defined or disabled as the default setting for all evpn instances that are created.  
By defining this knob, the e-tree-leaf is enabled, and all interfaces associated with this EVPN instance will by default be defined as leaf interfaces
(unless configured otherwise per AC) and any traffic will need to be forwarded to root ACs.

**Command syntax: e-tree-leaf**

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
    dnRouter(cfg-netsrv-evpn-inst)# e-tree-leaf
    dnRouter(cfg-netsrv-evpn-inst)#


**Removing Configuration**

To revert the e-tree-leaf configuration to its default of root
::

    dnRouter(cfg-netsrv-evpn-inst)# no e-tree-leaf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
