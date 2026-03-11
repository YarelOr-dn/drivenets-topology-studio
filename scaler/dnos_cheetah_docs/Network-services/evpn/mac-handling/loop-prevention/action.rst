network-services evpn mac-handling loop-prevention action
---------------------------------------------------------

**Minimum user role:** operator

The default setting for the Loop-protection action for all EVPN Instances, the default is suppress.
The supression prevents local learning and moves from remote to local.
Blackholing causes any packets received with a src/dest MAC that is suppressed to be dropped.

**Command syntax: action [action]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling loop-prevention

**Parameter table**

+-----------+------------------------------------------------------------------+---------------+----------+
| Parameter | Description                                                      | Range         | Default  |
+===========+==================================================================+===============+==========+
| action    | Set the action to be applied when the MAC Address is suppressed. | | suppress    | suppress |
|           |                                                                  | | blackhole   |          |
+-----------+------------------------------------------------------------------+---------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# loop-prevention
    dnRouter(cfg-evpn-mh-lp)# action blackole
    dnRouter(cfg-evpn-mh-lp)#


**Removing Configuration**

To revert the admin-state configuration to its default value of suppress
::

    dnRouter(cfg-evpn-mh-lp)# no action

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
