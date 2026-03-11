show rollback
-------------

**Minimum user role:** viewer

To view the configuration of the transaction file:

**Command syntax: show rollback** [rollback-id]

**Command mode:** recovery 

**Parameter table**

+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------+-------+
| Parameter   | Description                                                                                                                                   | Range |
+=============+===============================================================================================================================================+=======+
| rollback-id | The rollback-id of the commit transaction file. If you do not specify a rollback-id, all rollbacks available in the system will be displayed. | 0..50 |
|             | A value of 0 will display the current configuration.                                                                                          |       |
+-------------+-----------------------------------------------------------------------------------------------------------------------------------------------+-------+

**Example**
::

	dnRouter(RECOVERY)# show rollback 1
	#dnRouter config-start [27-Jun-2017 22:05:01]
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
	
	dnRouter(RECOVERY)# show rollback
	| Id | Time                 | User          | Log                                         |
	|----|----------------------+---------------+---------------------------------------------|
	|  1 | 27-Jun-2017 22:05:01 | ADMIN         | user logged something for this rollback     |
	|  2 | 27-Jun-2017 22:05:01 | MyName2       |                                             |
	|  3 | 27-Jun-2017 22:05:01 | MyName2       | Successful commit! Created by MyName2.      |
	|    |                      |               | Update bgp configuration                    |
	

**Command History**

+---------+-----------------------------------------------------------------------+
| Release | Modification                                                          |
+=========+=======================================================================+
| 6.0     | Command introduced                                                    |
+---------+-----------------------------------------------------------------------+
| 11.0    | Command added to recovery mode                                        |
+---------+-----------------------------------------------------------------------+
| 13.1    | Added display of the transaction's origin (CLI/netconf) to the output |
+---------+-----------------------------------------------------------------------+


