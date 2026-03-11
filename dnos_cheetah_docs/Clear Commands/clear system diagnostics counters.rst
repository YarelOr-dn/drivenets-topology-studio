clear system diagnostics counters
---------------------------------

**Minimum user role:** operator

You can use this command to clear all the counters for online diagnostics test results.

Supports clearing the following counters:

•	Packets Sent
•	Packets Lost
•	Last Fail Time
•	Last Uptime
•	Test Uptime
•	Test Fails.



**Command syntax: clear system diagnostics counters** test [test-type]

**Command mode:** operation

.. **Hierarchies**

**Note**

When test is specified, only the specific test counters are cleared. Otherwise all system diagnostics counters are cleared.

**Parameter table**

+---------------+--------------------+------------------+-------------------+
|               |                    |                  |                   |
| Parameter     | Description        | Value            | Default           |
+===============+====================+==================+===================+
|               |                    |                  |                   |
| test-type     | The type of test   | punt-datapath    | \-                |
|               |                    |                  |                   |
+---------------+--------------------+------------------+-------------------+


**Example**
::

	dnRouter# clear system diagnostics counters
	dnRouter# clear system diagnostics counters test punt-datapath


.. **Help line:** the type of the test

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+