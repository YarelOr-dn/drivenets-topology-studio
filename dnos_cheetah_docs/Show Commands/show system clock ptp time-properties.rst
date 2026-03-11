show system clock ptp time-properties
-------------------------------------

**Minimum user role:** viewer

To display the PTP clock time-properties dataset:

**Command syntax: show system clock ptp time-properties** [node-name] [node-id]

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

	dnRouter# show system clock ptp time-properties ncp 0

	   PTP Clock time-properties dataset parameters:
		   ToD:                      01-May-2023 11:09:00 UTC
		   Time source:              GPS
		   Current UTC offset:       1 sec
		   Current UTC offset valid: True
		   Leap59:                   False
		   Leap61:                   False
		   Time traceable:           False
		   Frequency traceable:      False
		   PTP timescale:            True

**Example**
::

	dnRouter# show system clock ptp time-properties

	ncp 0 (dn-ncp-0)

	   PTP Clock time-properties dataset parameters:
		   ToD:                      01-May-2023 11:09:00 UTC
		   Time source:              GPS
		   Current UTC offset:       1 sec
		   Current UTC offset valid: True
		   Leap59:                   False
		   Leap61:                   False
		   Time traceable:           False
		   Frequency traceable:      False
		   PTP timescale:            True

	ncp 1 (dn-ncp-1)

	   PTP Clock time-properties dataset parameters:
		   ToD:                      01-May-2023 11:09:01 UTC
		   Time source:              PTP
		   Current UTC offset:       1 sec
		   Current UTC offset valid: False
		   Leap59:                   False
		   Leap61:                   False
		   Time traceable:           False
		   Frequency traceable:      False
		   PTP timescale:            True

.. **Help line:** Display the PTP clock time-properties dataset

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
