network-services vpws instance description
------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN VPWS:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance

**Parameter table**

+-------------+------------------+------------------+---------+
| Parameter   | Description      | Range            | Default |
+=============+==================+==================+=========+
| description | vpws description | | string         | \-      |
|             |                  | | length 1-255   |         |
+-------------+------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# description "my vpws service"


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-network-services-vpws-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
