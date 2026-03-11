network-services evpn counters
------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for the EVPN service instances by default. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# counters
    dnRouter(cfg-netsrv-evpn-counters)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-evpn)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
