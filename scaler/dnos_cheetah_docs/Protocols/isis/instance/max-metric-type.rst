protocols isis instance max-metric-type
---------------------------------------

**Minimum user role:** operator

By default, only an IGP metric is modified to the configured max-metric once the max-metric is desired (administrative, on start-up, administrative per interface).
The operator can select if the max-metric value is imposed for the IGP metric, te-metric or link delay.
To set a new max-metric value:


**Command syntax: max-metric-type {igp [igp-admin-state], te [te-admin-state], delay [delay-admin-state]}**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- At least one metric type must be configured.

- It's require that at least one of the 3 metric types must be enabled (can be due to default enabled).

- The value of 16777215 for a given link result is that this link cannot be used in a topology that has the link metric as the metric type for which max-metric was used.

**Parameter table**

+-------------------+---------------------------------------------------------------------------+--------------+----------+
| Parameter         | Description                                                               | Range        | Default  |
+===================+===========================================================================+==============+==========+
| igp-admin-state   | Set IGP metric with max-metric value when such is desired                 | | enabled    | enabled  |
|                   |                                                                           | | disabled   |          |
+-------------------+---------------------------------------------------------------------------+--------------+----------+
| te-admin-state    | Set Traffic Engineering metric with max-metric value when such is desired | | enabled    | disabled |
|                   |                                                                           | | disabled   |          |
+-------------------+---------------------------------------------------------------------------+--------------+----------+
| delay-admin-state | Set Link Delay with max-metric value when such is desired                 | | enabled    | disabled |
|                   |                                                                           | | disabled   |          |
+-------------------+---------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# max-metric-type delay enabled

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# max-metric-type igp disabled te enabled


**Removing Configuration**

To revert all types to the default value:
::

    dnRouter(cfg-protocols-isis-inst)# no max-metric-type

To revert specific metric type to the default value:
::

    dnRouter(cfg-protocols-isis-inst)# no max-metric-type te

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
