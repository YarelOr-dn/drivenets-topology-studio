clear system diagnostics counters test
--------------------------------------

**Minimum user role:** operator

Clears system diagnostics counters per test or per component.


**Command syntax: clear system diagnostics counters test [test-type]** component [component-type]

**Command mode:** operation

.. **Hierarchies**

**Note**

When component is specified, only the specified component/s counters are cleared. Otherwise all system diagnostics counters per test are cleared.


**Parameter table**


+-------------------+------------------------+------------------+-------------------+
|                   |                        |                  |                   |
| Parameter         | Description            | Value            | Default           |
+===================+========================+==================+===================+
|                   |                        |                  |                   |
| test-type         | The type of test       | punt-datapath    | \-                |
+-------------------+------------------------+------------------+-------------------+
|                   |                        |                  |                   |
| component-type    | The type of component. | ncp              | all               |
+-------------------+------------------------+------------------+-------------------+


**Example**
::

	dnRouter# clear system diagnostics counters test punt-datapath
	dnRouter# clear system diagnostics counters test punt-datapath component ncp



.. **Help line:** diagnostics component id counters to be cleared.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+