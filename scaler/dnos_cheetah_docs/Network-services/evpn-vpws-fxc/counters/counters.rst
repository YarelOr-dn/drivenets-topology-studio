network-services evpn-vpws-fxc counters
---------------------------------------

**Minimum user role:** operator

Define whether counters should be allocated for the EVPN-VPWS-FXC service instances by default. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# counters
    dnRouter(cfg-netsrv-evpn-vpws-fxc-counters)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
