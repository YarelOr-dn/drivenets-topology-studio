show interfaces counters packet-length
--------------------------------------

**Minimum user role:** viewer

Packet length statistics provides the user with ingress & egress packet counters per packet length for each interface. To display interface counters for a specific packet length, use the following command. You can filter the display for a specific interface or a specific NCP.

**Command syntax: show interfaces counters packet-length** [interface-name]

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Bundle

- If you do not specify an interface-name, information from all interfaces will be displayed.

**Parameter table**

+----------------+---------------------------------------------------------+----------------------------------+
| Parameter      | Description                                             | Range                            |
+================+=========================================================+==================================+
| interface-name | Optionally filter the counters to a specific interface. | ge<interface speed>-<A>/<B>/<C>  |
|                |                                                         |                                  |
|                |                                                         | bundle-<bundle id>               |
+----------------+---------------------------------------------------------+----------------------------------+

The following is the counter displayed per interface.

+----------------------------+-------------------------------------------------------------------------------------+
| Counter                    | Description                                                                         |
+============================+=====================================================================================+
| RX 64 bytes packets        | The number of 64 byte packets received.                                             |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 64 bytes packets        | The number of 64 byte packets transmitted.                                          |
+----------------------------+-------------------------------------------------------------------------------------+
| RX 65-127 bytes packets    | The number of packets received which are between 65 and 127 bytes in size.          |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 65-127 bytes packets    | The number of packets transmitted which are between 65 and 127 bytes in size.       |
+----------------------------+-------------------------------------------------------------------------------------+
| RX 128-255 bytes packets   | The number of packets received which are between 128 and 255 bytes in size.         |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 128-255 bytes packets   | The number of packets transmitted which are between 128 and 255 bytes in size.      |
+----------------------------+-------------------------------------------------------------------------------------+
| RX 256-511 bytes packets   | The number of packets received which are between 256 and 511 bytes in size.         |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 256-511 bytes packets   | The number of packets transmitted which are between 256 and 511 bytes in size.      |
+----------------------------+-------------------------------------------------------------------------------------+
| RX 512-1023 bytes packets  | The number of packets received which are between 512 and 1023 bytes in size.        |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 512-1023 bytes packets  | The number of packets transmitted which are between 512 and 1023 bytes in size.     |
+----------------------------+-------------------------------------------------------------------------------------+
| RX 1024-1518 bytes packets | The number of packets received which are between 1024 and 1518 bytes in size.       |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 1024-1518 bytes packets | The number of packets transmitted which are between 1024 and 1518 bytes in size.    |
+----------------------------+-------------------------------------------------------------------------------------+
| RX 1519-max bytes packets  | The number of packets received which are between 1024 and maximum bytes in size.    |
+----------------------------+-------------------------------------------------------------------------------------+
| TX 1519-max bytes packets  | The number of packets transmitted which are between 1024 and maximum bytes in size. |
+----------------------------+-------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show interfaces counters packet-length
	| Interface   | RX/TX       | RX/TX      | RX/TX           | RX/TX       | RX/TX        | RX/TX         | RX/TX         |
	|             | 64B         | 65B-127B   | 128B-255B       | 256B-511B   | 512B-1023B   | 1024B-1518B   | 1519B-max     |
	|             | [pkts]      | [pkts]     | [pkts]          | [pkts]      | [pkts]       | [pkts]        | [pkts]        |
	|-------------+-------------+------------+-----------------+-------------+--------------+---------------+---------------|
	| bundle-3    | 1234/1571   | 1234/9706  | 123456789/42415 | 1234/324    | 1234/324     | 1571/1234     | 527985/123094 |
	| ge100-2/1/1 | 1234/1571   | 1234/9706  | 123456789/42415 | 1234/324    | 1234/324     | 1571/1234     | 527985/123094 |
	| ge100-1/1/1 | 1234/1571   | 1234/9706  | 123456789/42415 | 1234/324    | 1234/324     | 1571/1234     | 527985/123094 |


	dnRouter# show interfaces counters packet-length bundle-3
	| Interface   | RX/TX       | RX/TX      | RX/TX           | RX/TX       | RX/TX        | RX/TX         | RX/TX         |
	|             | 64B         | 65B-127B   | 128B-255B       | 256B-511B   | 512B-1023B   | 1024B-1518B   | 1519B-max     |
	|             | [pkts]      | [pkts]     | [pkts]          | [pkts]      | [pkts]       | [pkts]        | [pkts]        |
	|-------------+-------------+------------+-----------------+-------------+--------------+---------------+---------------|
	| bundle-3    | 1234/1571   | 1234/9706  | 123456789/42415 | 1234/324    | 1234/324     | 1571/1234     | 527985/123094 |





.. **Help line:** show interfaces packet length counters

**Command History**

+---------+-----------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                      |
+=========+===================================================================================================================================+
| 5.1.0   | Command introduced                                                                                                                |
+---------+-----------------------------------------------------------------------------------------------------------------------------------+
| 6.0     | Updated the command syntax show interfaces packet-length counters to show interfaces counters packet-length and updated examples. |
+---------+-----------------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Added mgmt0 and mgmt-ncc interfaces                                                                                               |
+---------+-----------------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Added NCP filter                                                                                                                  |
+---------+-----------------------------------------------------------------------------------------------------------------------------------+