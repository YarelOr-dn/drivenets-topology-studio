show system clock ptp foreign-masters
-------------------------------------

**Minimum user role:** viewer

To display the PTP clock list of all interfaces active foreign-masters of the system:

**Command syntax: show system clock ptp foreign-masters** [node-name] [node-id]

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
- Foreign-master data will be presented only for ports with non zero active foreign masters.
.. - By default (if node name not specified), output will show all the nodes in DNOS cluster.
.. - In Standalone mode, control ports are named ctrl-ncc-0/[0-1] and not ctrl-ncp-X/Y.

**Example**
::

	dnRouter# show system clock ptp foreign-masters ncp 0

	Interface ge400-0/0/0 clock Foreign-Master-Table dataset;
		State:                      Slave
		Best foreign-master index:  0

	| Idx | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
	|     |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
	|-----+-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
	| 0   | 05:06:A7:F8:E9:0A:9B:0C | False     | 0A:0E:0F:02:0A:11 | D4:05:AA:FE:EF:08:9A:01 | atomic-clock        | 140    | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |

	Interface ge400-0/0/1 clock Foreign-Master-Table dataset:
    State:                      Disabled

	Interface ge400-0/0/2 clock Foreign-Master-Table dataset:
		State:                      Slave
		Best foreign-master index:  0

	| Idx | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
	|     |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
	|-----+-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
	| 0   | 04:05:AA:FE:EF:08:9A:00 | False     | BA:4E:1F:28:3A:10 | D4:05:AA:FE:EF:08:9A:01 | PTP                 | 6      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |
	| 1   | 14:15:00:FD:CF:18:2B:E0 | False     | AA:AE:AF:A8:AA:A0 | D5:06:A7:F8:E9:01:9B:02 | internal-oscillator | 7      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |

	...

	dnRouter# show system clock ptp foreign-masters

	ncp 0 (dn-ncp-0)

		Interface ge400-0/0/0 clock Foreign-Master-Table dataset:
		State:                      Slave
		Best foreign-master index:  0

		| Idx | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
		|     |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
		|-----+-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
		| 0   | 05:06:A7:F8:E9:0A:9B:0C | False     | 0A:0E:0F:02:0A:11 | D4:05:AA:FE:EF:08:9A:01 | atomic-clock        | 140    | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |


		Interface ge400-0/0/3 clock Foreign-Master-Table dataset:
			State:                      Slave
			Best foreign-master index:  1

		| Idx | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
		|     |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
		|-----+-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
		| 0   | 04:05:AA:FE:EF:08:9A:00 | False     | BA:4E:1F:28:3A:10 | D4:05:AA:FE:EF:08:9A:01 | PTP                 | 6      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |
		| 1   | 14:15:00:FD:CF:18:2B:E0 | False     | AA:AE:AF:A8:AA:A0 | D5:06:A7:F8:E9:01:9B:02 | internal-oscillator | 7      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |

		...


	ncp 1 (dn-ncp-1)

		Interface ge400-1/0/1 clock Foreign-Master-Table dataset;
			State:                      Slave
			Best foreign-master index:  0

		| Idx | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
		|     |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
		|-----+-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
		| 0   | 05:06:A7:F8:E9:0A:9B:0C | False     | 0A:0E:0F:02:0A:11 | D4:05:AA:FE:EF:08:9A:01 | atomic-clock        | 140    | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |


.. **Help line:** Display the PTP clock foreign-masters datasets of all active interfaces

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
