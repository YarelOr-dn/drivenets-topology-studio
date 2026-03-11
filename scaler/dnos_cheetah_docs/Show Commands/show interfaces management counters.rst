show interfaces management counters
-----------------------------------

**Minimum user role:** viewer

To display counters for management interfaces:

**Command syntax: show interfaces management counters** [interface-name]

**Command mode:** operational

**Note**

- This command is applicable to the mgmt-ncc interfaces.

- If you do not filter by [interface-name], a summary table is displayed for all management interfaces.

..
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

+----------------+---------------------------------------------------------+---------------------+---------+
| Parameter      | Description                                             | Range               | Default |
+================+=========================================================+=====================+=========+
| interface-name | Optionally filter the counters to a specific interface. | mgmt0, mgmt-ncc-x   | \-      |
+----------------+---------------------------------------------------------+---------------------+---------+

The following counters are displayed:

+---------------------+---------------------------------------------------------------------------------------------------+
| Counter             | Description                                                                                       |
+=====================+===================================================================================================+
| Ethernet counters:                                                                                                      |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx octets           | The number of Ethernet octets received (also in bits/Megabits per second)                         |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx frames           | The number of Ethernet frames received (also in frames/Megaframes per second)                     |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx unicast frames   | The number of received Ethernet unicast frames (also in frames/Megaframes per second)             |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx broadcast frames | The number of received Ethernet broadcast frames (also in frames/Megaframes per second)           |
+---------------------+---------------------------------------------------------------------------------------------------+
| Rx multicast frames | The number of received Ethernet multicast frames (also in frames/Megaframes per second)           |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx octets           | The number of Ethernet octets transmitted (also in bits/Megabits per second)                      |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx frames           | The number of Ethernet frames transmitted (also in frames/Megaframes per second)                  |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx unicast frames   | The number of transmitted Ethernet unicast frames (also in frames/Megaframes per second)          |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx broadcast frames | The number of transmitted Ethernet broadcast frames (also in frames/Megaframes per second)        |
+---------------------+---------------------------------------------------------------------------------------------------+
| Tx multicast frames | The number of transmitted Ethernet multicast frames (also in frames/Megaframes per second)        |
+---------------------+---------------------------------------------------------------------------------------------------+
| Ethernet control                                                                                                        |
+---------------------+---------------------------------------------------------------------------------------------------+
| RX pause frames     | The bumber of received Ethernet pause frames                                                      |
+---------------------+---------------------------------------------------------------------------------------------------+
| TX pause frames     | The number of transmitted Ethernet pause frames                                                   |
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


	dnRouter# show interfaces management counters

	| Interface     | Operational | RX[Mbps] | TX[Mbps] | RX[pkts] | TX[pkts] | RX drops[pkts] | TX drops[pkts] |
	+---------------+-------------+----------+----------+----------+----------+----------------+----------------|
	| mgmt-ncc-0    | up          | 100.5    | 78.12    | 3124     | 10000000 | 123456789      | 3124           |
	| mgmt-ncc-1    | down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| mgmt0         | up          | 3.3      | 0.2      | 11523342 | 12345678 | 123456789      | 3124           |




	dnRouter# show interfaces management counters mgmt-ncc-0

	Interface mgmt-ncc-0:
	Operational state: up
	Ethernet counters:
	        RX octets:                      12345 (0 bps / 0 Mbps)
	        RX frames:                      111   (0 fps / 0 Mfps)
	        RX unicast frames:              111   (0 fps / 0 Mfps)
	        RX broadcast frames:            111   (0 fps / 0 Mfps)
	        RX multicast frames:            111   (0 fps / 0 Mfps)
	        TX octets:                      24690 (0 bps / 0 Mbps)
	        TX frames:                      222   (0 fps / 0 Mfps)
	        TX unicast frames:              222   (0 fps / 0 Mfps)
	        TX broadcast frames:            222   (0 fps / 0 Mfps)
	        TX multicast frames:            222   (0 fps / 0 Mfps)

	Ethernet control:
	        RX pause frames:                12
	        TX pause frames:                3

	Ethernet drop counters:
	        RX errors:                      130
	        RX too short:                   45
	        RX too long:                    5
	        RX FCS errors:                  123
	        RX internal MAC errors:         0
	        RX symbol errors:               68
	        TX errors:                      15

	Bundle Members:

	| Interface    | Operational   | RX[Mbps]   | TX[Mbps]   | RX[pkts]   | TX[pkts]   | RX drops[pkts]   | TX drops[pkts]   |
	|--------------+---------------+------------+------------+------------+------------+------------------+------------------|
	| mgmt-ncc-0/0 | up            | 0          | 0          | 1235       | 2690       | 0                | 0                |
	| mgmt-ncc-0/1 | up            | 0          | 0          | 15         | 690        | 0                | 0                |


	dnRouter# show interfaces counters mgmt0

	Interface mgmt0:
	Operational state: up
	Ethernet counters:
		RX octets:                    	12345 (0 bps / 0 Mbps)
		RX frames:                  	111   (0 fps / 0 Mfps)
		RX unicast frames:              111   (0 fps / 0 Mfps)
		RX broadcast frames:            111   (0 fps / 0 Mfps)
		RX multicast frames:           	111   (0 fps / 0 Mfps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                     	222   (0 fps / 0 Mfps)
		TX unicast frames:             	222   (0 fps / 0 Mfps)
		TX broadcast frames:            222   (0 fps / 0 Mfps)
		TX multicast frames:         	222   (0 fps / 0 Mfps)

	Ethernet errors counters:
		RX errors:                     	130
		RX too short:                	45
		RX too long:                   	5
		RX FCS errors:                	123
		RX internal MAC errors:        	1
		RX symbol errors:              	2
		TX errors:                  	15


.. **Help line:** show management interface counters

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 11.0    | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 16.1    | Added rate to the ethernet unicast, multicast and broadcast counters |
+---------+----------------------------------------------------------------------+
