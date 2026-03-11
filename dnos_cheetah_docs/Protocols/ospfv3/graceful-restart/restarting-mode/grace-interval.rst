protocols ospfv3 graceful-restart restarting-mode grace-interval
----------------------------------------------------------------

**Minimum user role:** operator

Configures OSPFV3 graceful restart restarting-mode grace-interval, which is the minimum interval between two consecutive graceful-restart events, below which the router must not enter restarting-mode.
To enable OSPFV3 graceful restart restarting-mode:

**Command syntax: grace-interval [grace-ineterval]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 graceful-restart restarting-mode

**Note**
- 'no grace-interval' - reverts restarting grace-interval to its default value.

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
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)# restarting-mode
    dnRouter(cfg-protocols-ospfv3-gr-restarting-mode)# grace-interval 1200


**Removing Configuration**

To revert restarting grace-interval to its default value
::

    dnRouter(cfg-ospfv3-gr-restarting-mode)# no grace-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
