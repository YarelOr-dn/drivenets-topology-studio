network-services evpn-vpws counters
-----------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for the EVPN-VPWS service instances by default. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# counters
    dnRouter(cfg-netsrv-evpn-vpws-counters)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-evpn-vpws)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
