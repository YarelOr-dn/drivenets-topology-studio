show system syncer reachability status
--------------------------------------

**Minimum user role:** viewer

Displays the syncer reachability status and the connected nodes. The syncer infrastructure is used to synchronize a subset of configuration from the local nodes.


**Command syntax: show system syncer reachability status**

**Command mode:** operational


**Note**

- Supported only on AI cluster formations.

- Node ID - Defined per system-type. Refer to the 'show system backplane reachability' command for the expected ranges.

- Reachability Status
	- Connected - the node is connected to syncer infrastructure.
	- Disconnected - the node disconnected from syncer infrastructure.
	- Joining - the node is in the process of joining the syncer infrastructure.

- Downtime - Another node's downtime if that node is disconnected.

- All the reachability data is displayed from the NCP connectivity perspective of the cluster.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------------------------------+----------------------------------+
| Parameter           | Description                                                                                              | Range                            |
+=====================+==========================================================================================================+==================================+
| Node Type           | The type of the node used to filter the output to a specific NCE type. Currently only supported for NCP  | NCP, NCF                         |
+---------------------+----------------------------------------------------------------------------------------------------------+----------------------------------+
| Node ID             | The ID of the node used to filter the output to a specific cluster element                               | /-                               |
+---------------------+----------------------------------------------------------------------------------------------------------+----------------------------------+
| Reachability Status | The reachability status of other nodes                                                                   | Connected, Disconnected, Joining |
+---------------------+----------------------------------------------------------------------------------------------------------+----------------------------------+
| Downtime            | The downtime in seconds of nodes that are disconnected                                                   | /-                               |
+---------------------+----------------------------------------------------------------------------------------------------------+----------------------------------+

**Example**
::

	dnRouter# show system syncer reachability status

	Syncer Status for NCP 5:

	| Node Type | Node ID | Reachability Status | Downtime |
	|-----------+---------+---------------------+----------|
	| NCP       | 0       | Connected           | -        |
	| NCP       | 1       | Connected           | -        |
	| NCP       | 2       | Connected           | -        |
	| NCP       | 3       | Joining             | -        |
	| NCP       | 4       | Connected           | -        |
	| NCP       | 6       | Disconnected        | 23 sec   |


	dnRouter# show system syncer reachability status
	Error: Command not supported by current system.

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 19.10   | Command introduced                            |
+---------+-----------------------------------------------+
| 19.11   | Additional informaion                         |
+---------+-----------------------------------------------+