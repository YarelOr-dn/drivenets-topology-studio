network-services evpn-vpws-fxc transport-protocol mpls fat-label
----------------------------------------------------------------

**Minimum user role:** operator

Configure the default (can be modified per instance) value for the fat-label. Flow Aware Transport (FAT) label is an identifier used to load balance packets as they pass through the network. The first PE device looks into the inner packet and calculates a hash, the FAT label. As the packet passes through the intermediate routers the FAT label is considered for load-balancing decisions. All packets of the same flow will result in the same FAT label and are sent on the same path.

**Command syntax: fat-label [fat-label]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc transport-protocol mpls

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
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp)# mpls
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)# fat-label enabled
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)#


**Removing Configuration**

To revert fat-label to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)# no fat-label

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
