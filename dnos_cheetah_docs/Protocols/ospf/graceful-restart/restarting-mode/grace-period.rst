protocols ospf graceful-restart restarting-mode grace-period
------------------------------------------------------------

**Minimum user role:** operator

Configures OSPF graceful restart restarting-mode grace-period.

**Command syntax: grace-period [grace-period]**

**Command mode:** config

**Hierarchies**

- protocols ospf graceful-restart restarting-mode

**Parameter table**

+--------------+-----------------------------------------------------------+---------+---------+
| Parameter    | Description                                               | Range   | Default |
+==============+===========================================================+=========+=========+
| grace-period | Specifying Graceful Restart restarting-mode grace period. | 60-1800 | 120     |
+--------------+-----------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)# restarting-mode
    dnRouter(cfg-protocols-ospf-gr-restarting-mode)# grace-period 200


**Removing Configuration**

To revert restarting grace-period to its default value
::

    dnRouter(cfg-ospf-gr-restarting-mode)# no grace-period

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
