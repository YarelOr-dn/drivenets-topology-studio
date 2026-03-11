protocols ospfv3 graceful-restart helper-mode cisco admin-state
---------------------------------------------------------------

**Minimum user role:** operator

Configures OSPFv3 graceful restart cisco restarting-mode admin-state. The command enables/disables the graceful restart restarter behavior on the router.

**Command syntax: helper-mode cisco admin-state [cisco-helper-mode-admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 graceful-restart

**Parameter table**

+-------------------------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter                     | Description                                                                      | Range      | Default |
+===============================+==================================================================================+============+=========+
| cisco-helper-mode-admin-state | Graceful Restart: Cisco helper mode admin state. When this leaf is set to true,  | enabled    | enabled |
|                               | the local system will listen to the peer Link Local Signaling field and          | disabled   |         |
|                               | cooperate with peer - when it sets the LLS Restart bit - to do LSDB              |            |         |
|                               | re-synchronization when it receives empty neighbor list from that peer           |            |         |
+-------------------------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)# helper-mode cisco admin-state enabled
    dnRouter(cfg-protocols-ospfv3-gr)# helper-mode cisco admin-state disabled


**Removing Configuration**

To revert helper-mode and admin-state to their default values
::

    dnRouter(cfg-protocols-ospfv3-gr)# no helper-mode cisco

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 13.1    | Added support for OSPFv3 |
+---------+--------------------------+
