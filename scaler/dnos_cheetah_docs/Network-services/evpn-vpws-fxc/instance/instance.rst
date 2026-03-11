network-services evpn-vpws-fxc instance
---------------------------------------

**Minimum user role:** operator

Configure a L2VPN EVPN-VPWS-FXC service instance.

**Command syntax: instance [evpn-vpws-fxc-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Note**

- The EVPN-VPWS-FXC service must use a unique name.

**Parameter table**

+--------------------+----------------------------------------------------------------------------+------------------+---------+
| Parameter          | Description                                                                | Range            | Default |
+====================+============================================================================+==================+=========+
| evpn-vpws-fxc-name | The name of the evpn-vpws-fxc -- used to address the evpn-vpws-fxc service | | string         | \-      |
|                    |                                                                            | | length 1-255   |         |
+--------------------+----------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-fxc-evpn-vpws-fxc1)#


**Removing Configuration**

To revert the specified EVPN-VPWS-FXC service to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no instance evpn-vpws-fxc1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
