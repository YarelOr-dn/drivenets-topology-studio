show system ipv4 fragmentation statistics
-----------------------------------------

**Minimum user role:** viewer

To display IPv4 fragmentation statistics per NCP:



**Command syntax: show system ipv4 fragmentation statistics** ncp [ncp-id]

**Command mode:** operational



**Note**

- When NCP is note specified, fragmentation statistics for all operational NCPs are displayed. When IPv4 fragmentation in transit is disabled globally, statistics will show 0.

- For each active session, the command displays the number of packets that underwent fragmentation and the resulting number of fragments.


.. - When no NCP-ID is specified, fragmentation statistics per all NCPs in up state are presented

	- when ipv4 fragmentation in transit is disabled globally statistics will show 0.

**Parameter table**

+-----------+-------------------+--------+---------+
| Parameter | Description       | Range  | Default |
+===========+===================+========+=========+
| ncp-id    | The ID of the NCP | 1..191 | \-      |
+-----------+-------------------+--------+---------+

**Example**
::

	dnRouter# show system ipv4 fragmentation statistics

	IPv4 fragmentation statistics:
	  Fragmented IPv4 packets: 234092
	  Generated IPv4 fragment packets: 1404482


	dnRouter# show system ipv4 fragmentation statistics ncp 9

	ncp-9:

	IPv4 fragmentation statistics:
	  Fragmented IPv4 packets: 34092
	  Generated IPv4 fragment packets: 201482


	dnRouter# show system ipv4 fragmentation statistics ncp 3

	ncp-3:

	IPv4 fragmentation statistics:
	  Fragmented IPv4 packets: 0
	  Generated IPv4 fragment packets: 0


	dnRouter# show system ipv4 fragmentation statistics ncp 17

	ncp 17 is not available

.. **Help line:** Display IPv4 fragmentation statistics per NCP


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


