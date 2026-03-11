network-services evpn-vpws instance interface
---------------------------------------------

**Minimum user role:** operator

Configure an interface for the EVPN VPWS service.

 - An interface must be a L2-service enabled interface.

 - An Interface cannot be assigned to multiple services. 

 The Designated Forwarder Election Algorithm is defined under multihoming. When the Prefernce Algorithm (Highest or Lowest) is defined on the ES, the invert preference algorithm knob allows that per EVI this can be inverted to allow the DF role to be shared between two PE devices for the different service instances.

 The propagation of service failures allows the CE to redirect traffic via other network elements when the the EVPN-VPWS service has not been established. This option is only valid in port-mode on whole physical or bundle interfaces. It is not valid for sub-interfaces

**Command syntax: interface [name]** df-invert-preference [invert-preference-algorithm] propagate-failures [action]

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Note**

- Support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y>.

**Parameter table**

+-----------------------------+----------------------------------------------------------------------------------+------------------+----------+
| Parameter                   | Description                                                                      | Range            | Default  |
+=============================+==================================================================================+==================+==========+
| name                        | the evpn-vpws service attachment circuit                                         | | string         | \-       |
|                             |                                                                                  | | length 1-255   |          |
+-----------------------------+----------------------------------------------------------------------------------+------------------+----------+
| invert-preference-algorithm | When the AC interface is connected to a multihomed Ethernet Segment and the DF   | | enabled        | disabled |
|                             | Election algorithm is the preference algorithm (highest or lowest) then enabling | | disabled       |          |
|                             | this knob will invert the algorithm for this EVPN instance, example instead of   |                  |          |
|                             | highest election it will elect the lowest preference as the DF                   |                  |          |
+-----------------------------+----------------------------------------------------------------------------------+------------------+----------+
| action                      | Action to perform on failure                                                     | | disabled       | disabled |
|                             |                                                                                  | | laser-off      |          |
+-----------------------------+----------------------------------------------------------------------------------+------------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-evpn-vpws-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# interface bundle-1 df-invert-preference enabled
    dnRouter(cfg-netsrv-evpn-vpws-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# interface ge100-0/0/0.10
    dnRouter(cfg-netsrv-evpn-vpws-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# interface ge100-0/0/5 propagate-failures laser-off
    dnRouter(cfg-netsrv-evpn-vpws-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# interface ge100-0/0/5 propagate-failures laser-off
    dnRouter(cfg-netsrv-evpn-vpws-inst)#



**Removing Configuration**

To remove the interface from its association with the EVPN VPWS instance
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
