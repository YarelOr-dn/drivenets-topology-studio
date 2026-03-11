show system syncer remote-transactions view
-------------------------------------------

**Minimum user role:** viewer

Provides an overview of the remote transactions (originated by remote nodes) as were locally applied, in comparison to what is originaly commited on the remote nodes.


**Command syntax: show system syncer remote-transactions view** node-type [node-type] \| node-id [node-id]

**Command mode:** operational


**Note**

- Supported only on AI cluster formations.


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

+------------------------------------+-----------------------------------------------------------------------------------------------------------+------------+
| Parameter                          | Description                                                                                               | Range      |
+====================================+===========================================================================================================+============+
| Node Type                          | The type of the node used to filter the output to a specific node type. Currently only supported for NCP  | NCP, NCF   |
+------------------------------------+-----------------------------------------------------------------------------------------------------------+------------+
| Node ID                            | The ID of the node used to filter the output to a specific cluster element                                | /-         |
|                                    |                                                                                                           | /-         |
+------------------------------------+-----------------------------------------------------------------------------------------------------------+------------+
| Applied Remote Node Transaction ID | The remote transaction ID that is currently applied by current node and originated on the remote node     | /-         |
|                                    |                                                                                                           |            |
+------------------------------------+-----------------------------------------------------------------------------------------------------------+------------+
| Remote Node Transaction ID         | The remote transaction ID last commited on the remote node                                                | /-         |
|                                    |                                                                                                           |            |
+------------------------------------+-----------------------------------------------------------------------------------------------------------+------------+

**Example**
::

	dnRouter# show system syncer remote-transactions view

    | Node Type | Node ID  | Applied Remote Node Transaction ID | Remote Node Transaction ID   |
    |-----------+----------+------------------------------------+------------------------------+
    | NCP       | 0        | 0_2                                | 0_2                          |
    | NCP       | 1        | 1_0                                | 1_1                          |
    | NCP       | 2        | 2_5                                | 2_7                          |
    | NCP       | 3        | 3_25                               | 3_25                         |
    | NCP       | 4        | 4_17                               | 4_18                         |
    | NCP       | 6        | 6_12                               | 6_12                         |


	dnRouter# show system syncer remote-transactions view node-type NCP node-id 4

    | Node Type | Node ID  | Applied Remote Node Transaction ID | Remote Node Transaction ID   |
    |-----------+----------+------------------------------------+------------------------------+
    | NCP       | 4        | 4_17                               | 4_18                         |


    dnRouter# show system syncer remote-transactions view
    Error: Command not supported by current system.

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 19.10   | Command introduced                            |
+---------+-----------------------------------------------+
