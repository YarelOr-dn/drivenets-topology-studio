network-services bridge-domain instance description
---------------------------------------------------

**Minimum user role:** operator

To add an optional description of the Bridge Domain Instance

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Parameter table**

+-------------+---------------------------+------------------+---------+
| Parameter   | Description               | Range            | Default |
+=============+===========================+==================+=========+
| description | bridge-domain description | | string         | \-      |
|             |                           | | length 1-255   |         |
+-------------+---------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# description "my bridge-domain service"


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-netsrv-bd-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
