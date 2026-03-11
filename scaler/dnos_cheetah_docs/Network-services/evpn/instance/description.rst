network-services evpn instance description
------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN EVPN:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Parameter table**

+-------------+------------------+------------------+---------+
| Parameter   | Description      | Range            | Default |
+=============+==================+==================+=========+
| description | evpn description | | string         | \-      |
|             |                  | | length 1-255   |         |
+-------------+------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# description "my evpn service"
    dnRouter(cfg-netsrv-evpn-inst)#


**Removing Configuration**

To remove description
::

    dnRouter(cfg-netsrv-evpn-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
