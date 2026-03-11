network-services evpn-vpws-fxc instance fxc-mode
------------------------------------------------

**Minimum user role:** operator

The EVPN-VPWS Flexible Cropss-connect Service has two modes of operation but currently vlan-aware is the available optrion.

**Command syntax: fxc-mode [fxc-mode]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Parameter table**

+-----------+------------------------------------------+------------+------------+
| Parameter | Description                              | Range      | Default    |
+===========+==========================================+============+============+
| fxc-mode  | Define whether the service is vlan-aware | vlan-aware | vlan-aware |
+-----------+------------------------------------------+------------+------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-evpn-vpws-fxc-inst)# fxc-mode vlan-aware


**Removing Configuration**

To revert the fxc-mode to its default
::

    dnRouter(cfg-evpn-vpws-fxc-inst)# no fxc-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
