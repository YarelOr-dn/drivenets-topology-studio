network-services multihoming interface designated-forwarder algorithm mod
-------------------------------------------------------------------------

**Minimum user role:** operator

Defines the mod algorithm as the algorithm that the user would like to use to choose the Default Forwarder.
The actual algorithm used will depend on the agreement between all the PE devices attached to the same ES.

**Command syntax: algorithm mod**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface designated-forwarder

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# algorithm mod
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To restore the algorithm to its default value.
::

    dnRouter(cfg-mh-int-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
