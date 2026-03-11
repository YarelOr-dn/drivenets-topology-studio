network-services evpn instance mac-handling loop-prevention mac-restore-timer
-----------------------------------------------------------------------------

**Minimum user role:** operator

Configure the period of the mac-restore timer in seconds for this EVPN instance. The mac address is automatically restored after being suppressed for the mac-restore timer period. The default is defined at the EVPN level. 

**Command syntax: mac-restore-timer [mac-restore-timer]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+-------------------+-------------------------+------------+---------+
| Parameter         | Description             | Range      | Default |
+===================+=========================+============+=========+
| mac-restore-timer | the MAC Restore period. | 10-1000000 | \-      |
+-------------------+-------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# mac-restore-timer 600
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To restore the mac-restore period to its default value.
::

    dnRouter(cfg-inst-mh-lp)# no mac-restore-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
