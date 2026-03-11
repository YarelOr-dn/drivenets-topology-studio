network-services multihoming designated-forwarder
-------------------------------------------------

**Minimum user role:** operator

To enter the designated-forwarder configuration mode:

**Command syntax: designated-forwarder**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To remove all default designated forwarder configurations:
::

    dnRouter(cfg-netsrv-mh)# no designated-forwader

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
