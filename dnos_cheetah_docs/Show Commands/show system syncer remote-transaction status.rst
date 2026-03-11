show system syncer remote-transaction status
--------------------------------------------

**Minimum user role:** viewer

Displays whether or not a nodes last local transaction was applied successfully on each of the remote nodes.


**Command syntax: show system syncer remote-transaction status** node-type [node-type] \| node-id [node-id]

**Command mode:** operational



**Note**

- Supported only on AI cluster formations.

- Remote Transaction Status
    - Succeeded - local NCP transaction was successfully applied on remote node.
    - Failed - local NCP transaction failed to be applied by remote node.
    - N/A - local NCP transaction status on a remote NCP is unknown.
    - Pending - local NCP transaction is pending to be processed by remote node.

**Parameter table**

+--------------------+-----------------------------------------------------------------------------------------------------------+---------------------------+-----------------+
| Parameter          | Description                                                                                               | Range                     | Default value   |
+====================+===========================================================================================================+===========================+=================+
| Node Type          | The type of the node used to filter the output to a specific node type. Currently only supported for NCP  | NCP, NCF                  | /-              |
+--------------------+-----------------------------------------------------------------------------------------------------------+---------------------------+-----------------+
| Node ID            | The ID of the node used to filter the output to a specific cluster element                                | from the existing range   | /-              |
|                    |                                                                                                           | in the show command       |                 |
+--------------------+-----------------------------------------------------------------------------------------------------------+---------------------------+-----------------+

The following information is displayed:

+---------------------------+-----------------------------------------------------------------------------------------------------------+-----------------------------------+
| Parameter                 | Description                                                                                               | Range                             |
+===========================+===========================================================================================================+===================================+
| Node Type                 | The type of the node used to filter the output to a specific node type. Currently only supported for NCP  | NCP, NCF                          |
+---------------------------+-----------------------------------------------------------------------------------------------------------+-----------------------------------+
| Node ID                   | The ID of the node used to filter the output to a specific cluster element                                | /-                                |
|                           |                                                                                                           | /-                                |
+---------------------------+-----------------------------------------------------------------------------------------------------------+-----------------------------------+
| Remote Transaction ID     | The ID of the remote transaction originated by the current node                                           | /-                                |
+---------------------------+-----------------------------------------------------------------------------------------------------------+-----------------------------------+
| Remote Transaction Status | The status of the remote transaction on the remote node                                                   | Succeeded, Failed, N/A, Pending   |
+---------------------------+-----------------------------------------------------------------------------------------------------------+-----------------------------------+
| Version                   | The peer's DNOS version                                                                                   | /-                                |
+---------------------------+-----------------------------------------------------------------------------------------------------------+-----------------------------------+

**Example**
::

	dnRouter# show system syncer remote-transaction status

    | Node Type | Node ID  | Remote Transaction ID | Remote Transaction Status    | Version  |
    |-----------+----------+-----------------------+------------------------------+----------+
    | NCP       | 0        | 5_25                  | Failed                       | v18_3_40 |
    | NCP       | 1        | 5_25                  | N/A                          | v18_3_40 |
    | NCP       | 2        | 5_25                  | Succeeded                    | v18_3_40 |
    | NCP       | 3        | 5_25                  | Succeeded                    | v18_3_40 |
    | NCP       | 4        | 5_25                  | Failed                       | V19.10   |
    | NCP       | 6        | 5_25                  | N/A                          | V19.10   |


	dnRouter# show system syncer remote-transaction status node-type NCP

    | Node Type | Node ID  | Remote Transaction ID | Remote Transaction Status    | Version  |
    |-----------+----------+-----------------------+------------------------------+----------+
    | NCP       | 0        | 5_25                  | Failed                       | v18_3_40 |
    | NCP       | 1        | 5_25                  | N/A                          | v18_3_40 |
    | NCP       | 2        | 5_25                  | Succeeded                    | v18_3_40 |
    | NCP       | 3        | 5_25                  | Succeeded                    | v18_3_40 |
    | NCP       | 4        | 5_25                  | Failed                       | V19.10   |
    | NCP       | 6        | 5_25                  | N/A                          | V19.10   |


	dnRouter# show system syncer remote-transaction status node-type NCP node-id 3

    | Node Type | Node ID  | Remote Transaction ID | Remote Transaction Status    | Version  |
    |-----------+----------+-----------------------+------------------------------+----------+
    | NCP       | 3        | 5_25                  | Succeeded                    | v18_3_40 |


    dnRouter# show system remote-transaction status
    Error: Command not supported by current system.

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 19.10   | Command introduced                            |
+---------+-----------------------------------------------+
