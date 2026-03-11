network-services evpn instance mac-handling mac-table-limit
-----------------------------------------------------------

**Minimum user role:** operator

Configure the maximum number of entries in the MAC Table for this EVPN instance. When this limit is reached, new MAC addresses will not be added to the MAC Table.

**Command syntax: mac-table-limit [mac-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling

**Parameter table**

+-----------------+-------------------------------------------------------------------------------+-----------+---------+
| Parameter       | Description                                                                   | Range     | Default |
+=================+===============================================================================+===========+=========+
| mac-table-limit | the maximum number of entries allowed in the mac-table for this EVPN instance | 20-220000 | \-      |
+-----------------+-------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# mac-table-limit 10000
    dnRouter(cfg-evpn-inst-mh)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-evpn-inst-mh)# no mac-table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
