request system process restart 
-------------------------------

**Minimum user role:** admin

You can restart a process in the NCP or NCC. Some processes cannot be restarted specifically; in this case, running the command will cause the entire container to restart.

Datapath restart will cause the physical interfaces on the NCP to shut down during the restart operation.

To restart the operation of a specific process:


**Command syntax: request system process restart** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id]} **[container-name]** [process-name]

**Command mode:** operational

**Note**

- You will be prompted to confirm the restart.

- If you do not specify a node, the process(es) on the active NCC will be restarted.

..
	**Internal Note**

	- Yes/no validation should exist for process restart operations

	- Warning should be displayed for process start. For non-restartable processes, the operation will reset the entire container after process restart.

	- datapath reset should shut down physical interfaces during the reset operation on the relevant NCP


**Parameter table**

+-------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------------------------------+
|                   |                                                                                                                          |                                             |
| Parameter         | Description                                                                                                              | Range                                       |
+===================+==========================================================================================================================+=============================================+
|                   |                                                                                                                          |                                             |
| ncp-id            | The unique identifier of the NCP                                                                                         | 0..max number of NCP per cluster type -1    |
+-------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------------------------------+
|                   |                                                                                                                          |                                             |
| ncc-id            | The unique identifier of the NCC                                                                                         | 0..1                                        |
+-------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------------------------------+
|                   |                                                                                                                          |                                             |
| ncf-id            | The unique identifier of the NCF                                                                                         | 0..max number of NCF per cluster type -1    |
+-------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------------------------------+
|                   |                                                                                                                          |                                             |
| container-name    | The container in which the process runs.                                                                                 | See "show system"                           |
+-------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------------------------------+
|                   |                                                                                                                          |                                             |
| process-name      | The name of the process to restart. If you do not   specify a process, all process within the container will restart.    | See "show system"                           |
+-------------------+--------------------------------------------------------------------------------------------------------------------------+---------------------------------------------+

**Example**
::

	dnRouter# request system process restart ncp 0 forwarding-engine
	Warning: Are you sure you want to perform a process restart? (Yes/No) [No]? 
	
	
	dnRouter# request system process restart ncp 0 forwarding-engine sshd
	Warning: Are you sure you want to perform a process restart? (Yes/No) [No]? 
	
	dnRouter# request system process restart ncc 0 management-engine transaction_manager
	Warning: Are you sure you want to perform a process restart? this process restart will cause container restart (Yes/No) [No]? 
	

.. **Help line:** request system operations

**Command History**

+-------------+-------------------------------------------------+
|             |                                                 |
| Release     | Modification                                    |
+=============+=================================================+
|             |                                                 |
| 6.0         | Command introduced                              |
+-------------+-------------------------------------------------+
|             |                                                 |
| 9.0         | Command not supported                           |
+-------------+-------------------------------------------------+
|             |                                                 |
| 10.0        | Command reintroduced                            |
+-------------+-------------------------------------------------+
|             |                                                 |
| 11.0        | Added option to restart a process in the NCF    |
+-------------+-------------------------------------------------+