network-services evpn-vpws instance transport-protocol mpls fat-label
---------------------------------------------------------------------

**Minimum user role:** operator

Flow Aware Transport (FAT) label is an identifier used to load balance packets as they pass through the network. The first PE device looks into the inner packet and calculates a hash, the FAT label. As the packet passes through intermediate routers the FAT label is considered for load-balancing decisions. All packets of the same flow result in the same FAT label and are sent on the same path.

**Command syntax: fat-label [fat-label]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance transport-protocol mpls

**Parameter table**

+-----------+----------------------------------+--------------+---------+
| Parameter | Description                      | Range        | Default |
+===========+==================================+==============+=========+
| fat-label | Define Requested FAT Label Usage | | enabled    | \-      |
|           |                                  | | disabled   |         |
+-----------+----------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# transport-protocol
    dnRouter(cfg-evpn-vpws-inst-tp)# mpls
    dnRouter(cfg-inst-tp-mpls)# fat-label enabled
    dnRouter(cfg-inst-tp-mpls)#


**Removing Configuration**

To revert fat-label to default:
::

    dnRouter(cfg-inst-tp-mpls)# no fat-label

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
