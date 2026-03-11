network-services evpn mac-handling loop-prevention mac-restore-timer
--------------------------------------------------------------------

**Minimum user role:** operator

Configure the default period of the mac-restore timer in seconds, the default is 300 seconds. The MAC address is automatically restored after being suppressed for the mac-restore timer period.

**Command syntax: mac-restore-timer [mac-restore-timer]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling loop-prevention

**Parameter table**

+-------------------+---------------------------------------+------------+---------+
| Parameter         | Description                           | Range      | Default |
+===================+=======================================+============+=========+
| mac-restore-timer | the default MAC Restore Timer period. | 10-1000000 | 300     |
+-------------------+---------------------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# loop-prevention
    dnRouter(cfg-evpn-mh-lp)# mac-restore-timer 600
    dnRouter(cfg-evpn-mh-lp)#


**Removing Configuration**

To restore the mac-restore-timer period to its default value.
::

    dnRouter(cfg-evpn-mh-lp)# no mac-restore-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
