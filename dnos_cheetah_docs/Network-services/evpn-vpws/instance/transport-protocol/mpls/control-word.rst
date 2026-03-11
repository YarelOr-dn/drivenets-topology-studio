network-services evpn-vpws instance transport-protocol mpls control-word
------------------------------------------------------------------------

**Minimum user role:** operator

Define the MPLS control word option. The Control-word is always zero when enabled and is used as a marker to identify between the inner layer 2 packet and the layer 3 encapsulation. The Control-word is only used with MPLS.

**Command syntax: control-word [control-word]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance transport-protocol mpls

**Parameter table**

+--------------+---------------------------------+--------------+---------+
| Parameter    | Description                     | Range        | Default |
+==============+=================================+==============+=========+
| control-word | Set control-word usage for evpn | | enabled    | \-      |
|              |                                 | | disabled   |         |
+--------------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# transport-protocol
    dnRouter(cfg-evpn-vpws-inst-tp)# mpls
    dnRouter(cfg-inst-tp-mpls)# control-word disabled
    dnRouter(cfg-inst-tp-mpls)#


**Removing Configuration**

To revert control-word to default:
::

    dnRouter(cfg-inst-tp-mpls)# no control-word

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
