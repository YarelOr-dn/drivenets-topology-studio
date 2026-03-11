system alarms admin-state
-------------------------

**Minimum user role:** operator

A global 'admin-state' enabled/disabled switch is provided to enable or disable the DNOS alarms. When this global switch is set to 'enabled', the alarms fault management monitoring is enabled, alarms are raised and cleard according to the system behavior. When this global switch is set to 'disabled', the alarms manager will be disabled, all raised alarms (active) alarms will be cleared (moved to alarms-history) and no new alarms will be raised.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system alarms

**Parameter table**

+-------------+-----------------------------------------+--------------+----------+
| Parameter   | Description                             | Range        | Default  |
+=============+=========================================+==============+==========+
| admin-state | DNOS Alarms admin-state enable/disabled | | enabled    | disabled |
|             |                                         | | disabled   |          |
+-------------+-----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-alarms)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
