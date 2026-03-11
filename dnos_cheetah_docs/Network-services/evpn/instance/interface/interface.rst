network-services evpn instance interface
----------------------------------------

**Minimum user role:** operator

Configure an interface for the EVPN service

 - Interface must be a l2-service enabled interface.

 - An Interface cannot be assigned to multiple services

**Command syntax: interface [name]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Note**

- support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y>

**Parameter table**

+-----------+--------------------------------------------+------------------+---------+
| Parameter | Description                                | Range            | Default |
+===========+============================================+==================+=========+
| name      | Associate an interface to the EVPN service | | string         | \-      |
|           |                                            | | length 1-255   |         |
+-----------+--------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-evpn-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface bundle-1
    dnRouter(cfg-netsrv-evpn-inst)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0.10
    dnRouter(cfg-evpn-inst-int)#



**Removing Configuration**

To remove the interface from its association with the EVPN instance
::

    dnRouter(cfg-netsrv-evpn-inst)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
