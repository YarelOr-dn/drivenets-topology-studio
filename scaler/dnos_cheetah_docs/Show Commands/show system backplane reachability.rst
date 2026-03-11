show system backplane reachability
----------------------------------

**Minimum user role:** viewer

To display the system backplane fabric reachability matrix:



**Command syntax: show system backplane reachability** { ncp [ncp-id] \| ncf [ncf-id]}

**Command mode:** operational



..
	**Internal Note**

	- Expected number of NCEs according to pre defined system-type

	- For Standalone types, there is no reachability output "command not supported for this type of system"

**Parameter table**

+-----------+----------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                | Range  | Default |
+===========+============================================================================+========+=========+
| ncp-id    | Filters the display to show connectivity statistics for the specified NCP. | 0..255 | \-      |
+-----------+----------------------------------------------------------------------------+--------+---------+
| ncf-id    | Filters the display to show connectivity statistics for the specified NCF. | 0..611 | \-      |
+-----------+----------------------------------------------------------------------------+--------+---------+

For each interface, the following information is displayed:

+------------------+-------------------------------------------------------------------------------+
| Field            | Description                                                                   |
+==================+===============================================================================+
| System Type      | CL-16                                                                         |
|                  | CL-32                                                                         |
|                  | CL-48                                                                         |
|                  | CL-49                                                                         |
|                  | CL-51                                                                         |
|                  | CL-64                                                                         |
|                  | CL-76                                                                         |
|                  | CL-86                                                                         |
|                  | CL-96                                                                         |
|                  | CL-153                                                                        |
|                  | CL-192                                                                        |
|                  | CL-409                                                                        |
|                  | CL-AI-8K-400G                                                                 |
|                  | AI-256-400G-2                                                                 |
|                  | AI-8192-400G-2                                                                |
|                  | AI-72-800G-2                                                                  |
|                  | AI-768-400G-1                                                                 |
+------------------+-------------------------------------------------------------------------------+
| Connection state | Displays the state of the connection.                                         |
|                  | Reachable - At least one single fabric lane has reachability to neighbor node |
|                  | Not reachable - There are no fabric lanes with reachability to neighbor node  |
+------------------+-------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system backplane reachability

	System Type: CL-16

	Fabric Reachability State:

	NCF-0:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 96                     |
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 96                     |

	NCP-0:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 96                     |

	NCP-1:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 95                     |

	NCP-2:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | not-reachable       | 0                      |
	| NCP-1              | not-reachable       | 0                      |
	| NCP-3              | not-reachable       | 0                      |

	NCP-3:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 96                     |
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |


	dnRouter# show system backplane reachability ncf

	Fabric Reachability State:

	NCF-0:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 96                     |
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 96                     |

	dnRouter# show system backplane reachability ncp

	Fabric Reachability State:

	NCP-0:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 96                     |

	NCP-1:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 95                     |

	NCP-2:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | not-reachable       | 0                      |
	| NCP-1              | not-reachable       | 0                      |
	| NCP-3              | not-reachable       | 0                      |

	NCP-3:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 96                     |
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |

	dnRouter# show system backplane reachability ncp 0

	Fabric Reachability State:

	NCP-0:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-1              | reachable           | 95                     |
	| NCP-2              | not-reachable       | 0                      |
	| NCP-3              | reachable           | 96                     |

**Example**
::

	## NC-AI NCP node examples ##
	dnRouter# show system backplane reachability

	System Type: CL-AI-8K-400G (SA-36CD-S-NCP)

	Fabric Reachability State:

	NCP-16:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 8                      |
	| NCP-1              | reachable           | 7                      |
	| NCP-2              | reachable           | 8                      |
	| ...                |                     |                        |
	| NCP-15             | reachable           | 8                      |
	| NCP-17             | reachable           | 0                      |
	| ...                |                     |                        |
	| NCP-249            | reachable           | 8                      |


    dnRouter# show system backplane reachability ncp 100
    Node type not supported

	dnRouter# show system backplane reachability ncp 100
    Node ID not supported

**Example**
::

	## NC-AI NCF node examples ##
	dnRouter# show system backplane reachability

	System Type:CL-AI-8K-400G (SA-48CD-NCF)

	Fabric Reachability State:

	NCF-0:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 8                      |
	| NCP-1              | reachable           | 7                      |
	| NCP-2              | reachable           | 8                      |
	| ...                |                     |                        |
	| NCP-23             | reachable           | 8                      |
	| NCF-396            | reachable           | 8                      |
	| NCF-432            | reachable           | 8                      |
	| ...                | reachable           | 8                      |
	| NCF-576            | reachable           | 8                      |

	dnRouter# show system backplane reachability

    System Type:CL-AI-8K-400G (SA-48CD-NCF)

	Fabric Reachability State:

	NCF-396:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCF-0              | reachable           | 0                      |
	| NCF-36             | reachable           | 0                      |
	| ...                |                     |                        |
	| NCP-360            | reachable           | 8                      |

	dnRouter# show system backplane reachability ncf 432

	Fabric Reachability State:

	NCF-432:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCF-0              | reachable           | 8                      |
	| NCF-36             | reachable           | 8                      |
	| ...                |                     |                        |
	| NCF-360            | reachable           | 8                      |

    dnRouter# show system backplane reachability ncf 100
    	Node type not supported

	dnRouter# show system backplane reachability ncf 100
	    Node ID not supported

**Example**
::

	dnRouter# show system backplane reachability

	System Type: CL-AI-256-400G (SA-38E-NCP)

	Fabric Reachability State:

	NCP-1:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 144                    |
	| NCP-2              | reachable           | 136                    |
	| ...                |                     |                        |
	| NCP-7              | not-reachable       | 0                      |


    dnRouter# show system backplane reachability ncf 1
    Node type not supported

	dnRouter# show system backplane reachability ncp 100
    Node ID not supported

**Example**
::

	dnRouter# show system backplane reachability

	System Type: AI-256-400G-2 (SA-128E-NCF)

	Fabric Reachability State:

	NCF-1:

	| Neighbor Node      | Reachability State  | Reachable Active Lanes |
	|--------------------+---------------------+------------------------|
	| NCP-0              | reachable           | 72                     |
	| NCP-1              | reachable           | 72                     |
	| NCP-2              | reachable           | 68                     |
	| ...                |                     |                        |
	| NCP-7              | not-reachable       | 0                      |


    dnRouter# show system backplane reachability ncp 1
    Node type not supported

	dnRouter# show system backplane reachability ncf 3
    Node ID not supported

.. **Help line:** show system backplane reachability

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 11.5    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added support for CL-51 and CL-76 cluster types |
+---------+-------------------------------------------------+
| 17.2    | Added support for CL-49 and CL-86 cluster types |
+---------+-------------------------------------------------+
| 19.10   | Added support for new AI cluster types          |
+---------+-------------------------------------------------+
