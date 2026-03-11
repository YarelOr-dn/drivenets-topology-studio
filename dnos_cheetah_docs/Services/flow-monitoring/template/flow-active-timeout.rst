services flow-monitoring template flow-active-timeout
-----------------------------------------------------

**Minimum user role:** operator

The flow-active-timeout defines how long an active flow can be cached in the flow cache table before it is aged out. In long flows, the flow records are aged out from the cache and the information is sent to the collector, even if packets related to this flow are still being observed. 

To configure the timeout for active flows:

**Command syntax: flow-active-timeout [flow-active-timeout]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring template

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter           | Description                                                                      | Range   | Default |
+=====================+==================================================================================+=========+=========+
| flow-active-timeout | This parameter configures the time in seconds after which a Flow is expired even | 0-86400 | 1800    |
|                     | though packets matching this Flow are still received by the Cache. The parameter |         |         |
|                     | value zero indicates infinity, meaning that there is no active timeout. If not   |         |         |
|                     | configured by the user, the Monitoring Device sets this parameter. Note that     |         |         |
|                     | this parameter corresponds to flow-monitoringMeteringProcessCacheActiveTimeout   |         |         |
|                     | in the Flow-monitoring MIB module.                                               |         |         |
+---------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# template myTemplate
    dnRouter(cfg-srv-flow-monitoring-myTemplate)# flow-active-timeout 60


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myTemplate)# no flow-active-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
