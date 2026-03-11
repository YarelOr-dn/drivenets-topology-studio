show interfaces control counters
--------------------------------

**Minimum user role:** viewer

To display counters statistics for control interfaces:



**Command syntax: show interfaces control counters** [interface-name]

**Command mode:** operational



**Note**

- If you do not specify an interface-name, a summary table is displayed for all interfaces.

..
	**Internal Note**

	- drop-summary parameter presents summary of all fabric drops in the system as follows:

	- RX drops [pkts] - sum of RX drops on all interfaces per specific component (NCP/NCF/NCC)

	- Ethernet drop counters "RX errors"

	- Ethernet drop counters "RX too short"

	- Access list counters "RX rule dropped"

	- TX drops [cells] - sum of "TX errors" on all interfaces per specific component (NCP/NCF/NCC)

	- A summary table presents the following counters:

	- RX [Mbps] - derived from Ethernet counter "RX octets"

	- TX [Mbps] - derived from Ethernet counter "TX octets"

	- RX [pkts] - is Ethernet counter "RX frames"

	- TX [pkts] - is Ethernet counter "TX frames"

	- RX drops [pkts]

	- Ethernet drop counters "RX errors"

	- Ethernet drop counters "RX too short"

	- Access list counters "RX rule dropped"

	- TX drops [pkts] - is Ethernet drop counters "TX errors"

**Parameter table**

+----------------+----------------------------------------------------------------------+-----------------------------------------------------+---------+
| Parameter      | Description                                                          | Range                                               | Default |
+================+======================================================================+=====================================================+=========+
| interface-name | Optionally filter the displayed information to a specific interface. | ctrl-ncp-x/y ctrl-ncf-x/y ctrl-ncc-x/y ctrl-ncm-x/y | \-      |
+----------------+----------------------------------------------------------------------+-----------------------------------------------------+---------+

The following information is displayed per interface:

+-----------------+-------------------------------------------------------------------------------------+
| Attribute       | Description                                                                         |
+=================+=====================================================================================+
| Interface       | The name of the interface                                                           |
+-----------------+-------------------------------------------------------------------------------------+
| Operational     | The state of the link (up/down)                                                     |
+-----------------+-------------------------------------------------------------------------------------+
| Rx (Mbps)       | The received Megabits per second:                                                   |
|                 | For physical interfaces, the value is derived from the “RX octets” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “RX octets” Forwarding counter    |
+-----------------+-------------------------------------------------------------------------------------+
| Tx (Mbps)       | The transmitted Megabits per second:                                                |
|                 | For physical interfaces, the value is derived from the “TX octets” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “TX octets” Forwarding counter    |
+-----------------+-------------------------------------------------------------------------------------+
| Rx (pkts)       | The received packets:                                                               |
|                 | For physical interfaces, the value is derived from the “RX frames” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “RX packets” Forwarding counter   |
+-----------------+-------------------------------------------------------------------------------------+
| Tx (pkts)       | The transmitted packets:                                                            |
|                 | For physical interfaces, the value is derived from the “TX frames” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “TX packets” Forwarding counter   |
+-----------------+-------------------------------------------------------------------------------------+
| Rx drops (pkts) | The number of received packets that were dropped:                                   |
|                 | For physical interfaces, the value is the sum of the following:                     |
|                 | Forwarding drops summary of logical and sub-IF “Total RX dropped”                   |
|                 | Ethernet “RX errors” drop counters                                                  |
|                 | Ethernet “RX too short” drop counters                                               |
|                 | For sub-interfaces, the value is equal to the “RX drops” Forwarding counter         |
+-----------------+-------------------------------------------------------------------------------------+
| Tx drops (pkts) | The number of transmitted packets that were dropped:                                |
|                 | For physical interfaces, the value is the sum of the following:                     |
|                 | Forwarding drops summary of logical and sub-IF “Total TX dropped”                   |
|                 | Ethernet “TX errors” drop counters                                                  |
|                 | For sub-interfaces, the value is equal to the “TX drops” Forwarding counter         |
+-----------------+-------------------------------------------------------------------------------------+

The following counters are displayed:

