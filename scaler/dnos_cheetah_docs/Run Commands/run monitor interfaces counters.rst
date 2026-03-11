run monitor interfaces counters
-------------------------------

**Minimum user role:** viewer

This command displays the interface counters similarly to the show interfaces counters command, but with periodic updates allowing to monitor the counters. The displayed information is updated every 3 seconds.

**Command syntax: run monitor interfaces counters** [interface-name-list]

**Command mode:** operation

.. **Note**

	- This command performs "show interfaces counters" with a "watch" interval of 3 sec

	- Take into consideration cases of more than 3 screen output (More than X lines)

	- If list of interfaces is specified, table will be presented per specific list of interfaces only

**Parameter table**

+---------------------+-----------------------------------------------------------------+-------------------------------------------------------+
| Parameter           | Description                                                     | Range                                                 |
+=====================+=================================================================+=======================================================+
| interface-name-list | Filter the display to a list of interfaces separated by a space | -  ge<interface speed>-<A>/<B>/<C>                    |
|                     |                                                                 |                                                       |
|                     |                                                                 | -  ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |
|                     |                                                                 |                                                       |
|                     |                                                                 | -  bundle-<bundle id>                                 |
|                     |                                                                 |                                                       |
|                     |                                                                 | -  bundle-<bundle id>.<sub-interface id>              |
|                     |                                                                 |                                                       |
|                     |                                                                 | -  mgmt0                                              |
+---------------------+-----------------------------------------------------------------+-------------------------------------------------------+

The following information is displayed per interface:

+-------------+-------------------------------------------------------------------------------------+
| Attribute   | Description                                                                         |
+=============+=====================================================================================+
| Interface   | The name of the interface                                                           |
+-------------+-------------------------------------------------------------------------------------+
| Operational | The state of the link (up/down)                                                     |
+-------------+-------------------------------------------------------------------------------------+
| Rx (Mbps)   | The received Megabits per second:                                                   |
|             | For physical interfaces, the value is derived from the “RX octets” Ethernet counter |
|             | For sub-interfaces, the value is derived from the “RX octets” Forwarding counter    |
+-------------+-------------------------------------------------------------------------------------+
| Tx (Mbps)   | The transmitted Megabits per second:                                                |
|             | For physical interfaces, the value is derived from the “TX octets” Ethernet counter |
|             | For sub-interfaces, the value is derived from the “TX octets” Forwarding counter    |
+-------------+-------------------------------------------------------------------------------------+
| Rx (pkts)   | The received packets:                                                               |
|             | For physical interfaces, the value is derived from the “RX frames” Ethernet counter |
|             | For sub-interfaces, the value is derived from the “RX packets” Forwarding counter   |
+-------------+-------------------------------------------------------------------------------------+
| Tx (pkts)   | The transmitted packets:                                                            |
|             | For physical interfaces, the value is derived from the “TX frames” Ethernet counter |
|             | For sub-interfaces, the value is derived from the “TX packets” Forwarding counter   |
+-------------+-------------------------------------------------------------------------------------+

**Example**
::


	dnRouter# run monitor interfaces counters
	| Interface    | Operational | RX[Mbps] | TX[Mbps]  | RX[pps] | TX[pps] | RX[pkts]  | TX[pkts] |
	+--------------+-------------+----------+-----------+---------+---------+-----------+----------|
	| ge100-1/1/1  | up          |        1 |         1 |    3124 | 10000000| 123456789 | 3124     |
	| bundle-2     | up          |        1 |         1 |    3124 | 12345678| 123456789 | 3124     |
	| bundle-2.100 | down        |        0 |         0 |       0 |        0| 123456789 | 3124     |


	dnRouter# run monitor interfaces counters bundle-2 bundle-2.100
	| Interface    | Operational | RX[Mbps] | TX[Mbps]  | RX[pps] | TX[pps] | RX[pkts]  | TX[pkts] |
	+--------------+-------------+----------+-----------+---------+---------+-----------+----------|
	| bundle-2     | up          |        1 |         1 |    3124 | 12345678| 123456789 | 3124     |
	| bundle-2.100 | down        |        0 |         0 |       0 |        0| 123456789 | 3124     |



.. **Help line:** monitor interface counters

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 5.1.0   | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 11.2    | Added option to filter the monitoring for a list of interfaces |
+---------+----------------------------------------------------------------+
