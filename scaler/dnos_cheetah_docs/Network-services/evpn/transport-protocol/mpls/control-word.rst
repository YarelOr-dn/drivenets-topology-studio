network-services evpn transport-protocol mpls control-word
----------------------------------------------------------

**Minimum user role:** operator

Define the MPLS control word option. The Control-word is always set to zero. When enabled it is added to the packets as a marker indicating that the the inner layer 2 packet is an ethernet packet. The Control-word is only used with MPLS transport layer.

**Command syntax: control-word [control-word]**

**Command mode:** config

**Hierarchies**

- network-services evpn transport-protocol mpls

**Parameter table**

+--------------+---------------------------------+--------------+---------+
| Parameter    | Description                     | Range        | Default |
+==============+=================================+==============+=========+
| control-word | Set control-word usage for evpn | | enabled    | enabled |
|              |                                 | | disabled   |         |
+--------------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# transport-protocol
    dnRouter(cfg-netsrv-evpn-tp)# mpls
    dnRouter(cfg-netsrv-evpn-tp-mpls)# control-word disabled
    dnRouter(cfg-netsrv-evpn-tp-mpls)#


**Removing Configuration**

To revert control-word to default:
::

    dnRouter(cfg-netsrv-evpn-tp-mpls)# no control-word

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.4    | Command introduced |
+---------+--------------------+
