commit confirm
--------------

**Minimum user role:** operator

In order for the commit to permanently apply, you must confirm the commit within the specified time using the commit command. Any user can confirm the commit. If the commit is not confirmed within the allocated time, the configuration automatically rolls back to the pre-commit state.

To confirm the commit:

**Command syntax: commit confirm** [confirm-time]

**Command mode:** operational

**Note**

- If another commit confirm is already running, you will not be able to confirm until the previous confirm is complete.

- To cancel a commit, use the "clear system commit" command.

- You can optionally display the currently pending commit confirm with the remaining time.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                 |                                                                                                                                                                            |             |             |
| Parameter       | Description                                                                                                                                                                | Range       | Default     |
+=================+============================================================================================================================================================================+=============+=============+
|                 |                                                                                                                                                                            |             |             |
| confirm-time    | The time (in minutes) to wait for a commit   confirm following a commit action. After this time, the commit will   automatically roll back if no commit action is done.    | 1..65535    | 10          |
+-----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit confirm
	Commit confirm will automatically rollback in 10 minutes unless confirmed
	Commit succeeded by ADMIN at 27-Jan-2017 22:11:00 UTC
	dnRouter(cfg)# commit
	Commit confirm
	
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit confirm 30
	Commit confirm will be automatically rolled back in 30 minutes unless confirmed
	
	...(no commit been made)
	Configuration commit rollback by ADMIN at 27-Jan-2017 22:11:00 UTC

.. **Help line:** Time (in minutes) before the commit will be automatically rollbacked

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+