clear twamp session
-------------------

**Minimum user role:** operator

The clear twamp session command enables to terminate TWAMP sessions. The termination command operates on control sessions, which also terminates all associated data sessions.

To clear active TWAMP sessions:

**Command syntax: clear twamp session** [connection-id]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clear twamp statistics, by default command clears all twamp statistics for all sessions. Connection-id applies to control session, Session-id applies for data sessions. Clearing control connection-id does not clear statistics of its respective data sessions. In order to clear data session-id, user must mention the control connection-id.

 - session id as seen in show services twamp session

**Parameter table**

+------------------+---------------------------------------------------------------------+------------------------------------------------------------------+-------------------+
|                  |                                                                     |                                                                  |                   |
| Parameter        | Description                                                         | Value                                                            | Default           |
+==================+=====================================================================+==================================================================+===================+
|                  |                                                                     | Available control session ID. See "show services twamp sessions" |                   |
| connection-id    | Terminates only the TWAMP session that matches the specified ID     |                                                                  | \-                |
+------------------+---------------------------------------------------------------------+------------------------------------------------------------------+-------------------+

**Example**
::

	dnRouter# clear twamp session 57
	TWAMP control session 57 was successfully terminated

	dnRouter# clear twamp session

	TWAMP control session 57 was successfully terminated
	TWAMP control session 58 was successfully terminated


.. **Help line:** Clear active twamp session

**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 11.2        | Command introduced                          |
+-------------+---------------------------------------------+