network-services evpn instance mac-handling loop-prevention mac-restore-max-cycles
----------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the number of suppression-restore cycles allowed before permanent suppression. When a MAC address is permanently suppressed only a manual command will release the MAC address. Default is defined at the EVPN level.

**Command syntax: mac-restore-max-cycles [mac-restore-max-cycles]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+------------------------+-------------------------------------------+----------------------+---------+
| Parameter              | Description                               | Range                | Default |
+========================+===========================================+======================+=========+
| mac-restore-max-cycles | the number of suppression cycles allowed. | | 1-10               | \-      |
|                        |                                           | | infinite           |         |
|                        |                                           | | restore-manually   |         |
+------------------------+-------------------------------------------+----------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# mac-restore-max-cycles 6
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To restore the mac-restore-max-cycles period to its default value of infinite.
::

    dnRouter(cfg-inst-mh-lp)# no mac-restore-max-cycles

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
