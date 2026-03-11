network-services bridge-domain instance interface
-------------------------------------------------

**Minimum user role:** operator

Configure an interface for the Bridge-Domain service instance

 - The Interface must be a l2-service enabled interface.

 - An Interface cannot be assigned to multiple services

**Command syntax: interface [name]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Note**

- support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y>

**Parameter table**

+-----------+--------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                  | Range            | Default |
+===========+==============================================================+==================+=========+
| name      | Associate an interface to the Bridge Domian service instance | | string         | \-      |
|           |                                                              | | length 1-255   |         |
+-----------+--------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# interface ge100-0/0/0
    dnRouter(cfg-bd-inst-ge100-0/0/0)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# interface bundle-1
    dnRouter(cfg-bd-inst-bundle-1)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# interface ge100-0/0/0.10
    dnRouter(cfg-bd-inst-ge100-0/0/0.10)#


**Removing Configuration**

To remove the interface from its association with the Bridge Domain instance
::

    dnRouter(cfg-netsrv-bd-inst)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
