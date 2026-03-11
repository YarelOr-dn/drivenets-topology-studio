network-services evpn-vpws-fxc instance protocols bgp route-distinguisher
-------------------------------------------------------------------------

**Minimum user role:** operator

To configure the route-distinguisher to enable the EVPN to use a L2VPN service.

**Command syntax: route-distinguisher [route-distinguisher]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance protocols bgp

**Note**

- The route-distinguisher must be unique amongst the EVPN, EVPN-VPWS and EVPN-VPWS-FXC services, it may be identical to an RD of a VPN service.

- Reconfiguring the route-distinguisher causes all routes to be withdrawn from the EVPN peers in the EVPN safi, and then to be re-advertised with an updated route-distinguisher.

- When set to auto, system will generate route-distinguisher in format <router-id>:<16bit>, BGP router-id must be configured and 16 bit are randomnly choosen.

- User cannot configure route-distinguisher value that match a different route-distinguisher regardless how route-distinguisher was generated (manual/auto)

**Parameter table**

+---------------------+-------------------------------------------------------------+-------+---------+
| Parameter           | Description                                                 | Range | Default |
+=====================+=============================================================+=======+=========+
| route-distinguisher | the route distinguisher for BGP as part of the EVPN service | \-    | \-      |
+---------------------+-------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# route-distinguisher 56335:1
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To remove the route-distinguisher:
::

    dnRouter(cfg-inst-protocols-bgp)# no route-distinguisher

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
