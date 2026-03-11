network-services evpn-vpws-fxc instance admin-state
---------------------------------------------------

**Minimum user role:** operator

Define the EVPN-VPWS-FXC service instance admin-state. By default the admin-state is enabled.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Parameter table**

+-------------+------------------------------------+--------------+---------+
| Parameter   | Description                        | Range        | Default |
+=============+====================================+==============+=========+
| admin-state | evpn-vpws-fxc instance admin-state | | enabled    | enabled |
|             |                                    | | disabled   |         |
+-------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# admin-state disabled
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)#


**Removing Configuration**

To revert the admin-state to its default: enabled
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
