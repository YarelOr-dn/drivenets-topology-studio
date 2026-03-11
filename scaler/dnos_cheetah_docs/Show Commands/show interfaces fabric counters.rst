show interfaces fabric counters
-------------------------------

**Minimum user role:** viewer



This command displays statistics about the fabric interfaces. If you specify an interface name, the output result is filtered to show only the information for the requested interface.

**Command syntax:show interfaces fabric counters** {[interface-name] \| drop-summary}

**Command mode:** operational



**Note**

- This command is applicable to fabric interfaces.

- If you do not filter by [interface-name], a summary table is displayed for all fabric interfaces.

..
	- if interface name is not specified, a summary table is presented for all fabric interfaces

	- drop-summary parameter presents summary of the following counters:

	- "FEC uncorrected errors" on all interface per specific NCP/NCF node

	- "RX CRC errors" on all interface per specific NCP/NCF node (shown also per lane)

	- if interface name is not specified and ncp-id/ncf-id is not specified, a summary table is presented with the following counters:

	- RX [Mbps] - derived from "RX data octets"

	- TX [Mbps] - derived from "TX data octets"

	- RX [cells] - "RX data cells" (shown also per lane)

	- TX [cells] - "TX data cells" (shown also per lane)

	- "RX CRC errors"

	- "FEC uncorrected errors"

**Parameter table**

+----------------+------------------------------------------------------------------------------------+--------------------------------+---------+
| Parameter      | Description                                                                        | Range                          | Default |
+================+====================================================================================+================================+=========+
| interface-name | Optionally filter the counters to a specific interface.                            | -  fab-ncpX-Y/Z/W              | \-      |
|                |                                                                                    | -  fab-ncpX-Y/Z/W/U            |         |
|                |                                                                                    | -  fab-ncfX-Y/Z/W              |         |
|                |                                                                                    | -  fab-ncfX-Y/Z/W/U            |         |
|                |                                                                                    |                                |         |
|                |                                                                                    | X - interface speed            |         |
|                |                                                                                    | Y - NCP/NCF id                 |         |
|                |                                                                                    | Z - slot id                    |         |
|                |                                                                                    | W - port id as shown at the WB |         |
|                |                                                                                    | U - port internal breakout     |         |
+----------------+------------------------------------------------------------------------------------+--------------------------------+---------+
| drop-summary   | Displays a summary of the following counters on all fabric interfaces per NCP/NCF: | \-                             | \-      |
|                | FEC uncorrected errors                                                             |                                |         |
|                | RX CRC errors                                                                      |                                |         |
+----------------+------------------------------------------------------------------------------------+--------------------------------+---------+

The following information is displayed per interface:

+------------------------+-----------------------------------------------------------------------------+
| Attribute              | Description                                                                 |
+========================+=============================================================================+
| Interface              | The name of the interface                                                   |
+------------------------+-----------------------------------------------------------------------------+
| Operational            | The state of the link (up/down)                                             |
+------------------------+-----------------------------------------------------------------------------+
| Rx (Mbps)              | The received Megabits per second:                                           |
|                        | the value is derived from the “RX data octets” Ethernet counter             |
+------------------------+-----------------------------------------------------------------------------+
| Tx (Mbps)              | The transmitted Megabits per second:                                        |
|                        | the value is derived from the “TX data octets” Ethernet counter             |
+------------------------+-----------------------------------------------------------------------------+
| Rx (cells)             | The received data cells                                                     |
+------------------------+-----------------------------------------------------------------------------+
| Tx (cells)             | The transmitted cells                                                       |
+------------------------+-----------------------------------------------------------------------------+
| Rx drops (pkts)        | The number of received packets that were dropped:                           |
|                        | For physical interfaces, the value is the sum of the following:             |
|                        | Forwarding drops summary of logical and sub-IF “Total RX dropped”           |
|                        | Ethernet “RX errors” drop counters                                          |
|                        | Ethernet “RX too short” drop counters                                       |
|                        | For sub-interfaces, the value is equal to the “RX drops” Forwarding counter |
+------------------------+-----------------------------------------------------------------------------+
| Tx drops (pkts)        | The number of transmitted packets that were dropped:                        |
|                        | For physical interfaces, the value is the sum of the following:             |
|                        | Forwarding drops summary of logical and sub-IF “Total TX dropped”           |
|                        | Ethernet “TX errors” drop counters                                          |
|                        | For sub-interfaces, the value is equal to the “TX drops” Forwarding counter |
+------------------------+-----------------------------------------------------------------------------+
| Rx CRC Errors          | The number of received cells with CRC errors                                |
+------------------------+-----------------------------------------------------------------------------+
| FEC Uncorrected Errors | The number of erred code words that were not corrected by the FEC sublayer. |
+------------------------+-----------------------------------------------------------------------------+

