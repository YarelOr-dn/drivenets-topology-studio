show dnos-internal qos summary
------------------------------

**Minimum user role:** viewer

To display a summary of the internal interfaces queue and the qos transmit counters:

**Command syntax: show dnos-internal qos summary** ncp [ncp-id]

**Command mode:** operation

.. **Note**

	- Some internal interfaces are used for Tx or Rx only. Those interfaces appear in the table only in their Rx or Tx capacity (i.e. no match on ingress for Tx only interfaces, etc.)

**Parameter table**

The displayed parameters are:

+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| Parameter      | Description                                                  | Values               | Range                                             |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| interface-name | Filter the displayed information for the specified interface | i<cname>-<f>/<s>/<p> | cname: cpu, oamp, rcy, sat                        |
|                |                                                              |                      | f: NCP number 0..192                              |
|                |                                                              |                      | s: slot number (currently 0)                      |
|                |                                                              |                      | p: local system port number example: ioamp-3/0/82 |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| Direction      | The transmission direction                                   | Transmit             | \-                                                |
|                |                                                              | Receive              |                                                   |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| qos-tag/queue  | The qos-tag value or queue priority                          | qos-tag              | 0..7                                              |
|                |                                                              | queue <value>        | 0..7                                              |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| Match (Kbps)   | The total number of Kbps that matched the rule               | \-                   | \-                                                |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| Drops (Kbps)   | The total number of Kbps that were dropped per rule          | \-                   | \-                                                |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| Match (pkts)   | The total number of packets that matched the rule            | \-                   | \-                                                |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+
| Drops (pkts)   | The total number of packets that were dropped per rule       | \-                   | \-                                                |
+----------------+--------------------------------------------------------------+----------------------+---------------------------------------------------+

**Example**
::

	dnRouter# show dnos-internal qos summary ncp 0

	| Interface    | Direction  | qos-tag/queue | Match[Kbps] | Drops[Kbps] | Match[pkts] | Drops[pkts] |
	|--------------+------------+---------------+-------------+-------------|-------------+-------------|
	| cputx-0/0/0  | Transmit   | qos-tag 0     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 1     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 2     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 3     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 4     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 5     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 6     | 2.1         | N/A         | 12000       | N/A         |
	| cputx-0/0/0  | Transmit   | qos-tag 7     | 2.1         | N/A         | 12000       | N/A         |
	| cpurx-0/0/84 | Receive    | priority 0    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 1    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 2    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 3    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 4    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 5    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 6    | 10.2        | 2.1         | 10000       | 3044        |
	| cpurx-0/0/84 | Receive    | priority 7    | 10.2        | 2.1         | 10000       | 3044        |

.. **Help line:** show summary of internal interfaces queue and qos transmit counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+


