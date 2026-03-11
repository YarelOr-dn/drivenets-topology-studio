request system alarms history purge
-----------------------------------

**Minimum user role:** operator


To delete the alarms history:


**Command syntax: request system alarms history purge** before-time [datetime]

**Command mode:** operator

**Note:**

- If the before-time is provided, the alarm history will clear all the generated alarm records before the specified time.

**Parameter table:**

+---------------+-------------------------------------------------------------------------------------------+------------------------+
|               |                                                                                           |                        |
| Parameter     | Description                                                                               | Range                  |
+===============+===========================================================================================+========================+
| datetime      | The alarm history will clear all the generated alarm records before the specified time.   | yyyy-mm-ddThh:mm:ss    |
+---------------+-------------------------------------------------------------------------------------------+------------------------+

**Example**
::

	dnRouter# request system alarms history purge before-time 2022-11-13T17:59:59
    Done.
	dnRouter#
	dnRouter# request system alarms history purge
    Done.
	dnRouter#


.. **Help line:** deleting alarms history till the specified time or all in case not specified.


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 18.0.11     | Command introduced    |
+-------------+-----------------------+
