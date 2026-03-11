show system clock ptp stats
---------------------------

**Minimum user role:** viewer

To display the PTP clock statistics:

**Command syntax: show system clock ptp stats** [node-name] [node-id]

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

  dnRouter# show system clock ptp stats ncp 0

  PTP clock statistics:
    Received packets:             128
    Sent packets:                 256
    Discarded packets:            3
    L2 received packets:		  48
    Receive queue overflows:      2

**Example**
::

  dnRouter# show system clock ptp stats

	ncp 0 (dn-ncp-0)

	PTP clock statistics:
		Received packets:             128
		Sent packets:                 256
		Discarded packets:            3
		L2 received packets:		  48
		Receive queue overflows:      2

	ncp 1 (dn-ncp-1)

	PTP clock statistics:
		Received packets:             0
		Sent packets:                 0
		Discarded packets:            0
		L2 received packets:		  0
		Receive queue overflows:      0

**Example**
::

    dnRouter# show system clock ptp stats
        Requested data is unavailable.

.. **Help line:** Display PTP clock statistics

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
