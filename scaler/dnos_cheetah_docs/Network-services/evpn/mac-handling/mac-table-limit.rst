network-services evpn mac-handling mac-table-limit
--------------------------------------------------

**Minimum user role:** operator

Configure the maximum number of entries in the MAC Table for any new EVPN instances. When this limit is reached, new MAC addresses will not be added to the MAC Table.

**Command syntax: mac-table-limit [mac-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter       | Description                                                                      | Range     | Default |
+=================+==================================================================================+===========+=========+
| mac-table-limit | the maximum number of entries allowed in the mac-table, to be applied to EVPN    | 20-220000 | 64000   |
|                 | instances.                                                                       |           |         |
+-----------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# mac-table-limit 10000
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-netsrv-evpn-mh)# no mac-table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
