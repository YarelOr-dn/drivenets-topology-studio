protocols ospfv3 graceful-restart restarting-mode
-------------------------------------------------

**Minimum user role:** operator

Configures OSPFv3 graceful restart restarting-mode. The command configures the minimum interval between two consecutive graceful restart events, below which the router must not enter restart mode.

**Command syntax: restarting-mode**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 graceful-restart

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)# restarting-mode
    dnRouter(cfg-protocols-ospfv3-gr-restarting-mode)#


**Removing Configuration**

To revert restarting-mode to its default value
::

    dnRouter(cfg-protocols-ospfv3-gr)# no restarting-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
