network-services evpn-vpws-fxc instance counters
------------------------------------------------

**Minimum user role:** operator

Define whether counters should be allocated for this EVPN-VPWS-FXC service instance. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# counters
    dnRouter(cfg-evpn-vpws-fxc-inst-counters)


**Removing Configuration**

To remove counter configurations for this instance
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
