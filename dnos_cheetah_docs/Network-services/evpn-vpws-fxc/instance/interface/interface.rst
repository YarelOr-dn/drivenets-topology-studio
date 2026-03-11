network-services evpn-vpws-fxc instance interface
-------------------------------------------------

**Minimum user role:** operator

Configure an interface for the EVPN VPWS FXC service.

 - An interface must be a L2-service enabled interface.

 - An Interface cannot be assigned to multiple services. 

 The Designated Forwarder Election Algorithm is defined under multihoming. When the Prefernce Algorithm (Highest or Lowest) is defined on the ES, the invert preference algorithm knob allows that per EVI this can be inverted to allow the DF role to be shared between two PE devices for the different service instances.

**Command syntax: interface [fxc-interface-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Note**

- Support only interface of type <geX-X/X/X.Y>/<bundle-X.Y>.

**Parameter table**

+--------------------+-----------------------------------------------------+------------------+---------+
| Parameter          | Description                                         | Range            | Default |
+====================+=====================================================+==================+=========+
| fxc-interface-name | Associate an interface to the EVPN-VPWS-FXC service | | string         | \-      |
|                    |                                                     | | length 1-255   |         |
+--------------------+-----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# interface ge100-0/0/0.10
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# interface bundle-1.120 df-invert-preference enabled
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)#



**Removing Configuration**

To remove the interface from its association with the EVPN VPWS FXC instance
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
