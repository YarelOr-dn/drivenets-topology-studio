network-services evpn instance counters
---------------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for this EVPN service instance. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# counters
    dnRouter(cfg-evpn-inst-counters)


**Removing Configuration**

To remove counter configurations for this instance
::

    dnRouter(cfg-netsrv-evpn-inst)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
