system alarms inventory alarm severity
--------------------------------------

**Minimum user role:** operator

Configures the alarm severity.

**Command syntax: severity [severity]**

**Command mode:** config

**Hierarchies**

- system alarms inventory alarm

**Note**

- Once the severity is updated all the active alarms matching the alarm name shall be updated with the new severity.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                                      | Range        | Default |
+===========+==================================================================================+==============+=========+
| severity  | Indicates the severity level of this alarm type. To provide a relevant severity  | | warning    | \-      |
|           | level based on a dynamic state and context, the severity level needs to be       | | minor      |         |
|           | defined by the instrumentation on the dynamic state, rather than being defined   | | major      |         |
|           | by the alarm type. Note that ‘clear’ is not a severity type.                     | | critical   |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# inventory
    dnRouter(cfg-system-alarms-inventory)# alarm <alarm-module> <alarm-name>
    dnRouter(cfg-alarms-inventory-alarm)# severity minor


**Removing Configuration**

To delete the severity configuration under the specific alarm:
::

    dnRouter(cfg-alarms-inventory-alarm)# no severity

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
