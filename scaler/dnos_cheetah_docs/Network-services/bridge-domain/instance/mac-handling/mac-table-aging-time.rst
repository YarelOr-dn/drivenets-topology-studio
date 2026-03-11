network-services bridge-domain instance mac-handling mac-table-aging-time
-------------------------------------------------------------------------

**Minimum user role:** operator

"Configure the aging time for the entries in the MAC Table for this EVPN instance.
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

- network-services bridge-domain instance mac-handling

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+----------------------------+---------+
| Parameter            | Description                                                                      | Range                      | Default |
+======================+==================================================================================+============================+=========+
| mac-table-aging-time | the aging time (in seconds) for the entries in the mac-table for this            | 0, 60, 120, 320, 640, 1280 | \-      |
|                      | Bridge-Domain instance                                                           |                            |         |
+----------------------+----------------------------------------------------------------------------------+----------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bd
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# mac-handling
    dnRouter(cfg-bd-inst-mh)# mac-table-aging-time 320
    dnRouter(cfg-bd-inst-mh)#


**Removing Configuration**

To restore the MAC Table aging time to its default value.
::

    dnRouter(cfg-bd-inst-mh)# no mac-table-aging-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
