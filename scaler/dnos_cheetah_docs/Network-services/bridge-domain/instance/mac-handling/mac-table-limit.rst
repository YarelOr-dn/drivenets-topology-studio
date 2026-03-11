network-services bridge-domain instance mac-handling mac-table-limit
--------------------------------------------------------------------

**Minimum user role:** operator

Configure the maximum number of entries in the MAC Table for this Bridge-Domain instance. When this limit is reached, new MAC addresses will not be added to the MAC Table.

**Command syntax: mac-table-limit [mac-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance mac-handling

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter       | Description                                                                      | Range    | Default |
+=================+==================================================================================+==========+=========+
| mac-table-limit | the maximum number of entries allowed in the mac-table for this Bridge-Domain    | 20-64000 | \-      |
|                 | instance                                                                         |          |         |
+-----------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# mac-handling
    dnRouter(cfg-bd-inst-mh)# mac-table-limit 10000
    dnRouter(cfg-bd-inst-mh)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-bd-inst-mh)# no mac-table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
