network-services evpn instance protocols bgp export-l2vpn-evpn policy
---------------------------------------------------------------------

**Minimum user role:** operator

To export routes according to route policy definition:

**Command syntax: export-l2vpn-evpn policy [export-l2vpn-evpn-policy]** [, export-l2vpn-evpn-policy, export-l2vpn-evpn-policy]

**Command mode:** config

**Hierarchies**

- network-services evpn instance protocols bgp

**Parameter table**

+--------------------------+----------------------------------------------------------------------------+------------------+---------+
| Parameter                | Description                                                                | Range            | Default |
+==========================+============================================================================+==================+=========+
| export-l2vpn-evpn-policy | Enable export of excommunity routes which comply with the specified policy | | string         | \-      |
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
    dnRouter(cfg-inst-protocols-bgp)# export-l2vpn-evpn policy L2_VPN_EXP_POL1, L2_EXP_IMP_POL2
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To stop exporting routes with policy:
::

    dnRouter(cfg-inst-protocols-bgp)# no export-l2vpn-evpn policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
