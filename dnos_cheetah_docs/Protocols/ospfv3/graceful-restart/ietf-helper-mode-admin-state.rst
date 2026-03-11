protocols ospfv3 graceful-restart helper-mode admin-state
---------------------------------------------------------

**Minimum user role:** operator

Configures OSPFv3 graceful restart IETF restarting-mode admin-state. The command enables/disables the graceful restart restarter behavior on the router.

**Command syntax: helper-mode admin-state [ietf-helper-mode-admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 graceful-restart

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
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)# helper-mode admin-state enabled
    dnRouter(cfg-protocols-ospfv3-gr)# helper-mode admin-state disabled


**Removing Configuration**

To revert helper-mode and admin-state to their default values
::

    dnRouter(cfg-protocols-ospfv3-gr)# no helper-mode

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 13.1    | Added support for OSPFv3 |
+---------+--------------------------+
