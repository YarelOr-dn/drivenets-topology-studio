network-services bridge-domain instance router-interface
--------------------------------------------------------

**Minimum user role:** operator

Configure a router-interface for the Bridge-Domain service instance

 - The Interface must be an IRB interface.

 - An IRB cannot be assigned to multiple Bridge-Domain services.

**Command syntax: router-interface [router-interface]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Note**

- Only supports <irbX> type interface.

**Parameter table**

+------------------+-------------------+------------------+---------+
| Parameter        | Description       | Range            | Default |
+==================+===================+==================+=========+
| router-interface | the IRB interface | | string         | \-      |
|                  |                   | | length 1-255   |         |
+------------------+-------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# router-interface irb10
    dnRouter(cfg-evpn-inst-ge100-0/0/0)#



**Removing Configuration**

To remove the interface from its association with the bridge-domain instance
::

    dnRouter(cfg-netsrv-bd-inst)# no router-interface irb10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
