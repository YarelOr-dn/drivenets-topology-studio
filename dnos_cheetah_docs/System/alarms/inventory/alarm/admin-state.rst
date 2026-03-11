system alarms inventory alarm admin-state
-----------------------------------------

**Minimum user role:** operator

To set the disable/enable for a specific alarm.
When the admin-state of an alarm is disabled, the alarm will not rise and
all active alarms of this alarm should be moved to the history.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system alarms inventory alarm

**Note**

- Setting the admin-state for the entire module is equal to setting the admin-state for each alarm separately.

**Parameter table**

+-------------+-----------------------------------------+--------------+---------+
| Parameter   | Description                             | Range        | Default |
+=============+=========================================+==============+=========+
| admin-state | DNOS Alarms admin-state enable/disabled | | enabled    | enabled |
|             |                                         | | disabled   |         |
+-------------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# inventory
    dnRouter(cfg-system-alarms-inventory)# alarm <alarm-module> <alarm-name>
    dnRouter(cfg-alarms-inventory-alarm)# admin-state disabled


**Removing Configuration**

To set the admin-state to default:
::

    dnRouter(cfg-alarms-inventory-alarm)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
