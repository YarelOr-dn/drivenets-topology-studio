network-services evpn instance mac-handling loop-prevention admin-state
-----------------------------------------------------------------------

**Minimum user role:** operator

Loop-protection for this EVPN Instance may be enabled/disabled. The default value is defined at the EVPN level.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+-------------+------------------------------------------------+--------------+---------+
| Parameter   | Description                                    | Range        | Default |
+=============+================================================+==============+=========+
| admin-state | Enable or Disable the loop-prevention handling | | enabled    | \-      |
|             |                                                | | disabled   |         |
+-------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# admin-state disabled
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To revert the admin-state configuration to its default value as defined at the EVPN level
::

    dnRouter(cfg-inst-mh-lp)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
