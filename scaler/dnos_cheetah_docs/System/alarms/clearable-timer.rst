system alarms clearable timer
-----------------------------

**Minimum user role:** operator

"A global timer that specifies the amount of time in minutes from rise-time after which a clearable alarm should be cleared.

**Command syntax: clearable timer [clearable-timer]**

**Command mode:** config

**Hierarchies**

- system alarms

**Parameter table**

+-----------------+------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                  | Range   | Default |
+=================+==============================================================================+=========+=========+
| clearable-timer | Specifies the timer that starts when alarm that is manually clearable raise. | 1-10800 | 1440    |
+-----------------+------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# clearable timer 120


**Removing Configuration**

To revert timer to default:
::

    dnRouter(cfg-system-alarms)# no clearable timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
