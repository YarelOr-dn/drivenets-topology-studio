network-services evpn transport-protocol mpls fat-label
-------------------------------------------------------

**Minimum user role:** operator

Flow Aware Transport (FAT) label is an identifier used to load balance packets as they pass through the network. The first PE looks into the inner packet and calculates a hash, the FAT label. As the packet passes through intermediate routers the FAT label is considered for load-balancing decisions. All packets of same flow will result in the same FAT label and are sent on the same path.

**Command syntax: fat-label [fat-label]**

**Command mode:** config

**Hierarchies**

- network-services evpn transport-protocol mpls

**Parameter table**

+-----------+----------------------------------+--------------+----------+
| Parameter | Description                      | Range        | Default  |
+===========+==================================+==============+==========+
| fat-label | Define Requested FAT Label Usage | | enabled    | disabled |
|           |                                  | | disabled   |          |
+-----------+----------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# transport-protocol
    dnRouter(cfg-netsrv-evpn-tp)# mpls
    dnRouter(cfg-netsrv-evpn-tp-mpls)# fat-label enabled
    dnRouter(cfg-netsrv-evpn-tp-mpls)#


**Removing Configuration**

To revert fat-label to default:
::

    dnRouter(cfg-netsrv-evpn-tp-mpls)# no fat-label

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.4    | Command introduced |
+---------+--------------------+