The following counters are displayed:

+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| Counter                                | Description                                                                                                     |
+========================================+=================================================================================================================+
| Cell counters:                                                                                                                                           |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| Rx data octets                         | The number of data octets received (also in bits/Megabits per second)                                           |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| RX data cells                          | The number of data cells received (also in cells/Megacells per second)                                          |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| RX control cells                       | The number of control cells received (also in cells/Megacells per second)                                       |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| Rx data octets                         | The number of data octets transmitted (also in bits/Megabits per second)                                        |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| RX data cells                          | The number of data cells transmitted (also in cells/Megacells per second)                                       |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| RX control cells                       | The number of control cells transmitted (also in cells/Megacells per second)                                    |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| Cell errors counters:                                                                                                                                    |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| RX CRC errors                          | The number of received cells with CRC errors                                                                    |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| RX dropped retransmitted control cells | The number of control cells that were dropped after retransmission                                              |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| FEC counters:                                                                                                                                            |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| FEC Corrected Errors                   | The number of erred code words that were corrected by the FEC sublayer                                          |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| FEC Uncorrected Errors                 | The number of erred code words that were not corrected by the FEC sublayer                                      |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| FEC Bit Errors                         | The number of received erred bits                                                                               |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
| FEC Symbol Errors                      | The number of received symbol errors                                                                            |
+----------------------------------------+-----------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show interfaces fabric counters

	| Interface              | Operational | RX[Mbps]| TX[Mbps]| RX[cells]| TX[cells]| RX CRC Errors | FEC uncorrected errors |
	+------------------------+-------------+---------+---------+----------+----------+---------------+------------------------|
	| fab-ncf400-0/0/0       | up          | 100.5   | 78.12   | 3124     | 10000000 | 123456789     | 0                      |
	| fab-ncp400-0/0/0       | down        | 0       | 0       | 0        | 0        | 0             | 0                      |
	| fab-ncp400-1/0/0       | up          | 12.9    | 1       | 3124     | 12345678 | 123456789     | 0                      |
	| fab-ncp400-2/0/0/0     | up          | 3.3     | 0.2     | 1152     | 12345678 | 123456789     | 0                      |
	| fab-ncp400-2/0/0/1     | up          | 3.2     | 0.2     | 152      | 123      | 12            | 0                      |
	| fab-ncp400-2/0/1       | up          | 3.3     | 0.2     | 1152     | 12345678 | 123456789     | 0                      |


	dnRouter# show interfaces fabric counters drop-summary

	| Component | RX CRC Errors  | FEC uncorrected errors |
	+-----------+----------------+------------------------|
	| ncp-0     | 0              | 0                      |
	| ncp-1     | 0              | 0                      |
	| ncp-2     | 0              | 0                      |
	| ncp-3     | 0              | 0                      |
	| ncf-0     | 0              | 0                      |


	dnRouter# show interfaces fabric counters fab-ncp400-0/0/0

	Interface fab-ncp400-0/0/0:
	Operational state: up
	Cell counters:
		RX data octets: 			12345 (0 bps / 0 Mbps)
		RX data cells:				111   (0 cps / 0 Mcps)
		RX control cells:			111   (0 cps / 0 Mcps)
		TX data octets:				24690 (0 bps / 0 Mbps)
		TX data cells:				222   (0 cps / 0 Mcps)
		TX control cells:			222   (0 cps / 0 Mcps)
	
	Cell errors counters:
		RX CRC errors:				130
		RX dropped retransmitted
			Control cells:			45

	FEC counters:
		FEC corrected errors:			5
		FEC uncorrected errors:			5
		FEC bit errors:				5
		FEC symbol errors:			5

	Fabric lane counters:

	| Lane id       | RX [cells]  | TX [cells]  | RX CRC errors | FEC corrected errors | FEC uncorreected errors | FEC bit errors | FEC symbol errors |
	|---------------+-------------+-------------+---------------+----------------------+-------------------------+----------------+-------------------|
	| 0 (sfi0/0)    | 100         | 100         | 100           | 1                    | 1                       | 1              | 1                 |
	| 1 (sfi0/1)    | 100         | 100         | 10            | 1                    | 1                       | 1              | 1                 |
	| 2 (sfi0/2)    | 100         | 100         | 10            | 1                    | 1                       | 1              | 1                 |
	| 3 (sfi0/3)    | 100         | 100         | 10            | 1                    | 1                       | 1              | 1                 |
	| 4 (sfi0/4)    | 100         | 100         | 0             | 1                    | 1                       | 1              | 1                 |
	| 5 (sfi0/5)    | 100         | 100         | 0             | 0                    | 0                       | 0              | 0                 |
	| 6 (sfi0/6)    | 100         | 100         | 0             | 0                    | 0                       | 0              | 0                 |
	| 7 (sfi0/7)    | 100         | 100         | 0             | 0                    | 0                       | 0              | 0                 |

	dnRouter# show interfaces fabric counters fab-ncf400-0/0/0

	Interface fab-ncf400-0/0/0:
	Operational state: up
	Cell counters:
		RX data octets: 			12345 (0 bps / 0 Mbps)
		RX data cells:				111   (0 cps / 0 Mcps)
		RX control cells:			111   (0 cps / 0 Mcps)
		TX data octets:				24690 (0 bps / 0 Mbps)
		TX data cells:				222   (0 cps / 0 Mcps)
		TX control cells:			222   (0 cps / 0 Mcps)
	
	Cell errors counters:
		RX CRC errors:				130
		RX Dropped retransmitted
			Control cells:			45

	FEC counters:
		FEC corrected errors:			5
		FEC uncorrected errors:			5
		FEC bit errors:				5
		FEC symbol errors:			5

	Fabric lane counters:

	| Lane id       | RX [cells]  | TX [cells]  | RX CRC errors | FEC corrected errors | FEC uncorreected errors | FEC bit errors | FEC symbol errors |
	|---------------+-------------+-------------+---------------+----------------------+-------------------------+----------------+-------------------|
	| 0 (sfi0/0)    | 100         | 100         | 100           | 1                    | 1                       | 1              | 1                 |
	| 1 (sfi0/1)    | 100         | 100         | 10            | 1                    | 1                       | 1              | 1                 |
	| 2 (sfi0/2)    | 100         | 100         | 10            | 1                    | 1                       | 1              | 1                 |
	| 3 (sfi0/3)    | 100         | 100         | 10            | 1                    | 1                       | 1              | 1                 |
	| 4 (sfi0/4)    | 100         | 100         | 0             | 1                    | 1                       | 1              | 1                 |
	| 5 (sfi0/5)    | 100         | 100         | 0             | 0                    | 0                       | 0              | 0                 |
	| 6 (sfi0/6)    | 100         | 100         | 0             | 0                    | 0                       | 0              | 0                 |
	| 7 (sfi0/7)    | 100         | 100         | 0             | 0                    | 0                       | 0              | 0                 |


.. **Help line:** show fabric interface counters

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.0    | Command introduced                                 |
+---------+----------------------------------------------------+
| 11.2    | Added fabric lane counters                         |
+---------+----------------------------------------------------+
| 16.2    | Added per fabric lane FEC error counters           |
+---------+----------------------------------------------------+
