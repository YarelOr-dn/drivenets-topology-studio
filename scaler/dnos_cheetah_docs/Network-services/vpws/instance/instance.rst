network-services vpws instance
------------------------------

**Minimum user role:** operator

To configure the name of a L2VPN VPWS service:

**Command syntax: instance [vpws-name]**

**Command mode:** config

**Hierarchies**

- network-services vpws

**Note**

- The VPWS service must use a unique name.

**Parameter table**

+-----------+----------------------------------------------------------+------------------+---------+
| Parameter | Description                                              | Range            | Default |
+===========+==========================================================+==================+=========+
| vpws-name | The name of the vpws -- used to address the vpws service | | string         | \-      |
|           |                                                          | | length 1-255   |         |
+-----------+----------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)#


**Removing Configuration**

To revert the specified VPWS service to default:
::

    dnRouter(cfg-network-services-vpws)# no instance VPWS_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
