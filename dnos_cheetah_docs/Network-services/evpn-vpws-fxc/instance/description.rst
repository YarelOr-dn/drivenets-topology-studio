network-services evpn-vpws-fxc instance description
---------------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN EVPN-VPWS-FXC:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Parameter table**

+-------------+---------------------------+------------------+---------+
| Parameter   | Description               | Range            | Default |
+=============+===========================+==================+=========+
| description | evpn-vpws-fxc description | | string         | \-      |
|             |                           | | length 1-255   |         |
+-------------+---------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# description "my evpn-vpws-fxc service"
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)#


**Removing Configuration**

To remove description
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
