show rollback
-------------

**Minimum user role:** viewer

To view the configuration of the transaction file:

**Command syntax: show rollback** [rollback-id]

**Command mode:** operational



.. **Note**

	- this command is aliased with "show file rollback".

	- Show rollback 0 displays the current configuration

**Parameter table**

+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------+-------+
| Parameter   | Description                                                                                                                                   | Range |
+=============+===============================================================================================================================================+=======+
| rollback-id | The rollback-id of the commit transaction file. If you do not specify a rollback-id, all rollbacks available in the system will be displayed. | 0..50 |
|             | A value of 0 will display the current configuration.                                                                                          |       |
+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------+-------+

**Example**
::

	dnRouter# show rollback 1
	#dnRouter config-start [27-Jun-2017 22:11:00]
	# version 6
	# user ADMIN
	# user logged something for this rollback
	system name dnRouter
	system login user RootUser 
	system login user RootUser description MyrootUser
	.
	.
	.
	#dnRouter config-end
	
	dnRouter# show rollback
	| Id | Time                 | User       | Via       | Log                                         |
	|----|----------------------+------------+-----------+---------------------------------------------|
	|  0 | 27-Jun-2017 22:05:01 | ADMIN      | cli       | user logged something for this rollback     |
	|  1 | 27-Jun-2017 22:06:01 | ADMIN      | cli       | user logged something for this rollback     |
	|  2 | 27-Jun-2017 22:07:01 | MyName2    | netconf   |                                             |
	|  3 | 27-Jun-2017 22:08:01 | MyName2    | cli       | Successful commit! Created by MyName2.      |
	|    |                      |            |           | Update bgp configuration                    |
	|  4 | 27-Jun-2017 20:09:01 | MyName     | cli       |                                             |
	
	

.. **Help line:** view the configuration of the transaction file

**Command History**

+---------+------------------------------------------------------------------------+
| Release | Modification                                                           |
+=========+========================================================================+
| 6.0     | Command introduced                                                     |
+---------+------------------------------------------------------------------------+
| 11.0    | Command added to recovery mode                                         |
+---------+------------------------------------------------------------------------+
| 13.1    | Added display of the transaction's origin (CLI/netconf) to the output  |
+---------+------------------------------------------------------------------------+
