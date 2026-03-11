network-services evpn-vpws instance admin-state
-----------------------------------------------

**Minimum user role:** operator

Define the EVPN_VPWS service instance admin-state. By default the admin-state is enabled.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Parameter table**

+-------------+--------------------------------+--------------+---------+
| Parameter   | Description                    | Range        | Default |
+=============+================================+==============+=========+
| admin-state | evpn-vpws instance admin-state | | enabled    | enabled |
|             |                                | | disabled   |         |
+-------------+--------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# admin-state disabled
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To revert the admin-state to its default: enabled
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
