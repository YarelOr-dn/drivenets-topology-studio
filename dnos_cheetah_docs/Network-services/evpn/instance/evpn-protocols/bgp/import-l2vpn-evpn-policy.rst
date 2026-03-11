network-services evpn instance protocols bgp import-l2vpn-evpn policy
---------------------------------------------------------------------

**Minimum user role:** operator

To import routes according to route policy definition:

**Command syntax: import-l2vpn-evpn policy [import-l2vpn-evpn-policy]** [, import-l2vpn-evpn-policy, import-l2vpn-evpn-policy]

**Command mode:** config

**Hierarchies**

- network-services evpn instance protocols bgp

**Parameter table**

+--------------------------+----------------------------------------------------------------------------+------------------+---------+
| Parameter                | Description                                                                | Range            | Default |
+==========================+============================================================================+==================+=========+
| import-l2vpn-evpn-policy | Enable import of excommunity routes which comply with the specified policy | | string         | \-      |
|                          |                                                                            | | length 1-255   |         |
+--------------------------+----------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# evpn-protocols
    dnRouter(cfg-evpn-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# import-l2vpn-evpn policy L2_VPN_IMP_POL1, L2_VPN_IMP_POL2
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To stop exporting routes with policy:
::

    dnRouter(cfg-inst-protocols-bgp)# no import-l2vpn-evpn policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
