system alarms clearable-timer-state
-----------------------------------

**Minimum user role:** operator

Global switch that enables or disables the automatic clearance of the clearable-alarms from the active alarms list, once the clearable-timer has passed.
The timer starts counting once clearable-timer-state was enabled.
Setting the clearable clearable-timer-state to 'disabled', will cancel the clearable functionality.

**Command syntax: clearable-timer-state [clearable-admin-state]**

**Command mode:** config

**Hierarchies**

- system alarms

**Parameter table**

+-----------------------+-----------------------------------+--------------+----------+
| Parameter             | Description                       | Range        | Default  |
+=======================+===================================+==============+==========+
| clearable-admin-state | DNOS clearable alarms admin-state | | enabled    | disabled |
|                       |                                   | | disabled   |          |
+-----------------------+-----------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# clearable-timer-state disabled


**Removing Configuration**

Reverts clearable admin-state to default:
::

    dnRouter(cfg-system-alarms-clearable)# no clearable-timer-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
