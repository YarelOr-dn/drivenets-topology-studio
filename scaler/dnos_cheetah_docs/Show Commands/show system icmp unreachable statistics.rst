show system icmp unreachable statistics
---------------------------------------------

**Minimum user role:** viewer

To display ICMP unreachable statistics counters per NCP:



**Command syntax: show system icmp unreachable statistics** ncp [ncp-id]

**Command mode:** operational



.. 
	**Internal Note**

	- When no NCP-ID is specified, statistics per all NCPs in up state are presented

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                                                                                         | Value  | Default |
+===========+=====================================================================================================================================================+========+=========+
| ncp-id    | Displays the unreachable statistics counters for the specified NCP only. If you do not specify an NCP, the counters for all NCPs will be displayed. | 0..191 | All     |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# show system icmp unreachable statistics

	ncp-0:

	Dropped packets with DF flag: 123
	Generated ICMP type 3 code 4 messages: 100
	Generated ICMPv6 type 2 code 0 messages: 23


	ncp-1:

	Dropped packets with DF flag: 223
	Generated ICMP type 3 code 4 messages: 210
	Generated ICMPv6 type 2 code 0 messages: 13


	dnRouter# show system icmp unreachable statistics ncp 0

	ncp-0:

	Dropped packets with DF flag: 123
	Generated ICMP type 3 code 4 messages: 100
	Generated ICMPv6 type 2 code 0 messages: 23
	
	dnRouter# show system icmp unreachable statistics ncp 5
	
	ncp 5 is not available
	
	
	

.. **Help line:** display icmp unreachable statistics per NCP

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


