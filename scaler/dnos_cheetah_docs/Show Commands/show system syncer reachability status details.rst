show system syncer reachability status details
----------------------------------------------

**Minimum user role:** viewer

Displays the current node's syncer connectivity status and additional informaion that better reflects the system state.


**Command syntax: show system syncer reachability status details**

**Command mode:** operational


**Note**

- Supported only on AI cluster formations.

- The following command expands the output of the "show system syncer reachability status" command with the connectivity of the current node to the cluster.

- Connectivity Statuses
	- Disconnected - the node is disconnected from the syncer infrastructure, appears only when ICE interface is disabled.
	- Connected - the node is connected to the syncer infrastructure.
	- Joining - the node is in the process of joining the syncer infrastructure.
	- Failed - the node failed while joinning the syncer infrastructure or in runtime.

- If additional informaion on the current state is available, it will be displayed in the output.

- The possible additional information per connectivity status:

+---------------------+-------------------------------------------------------------------------------------+
| Connectivity Status | Additional Information (Optional)                                                   |
+=====================+=====================================================================================+
| Connected           |                                                                                     |
+---------------------+-------------------------------------------------------------------------------------+
| Disconnected        | - ICE interface isn't enabled.                                                      |
+---------------------+-------------------------------------------------------------------------------------+
| Joining             | - discovering other cluster nodes.                                                  |
|                     | - waiting for automatical removal of unreachable node that had the same ip address. |
|                     | - pending cluster convergance.                                                      |
+---------------------+-------------------------------------------------------------------------------------+
| Failed              | - duplicate ip address.                                                             |
|                     | - internal error.                                                                   |
+---------------------+-------------------------------------------------------------------------------------+


**Example**
::

	dnRouter# show system syncer reachability status details

	Current Node Connectivity Status: Disconnected
	Additional Info: ICE interface isn't enabled.

	Syncer Status for NCP 1:

	| Node Type | Node ID | Reachability Status | Downtime |
	|-----------+---------+---------------------+----------|

	dnRouter# show system syncer reachability status details

	Current Node Connectivity Status: Joining
	Additional Info: discovering other cluster nodes.

	Syncer Status for NCP 1:

	| Node Type | Node ID | Reachability Status | Downtime |
	|-----------+---------+---------------------+----------|

	dnRouter# show system syncer reachability status details

	Current Node Connectivity Status: Joining
	Additional Info: pending cluster convergance.

	Syncer Status for NCP 1:

	| Node Type | Node ID | Reachability Status | Downtime |
	|-----------+---------+---------------------+----------|

	dnRouter# show system syncer reachability status details

	Current Node Connectivity Status: Connected

	Syncer Status for NCP 1:

	| Node Type | Node ID | Reachability Status | Downtime |
	|-----------+---------+---------------------+----------|
	| NCP       | 0       | Connected           | -        |
	| NCP       | 1       | Connected           | -        |
	| NCP       | 2       | Disconnected        | 80 sec   |
	| NCP       | 3       | Joining             | -        |

	dnRouter# show system syncer reachability status details

	Current Node Connectivity Status: Failed
	Additional Info: internal error.

	Syncer Status for NCP 1:

	| Node Type | Node ID | Reachability Status | Downtime |
	|-----------+---------+---------------------+----------|

	dnRouter# show system syncer reachability status details
	Error: Command not supported by current system.

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| TBD     | Command introduced                            |
+---------+-----------------------------------------------+