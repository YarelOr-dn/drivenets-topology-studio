protocols ospf graceful-restart restarting-mode admin-state
-----------------------------------------------------------

**Minimum user role:** operator

Configures OSPF graceful restart IETF restarting-mode admin-state. The command enables/disables the graceful restart restarter behavior on the router.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf graceful-restart restarting-mode

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | When the value of this leaf is set to true, graceful restart restarting-mode is  | | enabled    | disabled |
|             | enabled on the local system. In this case, the system will use Grace-LSAs to     | | disabled   |          |
|             | signal that it is restarting to its neighbors.                                   |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)# restarting-mode
    dnRouter(cfg-ospf-gr-restarting-mode)# admin-state enabled
    dnRouter(cfg-ospf-gr-restarting-mode)# admin-state disabled


**Removing Configuration**

To revert admin-state to its default value
::

    dnRouter(cfg-protocols-ospf-gr-restarting-mode)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
