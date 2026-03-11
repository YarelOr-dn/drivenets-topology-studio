network-services evpn-vpws-fxc instance protocols bgp import-l2vpn-evpn route-target
------------------------------------------------------------------------------------

**Minimum user role:** operator

To import BGP routes with the route-target specified into the L2VPN-EVPN-VPWS-FXC service.

**Command syntax: import-l2vpn-evpn route-target [import-l2vpn-evpn-route-target]** [, import-l2vpn-evpn-route-target, import-l2vpn-evpn-route-target]

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance protocols bgp

**Parameter table**

+--------------------------------+-----------------------------------------------------------------------+-------+---------+
| Parameter                      | Description                                                           | Range | Default |
+================================+=======================================================================+=======+=========+
| import-l2vpn-evpn-route-target | Enable import of routes with route-target specified to the vrf tables | \-    | \-      |
+--------------------------------+-----------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# evpn-vpws-fxc-protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# import-l2vpn-evpn route-target 49844:20, 49844:30
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To stop importing routes with the specified route-target:
::

    dnRouter(cfg-inst-protocols-bgp)# no import-l2vpn-evpn route-target 49844:30

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
