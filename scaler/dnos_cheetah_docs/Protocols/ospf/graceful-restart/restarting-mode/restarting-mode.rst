protocols ospf graceful-restart restarting-mode
-----------------------------------------------

**Minimum user role:** operator

Configures OSPF graceful restart restarting-mode. The command configures the minimum interval between two consecutive graceful restart events, below which the router must not enter restart mode.

**Command syntax: restarting-mode**

**Command mode:** config

**Hierarchies**

- protocols ospf graceful-restart

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)# restarting-mode
    dnRouter(cfg-protocols-ospf-gr-restarting-mode)#


**Removing Configuration**

To revert restarting-mode to its default value
::

    dnRouter(cfg-protocols-ospf-gr)# no restarting-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
