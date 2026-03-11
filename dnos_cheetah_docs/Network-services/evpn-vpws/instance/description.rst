network-services evpn-vpws instance description
-----------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN EVPN VPWS:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Parameter table**

+-------------+-----------------------+------------------+---------+
| Parameter   | Description           | Range            | Default |
+=============+=======================+==================+=========+
| description | evpn-vpws description | | string         | \-      |
|             |                       | | length 1-255   |         |
+-------------+-----------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# description "my evpn-vpws service"
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To remove description
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
