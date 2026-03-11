network-services bridge-domain mac-handling mac-table-aging-time
----------------------------------------------------------------

**Minimum user role:** operator

"Configure the default aging time for the entries in the MAC Table that will be set for any new bridge-domain instances.
Allowed aging time values are: 0 (no aging), 60, 120, 320, 640, 1280 seconds.
If the aging time is set to zero, no aging will be applied. The entries will remain until removed manually via the clear command.
The aging mechanism implementation has some variabilities such that the actual aging time is:

 60 +/- 20 seconds 
 120 +/- 40 seconds 
 320 +/- 160 seconds 
 640 +/- 320 seconds 
 1280 +/- 640 seconds"

**Command syntax: mac-table-aging-time [mac-table-aging-time]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain mac-handling

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+----------------------------+---------+
| Parameter            | Description                                                                      | Range                      | Default |
+======================+==================================================================================+============================+=========+
| mac-table-aging-time | the default mac-table aging time (in seconds), to be applied to Bridge-Domain    | 0, 60, 120, 320, 640, 1280 | 320     |
|                      | instances.                                                                       |                            |         |
+----------------------+----------------------------------------------------------------------------------+----------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bd
    dnRouter(cfg-netsrv-bd)# mac-handling
    dnRouter(cfg-netsrv-bd-mh)# mac-table-aging-time 320
    dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To restore the MAC Table aging time to its default value.
::

    dnRouter(cfg-netsrv-bd-mh)# no mac-table-aging-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