+---------------------+---------------------------------------------------------------------------------------------------+
| Counter             | Description                                                                                       |
+=====================+===================================================================================================+
| Ethernet counters:                                                                                                      |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx octets           | The number of Ethernet octets received (also in bits/Megabits per second)                         |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx frames           | The number of Ethernet frames received                                                            |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx unicast frames   | The number of received Ethernet unicast frames                                                    |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx broadcast frames | The number of received Ethernet broadcast frames                                                  |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx multicast frames | he number of received Ethernet multicast frames                                                   |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx octets           | The number of Ethernet octets transmitted (also in bits/Megabits per second)                      |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx frames           | The number of Ethernet frames transmitted                                                         |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx unicast frames   | The number of transmitted Ethernet unicast frames                                                 |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx broadcast frames | The number of transmitted Ethernet broadcast frames                                               |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx multicast frames | The number of transmitted Ethernet multicast frames                                               |
+---------------------+---------------------------------------------------------------------------------------------------+
| Ethernet drop counters:                                                                                                 |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx errors           | The number of RX dropped Ethernet frames according to the ifInErrors counter (RFC2665)            |
+---------------------+---------------------------------------------------------------------------------------------------+
| RX too short        | The number of RX dropped Ethernet frames with a frame size less than 64 bytes                     |
+---------------------+---------------------------------------------------------------------------------------------------+
| RX too long         | The number of RX dropped Ethernet frames with a frame size exceeding MTU on the ingress interface |
+---------------------+---------------------------------------------------------------------------------------------------+
| RX FCS errors       | The number of RX dropped Ethernet frames with FCS errors                                          |
+---------------------+---------------------------------------------------------------------------------------------------+
| TX errors           | The number of TX dropped Ethernet frames according to the ifOutErrors counter (RFC2665)           |
+---------------------+---------------------------------------------------------------------------------------------------+

**Example**
::


	dnRouter# show interfaces control counters

	| Interface     | Operational | RX[Mbps] | TX[Mbps] | RX[pkts] | TX[pkts] | RX drops[pkts] | TX drops[pkts] |
	+---------------+-------------+----------+----------+----------+----------+----------------+----------------|
	| ctrl-ncc-0/0  | up          | 100.5    | 78.12    | 3124     | 10000000 | 123456789      | 3124           |
	| ctrl-ncf-0/0  | down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| ctrl-ncm-A0/0 | up          | 12.9     | 1        | 3124     | 12345678 | 123456789      | 3124           |
	| ctrl-ncp-0/0  | up          | 3.3      | 0.2      | 1152     | 12345678 | 123456789      | 3124           |
	| ice0          | up          | 0        | 0        | 100      | 100      | N/A            | N/A            |


	dnRouter# show interfaces control counters drop-summary

	| Component | RX Drops [pkts]  | TX Drops [pkts]  |
	+-----------+------------------+------------------|
	| ncm-A0    | 0                | 0                |
	| ncm-B0    | 0                | 0                |
	| ncp-0     | 0                | 0                |
	| ncp-1     | 0                | 0                |
	| ncp-2     | 0                | 0                |
	| ncp-3     | 0                | 0                |
	| ncf-0     | 0                | 0                |


	dnRouter# show interfaces control counters ctrl-ncm-A0/0

	Interface ctrl-ncm-A0/0:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		RX unicast frames:              111
		RX broadcast frames:            111
		RX multicast frames:            111
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)
		TX unicast frames:              222
		TX broadcast frames:            222
		TX multicast frames:            222

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX FCS errors:                  123
		TX errors:                      15


	dnRouter# show interfaces control counters ctrl-ncc-0/0

	Interface ctrl-ncc-0/0:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		RX unicast frames:              111
		RX broadcast frames:            111
		RX multicast frames:            111
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)
		TX unicast frames:              222
		TX broadcast frames:            222
		TX multicast frames:            222

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX alignment errors:            1
		RX FCS errors:                  123
		RX symbol errors:               2
		TX errors:                      15


	dnRouter# show interfaces control counters ctrl-ncp-0/0

	Interface ctrl-ncp-0/0:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		RX unicast frames:              111
		RX broadcast frames:            111
		RX multicast frames:            111
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)
		TX unicast frames:              222
		TX broadcast frames:            222
		TX multicast frames:            222

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX alignment errors:            1
		RX FCS errors:                  123
		RX symbol errors:               2
		TX errors:                      15


	dnRouter# show interfaces control counters ctrl-ncf-0/0

	Interface ctrl-ncf-0/0:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		RX unicast frames:              111
		RX broadcast frames:            111
		RX multicast frames:            111
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)
		TX unicast frames:              222
		TX broadcast frames:            222
		TX multicast frames:            222

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX alignment errors:            1
		RX FCS errors:                  123
		RX symbol errors:               2
		TX errors:                      15


	dnRouter# show interfaces control counters ice0

	Interface ice0:
	Operational state: up
	Ethernet counters:
			RX octets:                      12345 (0 bps / 0 Mbps)
			RX frames:                      111   (0 fps / 0 Mfps)
			TX octets:                      24690 (0 bps / 0 Mbps)
			TX frames:                      222   (0 fps / 0 Mfps)

.. **Help line:** show control interface counters

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 19.10   | Added support for ICE interfaces |
+---------+----------------------------------+
