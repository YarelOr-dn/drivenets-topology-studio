protocols ospfv3 graceful-restart restarting-mode admin-state
-------------------------------------------------------------

**Minimum user role:** operator

Configures OSPFv3 graceful restart IETF restarting-mode admin-state. The command enables/disables the graceful restart restarter behavior on the router.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 graceful-restart restarting-mode

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | When the value of this leaf is set to true, graceful restart restarting-mode is  | | enabled    | enabled |
|             | enabled on the local system. In this case, the system will use Grace-LSAs to     | | disabled   |         |
|             | signal that it is restarting to its neighbors.                                   |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)# restarting-mode
    dnRouter(cfg-ospfv3-gr-restarting-mode)# admin-state enabled
    dnRouter(cfg-ospfv3-gr-restarting-mode)# admin-state disabled


**Removing Configuration**

To revert admin-state to its default value
::

    dnRouter(cfg-protocols-ospfv3-gr-restarting-mode)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
