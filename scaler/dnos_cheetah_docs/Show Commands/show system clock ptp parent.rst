show system clock ptp parent
----------------------------

**Minimum user role:** viewer

To display the PTP clock parent dataset:

**Command syntax: show system clock ptp parent** [node-name] [node-id]

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

	dnRouter# show system clock ptp parent ncp 0

	   PTP Clock Parent dataset parameters:
	       Identity:                 12:B:BB:FB:1F:28:1A:11
		   Port number:              2
	       GM identity:              D4:05:AA:FE:EF:08:9A:01
	       GM clock class:           6
		   GM clock accuracy:        0xFE
		   GM offset-log-variance:   0xFFFF
		   GM priority-2:            128

**Example**
::

	dnRouter# show system clock ptp parent

	ncp 0 (dn-ncp-0)

	   PTP Clock Parent dataset parameters:
	       Identity:                 12:B:BB:FB:1F:28:1A:11
		   Port number:              2
	       GM identity:              D4:05:AA:FE:EF:08:9A:01
	       GM clock class:           7
		   GM clock accuracy:        0xFE
		   GM offset-log-variance:   0xFFFF
		   GM priority-2:            128

	ncp 1 (dn-ncp-1)

	   PTP Clock Parent dataset parameters:
	       Identity:                 D4:05:AA:FE:EF:08:9A:01
		   Port number:              2
	       GM identity:              44:55:DA:1E:2F:33:9A:02
	       GM clock class:           6
		   GM clock accuracy:        0xFE
		   GM offset-log-variance:   0xFFFF
		   GM priority-2:            128

**Example**
::

    dnRouter# show system clock ptp

        Requested data is unavailable.

.. **Help line:** Display the PTP clock parent dataset

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
