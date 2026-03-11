show system clock synce
-----------------------

**Minimum user role:** viewer

To display Synchronous-Ethernet timing attributes of the system:

**Command syntax: show system clock synce** [node-name] [node-id]

**Command mode:** operational

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter | Description                                                                                                                                | Range              |
+===========+============================================================================================================================================+====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP                |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..191        |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Note**

.. - By default (if node name not specified), output will show all the nodes in DNOS cluster.
.. - In Standalone mode, control ports are named ctrl-ncc-0/[0-1] and not ctrl-ncp-X/Y.

**Example**
::

	dnRouter# show system clock synce ncp 0

	   Clock configuration:
	       SyncE:  enabled
	       Network-type: option-1
	       QL-based selection: enabled
	       10MHz SMB direction: input

	   Active clock state:
	       DPLL ref clock state: locked
	       Active source name: ge400-0/0/1
	       Active source alarm raised: true (alarm reason: esmc-to)

	   Service state : OK
	   Last state change: 1 day, 01:01:05
	   Last holdover duration: 10 seconds
	   Last ref source change time: 1 day, 01:11:32
	   Clock quality level: ql_prc

	Timing reference source list:

	| Interface          | Prio. | QL      | WTR   | holdoff | holdoff     | holdoff          | lockout | signal | alarm  | alarm       | WTR         | wtr remain |
	|                    |       |         | [min] | [mSec]  | status      | events           |         | fail   | raised | reason      | status      | [min]      |
	+--------------------+-------+---------+-------+---------+-------------+------------------+---------+--------+--------+-------------+-------------+------------|
	| ge400-0/0/0        | 2     | ql_dnu  | 5     | 300     | not-running | 10               | false   | false  | false  |             | not-running | 5          |
	| *ge400-0/0/1       | 3     | ql-prc  | 5     | 300     | not-running | 1                | false   | false  | true   | esmc-to     | runnnig     | 1          |
	| smb_10mhz          | 1     | ql-prc  | 5     | 300     | not-running | 0                | true    | false  | false  |             | not-running | 5          |

	* Active source clock

	dnRouter# show system clock synce

	ncp 0 (dn-ncp-0)

	   Clock configuration:
	       SyncE:  enabled
	       Network-type: option-1
	       QL-based selection: enabled
	       10MHz SMB direction: input

	   Active clock state:
	       DPLL ref clock state: locked
	       Active source name: ge400-0/0/1
	       Active source alarm raised: false

	   Service state : FAIL
	   Last state change: 1 day, 01:01:05
	   Last holdover duration: 10 seconds
	   Last ref source change time: 1 day, 01:11:32
	   Clock quality level: ql_prc

	Timing reference source list:

	| Interface          | Prio. | QL      | WTR   | holdoff | holdoff     | holdoff          | lockout | signal | alarm  | alarm       | WTR         | wtr remain |
	|                    |       |         | [min] | [mSec]  | status      | events           |         | fail   | raised | reason      | status      | [min]      |
	+--------------------+-------+---------+-------+---------+-------------+------------------+---------+--------+--------+-------------+-------------+------------|
	| ge400-0/0/0        | 2     | ql_dnu  | 5     | 300     | not-running | 10               | false   | false  | false  |             | not-running | 5          |
	| *ge400-0/0/1       | 3     | ql_prc  | 5     | 300     | not-running | 1                | false   | false  | false  |             | runnnig     | 1          |
	| smb_10mhz          | 1     | ql_prc  | 5     | 300     | not-running | 0                | true    | false  | true   | ESMC TO     | not-running | 5          |

	* Active source clock

	ncp 1 (dn-ncp-1)

	   Clock configuration:
	       SyncE:  enabled
	       Network-type: option-1
	       QL-based selection: enabled
	       10MHz SMB direction: input

	   Active clock state:
	       DPLL ref clock state: locked
	       Active source name: ge400-0/0/0
	       Active source alarm raised: false

	   Service state : OK
	   Last state change: 1 day, 01:01:05
	   Last holdover duration: 10 seconds
	   Last ref source change time: 1 day, 01:11:32
	   Clock quality level: ql_prc

	Timing reference source list:

	| Interface          | Prio. | QL      | WTR   | holdoff | holdoff     | holdoff          | lockout | signal | alarm  | alarm       | WTR         | wtr remain |
	|                    |       |         | [min] | [mSec]  | status      | events           |         |        | raised | reason      | status      | [min]      |
	+--------------------+-------+---------+-------+---------+-------------+------------------+---------+--------+--------+-------------+-------------+------------|
	| *ge400-1/0/10      | 1     | ql_prc  | 5     | 400     | not-running | 10               | false   | false  | false  |             | not-running | 5          |
	| ge400-1/0/11       | 3     | ql_sec  | 5     | 300     | not-running | 1                | false   | false  | false  |             | runnnig     | 1          |
	| smb_10mhz          | 2     | ql_prc  | 5     | 300     | not-running | 0                | true    | false  | true   | OOR         | not-running | 5          |

	* Active source clock

	dnRouter# show system clock synce ncp 0

	   Clock configuration:
	       SyncE:  enabled
	       Network-type: option-1
	       QL-based selection: enabled
	       10MHz SMB direction: input

	   Active clock state:
	       DPLL ref clock state: locked
	       Active source name: ge400-0/0/1
	       Active source alarm raised: true (alarm reason: timing-loop)

	   Service state : OK
	   Last state change: 1 day, 01:01:05
	   Last holdover duration: 10 seconds
	   Last ref source change time: 1 day, 01:11:32
	   Clock quality level: ql_prc

	Timing reference source list:

	| Interface          | Prio. | QL      | WTR   | holdoff | holdoff     | holdoff          | lockout | signal | alarm  | alarm       | WTR         | wtr remain |
	|                    |       |         | [min] | [mSec]  | status      | events           |         | fail   | raised | reason      | status      | [min]      |
	+--------------------+-------+---------+-------+---------+-------------+------------------+---------+--------+--------+-------------+-------------+------------|
	| ge400-0/0/0        | 2     | ql_dnu  | 5     | 300     | not-running | 10               | false   | false  | false  |             | not-running | 5          |
	| *ge400-0/0/1       | 3     | ql-prc  | 5     | 300     | not-running | 1                | false   | false  | true   | timing-loop | runnnig     | 1          |
	| smb_10mhz          | 1     | ql-prc  | 5     | 300     | not-running | 0                | true    | false  | false  |             | not-running | 5          |

	* Active source clock

.. **Help line:** Display system or node specific synchronous-ethernet information

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 17.2    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
