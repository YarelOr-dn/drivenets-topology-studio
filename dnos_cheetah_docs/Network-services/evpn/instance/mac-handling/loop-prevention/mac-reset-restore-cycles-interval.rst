network-services evpn instance mac-handling loop-prevention mac-reset-restore-cycles-interval
---------------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure (for this EVPN instance) the mac-reset-restore-cycles-interval timer in hours, the default is 24 hours. The mac address is automatically restored after being suppressed for the mac-restore timer period.

**Command syntax: mac-reset-restore-cycles-interval [mac-reset-restore-cycles-interval]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+-----------------------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter                         | Description                                                                      | Range | Default |
+===================================+==================================================================================+=======+=========+
| mac-reset-restore-cycles-interval | Time interval to be applied following removal of suppression, before clearing    | 1-72  | \-      |
|                                   | the restore-cycles counter, assuming no further sanctions are applied.           |       |         |
+-----------------------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# mac-reset-restore-cycles-interval 50
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To restore the mac-reset-restore-cycles-interval period to its default value of 24 hours.
::

    dnRouter(cfg-inst-mh-lp)# no mac-reset-restore-cycles-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
