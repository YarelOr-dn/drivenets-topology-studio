protocols isis graceful-restart
-------------------------------

**Minimum user role:** operator

Typically when a router restarts, all its peers detect that the device is not available and update their routing tables accordingly. To avoid routing flaps, graceful restart maintains the data-path behavior for a grace period to allow the device to restart. In this way, graceful restart allows the device to restart with minimal effect on the network. When enabled, the restarting routing device is not removed from the network topology during the restart period and the adjacencies are reestablished after restart is complete.

All graceful restart parameter values must be identical for all IS-IS instances.

To configure graceful restart:

**Command syntax: graceful-restart [admin-state]** grace-interval [grace-interval] helper [helper-state]

**Command mode:** config

**Hierarchies**

- protocols isis

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter      | Description                                                                      | Range        | Default  |
+================+==================================================================================+==============+==========+
| admin-state    | The administrative state of the graceful restart feature.                        | | enabled    | disabled |
|                |                                                                                  | | disabled   |          |
+----------------+----------------------------------------------------------------------------------+--------------+----------+
| grace-interval | Specifies how long (in seconds) the restarting device and its helpers continue   | 5-600        | 120      |
|                | to forward packets without disrupting network performance.                       |              |          |
+----------------+----------------------------------------------------------------------------------+--------------+----------+
| helper-state   | The administrative state of the graceful restart capability on the helper        | | enabled    | enabled  |
|                | device.                                                                          | | disabled   |          |
+----------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# graceful-restart disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# graceful-restart enabled
    dnRouter(cfg-protocols-isis)# graceful-restart enabled grace-interval 500 helper enabled
    dnRouter(cfg-protocols-isis)# graceful-restart enabled helper disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# graceful-restart disabled
    dnRouter(cfg-protocols-isis)# graceful-restart disabled grace-interval 500 helper enabled
    dnRouter(cfg-protocols-isis)# graceful-restart disabled helper disabled


**Removing Configuration**

To revert all graceful restart parameters to their default values:
::

    dnRouter(cfg-protocols-isis)# no graceful-restart

To revert the helper capability to the default state:
::

    dnRouter(cfg-protocols-isis)# no graceful-restart disabled helper

To revert the grace-interval to the default value:
::

    dnRouter(cfg-protocols-isis)# no graceful-restart enabled grace-interval

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 6.0     | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 9.0     | Changed default admin-state and helper-state, changed interval range |
+---------+----------------------------------------------------------------------+
| 10.0    | Removed requirement to specify admin-state in "no" commands          |
+---------+----------------------------------------------------------------------+
