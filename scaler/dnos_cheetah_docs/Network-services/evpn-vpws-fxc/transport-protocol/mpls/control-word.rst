network-services evpn-vpws-fxc transport-protocol mpls control-word
-------------------------------------------------------------------

**Minimum user role:** operator

Configure the default (can be modified per instance) MPLS control word option. The Control-word is always zero when enabled and is used as a marker to identify between the inner layer 2 packet and the layer 3 encapsulation. The Control-word is only used with MPLS.

**Command syntax: control-word [control-word]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc transport-protocol mpls

**Parameter table**

+--------------+------------------------------------------+--------------+---------+
| Parameter    | Description                              | Range        | Default |
+==============+==========================================+==============+=========+
| control-word | Set control-word usage for evpn-vpws-fxc | | enabled    | enabled |
|              |                                          | | disabled   |         |
+--------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp)# mpls
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)# control-word disabled
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)#


**Removing Configuration**

To revert control-word to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp-mpls)# no control-word

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
