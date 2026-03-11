network-services evpn mac-handling loop-prevention admin-state
--------------------------------------------------------------

**Minimum user role:** operator

Loop-protection enabled is the default setting for all evpn instances that are created.
The loop-protection may be disabled by default if this admin-state is set to disabled.
Individual EVPN instances can be configured otherwise to override this default setting.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling loop-prevention

**Parameter table**

+-------------+------------------------------------------------+--------------+---------+
| Parameter   | Description                                    | Range        | Default |
+=============+================================================+==============+=========+
| admin-state | Enable or Disable the loop-prevention handling | | enabled    | enabled |
|             |                                                | | disabled   |         |
+-------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# loop-prevention
    dnRouter(cfg-evpn-mh-lp)# admin-state disabled
    dnRouter(cfg-evpn-mh-lp)#


**Removing Configuration**

To revert the admin-state configuration to its default of enabled
::

    dnRouter(cfg-evpn-mh-lp)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
