request system process stop
---------------------------

**Minimum user role:** admin

You can stop a running process in an NCC, NCP, or NCF. The system does not consider a process that has stopped as a failure event and so does not try to recover the process automatically. To start a process, run the command "request system process restart".

To stop the operation of a specific process:


**Command syntax: request system process stop {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id]} [container-name] [process-name]**

**Command mode:** operational

**Note**

- You will be prompted to confirm the process you want to stop.

- Stopping a process is the responsiblity of the user. The system may not function correctly when processes are stopped.

..
	**Internal Note**
	- Yes/no validation should exist for process restart operations

**Parameter table**

+-------------------+-----------------------------------------------------------------------+---------------------------------------------+----------------+
|                   |                                                                       |                                             |                |
| Parameter         | Description                                                           | Range                                       | Default        |
+===================+=======================================================================+=============================================+================+
|                   |                                                                       |                                             |                |
| ncp-id            | The unique identifier of the NCP.                                     | 0..max number of NCP per cluster type -1    | /-             |
+-------------------+-----------------------------------------------------------------------+---------------------------------------------+----------------+
|                   |                                                                       |                                             |                |
| ncc-id            | The unique identifier of the NCC.                                     | 0..1                                        | /-             |
+-------------------+-----------------------------------------------------------------------+---------------------------------------------+----------------+
|                   |                                                                       |                                             |                |
| ncf-id            | The unique identifier of the NCF.                                     | 0..max number of NCF per cluster type -1    | /-             |
+-------------------+-----------------------------------------------------------------------+---------------------------------------------+----------------+
|                   |                                                                       |                                             |                |
| container-name    | The container in which the process runs.                              | See "show system"                           | /-             |
+-------------------+-----------------------------------------------------------------------+---------------------------------------------+----------------+
|                   |                                                                       |                                             |                |
| process-name      | The name of the process to stop.                                      | See "show system"                           | /-             |
+-------------------+-----------------------------------------------------------------------+---------------------------------------------+----------------+

**Example**
::

	dnRouter# request system process stop ncc 0 routing-engine routing:pimd
	Warning: Are you sure you want to perform a process stop? (Yes/No) [No]?


.. **Help line:** request system operations

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
