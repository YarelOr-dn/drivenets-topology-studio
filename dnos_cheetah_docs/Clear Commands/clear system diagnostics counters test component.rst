clear system diagnostics counters test component
------------------------------------------------

**Minimum user role:** operator

Clears all system diagnostics counters per component or per component id.

**Command syntax: clear system diagnostics counters test [test-type] component [component-type]** [component-id]

**Command mode:** operation

.. **Hierarchies**

**Note**

- When component-id is specified, only the specified component-ids counters are cleared. Otherwise all system diagnostics counters per component-type are cleared.


**Parameter table**

+-------------------+--------------------------+--------------------------+-------------------+
|                   |                          |                          |                   |
| Parameter         | Description              | Value                    | Default           |
+===================+==========================+==========================+===================+
|                   |                          |                          |                   |
| test-type         | The type of test.        | punt-datapath            | \-                |
|                   |                          |                          |                   |
+-------------------+--------------------------+--------------------------+-------------------+
|                   |                          |                          |                   |
| component-type    | The type of component.   | ncp                      | all               |
|                   |                          |                          |                   |
+-------------------+--------------------------+--------------------------+-------------------+
|                   |                          |                          |                   |
| component-id      | The id of the component. | any legal ncp-id, all    | all               |
|                   |                          |                          |                   |
+-------------------+--------------------------+--------------------------+-------------------+


**Example**
::

	dnRouter# clear system diagnostics counters test punt-datapath
	dnRouter# clear system diagnostics counters

.. **Help line:** diagnostics component id counters to be cleared.

**Command History**

+-------------+------------------------------------+
|             |                                    |
| Release     | Modification                       |
+=============+====================================+
|             |                                    |
| 13.1        | Command introduced                 |
+-------------+------------------------------------+