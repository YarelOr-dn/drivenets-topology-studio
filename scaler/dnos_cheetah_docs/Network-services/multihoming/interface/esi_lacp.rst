network-services multihoming interface esi lacp
-----------------------------------------------

**Minimum user role:** operator

Sets the ESI of the interface. 

**Command syntax: esi lacp [esi-lacp-source]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter       | Description                                                                      | Range     | Default |
+=================+==================================================================================+===========+=========+
| esi-lacp-source | Select whether the LACP System-id and Port key shall be taken from the remote CE | remote-id | \-      |
|                 | (future: or from the local side)                                                 |           |         |
+-----------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# esi lacp remote-id
    dnRouter(cfg-netsrv-mh-int)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no esi

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
