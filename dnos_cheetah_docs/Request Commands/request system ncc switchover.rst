request system ncc switchover
-----------------------------

**Minimum user role:** admin

When performing a switchover to the standby NCC, you will be prompted to confirm the switchover request. After the request is confirmed, the system will check if the standby NCC is ready for switchover:

- If the NCC is ready for switchover, the switchover will take place and a confirmation message will display. This will terminate all active SSH sessions. After the switchover process finishes, you will need to start a new CLI session.

- If the NCC is not ready for switchover, a failure message is displayed.


To trigger a switchover between the active NCC and the standby NCC:

**Command syntax: request system ncc switchover**

**Command mode:** operational

**Note**

- The switchover operation will terminate all SSH sessions. User will have to reconnect CLI session after the switchover has completed.


**Example**
::

	dnRouter# request system ncc switchover
	Warning: Are you sure you want to perform NCC switchover (Yes/No) [No]? Y
	Standby NCC is not ready for switchover, operation was aborted
	dnRouter#
	
	dnRouter# request system ncc switchover
	Warning: Are you sure you want to perform NCC switchover (Yes/No) [No]? Yes
	Switchover operation was initiated, all CLI sessions are terminated.

.. **Help line:** switchover from active NCC to standby one

**Command History**

+-------------+--------------------------+
|             |                          |
| Release     | Modification             |
+=============+==========================+
|             |                          |
| 6.0         | Command introduced       |
+-------------+--------------------------+
|             |                          |
| 9.0         | Command not supported    |
+-------------+--------------------------+
|             |                          |
| 11.0        | Command reintroduced     |
+-------------+--------------------------+