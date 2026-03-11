protocols ospf graceful-restart helper-mode ietf admin-state
------------------------------------------------------------

**Minimum user role:** operator

Configures OSPF graceful restart IETF restarting-mode admin-state. The command enables/disables the graceful restart restarter behavior on the router.

**Command syntax: helper-mode ietf admin-state [ietf-helper-mode-admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf graceful-restart

**Parameter table**

+------------------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter                    | Description                                                                      | Range        | Default |
+==============================+==================================================================================+==============+=========+
| ietf-helper-mode-admin-state | Graceful Restart standard IETF helper mode admin state. When this leaf is set to | | enabled    | enabled |
|                              | true, the local system will accept Grace-LSAs from remote systems, and suppress  | | disabled   |         |
|                              | withdrawl of adjacencies of the system for the grace period specified            |              |         |
+------------------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)# helper-mode ietf admin-state enabled
    dnRouter(cfg-protocols-ospf-gr)# helper-mode ietf admin-state disabled


**Removing Configuration**

To revert helper-mode and admin-state to their default values
::

    dnRouter(cfg-protocols-ospf-gr)# no helper-mode ietf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
