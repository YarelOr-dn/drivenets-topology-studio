show lldp counters
-------------------

**Minimum user role:** viewer

To display LLDP counters per interface:



**Command syntax: show lldp counters** [interface-name]

**Command mode:** operational




**Parameter table**

+----------------+------------------------------------------------------------------+---------------------------------+
| Parameter      | Description                                                      | Range                           |
+================+==================================================================+=================================+
| interface-name | Filters the information to display only the specified interface. | ge<interface speed>-<A>/<B>/<C> |
+----------------+------------------------------------------------------------------+---------------------------------+

The following counters are displayed per interface:

+---------------------+----------------------------------------------------------+
| Counter             | Description                                              |
+=====================+==========================================================+
| LLDP PDU TX         | The number of outgoing LLDP PDU packets                  |
+---------------------+----------------------------------------------------------+
| LLDP PDU RX         | The number of incoming packets                           |
+---------------------+----------------------------------------------------------+
| Invalid RX LLDP PDU | The number of incoming discarded LLDP PDU packets        |
+---------------------+----------------------------------------------------------+
| Discarded           | The total number of received TLVs that were discarded    |
+---------------------+----------------------------------------------------------+
| Unrecognized        | The total number of received TLVs that were unrecognized |
+---------------------+----------------------------------------------------------+
| Inserted            | The number of new neighbors created on the port          |
+---------------------+----------------------------------------------------------+
| Deleted             | The number of neighbor age outs on the port              |
+---------------------+----------------------------------------------------------+

**Example**
::

	dnRouter# show lldp counters

	| Interface    | LLDP PDU RX | LLDP PDU TX | Invalid RX LLDP PDU | Discarded | Unrecognized | Inserted | Deleted |
	|              | [pkts]      | [pkts]      | [pkts]              | [tlvs]    | [tlvs]       |          |         |
	|--------------+-------------+-------------+---------------------+-----------+--------------+----------+---------|
	| ge100-1/1/1  | 12345       | 1111        | 0                   | 0         | 1            | 0        |0        |
	| ge100-1/2/1  | 12345       | 1111        | 0                   | 0         | 1            | 0        |0        |
	| ge100-3/2/1  | 12345       | 4567        | 0                   | 0         | 1            | 0        |0        |
	| ge100-4/2/1  | 12345       | 1111        | 0                   | 0         | 1            | 0        |0        |


	dnRouter# show lldp counters ge100-1/1/1

	| Interface    | LLDP PDU RX | LLDP PDU TX | Invalid RX LLDP PDU | Discarded | Unrecognized | Inserted | Deleted |
	|              | [pkts]      | [pkts]      | [pkts]              | [tlvs]    | [tlvs]       |          |         |
	|--------------+-------------+-------------+---------------------+-----------+--------------+----------+---------|
	| ge100-1/1/1  | 12345       | 1111        | 0                   | 0         | 1            | 0        |0        |


.. **Help line:** show lldp counter list

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Command supported             |
+---------+-------------------------------+
