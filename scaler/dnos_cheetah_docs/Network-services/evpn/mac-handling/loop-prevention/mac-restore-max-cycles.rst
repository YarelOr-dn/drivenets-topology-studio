network-services evpn mac-handling loop-prevention mac-restore-max-cycles
-------------------------------------------------------------------------

**Minimum user role:** operator

Configure the number of suppression-restore cycles allowed before a permanent supprfession, the default is infinite. When a MAC address is permanently suppressed only a manual command releases the MAC address.

**Command syntax: mac-restore-max-cycles [mac-restore-max-cycles]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling loop-prevention

**Parameter table**

+------------------------+-------------------------------------------+----------------------+----------+
| Parameter              | Description                               | Range                | Default  |
+========================+===========================================+======================+==========+
| mac-restore-max-cycles | the number of suppression cycles allowed. | | 1-10               | infinite |
|                        |                                           | | infinite           |          |
|                        |                                           | | restore-manually   |          |
+------------------------+-------------------------------------------+----------------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# loop-prevention
    dnRouter(cfg-evpn-mh-lp)# mac-restore-max-cycles 6
    dnRouter(cfg-evpn-mh-lp)#


**Removing Configuration**

To restore the mac-restore-max-cycles period to its default value of infinite.
::

    dnRouter(cfg-evpn-mh-lp)# no mac-restore-max-cycles

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
