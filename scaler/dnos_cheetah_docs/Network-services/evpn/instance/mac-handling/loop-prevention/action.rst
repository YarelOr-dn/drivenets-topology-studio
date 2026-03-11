network-services evpn instance mac-handling loop-prevention action
------------------------------------------------------------------

**Minimum user role:** operator

Loop-protection action for these EVPN Instances, the default is suppress.
Supression prevents local learning and moves from remote to local.
Blackholing causes any packets received with a src/dest MAC that is suppressed to be dropped.
The default value is defined at the EVPN level.

**Command syntax: action [action]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+-----------+------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                      | Range         | Default |
+===========+==================================================================+===============+=========+
| action    | Set the action to be applied when the MAC Address is suppressed. | | suppress    | \-      |
|           |                                                                  | | blackhole   |         |
+-----------+------------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# action blackhole
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To revert the action to its default value as defined at the EVPN level
::

    dnRouter(cfg-inst-mh-lp)# no action

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
