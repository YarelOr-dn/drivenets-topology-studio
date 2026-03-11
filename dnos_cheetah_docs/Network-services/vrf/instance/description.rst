network-services vrf instance description
-----------------------------------------

**Minimum user role:** operator

To set a description for the VRF instance:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance

**Note**

- Legal string length is 1-255 characters.

**Parameter table**

+-------------+-----------------+------------------+---------+
| Parameter   | Description     | Range            | Default |
+=============+=================+==================+=========+
| description | vrf description | | string         | \-      |
|             |                 | | length 1-255   |         |
+-------------+-----------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# description MyDescription-vrf_1

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_2
    dnRouter(cfg-netsrv-vrf-inst)# description My description vrf-2


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-netsrv-vrf-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
