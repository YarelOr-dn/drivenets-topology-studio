network-services evpn-vpws-fxc instance protocols bgp export-l2vpn-evpn route-target
------------------------------------------------------------------------------------

**Minimum user role:** operator

To export routes with the route-target tag:

**Command syntax: export-l2vpn-evpn route-target [export-l2vpn-evpn-route-target]** [, export-l2vpn-evpn-route-target, export-l2vpn-evpn-route-target]

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance protocols bgp

**Parameter table**

+--------------------------------+-----------------------------------------------+-------+---------+
| Parameter                      | Description                                   | Range | Default |
+================================+===============================================+=======+=========+
| export-l2vpn-evpn-route-target | Enable export of routes with route-target tag | \-    | \-      |
+--------------------------------+-----------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# evpn-vpws-protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# export-l2vpn-evpn route-target 49844:20, 49844:30
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To stop exporting routes with the specified route-target:
::

    dnRouter(cfg-inst-protocols-bgp)# no export-l2vpn-evpn route-target 49844:30

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
