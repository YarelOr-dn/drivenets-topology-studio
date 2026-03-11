network-services multihoming interface designated-forwarder
-----------------------------------------------------------

**Minimum user role:** operator

To enter the designated-forwarder configuration mode:

**Command syntax: designated-forwarder**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To remove all designated forwarder configurations:
::

    dnRouter(cfg-netsrv-mh-int)# no designated-forwader

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
