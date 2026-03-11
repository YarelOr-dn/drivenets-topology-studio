network-services vpws instance pw fat-label
-------------------------------------------

**Minimum user role:** operator

Flow Aware Transport (FAT) label is an identifier used to load balance packets as they pass through the network. The first PE looks into the inner packet and calculates a hash, the FAT label. As the packet passes through intermediate routers the FAT label is considered for load-balancing decisions. All packets of same flow will result in the same FAT label and are sent on the same path.

**Command syntax: fat-label [fat-label]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Parameter table**

+-----------+----------------------------------+------------------+----------+
| Parameter | Description                      | Range            | Default  |
+===========+==================================+==================+==========+
| fat-label | Define Requested FAT Label Usage | | enabled        | disabled |
|           |                                  | | send-only      |          |
|           |                                  | | receive-only   |          |
|           |                                  | | disabled       |          |
+-----------+----------------------------------+------------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# fat-label enabled


**Removing Configuration**

To revert FAT-label to default:
::

    dnRouter(cfg-vpws-inst-pw)# no fat-label

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
