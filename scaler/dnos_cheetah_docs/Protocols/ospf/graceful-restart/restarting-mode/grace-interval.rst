protocols ospf graceful-restart restarting-mode grace-interval
--------------------------------------------------------------

**Minimum user role:** operator

Configures OSPF graceful restart restarting-mode grace-interval, which is the minimum interval between two consecutive graceful-restart events, below which the router must not enter restarting-mode.

**Command syntax: grace-interval [grace-ineterval]**

**Command mode:** config

**Hierarchies**

- protocols ospf graceful-restart restarting-mode

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| grace-ineterval | Specifying Graceful Restart restarting-mode grace interval. The minimum allowed  | 60-3600 | 60      |
|                 | interval between consecutive graceful restart events.                            |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)# restarting-mode
    dnRouter(cfg-protocols-ospf-gr-restarting-mode)# grace-interval 1200


**Removing Configuration**

To revert restarting grace-interval to its default value
::

    dnRouter(cfg-ospf-gr-restarting-mode)# no grace-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
