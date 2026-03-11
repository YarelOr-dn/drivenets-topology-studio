protocols ospfv3 graceful-restart restarting-mode grace-period
--------------------------------------------------------------

**Minimum user role:** operator

Configures OSPFV3 graceful restart restarting-mode grace-period.

**Command syntax: grace-period [grace-period]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 graceful-restart restarting-mode

**Note**
- 'no grace-period' - reverts restarting grace-period to its default value.

**Parameter table**

+--------------+-----------------------------------------------------------+---------+---------+
| Parameter    | Description                                               | Range   | Default |
+==============+===========================================================+=========+=========+
| grace-period | Specifying Graceful Restart restarting-mode grace period. | 60-1800 | 120     |
+--------------+-----------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)# restarting-mode
    dnRouter(cfg-protocols-ospfv3-gr-restarting-mode)# grace-period 200


**Removing Configuration**

To revert restarting grace-period to its default value
::

    dnRouter(cfg-ospfv3-gr-restarting-mode)# no grace-period

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
