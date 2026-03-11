clear system commit
-------------------

**Minimum user role:** operator

To cancel the tentative commit performed with the commit confirm command:

**Command syntax: clear system commit**

**Command mode:** operation

.. **Hierarchies**

**Note**

- Canceling a commit confirm command is equivalent to a rollback 1 action.

- If no pending commit or current commit is running, a message is displayed that no commit is scheduled.

- Any user with the right privileges can clear a pending commit.


.. **Parameter table**


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit confirm
	Commit confirm will automatically rollback in 10 minutes unless confirmed
	Commit succeeded by ADMIN at 27-Jan-2017 22:11:00 UTC
	
	dnRouter# clear system commit
	Configuration commit rollback by ADMIN at 27-Jan-2017 22:11:00 UTC
	
	.. (no configuration being done)
	dnRouter# clear system commit
	ERROR: No commit confirm scheduled
	
	
.. **Help line:** cancel the tentative commit performed by the user with the commit confirm command


**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 6.0         | Command introduced                          |
+-------------+---------------------------------------------+