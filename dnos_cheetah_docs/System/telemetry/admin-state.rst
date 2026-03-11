system telemetry admin-state
----------------------------

**Minimum user role:** operator

To enable/disable system wide dial-out telemetry:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system telemetry

**Parameter table**

+-------------+---------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                         | Range        | Default |
+=============+=====================================================================+==============+=========+
| admin-state | Set whether system wide telemetry dial-out feature enabled/disabled | | enabled    | enabled |
|             |                                                                     | | disabled   |         |
+-------------+---------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-telemetry)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
