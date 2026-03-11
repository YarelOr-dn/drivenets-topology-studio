network-services evpn instance
------------------------------

**Minimum user role:** operator

Configure a L2VPN EVPN service

**Command syntax: instance [evpn-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Note**

- The EVPN service must use a unique name.

**Parameter table**

+-----------+----------------------------------------------------------+------------------+---------+
| Parameter | Description                                              | Range            | Default |
+===========+==========================================================+==================+=========+
| evpn-name | The name of the evpn -- used to address the evpn service | | string         | \-      |
|           |                                                          | | length 1-255   |         |
+-----------+----------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)#


**Removing Configuration**

To revert the specified EVPN service to default:
::

    dnRouter(cfg-netsrv-evpn-inst)# no instance evpn1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
