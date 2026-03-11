network-services evpn instance router-interface
-----------------------------------------------

**Minimum user role:** operator

An integrated-routing-bridging interface (IRB) can be used to provide L3 services, such as Default-GW for the EVPN L2 service.
The IRB interface is associated with an L2 service, such as an EVPN instance or a Bridge-Domain instance, and an L3 VRF (can be the default VRF).
An IRB cannot be assigned to multiple EVPN services or shared between an EVPN and a Bridge-Domains service.
A single IRB interface can be associated per EVPN service instance.
To configure a router-interface for the EVPN service instance:

**Command syntax: router-interface [router-interface]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Note**

- Only supports <irbX> type interface.

- An IRB cannot be assigned to multiple EVPN services or shared between EVPN and Bridge-Domain services.

- A single IRB interface can be associated per EVPN service instance.

- The IRB address must differ from the bgp router-id

**Parameter table**

+------------------+------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                  | Range            | Default |
+==================+==============================================================================+==================+=========+
| router-interface | Associate an integrated-routing-bridging interface (IRB) to the EVPN service | | string         | \-      |
|                  |                                                                              | | length 1-255   |         |
+------------------+------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# router-interface irb0
    dnRouter(cfg-evpn-inst-irb0)#


**Removing Configuration**

To remove the association of an IRB interface from the EVPN instance,, and revert all related configuration to default behavior
::

    dnRouter(cfg-netsrv-evpn-inst)# no router-interface irb0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
