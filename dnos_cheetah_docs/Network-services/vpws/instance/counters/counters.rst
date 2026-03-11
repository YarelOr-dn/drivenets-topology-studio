network-services vpws instance counters
---------------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for this VPWS service instance. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services vpws instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vpws
    dnRouter(cfg-netsrv-vpws)# instance vpws1
    dnRouter(cfg-netsrv-vpws-inst)# counters
    dnRouter(cfg-vpws-inst-counters)


**Removing Configuration**

To remove counter configurations for this instance
::

    dnRouter(cfg-netsrv-vpws-inst)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
