network-services evpn-vpws instance
-----------------------------------

**Minimum user role:** operator

Configure a L2VPN EVPN VPWS service.

**Command syntax: instance [evpn-vpws-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Note**

- The EVPN VPWS service must use a unique name.

**Parameter table**

+----------------+--------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                        | Range            | Default |
+================+====================================================================+==================+=========+
| evpn-vpws-name | The name of the evpn-vpws -- used to address the evpn-vpws service | | string         | \-      |
|                |                                                                    | | length 1-255   |         |
+----------------+--------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To revert the specified EVPN VPWS service to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no instance evpn-vpws1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
