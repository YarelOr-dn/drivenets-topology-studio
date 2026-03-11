protocols isis instance interface address-family ldp-sync
---------------------------------------------------------

**Minimum user role:** operator

The IS-IS-LDP synchronization allows IS-IS to advertise a link where LDP is not fully functional (for example, session not established). The link is then deemed as less preferred.

**Command syntax: ldp-sync [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**
- This command is valid only for ipv4-unicast address-family.
- This command is not applicable to loopback interfaces.
- Synchronization with LDP is not done by default.

**Parameter table**

+-------------+---------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                               | Range        | Default  |
+=============+===========================================================================+==============+==========+
| admin-state | The administrative state for enabling/disabling IS-IS-LDP synchronization | | enabled    | disabled |
|             |                                                                           | | disabled   |          |
+-------------+---------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# ldp-sync enabled

    dnRouter(cfg-protocols-isis-inst)# interface bundle-3
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# ldp-sync enabled


**Removing Configuration**

To revert ldp-sync to the default admin-state:
::

    dnRouter(cfg-inst-if-afi)# no ldp-sync

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
| 13.2    | Command updated    |
+---------+--------------------+
