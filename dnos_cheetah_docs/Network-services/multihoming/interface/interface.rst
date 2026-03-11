network-services multihoming interface
--------------------------------------

**Minimum user role:** operator

Configure a multihomed interface.

 - An interface must be a l2-service enabled interface.



**Command syntax: interface [name]**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Note**

- Support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y>.

**Parameter table**

+-----------+------------------------------------------------+------------------+---------+
| Parameter | Description                                    | Range            | Default |
+===========+================================================+==================+=========+
| name      | Associate an interface to the EVPN Multihoming | | string         | \-      |
|           |                                                | | length 1-255   |         |
+-----------+------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface bundle-1
    dnRouter(cfg-netsrv-mh-int)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0.10
    dnRouter(cfg-evpn-mh-int)#



**Removing Configuration**

To remove the interface from its association to multihoming
::

    dnRouter(cfg-netsrv-mh)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
