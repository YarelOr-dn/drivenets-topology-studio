system telemetry subscription admin-state
-----------------------------------------

**Minimum user role:** operator

To enable/disable a telemetry subscription:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system telemetry subscription

**Parameter table**

+-------------+----------------------------------------------+--------------+---------+
| Parameter   | Description                                  | Range        | Default |
+=============+==============================================+==============+=========+
| admin-state | Set whether subscription is enabled/disabled | | enabled    | enabled |
|             |                                              | | disabled   |         |
+-------------+----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# subscription my-subscription
    dnRouter(cfg-system-telemetry-subscription)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-telemetry-subscription)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
