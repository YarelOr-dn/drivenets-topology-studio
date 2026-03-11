protocols isis instance advertise max-metric
--------------------------------------------

**Minimum user role:** operator

The advertise max-metric command enables to administratively set IS-IS to advertise the maximum metric value for for all instance links to the value of the configured max-metric. When the value is set to 16777214 it will be considered as the least preferable in path calculations (but may still be chosen). When the value is set to 16777215 the router will be excluded from path calculations.

To advertise a max-metric value:


**Command syntax: advertise max-metric [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- The behavior is independent of the IS-IS overload behavior. max-metric will be advertised as long as the configuration is enabled.

- Metric-style must be set to "wide".

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Administrative setting IS-IS to advertise a max-metric value. See "isis instance | | enabled    | disabled |
|             | max-metric"                                                                      | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# advertise max-metric enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-afi)# no advertise max-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
