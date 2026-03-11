show system clock ptp servo
---------------------------

**Minimum user role:** viewer

To display the PTP servo thread status:

**Command syntax: show system clock ptp servo** [node-name] [node-id]

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
- When the PTP feature is disabled or node is not in an operational state, data will not be available.

.. - By default (if node name not specified), output will show all the nodes in DNOS cluster.
.. - In Standalone mode, control ports are named ctrl-ncc-0/[0-1] and not ctrl-ncp-X/Y.

**Example**
::

	dnRouter# show system clock ptp servo ncp 0

	PTP servo state parameters:
	   State:       	        phase-locked
	   Config:
	   State duration:          1 days, 3:52:13
	   Lock status:             locked
	   Frequency correction:  	1 ppt
	   Phase correction:        2 nsec
	   Offset from master:      10 nsec
	   Mean path delay:         97 nsec
	   Sync packet rate:        3
	   Delay packet rate:       4

**Example**
::

	dnRouter# show system clock ptp servo

	ncp 0 (dn-ncp-0)

	PTP servo state parameters:
	   State:       	        holdover
	   Config:
	   State duration:          2 days, 11:12:31
	   Lock status:             unlocked
	   Frequency correction:  	2 ppt
	   Phase correction:        2 nsec
	   Offset from master:      11 nsec
	   Mean path delay:         67 nsec
	   Sync packet rate:        2
	   Delay packet rate:       3

	ncp 1 (dn-ncp-1)

	PTP servo state parameters:
	   State:       	        frequency-locked
	   Config:
	   State duration:          0 days, 4:12:3
	   Lock status:             locked
	   Frequency correction:  	2 ppt
	   Phase correction:        2 nsec
	   Offset from master:      11 nsec
	   Mean path delay:         67 nsec
	   Sync packet rate:        2
	   Delay packet rate:       3

**Example**
::

    dnRouter# show system clock ptp servo

        Requested data is unavailable.

.. **Help line:** Display the PTP clock servo state

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
