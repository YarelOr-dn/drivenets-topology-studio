network-services bridge-domain instance
---------------------------------------

**Minimum user role:** operator

Configure a Bridge-Domain service

**Command syntax: instance [bd-name]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain

**Note**

- The Bridge-Domain service must use a unique name.

- The number of Bridge-Domain instances that can be defined is limited to 1000.

**Parameter table**

+-----------+------------------------------------------------------+------------------+---------+
| Parameter | Description                                          | Range            | Default |
+===========+======================================================+==================+=========+
| bd-name   | The name of the bd -- used to address the bd service | | string         | \-      |
|           |                                                      | | length 1-255   |         |
+-----------+------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)#


**Removing Configuration**

To revert the specified Bridge-Domain service to default:
::

    dnRouter(cfg-netsrv-bd)# no instance bd1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
