system alarms clearable timer clearable-admin-state
---------------------------------------------------

**Minimum user role:** operator

A global 'clearable admin-state' enabled/disabled switch is provided to enable or disable the automatic clearance of the clearable alarms from the active alarms list, once the clearable timer has passed.
The timer counting starts once the admin-state was set to enabled alarms clearable timer functionality.
Setting the clearable to admin-state 'disabled', will cancel the clearable functionality.

**Command syntax: clearable timer clearable-admin-state [clearable-admin-state]**

**Command mode:** config

**Hierarchies**

- system alarms

**Parameter table**

+-----------------------+---------------------------------------------------+------------+----------+
| Parameter             | Description                                       | Range      | Default  |
+=======================+===================================================+============+==========+
| clearable-admin-state | DNOS Alarms clearable admin-state enable/disabled | enabled    | disabled |
|                       |                                                   | disabled   |          |
+-----------------------+---------------------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# clearable clearable-admin-state disabled


**Removing Configuration**

To revert clearable admin-state to default:
::

    dnRouter(cfg-system-alarms-clearable)# no clearable-admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
