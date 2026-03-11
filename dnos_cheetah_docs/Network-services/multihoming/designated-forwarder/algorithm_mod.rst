network-services multihoming designated-forwarder algorithm mod
---------------------------------------------------------------

**Minimum user role:** operator

Defines the default value to be the mod algorithm, for the algorithm that the user would like to use to choose the Designated Forwarder.
This value can be modified per interface by setting the per interface knob.

**Command syntax: algorithm mod**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# algorithm mod
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To restore the default value of the algorithm to mod.
::

    dnRouter(cfg-netsrv-mh-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
