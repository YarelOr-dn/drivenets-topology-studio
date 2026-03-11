protocols ospf instance max-metric router-lsa metric-types
----------------------------------------------------------

**Minimum user role:** operator

By default, only igp metric will be modified to the configured max-metric once max-metric is desired (administrative, on start-up). 
Operator can select if max-metric value will be imposed for igp metric, te-metric or link delay
To set a new max-metric value:


**Command syntax: max-metric router-lsa metric-types {igp [igp-admin-state], te [te-admin-state], delay [delay-admin-state]}**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- At least one metric type must be configured

- Require at least one of the 3 metric types must be enabled (can be due to default enabled)

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
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance area_1
    dnRouter(cfg-protocols-ospf-inst)# max-metric router-lsa metric-types delay enabled

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance area_1
    dnRouter(cfg-protocols-ospf-inst)# max-metric router-lsa metric-types igp disabled te enabled


**Removing Configuration**

To revert all types to the default value:
::

    dnRouter(cfg-protocols-ospf-inst)# no max-metric router-lsa metric-types

To revert specific metric type to the default value:
::

    dnRouter(cfg-protocols-ospf-inst)# no max-metric router-lsa metric-types te

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
