network-services evpn instance interface e-tree
-----------------------------------------------

**Minimum user role:** operator

The e-tree configuration defines for the AC whether it should act as an e-tree root or an e-tree leaf.
As an e-tree root traffic may be forwarded to all ACs (local or remote) attached to the EVPN instance. As an e-tree leaf this AC may only forward traffic to root ACs (local or remote) attached to the EVPN instance.

**Command syntax: e-tree [e-tree]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance interface

**Parameter table**

+-----------+-------------------------------------------------------+----------+---------+
| Parameter | Description                                           | Range    | Default |
+===========+=======================================================+==========+=========+
| e-tree    | configure whether this interface is a root or leaf AC | | root   | \-      |
|           |                                                       | | leaf   |         |
+-----------+-------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0
    dnRouter(cfg-evpn-inst-ge100-0/0/0)# e-tree leaf
    dnRouter(cfg-evpn-inst-ge100-0/0/0)#


**Removing Configuration**

To revert the e-tree configuration for this interface to its default value.
::

    dnRouter(cfg-evpn-inst-ge100-0/0/0)# no e-tree

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
