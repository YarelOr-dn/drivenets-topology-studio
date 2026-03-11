services flow-monitoring template flow-idle-timeout
---------------------------------------------------

**Minimum user role:** operator

Flow-idle-timeout defines how long a flow is considered active when no packet related to this flow is observed.

To configure the timeout for idle flows:

**Command syntax: flow-idle-timeout [flow-idle-timeout]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring template

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter         | Description                                                                      | Range   | Default |
+===================+==================================================================================+=========+=========+
| flow-idle-timeout | This parameter configures the time in seconds after which a Flow is expired if   | 0-86400 | 15      |
|                   | no more packets matching this Flow are received by the Cache. The parameter      |         |         |
|                   | value zero indicates infinity, meaning that there is no idle timeout. If not     |         |         |
|                   | configured by the user, the Monitoring Device sets this parameter. Note that     |         |         |
|                   | this parameter corresponds to flow-monitoringMeteringProcessCacheIdleTimeout in  |         |         |
|                   | the Flow-monitoring MIB module.                                                  |         |         |
+-------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# template myTemplate
    dnRouter(cfg-srv-flow-monitoring-myTemplate)# flow-idle-timeout 30


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myTemplate)# no flow-idle-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
