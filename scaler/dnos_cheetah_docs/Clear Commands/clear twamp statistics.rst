clear twamp statistics
----------------------

**Minimum user role:** operator

To clear TWAMP statistics:

**Command syntax: clear twamp statistics** {control [connection-id] data [session-id]}

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clear twamp statistics, by default command clears all twamp statistics for all sessions. Connection-id applies to control session, Session-id applies for data sessions. Clearing control connection-id does not clear statistics of its respective data sessions. In order to clear data session-id, user must mention the control connection-id.

 - session id as seen in show services twamp session

**Parameter table**

+------------------+----------------------------------------------------------------------+------------------------------------------------------------------+-------------------+
|                  |                                                                      |                                                                  |                   |
| Parameter        | Description                                                          | Value                                                            | Default           |
+==================+======================================================================+==================================================================+===================+
|                  |                                                                      | Available control session ID. See "show services twamp sessions" |                   |
| connection-id    | Clears TWAMP statistics for the specified control   session only.    |                                                                  | \-                |
+------------------+----------------------------------------------------------------------+------------------------------------------------------------------+-------------------+
|                  |                                                                      | Available data session ID. See "show services twamp sessions"    | \-                |
| session-id       | Clears TWAMP statistics for the specified data   session only.       |                                                                  |                   |
+------------------+----------------------------------------------------------------------+------------------------------------------------------------------+-------------------+


**Example**
::

	dnRouter# clear twamp statistics control [connection-id]
	dnRouter# clear twamp statistics control [connection-id] data [session-id]

	dnRouter# clear twamp statistics control 1
	dnRouter# clear twamp statistics control 1 data 2

	dnRouter# clear twamp statistics



.. **Help line:**

**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 11.2        | Command introduced                          |
+-------------+---------------------------------------------+