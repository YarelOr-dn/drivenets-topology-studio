network-services bridge-domain mac-handling mac-table-limit
-----------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 20-6400)for the maximum number of entries in the MAC Table for any new Bridge-Domain instances defined. When this limit is reached, new MAC addresses will not be added to the MAC Table.

**Command syntax: mac-table-limit [mac-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain mac-handling

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter       | Description                                                                      | Range    | Default |
+=================+==================================================================================+==========+=========+
| mac-table-limit | the default value for the maximum number of entries allowed in the mac-table     | 20-64000 | 64000   |
|                 | that will be applied to any new Bridge-Domain instances subsequently created.    |          |         |
+-----------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# mac-handling
    dnRouter(cfg-netsrv-bd-mh)# mac-table-limit 10000
    dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-netsrv-bd-mh)# no mac-table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
