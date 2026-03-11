network-services evpn-vpws instance counters
--------------------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for this EVPN-VPWS service instance. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# counters
    dnRouter(cfg-evpn-vpws-inst-counters)


**Removing Configuration**

To remove counter configurations for this instance
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
