request system alarms clear-alarm
---------------------------------

**Minimum user role:** operator

**Command syntax: request system alarms clear alarm [alarm-operator-id]**

**Description:** Clears clearable alarms from the active alarms and moves them to the alarm history.

**Command mode:** operator

**Note:**

-  alarm-operator-id a unique id per alarm, presented under show system alarms details.

**Parameter table:**

+----------------------+------------------------------------------+----------------------------------------------+---------------+
| Parameter            | Description                              |  Values                                      | Default value |
+======================+==========================================+==============================================+===============+
| alarm-operator-id    | The alarm id                             |  Random generated number                     | \-            |
+----------------------+------------------------------------------+----------------------------------------------+---------------+


**Example**
::

	dnRouter# request system alarms clear alarm 1313

	dnRouter# request system alarms clear alarm 1312
    ERROR: alarm 1312 is not manual clearable
	dnRouter# request system alarms clear alarm 9999
    ERROR: Unknown id: 9999


.. **Help line:**


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.2        | Command introduced    |
+-------------+-----------------------+